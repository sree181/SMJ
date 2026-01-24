#!/usr/bin/env python3
"""
Run Pipeline for All Missing Fields
Creates a temporary directory with PDFs for papers missing data and runs the pipeline
"""

import os
import logging
import asyncio
import shutil
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
from high_performance_pipeline import HighPerformancePipeline

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MissingFieldsPipelineRunner:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.temp_dir = Path("temp_missing_fields_pdfs")
    
    def find_papers_missing_data(self) -> Set[str]:
        """Find all papers with missing data"""
        papers_to_process = set()
        
        logger.info("Finding papers with missing data...")
        
        with self.driver.session() as session:
            # Papers missing titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing titles: {count}")
            
            # Papers missing authors
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT EXISTS((p)<-[:AUTHORED_BY]-())
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing authors: {count}")
            
            # Papers missing theories
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_THEORY]->()
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing theories: {count}")
            
            # Papers missing methods
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_METHOD]->()
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing methods: {count}")
            
            # Papers missing phenomena
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:STUDIES_PHENOMENON]->()
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing phenomena: {count}")
            
            # Papers missing research questions
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:ADDRESSES]->()
                RETURN DISTINCT p.paper_id
            """)
            count = 0
            for record in result:
                papers_to_process.add(record["p.paper_id"])
                count += 1
            logger.info(f"  Papers missing research questions: {count}")
        
        logger.info(f"\nTotal unique papers with missing data: {len(papers_to_process)}")
        return papers_to_process
    
    def find_pdf_path(self, paper_id: str) -> Path:
        """Find PDF file for a paper_id"""
        patterns = [
            f"{paper_id}.pdf",
            f"**/{paper_id}.pdf",
            f"**/*{paper_id}*.pdf",
            f"pdfs/{paper_id}.pdf",
            f"pdfs/**/{paper_id}.pdf"
        ]
        
        for pattern in patterns:
            matches = list(Path(".").glob(pattern))
            if matches:
                return matches[0]
        
        return None
    
    def extract_year_from_filename(self, pdf_path: Path) -> Optional[int]:
        """Extract year from filename (e.g., 2010_353.pdf -> 2010)"""
        if not pdf_path:
            return None
        
        # Extract filename without extension
        filename = pdf_path.stem
        
        # Try to extract year from beginning of filename
        # Pattern: YYYY_XXXX or YYYY-XXXX
        match = re.match(r'^(\d{4})[_-]', filename)
        if match:
            year = int(match.group(1))
            # Validate year is reasonable (1900-2100)
            if 1900 <= year <= 2100:
                return year
        
        return None
    
    def update_paper_years(self, paper_pdf_mapping: dict):
        """Update paper years in Neo4j from filenames"""
        logger.info("\nUpdating paper years from filenames...")
        
        updates = 0
        batch_size = 100
        
        try:
            with self.driver.session() as session:
                # Prepare batch updates
                updates_list = []
                for paper_id, pdf_path in paper_pdf_mapping.items():
                    year = self.extract_year_from_filename(pdf_path)
                    if year:
                        updates_list.append({"paper_id": paper_id, "year": year})
                
                # Process in batches
                for i in range(0, len(updates_list), batch_size):
                    batch = updates_list[i:i+batch_size]
                    
                    # Batch update using UNWIND
                    result = session.run("""
                        UNWIND $updates as update
                        MATCH (p:Paper {paper_id: update.paper_id})
                        WHERE p.year IS NULL OR p.year = 0
                        SET p.year = update.year, p.updated_at = datetime()
                        RETURN count(p) as updated
                    """, updates=batch)
                    
                    batch_updates = result.single()["updated"]
                    updates += batch_updates
                    
                    if (i + batch_size) % 500 == 0:
                        logger.info(f"  Updated {updates} papers so far...")
        
        except Exception as e:
            logger.error(f"Error updating paper years: {e}")
            logger.warning("Continuing with pipeline...")
        
        logger.info(f"✓ Updated {updates} papers with years from filenames")
        return updates
    
    def create_temp_directory(self, paper_ids: Set[str]) -> Tuple[Path, Dict[str, Path]]:
        """Create temporary directory with symlinks to PDFs and return paper-pdf mapping"""
        # Clean up old temp dir if exists
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        self.temp_dir.mkdir(exist_ok=True)
        
        pdfs_found = 0
        pdfs_missing = 0
        paper_pdf_mapping = {}  # Store mapping for year extraction
        
        for paper_id in paper_ids:
            pdf_path = self.find_pdf_path(paper_id)
            if pdf_path and pdf_path.exists():
                # Store mapping
                paper_pdf_mapping[paper_id] = pdf_path
                
                # Create symlink
                symlink_path = self.temp_dir / f"{paper_id}.pdf"
                try:
                    symlink_path.symlink_to(pdf_path.absolute())
                    pdfs_found += 1
                except Exception as e:
                    logger.warning(f"Failed to create symlink for {paper_id}: {e}")
            else:
                pdfs_missing += 1
        
        logger.info(f"\nPDFs found: {pdfs_found}")
        logger.info(f"PDFs missing: {pdfs_missing}")
        
        return self.temp_dir, paper_pdf_mapping
    
    async def run_pipeline(self, limit: int = None):
        """Run pipeline for all papers with missing data"""
        # Find papers
        paper_ids = self.find_papers_missing_data()
        
        if limit:
            paper_ids = set(list(paper_ids)[:limit])
            logger.info(f"Limiting to first {limit} papers")
        
        # Create temp directory and get paper-pdf mapping
        temp_dir, paper_pdf_mapping = self.create_temp_directory(paper_ids)
        
        if not list(temp_dir.glob("*.pdf")):
            logger.error("No PDFs found to process")
            return
        
        # Update paper years from filenames BEFORE running pipeline
        self.update_paper_years(paper_pdf_mapping)
        
        # Run pipeline
        logger.info(f"\nStarting pipeline for {len(list(temp_dir.glob('*.pdf')))} papers...")
        
        pipeline = HighPerformancePipeline(
            max_workers=10,  # Reduced for stability
            progress_file=Path("missing_fields_progress.json")
        )
        
        # Run the pipeline
        stats = await pipeline.run(
            base_dir=temp_dir,
            year_range=None,
            resume=True  # Skip already processed papers
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Processed: {stats.processed}")
        logger.info(f"Failed: {stats.failed}")
        logger.info(f"Skipped: {stats.skipped}")
        
        # Clean up temp directory
        logger.info(f"\nCleaning up temporary directory...")
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def close(self):
        self.driver.close()

async def main():
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Processing first {limit} papers...")
    
    runner = MissingFieldsPipelineRunner()
    try:
        await runner.run_pipeline(limit=limit)
    finally:
        runner.close()

if __name__ == "__main__":
    asyncio.run(main())
