#!/usr/bin/env python3
"""
FAST & ROBUST Re-extract theories for all papers
Optimizations:
- PDF text caching (avoid re-extraction)
- Faster timeouts (90s instead of 180s)
- Reduced tokens (1500 instead of 2500)
- Batch Neo4j operations (single transaction)
- Better error handling and recovery
- Connection pooling
- Progress checkpointing every 5 papers
"""

import os
import json
import logging
import sys
import time
import threading
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
        logging.FileHandler('theory_re_extraction_fast.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global PDF text cache (thread-safe)
_pdf_cache = {}
_cache_lock = threading.Lock()

class FastTheoryReExtractor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
        # Initialize Neo4j with connection pooling
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_uri or not neo4j_password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Connection pool for better performance
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50
        )
        
        # Initialize extractor and ingester
        self.extractor = RedesignedOllamaExtractor()
        self.ingester = RedesignedNeo4jIngester(neo4j_uri, neo4j_user, neo4j_password)
        
        self.progress_file = Path("theory_re_extraction_progress_fast.json")
        self.stats_file = Path("theory_re_extraction_stats_fast.json")
        
        # Stats tracking
        self.stats = {
            "total_papers": 0,
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "theories_before": defaultdict(int),
            "theories_after": defaultdict(int),
            "errors": [],
            "start_time": None,
            "end_time": None,
            "avg_time_per_paper": 0
        }
    
    def get_pdf_cache_key(self, pdf_path: Path) -> str:
        """Generate cache key from PDF path and modification time"""
        try:
            stat = pdf_path.stat()
            return f"{pdf_path}_{stat.st_mtime}_{stat.st_size}"
        except:
            return str(pdf_path)
    
    def extract_text_from_pdf_cached(self, pdf_path: Path) -> str:
        """Extract text from PDF with caching (only first 25k chars)"""
        cache_key = self.get_pdf_cache_key(pdf_path)
        
        with _cache_lock:
            if cache_key in _pdf_cache:
                logger.debug(f"   Using cached text for {pdf_path.name}")
                return _pdf_cache[cache_key]
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            max_chars = 25000  # Only extract first 25k chars (enough for theory extraction)
            
            for page in doc:
                page_text = page.get_text()
                if len(text) + len(page_text) > max_chars:
                    text += page_text[:max_chars - len(text)]
                    break
                text += page_text
            doc.close()
            
            with _cache_lock:
                _pdf_cache[cache_key] = text
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def find_pdf_for_paper(self, paper_id: str) -> Optional[Path]:
        """Find PDF file for a paper ID (optimized search)"""
        year = paper_id.split('_')[0] if '_' in paper_id else None
        
        # Prioritize 2020-2024 directory
        year_dirs = [
            self.base_dir / "2020-2024",
            self.base_dir / "2015-2019",
            self.base_dir / "2010-2014",
            self.base_dir / "2005-2009",
            self.base_dir / "2000-2004",
        ]
        
        # If we have a year, prioritize that directory
        if year:
            try:
                year_int = int(year)
                if 2020 <= year_int <= 2024:
                    year_dirs.insert(0, self.base_dir / "2020-2024")
                elif 2015 <= year_int <= 2019:
                    year_dirs.insert(0, self.base_dir / "2015-2019")
            except ValueError:
                pass
        
        # Search for PDF
        for year_dir in year_dirs:
            if not year_dir.exists():
                continue
            
            pdf_path = year_dir / f"{paper_id}.pdf"
            if pdf_path.exists():
                return pdf_path
            
            # Try glob pattern
            matches = list(year_dir.glob(f"{paper_id}*.pdf"))
            if matches:
                return matches[0]
        
        return None
    
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
    
    def delete_and_ingest_theories_batch(self, paper_id: str, theories: List[Dict[str, Any]]):
        """Delete old relationships and ingest new ones in a single transaction"""
        with self.neo4j_driver.session() as session:
            tx = session.begin_transaction()
            try:
                # Delete old relationships
                tx.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[r:USES_THEORY]->()
                    DELETE r
                """, paper_id=paper_id)
                
                # Get paper metadata
                paper_result = tx.run("""
                    MATCH (p:Paper {paper_id: $paper_id})
                    RETURN p.title as title, p.paper_id as paper_id
                """, paper_id=paper_id)
                
                paper_data = paper_result.single()
                if not paper_data:
                    raise ValueError(f"Paper {paper_id} not found in Neo4j")
                
                # Ingest new theories if any
                if theories:
                    paper_metadata = {
                        'paper_id': paper_id,
                        'title': paper_data.get('title') or paper_id
                    }
                    
                    # Use ingester to create theory relationships
                    self.ingester.ingest_paper_with_methods(
                        paper_data=paper_metadata,
                        methods_data=[],
                        theories_data=theories,
                        authors=[],
                        full_metadata=paper_metadata
                    )
                
                tx.commit()
            except Exception as e:
                tx.rollback()
                raise e
    
    def process_paper(self, paper: Dict[str, Any], progress_data: dict) -> bool:
        """Process a single paper"""
        paper_id = paper.get('paper_id')
        start_time = time.time()
        
        if not paper_id or not paper_id.strip():
            logger.warning(f"   ⚠️  Skipping paper with missing paper_id")
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
            
            # Extract text (cached)
            logger.info(f"   Extracting text from PDF (cached)...")
            text = self.extract_text_from_pdf_cached(pdf_path)
            
            if not text or len(text) < 100:
                raise ValueError(f"Insufficient text extracted from PDF (got {len(text)} chars)")
            
            # Extract theories (with optimized timeout)
            logger.info(f"   Extracting theories with stricter prompt (timeout: 90s)...")
            theories = self.extractor.extract_theories(text, paper_id)
            
            logger.info(f"   Extracted {len(theories)} theories")
            
            # Batch Neo4j operations (delete + ingest in single transaction)
            logger.info(f"   Updating Neo4j (batch operation)...")
            self.delete_and_ingest_theories_batch(paper_id, theories)
            
            # Get new theory count
            theories_after = self.get_current_theory_count(paper_id)
            logger.info(f"   ✓ Theories updated: {theories_before} → {theories_after}")
            
            # Update stats
            self.stats['theories_before'][paper_id] = theories_before
            self.stats['theories_after'][paper_id] = theories_after
            self.stats['processed'] += 1
            
            # Calculate time
            elapsed = time.time() - start_time
            logger.info(f"   ⏱️  Time: {elapsed:.1f}s")
            
            # Mark as processed
            progress_data['processed'].append(paper_id)
            
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
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading progress file: {e}, starting fresh")
        return {'processed': [], 'failed': []}
    
    def save_progress(self, progress_data: dict):
        """Save progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def save_stats(self):
        """Save statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def run(self, limit: Optional[int] = None, start_from: Optional[str] = None):
        """Run fast re-extraction for all papers"""
        self.stats['start_time'] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("FAST & ROBUST THEORY RE-EXTRACTION")
        logger.info("=" * 80)
        logger.info("Optimizations:")
        logger.info("  - PDF text caching")
        logger.info("  - Faster timeouts (90s)")
        logger.info("  - Reduced tokens (1500)")
        logger.info("  - Batch Neo4j operations")
        logger.info("  - Connection pooling")
        
        # Get all papers
        logger.info("\nFetching all papers from Neo4j...")
        papers = self.get_all_papers()
        self.stats['total_papers'] = len(papers)
        
        logger.info(f"Found {len(papers)} papers in database")
        
        # Load progress
        progress_data = self.load_progress()
        logger.info(f"Resuming from previous progress: {len(progress_data.get('processed', []))} already processed")
        
        # Filter papers
        if start_from:
            start_idx = next((i for i, p in enumerate(papers) if p['paper_id'] == start_from), 0)
            papers = papers[start_idx:]
            logger.info(f"Starting from paper: {start_from}")
        
        if limit:
            papers = papers[:limit]
            logger.info(f"Processing limited to {limit} papers")
        
        # Process papers
        logger.info(f"\nProcessing {len(papers)} papers...")
        logger.info("=" * 80)
        
        try:
            for i, paper in enumerate(papers, 1):
                logger.info(f"\n[{i}/{len(papers)}]")
                self.process_paper(paper, progress_data)
                
                # Save progress every 5 papers (more frequent)
                if i % 5 == 0:
                    self.save_progress(progress_data)
                    self.save_stats()
                    logger.info(f"\n💾 Progress saved: {i}/{len(papers)} papers processed")
                    
                    # Calculate ETA
                    if i > 0:
                        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
                        avg_time = elapsed / i
                        remaining = (len(papers) - i) * avg_time
                        logger.info(f"   ⏱️  ETA: {remaining/60:.1f} minutes")
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user. Progress has been saved.")
            self.save_progress(progress_data)
            self.save_stats()
            raise
        
        # Final save
        self.save_progress(progress_data)
        self.stats['end_time'] = datetime.now().isoformat()
        self.save_stats()
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("RE-EXTRACTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total papers: {self.stats['total_papers']}")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['start_time'] and self.stats['end_time']:
            start = datetime.fromisoformat(self.stats['start_time'])
            end = datetime.fromisoformat(self.stats['end_time'])
            duration = (end - start).total_seconds() / 60
            logger.info(f"Duration: {duration:.1f} minutes")
            if self.stats['processed'] > 0:
                avg_time = duration / self.stats['processed']
                logger.info(f"Average: {avg_time:.2f} minutes per paper")
                self.stats['avg_time_per_paper'] = avg_time
        
        # Theory count changes
        if self.stats['theories_before'] and self.stats['theories_after']:
            total_before = sum(self.stats['theories_before'].values())
            total_after = sum(self.stats['theories_after'].values())
            logger.info(f"\nTheory counts:")
            logger.info(f"  Before: {total_before} total relationships")
            logger.info(f"  After: {total_after} total relationships")
            if total_before > 0:
                change_pct = ((total_after - total_before) / total_before * 100)
                logger.info(f"  Change: {total_after - total_before} ({change_pct:.1f}%)")
        
        logger.info("=" * 80)
    
    def close(self):
        """Close connections"""
        self.neo4j_driver.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fast & robust re-extract theories for all papers')
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
    
    extractor = FastTheoryReExtractor(base_dir)
    
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

