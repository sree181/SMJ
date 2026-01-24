#!/usr/bin/env python3
"""
Batch process all papers in 2025-2029 folder with complete extraction pipeline
Includes progress tracking, validation, and Neo4j persistence
"""

from redesigned_methodology_extractor import RedesignedMethodologyProcessor, RedesignedNeo4jIngester
from pathlib import Path
import json
import sys
import time
from datetime import datetime
from collections import defaultdict
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, paper_dir: Path):
        self.paper_dir = paper_dir
        load_dotenv()
        
        # Initialize Neo4j connection for relationship computation
        neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://fe285b91.databases.neo4j.io")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.processor = RedesignedMethodologyProcessor()
        
        # Initialize embedding model for paper embeddings
        logger.info("Loading embedding model for paper embeddings...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✓ Embedding model loaded")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load embedding model: {e}. Embeddings will be skipped.")
            self.embedding_model = None
        
        self.stats = {
            "total_papers": 0,
            "processed": 0,
            "failed": 0,
            "extraction_counts": defaultdict(int),
            "relationship_counts": defaultdict(int),
            "errors": []
        }
        self.progress_file = Path("batch_extraction_progress.json")
        self.results_file = Path("batch_extraction_results.json")
        
    def load_progress(self):
        """Load previous progress if exists"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"processed_papers": [], "failed_papers": []}
    
    def save_progress(self, progress_data):
        """Save current progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def validate_extraction(self, result: dict, paper_id: str) -> dict:
        """Validate extraction quality"""
        validation = {
            "paper_id": paper_id,
            "timestamp": datetime.now().isoformat(),
            "valid": True,
            "issues": []
        }
        
        # Check paper metadata
        paper_meta = result.get("paper_metadata", {})
        if not paper_meta.get("title"):
            validation["issues"].append("Missing title")
            validation["valid"] = False
        if not paper_meta.get("abstract"):
            validation["issues"].append("Missing abstract")
        
        # Check extraction counts
        counts = {
            "authors": len(result.get("authors", [])),
            "methods": len(result.get("methods", [])),
            "theories": len(result.get("theories", [])),
            "research_questions": len(result.get("research_questions", [])),
            "variables": len(result.get("variables", [])),
            "findings": len(result.get("findings", [])),
            "contributions": len(result.get("contributions", [])),
            "software": len(result.get("software", [])),
            "datasets": len(result.get("datasets", []))
        }
        
        validation["counts"] = counts
        
        # Warn if very few extractions
        if counts["methods"] == 0:
            validation["issues"].append("No methods extracted")
        if counts["theories"] == 0:
            validation["issues"].append("No theories extracted")
        if counts["research_questions"] == 0:
            validation["issues"].append("No research questions extracted")
        
        return validation
    
    def compute_paper_relationships(self, paper_id: str, paper_year: int = None):
        """
        Compute Phase 1 relationships after paper is ingested:
        - USES_SAME_THEORY
        - USES_SAME_METHOD
        - USES_SAME_VARIABLES
        - TEMPORAL_SEQUENCE
        """
        with self.neo4j_driver.session() as session:
            # Get paper's theories, methods, and variables
            theories = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_THEORY {role: "primary"}]->(t:Theory)
                RETURN t.name as theory_name
            """, paper_id=paper_id).data()
            
            methods = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_METHOD]->(m:Method)
                RETURN m.name as method_name, m.type as method_type
            """, paper_id=paper_id).data()
            
            variables = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_VARIABLE]->(v:Variable)
                RETURN v.variable_name as variable_name
            """, paper_id=paper_id).data()
            
            # Get paper year if not provided
            if paper_year is None:
                paper_data = session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})
                    RETURN p.publication_year as year
                """, paper_id=paper_id).single()
                if paper_data:
                    paper_year = paper_data.get("year", 0)
            
            relationship_count = 0
            
            # 1. USES_SAME_THEORY: Find papers using same primary theories
            if theories:
                theory_names = [t["theory_name"] for t in theories]
                for theory_name in theory_names:
                    result = session.run("""
                        MATCH (p1:Paper {paper_id: $paper_id})-[r1:USES_THEORY {role: "primary"}]->(t:Theory {name: $theory_name})
                        MATCH (p2:Paper)-[r2:USES_THEORY {role: "primary"}]->(t)
                        WHERE p1 <> p2
                        AND NOT EXISTS((p1)-[:USES_SAME_THEORY]->(p2))
                        WITH p1, p2, t, 
                             abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                        MERGE (p1)-[rel:USES_SAME_THEORY {
                            theory_name: $theory_name,
                            temporal_gap: temporal_gap
                        }]->(p2)
                        RETURN count(rel) as count
                    """, paper_id=paper_id, theory_name=theory_name).single()
                    if result:
                        relationship_count += result["count"]
                        self.stats["relationship_counts"]["USES_SAME_THEORY"] += result["count"]
            
            # 2. USES_SAME_METHOD: Find papers using same methods
            if methods:
                for method in methods:
                    method_name = method["method_name"]
                    result = session.run("""
                        MATCH (p1:Paper {paper_id: $paper_id})-[r1:USES_METHOD]->(m:Method {name: $method_name})
                        MATCH (p2:Paper)-[r2:USES_METHOD]->(m)
                        WHERE p1 <> p2
                        AND NOT EXISTS((p1)-[:USES_SAME_METHOD]->(p2))
                        WITH p1, p2, m,
                             abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                        MERGE (p1)-[rel:USES_SAME_METHOD {
                            method_name: $method_name,
                            temporal_gap: temporal_gap
                        }]->(p2)
                        RETURN count(rel) as count
                    """, paper_id=paper_id, method_name=method_name).single()
                    if result:
                        relationship_count += result["count"]
                        self.stats["relationship_counts"]["USES_SAME_METHOD"] += result["count"]
            
            # 3. USES_SAME_VARIABLES: Find papers using same variables (if 2+ shared)
            if len(variables) >= 2:
                variable_names = [v["variable_name"] for v in variables]
                result = session.run("""
                    MATCH (p1:Paper {paper_id: $paper_id})-[r1:USES_VARIABLE]->(v:Variable)
                    WHERE v.variable_name IN $variable_names
                    WITH p1, collect(DISTINCT v.variable_name) as p1_vars
                    
                    MATCH (p2:Paper)-[r2:USES_VARIABLE]->(v2:Variable)
                    WHERE v2.variable_name IN $variable_names
                    AND p1 <> p2
                    WITH p1, p1_vars, p2, collect(DISTINCT v2.variable_name) as p2_vars
                    
                    WITH p1, p2, p1_vars, p2_vars,
                         [v IN p1_vars WHERE v IN p2_vars] as shared_vars
                    WHERE size(shared_vars) >= 2
                    AND NOT EXISTS((p1)-[:USES_SAME_VARIABLES]->(p2))
                    
                    MERGE (p1)-[rel:USES_SAME_VARIABLES {
                        variable_overlap: size(shared_vars),
                        variable_types: shared_vars,
                        temporal_gap: abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0))
                    }]->(p2)
                    RETURN count(rel) as count
                """, paper_id=paper_id, variable_names=variable_names).single()
                if result:
                    relationship_count += result["count"]
                    self.stats["relationship_counts"]["USES_SAME_VARIABLES"] += result["count"]
            
            # 4. TEMPORAL_SEQUENCE: Create temporal relationships with papers in same topic area
            if paper_year and paper_year > 0:
                # Find papers with similar topics (share theories or methods) within 5 years
                result = session.run("""
                    MATCH (p1:Paper {paper_id: $paper_id})
                    OPTIONAL MATCH (p1)-[:USES_THEORY {role: "primary"}]->(t:Theory)<-[:USES_THEORY {role: "primary"}]-(p2:Paper)
                    WHERE p1 <> p2
                    AND p2.publication_year IS NOT NULL
                    AND abs(p1.publication_year - p2.publication_year) <= 5
                    AND NOT EXISTS((p1)-[:TEMPORAL_SEQUENCE]->(p2))
                    
                    WITH p1, p2, 
                         CASE 
                           WHEN p1.publication_year < p2.publication_year THEN p2.publication_year - p1.publication_year
                           ELSE p1.publication_year - p2.publication_year
                         END as time_gap,
                         CASE 
                           WHEN p1.publication_year < p2.publication_year THEN "before"
                           ELSE "after"
                         END as sequence
                    
                    WHERE time_gap > 0
                    MERGE (p1)-[rel:TEMPORAL_SEQUENCE {
                        time_gap: time_gap,
                        sequence: sequence,
                        context: "same_theory"
                    }]->(p2)
                    RETURN count(rel) as count
                """, paper_id=paper_id, paper_year=paper_year).single()
                if result:
                    relationship_count += result["count"]
                    self.stats["relationship_counts"]["TEMPORAL_SEQUENCE"] += result["count"]
            
            return relationship_count
    
    def _generate_paper_embedding(self, paper_id: str, result: dict):
        """Generate and store embedding for a paper"""
        if not self.embedding_model:
            return
        
        try:
            # Get paper text for embedding
            paper_meta = result.get("paper_metadata", {})
            title = paper_meta.get("title", "") or ""
            abstract = paper_meta.get("abstract", "") or ""
            
            # Combine title and abstract (limit to 3000 chars for speed)
            paper_text = f"{title}. {abstract}"[:3000]
            
            if not paper_text.strip():
                logger.warning(f"   ⚠️  No text for embedding: {paper_id}")
                return
            
            # Generate embedding
            embedding = self.embedding_model.encode(paper_text, convert_to_numpy=True)
            embedding_list = embedding.tolist()
            
            # Store in Neo4j
            with self.neo4j_driver.session() as session:
                session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})
                    SET p.embedding = $embedding,
                        p.embedding_model = 'all-MiniLM-L6-v2',
                        p.embedding_dim = 384
                """, paper_id=paper_id, embedding=embedding_list)
            
            logger.info(f"   ✓ Embedding generated for {paper_id}")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Failed to generate embedding for {paper_id}: {str(e)[:100]}")
    
    def process_paper(self, pdf_path: Path, progress_data: dict) -> dict:
        """Process a single paper"""
        paper_id = pdf_path.stem
        
        # Skip if already processed
        if paper_id in progress_data["processed_papers"]:
            logger.info(f"⏭️  Skipping {paper_id} (already processed)")
            return {"status": "skipped", "paper_id": paper_id}
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {paper_id}")
        logger.info(f"{'='*70}")
        
        start_time = time.time()
        
        try:
            # Retry logic for paper processing (handles Neo4j connection issues)
            max_retries = 3
            retry_delay = 5
            result = None
            
            for attempt in range(max_retries):
                try:
                    result = self.processor.process_paper(pdf_path)
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if "routing information" in error_str or "connection" in error_str or "timeout" in error_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"   ⚠️  Neo4j connection issue (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    # If not a connection error or max retries reached, re-raise
                    raise
            
            if result is None:
                raise Exception("Failed to process paper after retries")
            
            # Validate extraction
            validation = self.validate_extraction(result, paper_id)
            
            # Update stats
            self.stats["processed"] += 1
            for key, count in validation["counts"].items():
                self.stats["extraction_counts"][key] += count
            
            processing_time = time.time() - start_time
            
            # Log results
            logger.info(f"✅ Successfully processed {paper_id}")
            logger.info(f"   Processing time: {processing_time:.1f}s")
            logger.info(f"   Methods: {validation['counts']['methods']}")
            logger.info(f"   Theories: {validation['counts']['theories']}")
            logger.info(f"   Research Questions: {validation['counts']['research_questions']}")
            logger.info(f"   Variables: {validation['counts']['variables']}")
            logger.info(f"   Findings: {validation['counts']['findings']}")
            logger.info(f"   Contributions: {validation['counts']['contributions']}")
            logger.info(f"   Software: {validation['counts']['software']}")
            logger.info(f"   Datasets: {validation['counts']['datasets']}")
            
            if validation["issues"]:
                logger.warning(f"   ⚠️  Issues: {', '.join(validation['issues'])}")
            
            # Compute paper-to-paper relationships (with retry)
            logger.info(f"   Computing relationships...")
            paper_meta = result.get("paper_metadata", {})
            paper_year = paper_meta.get("publication_year")
            
            try:
                relationship_count = self.compute_paper_relationships(paper_id, paper_year)
                if relationship_count > 0:
                    logger.info(f"   ✓ Created {relationship_count} relationships")
            except Exception as e:
                error_str = str(e).lower()
                if "routing information" in error_str or "connection" in error_str:
                    logger.warning(f"   ⚠️  Relationship computation failed (connection issue), will retry later")
                else:
                    logger.warning(f"   ⚠️  Relationship computation failed: {str(e)[:100]}")
            
            # Generate and store paper embedding
            if self.embedding_model:
                try:
                    self._generate_paper_embedding(paper_id, result)
                except Exception as e:
                    logger.warning(f"   ⚠️  Embedding generation failed: {str(e)[:100]}")
            
            # Update progress
            progress_data["processed_papers"].append(paper_id)
            self.save_progress(progress_data)
            
            return {
                "status": "success",
                "paper_id": paper_id,
                "processing_time": processing_time,
                "validation": validation,
                "result": result
            }
            
        except Exception as e:
            self.stats["failed"] += 1
            error_msg = f"Failed to process {paper_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.stats["errors"].append({
                "paper_id": paper_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            # Update progress
            progress_data["failed_papers"].append(paper_id)
            self.save_progress(progress_data)
            
            return {
                "status": "failed",
                "paper_id": paper_id,
                "error": str(e)
            }
    
    def print_summary(self):
        """Print processing summary"""
        logger.info(f"\n{'='*70}")
        logger.info("BATCH PROCESSING SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total papers: {self.stats['total_papers']}")
        logger.info(f"✅ Processed: {self.stats['processed']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"⏭️  Skipped: {self.stats['total_papers'] - self.stats['processed'] - self.stats['failed']}")
        
        logger.info(f"\n📊 Extraction Totals:")
        for key, count in sorted(self.stats["extraction_counts"].items()):
            avg = count / self.stats["processed"] if self.stats["processed"] > 0 else 0
            logger.info(f"   {key.capitalize()}: {count} (avg: {avg:.1f} per paper)")
        
        logger.info(f"\n🔗 Relationship Totals:")
        for key, count in sorted(self.stats["relationship_counts"].items()):
            logger.info(f"   {key}: {count}")
        
        if self.stats["errors"]:
            logger.info(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10
                logger.info(f"   - {error['paper_id']}: {error['error'][:100]}")
    
    def save_results(self, all_results: list):
        """Save all results to JSON"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "results": all_results
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"\n💾 Results saved to: {self.results_file}")
    
    def run(self):
        """Run batch processing"""
        # Get all PDF files
        pdf_files = sorted(list(self.paper_dir.glob("*.pdf")))
        self.stats["total_papers"] = len(pdf_files)
        
        if not pdf_files:
            logger.error(f"No PDF files found in {self.paper_dir}")
            return
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Starting batch processing")
        logger.info(f"Directory: {self.paper_dir}")
        logger.info(f"Total papers: {self.stats['total_papers']}")
        logger.info(f"{'='*70}\n")
        
        # Load previous progress
        progress_data = self.load_progress()
        logger.info(f"📋 Loaded progress: {len(progress_data['processed_papers'])} already processed")
        
        all_results = []
        start_time = time.time()
        last_progress_time = time.time()
        
        for i, pdf_path in enumerate(pdf_files, 1):
            # Print progress every 5 papers or every 5 minutes
            elapsed = time.time() - last_progress_time
            if i % 5 == 0 or elapsed > 300:
                elapsed_total = time.time() - start_time
                remaining = (elapsed_total / i) * (self.stats["total_papers"] - i) if i > 0 else 0
                logger.info(f"\n📊 Progress: {i}/{self.stats['total_papers']} papers")
                logger.info(f"   Processed: {self.stats['processed']}, Failed: {self.stats['failed']}")
                logger.info(f"   Elapsed: {elapsed_total/60:.1f} min, Est. remaining: {remaining/60:.1f} min")
                last_progress_time = time.time()
            
            # Process paper
            result = self.process_paper(pdf_path, progress_data)
            all_results.append(result)
        
        # Final summary
        total_time = time.time() - start_time
        logger.info(f"\n{'='*70}")
        logger.info(f"Batch processing completed in {total_time/60:.1f} minutes")
        logger.info(f"{'='*70}")
        
        self.print_summary()
        self.save_results(all_results)
        
        logger.info(f"\n✅ Batch processing complete!")
        logger.info(f"   Progress file: {self.progress_file}")
        logger.info(f"   Results file: {self.results_file}")
        logger.info(f"   Log file: batch_extraction.log")
        
        # Close Neo4j connection
        self.neo4j_driver.close()

def main():
    if len(sys.argv) > 1:
        paper_dir = Path(sys.argv[1])
    else:
        paper_dir = Path("2025-2029")
    
    if not paper_dir.exists():
        logger.error(f"Directory not found: {paper_dir}")
        sys.exit(1)
    
    processor = BatchProcessor(paper_dir)
    processor.run()

if __name__ == "__main__":
    main()

