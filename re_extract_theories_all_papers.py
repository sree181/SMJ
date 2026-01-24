#!/usr/bin/env python3
"""
Re-extract theories for all papers using the stricter extraction prompt
This will replace existing theory relationships with more accurate ones
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

import fitz  # PyMuPDF
from neo4j import GraphDatabase
from dotenv import load_dotenv

from redesigned_methodology_extractor import RedesignedOllamaExtractor, RedesignedNeo4jIngester

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('theory_re_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TheoryReExtractor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.extractor = RedesignedOllamaExtractor()
        
        # Initialize Neo4j
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_uri or not neo4j_password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.ingester = RedesignedNeo4jIngester(neo4j_uri, neo4j_user, neo4j_password)
        
        self.progress_file = Path("theory_re_extraction_progress.json")
        self.stats = {
            "total_papers": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "theories_before": defaultdict(int),
            "theories_after": defaultdict(int),
            "errors": []
        }
    
    def find_pdf_for_paper(self, paper_id: str) -> Optional[Path]:
        """Find PDF file for a paper ID by searching year directories"""
        # Paper IDs are typically like "2021_4373" where 2021 is the year
        year = paper_id.split('_')[0] if '_' in paper_id else None
        
        # Search in year directories
        year_dirs = [
            self.base_dir / "2020-2024",
            self.base_dir / "2015-2019",
            self.base_dir / "2010-2014",
            self.base_dir / "2005-2009",
            self.base_dir / "2000-2004",
            self.base_dir / "1995-1999",
            self.base_dir / "1990-1994",
            self.base_dir / "1985-1989",
        ]
        
        # If we have a year, prioritize that directory
        if year:
            year_int = int(year)
            if 2020 <= year_int <= 2024:
                year_dirs.insert(0, self.base_dir / "2020-2024")
            elif 2015 <= year_int <= 2019:
                year_dirs.insert(0, self.base_dir / "2015-2019")
            elif 2010 <= year_int <= 2014:
                year_dirs.insert(0, self.base_dir / "2010-2014")
            elif 2005 <= year_int <= 2009:
                year_dirs.insert(0, self.base_dir / "2005-2009")
            elif 2000 <= year_int <= 2004:
                year_dirs.insert(0, self.base_dir / "2000-2004")
        
        # Search for PDF
        for year_dir in year_dirs:
            if not year_dir.exists():
                continue
            
            pdf_path = year_dir / f"{paper_id}.pdf"
            if pdf_path.exists():
                return pdf_path
            
            # Also try without extension
            for pdf_file in year_dir.glob(f"{paper_id}*"):
                if pdf_file.suffix.lower() == '.pdf':
                    return pdf_file
        
        return None
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Get all papers from Neo4j"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, 
                       p.title as title,
                       p.publication_year as year
                ORDER BY p.paper_id
            """)
            
            papers = []
            for record in result:
                papers.append({
                    'paper_id': record['paper_id'],
                    'title': record['title'],
                    'year': record.get('year')
                })
            return papers
    
    def get_current_theory_count(self, paper_id: str) -> int:
        """Get current number of theories for a paper"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_THEORY]->(t:Theory)
                RETURN count(DISTINCT t) as count
            """, paper_id=paper_id)
            
            record = result.single()
            return record['count'] if record else 0
    
    def delete_existing_theory_relationships(self, paper_id: str):
        """Delete all existing theory relationships for a paper"""
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_THEORY]->()
                DELETE r
            """, paper_id=paper_id)
            logger.debug(f"   Deleted existing theory relationships for {paper_id}")
    
    def re_extract_theories(self, paper_id: str, pdf_path: Path) -> Dict[str, Any]:
        """Re-extract theories for a paper"""
        # Extract text
        logger.info(f"   Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text or len(text) < 100:
            raise ValueError(f"Insufficient text extracted from PDF (got {len(text)} chars)")
        
        # Extract theories using the updated, stricter prompt
        logger.info(f"   Extracting theories with stricter prompt...")
        theories = self.extractor.extract_theories(text, paper_id)
        
        return {
            'theories': theories,
            'text_length': len(text)
        }
    
    def ingest_theories(self, paper_id: str, theories: List[Dict[str, Any]]):
        """Ingest theories into Neo4j"""
        if not paper_id or not paper_id.strip():
            raise ValueError(f"Invalid paper_id: {paper_id}")
        
        # Get paper metadata (minimal, just for ingestion)
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                RETURN p.title as title, p.paper_id as paper_id
            """, paper_id=paper_id)
            
            paper_data = result.single()
            if not paper_data:
                raise ValueError(f"Paper {paper_id} not found in Neo4j")
            
            # Create minimal paper data for ingestion
            paper_metadata = {
                'paper_id': paper_id,
                'title': paper_data.get('title') or paper_id
            }
            
            # Ensure paper_id is set
            if not paper_metadata.get('paper_id'):
                paper_metadata['paper_id'] = paper_id
            
            # Ingest theories only
            self.ingester.ingest_paper_with_methods(
                paper_data=paper_metadata,
                methods_data=[],  # No methods
                theories_data=theories,
                authors=[],  # No authors
                full_metadata=paper_metadata
            )
    
    def process_paper(self, paper: Dict[str, Any], progress_data: dict) -> bool:
        """Process a single paper"""
        paper_id = paper.get('paper_id')
        
        # Skip if paper_id is missing or empty
        if not paper_id or not paper_id.strip():
            logger.warning(f"   ⚠️  Skipping paper with missing paper_id: {paper}")
            self.stats['skipped'] += 1
            return False
        
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing: {paper_id}")
            logger.info(f"Title: {paper.get('title', 'N/A')[:80]}...")
            
            # Check if already processed
            if paper_id in progress_data.get('processed', []):
                logger.info(f"   ⏭️  Already processed, skipping")
                self.stats['skipped'] += 1
                return True
            
            # Get current theory count
            theories_before = self.get_current_theory_count(paper_id)
            logger.info(f"   Current theories: {theories_before}")
            
            # Find PDF
            pdf_path = self.find_pdf_for_paper(paper_id)
            if not pdf_path:
                logger.warning(f"   ⚠️  PDF not found for {paper_id}")
                progress_data['failed'].append({
                    'paper_id': paper_id,
                    'reason': 'PDF not found',
                    'timestamp': datetime.now().isoformat()
                })
                self.stats['failed'] += 1
                return False
            
            logger.info(f"   Found PDF: {pdf_path.name}")
            
            # Re-extract theories
            extraction_result = self.re_extract_theories(paper_id, pdf_path)
            theories = extraction_result['theories']
            
            logger.info(f"   Extracted {len(theories)} theories")
            
            # Delete old relationships
            logger.info(f"   Deleting old theory relationships...")
            self.delete_existing_theory_relationships(paper_id)
            
            # Ingest new theories
            if theories:
                logger.info(f"   Ingesting {len(theories)} new theories...")
                self.ingest_theories(paper_id, theories)
                
                # Get new theory count
                theories_after = self.get_current_theory_count(paper_id)
                logger.info(f"   ✓ Theories updated: {theories_before} → {theories_after}")
                
                self.stats['theories_before'][paper_id] = theories_before
                self.stats['theories_after'][paper_id] = theories_after
            else:
                logger.info(f"   ⚠️  No theories extracted (stricter extraction)")
                theories_after = 0
                self.stats['theories_before'][paper_id] = theories_before
                self.stats['theories_after'][paper_id] = 0
            
            # Mark as processed
            progress_data['processed'].append(paper_id)
            self.stats['processed'] += 1
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing {paper_id}: {str(e)}"
            logger.error(f"   ✗ {error_msg}")
            progress_data['failed'].append({
                'paper_id': paper_id,
                'reason': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.stats['errors'].append(error_msg)
            self.stats['failed'] += 1
            return False
    
    def load_progress(self) -> dict:
        """Load progress from file"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {'processed': [], 'failed': []}
    
    def save_progress(self, progress_data: dict):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def run(self, limit: Optional[int] = None, start_from: Optional[str] = None):
        """Run re-extraction for all papers"""
        logger.info("=" * 80)
        logger.info("THEORY RE-EXTRACTION WITH STRICTER PROMPT")
        logger.info("=" * 80)
        
        # Get all papers
        logger.info("Fetching all papers from Neo4j...")
        papers = self.get_all_papers()
        self.stats['total_papers'] = len(papers)
        
        logger.info(f"Found {len(papers)} papers in database")
        
        # Load progress
        progress_data = self.load_progress()
        logger.info(f"Resuming from previous progress: {len(progress_data.get('processed', []))} already processed")
        
        # Filter papers
        if start_from:
            # Start from a specific paper
            start_idx = next((i for i, p in enumerate(papers) if p['paper_id'] == start_from), 0)
            papers = papers[start_idx:]
            logger.info(f"Starting from paper: {start_from}")
        
        if limit:
            papers = papers[:limit]
            logger.info(f"Processing limited to {limit} papers")
        
        # Process papers
        logger.info(f"\nProcessing {len(papers)} papers...")
        logger.info("=" * 80)
        
        for i, paper in enumerate(papers, 1):
            logger.info(f"\n[{i}/{len(papers)}]")
            self.process_paper(paper, progress_data)
            
            # Save progress every 10 papers
            if i % 10 == 0:
                self.save_progress(progress_data)
                logger.info(f"\nProgress saved: {i}/{len(papers)} papers processed")
        
        # Final save
        self.save_progress(progress_data)
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("RE-EXTRACTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total papers: {self.stats['total_papers']}")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        # Theory count changes
        if self.stats['theories_before'] and self.stats['theories_after']:
            total_before = sum(self.stats['theories_before'].values())
            total_after = sum(self.stats['theories_after'].values())
            logger.info(f"\nTheory counts:")
            logger.info(f"  Before: {total_before} total relationships")
            logger.info(f"  After: {total_after} total relationships")
            logger.info(f"  Change: {total_after - total_before} ({((total_after - total_before) / total_before * 100):.1f}%)")
        
        logger.info("=" * 80)
    
    def close(self):
        """Close connections"""
        self.neo4j_driver.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-extract theories for all papers with stricter prompt')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process')
    parser.add_argument('--start-from', type=str, help='Start from a specific paper ID')
    parser.add_argument('--base-dir', type=str, 
                       default='/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal',
                       help='Base directory containing year folders with PDFs')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"Error: Base directory not found: {base_dir}")
        sys.exit(1)
    
    extractor = TheoryReExtractor(base_dir)
    
    try:
        extractor.run(limit=args.limit, start_from=args.start_from)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user. Progress has been saved.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        extractor.close()

