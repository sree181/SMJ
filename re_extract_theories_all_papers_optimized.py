#!/usr/bin/env python3
"""
OPTIMIZED Re-extract theories for all papers using the stricter extraction prompt
Optimizations:
- Parallel processing (multiprocessing)
- PDF text caching
- Faster timeouts (90s instead of 180s)
- Batch Neo4j operations
- Better error handling and recovery
- Connection pooling
"""

import os
import json
import logging
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from multiprocessing import Pool, Manager, cpu_count
from functools import lru_cache
import threading

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
        logging.FileHandler('theory_re_extraction_optimized.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global cache for PDF text (thread-safe)
_pdf_cache = {}
_cache_lock = threading.Lock()

class OptimizedTheoryReExtractor:
    def __init__(self, base_dir: Path, num_workers: int = None):
        self.base_dir = base_dir
        self.num_workers = num_workers or min(cpu_count(), 4)  # Max 4 workers to avoid overwhelming OLLAMA
        
        # Initialize Neo4j
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_uri or not neo4j_password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Use connection pool for better performance
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50
        )
        
        self.progress_file = Path("theory_re_extraction_progress_optimized.json")
        self.stats_file = Path("theory_re_extraction_stats.json")
        
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
            "end_time": None
        }
    
    def get_pdf_cache_key(self, pdf_path: Path) -> str:
        """Generate cache key from PDF path and modification time"""
        stat = pdf_path.stat()
        return f"{pdf_path}_{stat.st_mtime}_{stat.st_size}"
    
    def extract_text_from_pdf_cached(self, pdf_path: Path) -> str:
        """Extract text from PDF with caching"""
        cache_key = self.get_pdf_cache_key(pdf_path)
        
        with _cache_lock:
            if cache_key in _pdf_cache:
                logger.debug(f"   Using cached text for {pdf_path.name}")
                return _pdf_cache[cache_key]
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            # Only extract first 25k chars (enough for theory extraction)
            max_chars = 25000
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
        """Find PDF file for a paper ID by searching year directories"""
        year = paper_id.split('_')[0] if '_' in paper_id else None
        
        # Search in year directories (prioritize 2020-2024)
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
                elif 2010 <= year_int <= 2014:
                    year_dirs.insert(0, self.base_dir / "2010-2014")
            except ValueError:
                pass
        
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
    
    def process_single_paper(self, paper: Dict[str, Any], progress_data: dict) -> Dict[str, Any]:
        """Process a single paper (for parallel execution)"""
        paper_id = paper.get('paper_id')
        result = {
            'paper_id': paper_id,
            'success': False,
            'theories_before': 0,
            'theories_after': 0,
            'error': None,
            'skipped': False
        }
        
        if not paper_id or not paper_id.strip():
            result['error'] = 'Missing paper_id'
            result['skipped'] = True
            return result
        
        try:
            # Check if already processed
            if paper_id in progress_data.get('processed', []):
                result['skipped'] = True
                return result
            
            # Create extractor and ingester for this worker
            extractor = RedesignedOllamaExtractor()
            ingester = RedesignedNeo4jIngester(
                self.neo4j_uri, 
                self.neo4j_user, 
                self.neo4j_password
            )
            
            # Get current theory count
            theories_before = self.get_current_theory_count(paper_id)
            result['theories_before'] = theories_before
            
            # Find PDF
            pdf_path = self.find_pdf_for_paper(paper_id)
            if not pdf_path:
                result['error'] = 'PDF not found'
                return result
            
            # Extract text (cached)
            text = self.extract_text_from_pdf_cached(pdf_path)
            if not text or len(text) < 100:
                result['error'] = f'Insufficient text ({len(text)} chars)'
                return result
            
            # Extract theories with optimized timeout
            theories = extractor.extract_theories(text, paper_id)
            
            # Batch Neo4j operations in single transaction
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
                    
                    # Ingest new theories
                    if theories:
                        paper_metadata = {
                            'paper_id': paper_id,
                            'title': paper_data.get('title') or paper_id
                        }
                        
                        # Use ingester to create theory relationships
                        ingester.ingest_paper_with_methods(
                            paper_data=paper_metadata,
                            methods_data=[],
                            theories_data=theories,
                            authors=[],
                            full_metadata=paper_metadata
                        )
                    
                    tx.commit()
                    
                    # Get new theory count
                    theories_after = self.get_current_theory_count(paper_id)
                    result['theories_after'] = theories_after
                    result['success'] = True
                    
                except Exception as e:
                    tx.rollback()
                    raise e
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error processing {paper_id}: {e}")
            return result
    
    def process_papers_parallel(self, papers: List[Dict[str, Any]], progress_data: dict):
        """Process papers in parallel"""
        logger.info(f"Processing {len(papers)} papers with {self.num_workers} workers...")
        
        # Filter out already processed papers
        papers_to_process = [
            p for p in papers 
            if p.get('paper_id') not in progress_data.get('processed', [])
        ]
        
        logger.info(f"  {len(papers_to_process)} papers to process (skipping {len(papers) - len(papers_to_process)} already processed)")
        
        # Process in batches to save progress frequently
        batch_size = 10
        processed_count = 0
        
        for i in range(0, len(papers_to_process), batch_size):
            batch = papers_to_process[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(papers_to_process) + batch_size - 1) // batch_size
            
            logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} papers)...")
            
            # Process batch in parallel
            with Pool(processes=self.num_workers) as pool:
                # Create partial function with progress_data
                results = pool.starmap(
                    self._process_paper_wrapper,
                    [(paper, progress_data) for paper in batch]
                )
            
            # Update stats and progress
            for result in results:
                if result['skipped']:
                    self.stats['skipped'] += 1
                elif result['success']:
                    self.stats['processed'] += 1
                    progress_data['processed'].append(result['paper_id'])
                    self.stats['theories_before'][result['paper_id']] = result['theories_before']
                    self.stats['theories_after'][result['paper_id']] = result['theories_after']
                else:
                    self.stats['failed'] += 1
                    progress_data['failed'].append({
                        'paper_id': result['paper_id'],
                        'reason': result['error'],
                        'timestamp': datetime.now().isoformat()
                    })
                    self.stats['errors'].append(f"{result['paper_id']}: {result['error']}")
            
            # Save progress after each batch
            self.save_progress(progress_data)
            processed_count += len(batch)
            logger.info(f"  Batch {batch_num} complete. Total processed: {processed_count}/{len(papers_to_process)}")
            
            # Small delay between batches to avoid overwhelming OLLAMA
            if i + batch_size < len(papers_to_process):
                time.sleep(2)
    
    def _process_paper_wrapper(self, paper: dict, progress_data: dict) -> dict:
        """Wrapper for multiprocessing (creates new connections per worker)"""
        # Re-initialize connections for this worker
        extractor_instance = OptimizedTheoryReExtractor(self.base_dir, num_workers=1)
        return extractor_instance.process_single_paper(paper, progress_data)
    
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
        """Run optimized re-extraction for all papers"""
        self.stats['start_time'] = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info("OPTIMIZED THEORY RE-EXTRACTION WITH STRICTER PROMPT")
        logger.info("=" * 80)
        logger.info(f"Workers: {self.num_workers}")
        logger.info(f"PDF caching: Enabled")
        logger.info(f"Batch processing: Enabled (10 papers per batch)")
        
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
        logger.info("\n" + "=" * 80)
        try:
            self.process_papers_parallel(papers, progress_data)
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
                logger.info(f"Average: {duration / self.stats['processed']:.2f} minutes per paper")
        
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
    
    parser = argparse.ArgumentParser(description='Optimized re-extract theories for all papers')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process')
    parser.add_argument('--start-from', type=str, help='Start from a specific paper ID')
    parser.add_argument('--workers', type=int, default=None, help='Number of parallel workers (default: min(CPU, 4))')
    parser.add_argument('--base-dir', type=str, 
                       default='/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal',
                       help='Base directory containing year folders with PDFs')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"Error: Base directory not found: {base_dir}")
        sys.exit(1)
    
    extractor = OptimizedTheoryReExtractor(base_dir, num_workers=args.workers)
    
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

