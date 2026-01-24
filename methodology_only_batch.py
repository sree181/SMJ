#!/usr/bin/env python3
"""
Focused Methodology-Only Batch Processor using OLLAMA
Processes all papers from 1985-1994 extracting ONLY methodology information
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from dotenv import load_dotenv

from methodology_only_extractor import MethodologyOnlyProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('methodology_only_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MethodologyOnlyBatchProcessor:
    """Batch processor for methodology-only extraction using OLLAMA"""
    
    def __init__(self, base_dir: Path, neo4j_uri: str = None, neo4j_user: str = None, 
                 neo4j_password: str = None, ollama_model: str = "codellama:7b"):
        self.base_dir = base_dir
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.ollama_model = ollama_model
        
        # Initialize the methodology-only processor
        self.processor = MethodologyOnlyProcessor(
            neo4j_uri=self.neo4j_uri,
            neo4j_user=self.neo4j_user,
            neo4j_password=self.neo4j_password,
            ollama_model=self.ollama_model
        )
        
        # Processing statistics
        self.stats = {
            'total_papers': 0,
            'processed_papers': 0,
            'failed_papers': 0,
            'total_methodologies': 0,
            'quantitative_methods': 0,
            'qualitative_methods': 0,
            'mixed_methods': 0,
            'other_methods': 0,
            'processing_time': 0,
            'errors': []
        }
    
    def get_temporal_windows(self, start_year: int, end_year: int) -> List[Tuple[int, int]]:
        """Generate 5-year temporal windows"""
        windows = []
        current_start = start_year
        
        while current_start <= end_year:
            current_end = min(current_start + 4, end_year)  # 5-year window (inclusive)
            windows.append((current_start, current_end))
            current_start = current_end + 1
        
        return windows
    
    def find_papers_in_window(self, start_year: int, end_year: int) -> List[Path]:
        """Find all PDF papers in the specified year range"""
        papers = []
        
        # Look for papers in the base directory
        for pdf_file in self.base_dir.glob("*.pdf"):
            try:
                year = int(pdf_file.stem.split('_')[0])
                if start_year <= year <= end_year:
                    papers.append(pdf_file)
            except (ValueError, IndexError):
                continue
        
        # Also look in subdirectories
        for subdir in self.base_dir.iterdir():
            if subdir.is_dir():
                for pdf_file in subdir.glob("*.pdf"):
                    try:
                        year = int(pdf_file.stem.split('_')[0])
                        if start_year <= year <= end_year:
                            papers.append(pdf_file)
                    except (ValueError, IndexError):
                        continue
        
        return sorted(papers, key=lambda x: x.name)
    
    def process_single_paper(self, pdf_path: Path, window_name: str) -> Dict[str, Any]:
        """Process a single paper for methodology-only extraction"""
        paper_id = pdf_path.stem
        start_time = time.time()
        
        try:
            logger.info(f"Processing methodology ONLY for: {paper_id}")
            
            # Process the paper (methodology only)
            result = self.processor.process_paper(pdf_path)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['processed_papers'] += 1
            self.stats['total_methodologies'] += 1
            
            methodology = result.get('methodology', {})
            method_type = methodology.get('type', 'other')
            
            if method_type == 'quantitative':
                self.stats['quantitative_methods'] += 1
            elif method_type == 'qualitative':
                self.stats['qualitative_methods'] += 1
            elif method_type == 'mixed':
                self.stats['mixed_methods'] += 1
            else:
                self.stats['other_methods'] += 1
            
            logger.info(f"✓ Successfully processed methodology ONLY for {paper_id} in {processing_time:.2f}s")
            
            return {
                'paper_id': paper_id,
                'window': window_name,
                'status': 'success',
                'processing_time': processing_time,
                'methodology_type': method_type,
                'confidence': methodology.get('confidence', 0.0),
                'quant_methods': len(methodology.get('analysis', {}).get('quant_methods', [])),
                'qual_methods': len(methodology.get('analysis', {}).get('qual_methods', [])),
                'designs': len(methodology.get('design', [])),
                'extraction_notes': methodology.get('extraction_notes', '')[:100]
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Failed to process {paper_id}: {str(e)}"
            logger.error(error_msg)
            
            self.stats['failed_papers'] += 1
            self.stats['errors'].append({
                'paper_id': paper_id,
                'window': window_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'paper_id': paper_id,
                'window': window_name,
                'status': 'failed',
                'processing_time': processing_time,
                'error': str(e)
            }
    
    def process_temporal_window(self, start_year: int, end_year: int, max_workers: int = 2) -> Dict[str, Any]:
        """Process all papers in a temporal window"""
        window_name = f"{start_year}-{end_year}"
        logger.info(f"🚀 Processing methodology-only window: {window_name}")
        
        # Find papers in this window
        papers = self.find_papers_in_window(start_year, end_year)
        
        if not papers:
            logger.warning(f"No papers found for window {window_name}")
            return {
                'window': window_name,
                'total_papers': 0,
                'processed_papers': 0,
                'failed_papers': 0,
                'results': []
            }
        
        logger.info(f"Found {len(papers)} papers in window {window_name}")
        self.stats['total_papers'] += len(papers)
        
        # Process papers with parallel execution
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_paper = {
                executor.submit(self.process_single_paper, paper, window_name): paper 
                for paper in papers
            }
            
            # Process completed tasks with progress bar
            with tqdm(total=len(papers), desc=f"Processing {window_name}") as pbar:
                for future in as_completed(future_to_paper):
                    paper = future_to_paper[future]
                    try:
                        result = future.result()
                        results.append(result)
                        pbar.update(1)
                    except Exception as e:
                        logger.error(f"Unexpected error processing {paper.name}: {e}")
                        results.append({
                            'paper_id': paper.stem,
                            'window': window_name,
                            'status': 'failed',
                            'error': str(e)
                        })
                        pbar.update(1)
        
        # Calculate window statistics
        successful = len([r for r in results if r['status'] == 'success'])
        failed = len([r for r in results if r['status'] == 'failed'])
        
        logger.info(f"✓ Completed window {window_name}: {successful} successful, {failed} failed")
        
        return {
            'window': window_name,
            'total_papers': len(papers),
            'processed_papers': successful,
            'failed_papers': failed,
            'results': results
        }
    
    def process_all_windows(self, start_year: int, end_year: int, max_workers: int = 2) -> Dict[str, Any]:
        """Process all temporal windows from start_year to end_year"""
        logger.info(f"🎯 Starting Methodology-ONLY Extraction: {start_year}-{end_year}")
        logger.info(f"Using model: {self.ollama_model}")
        logger.info(f"Max workers: {max_workers}")
        logger.info("🔍 Extracting ONLY methodology sections - no other content")
        
        start_time = time.time()
        
        # Get temporal windows
        windows = self.get_temporal_windows(start_year, end_year)
        logger.info(f"Temporal windows: {[f'{w[0]}-{w[1]}' for w in windows]}")
        
        # Process each window
        window_results = []
        for start_win, end_win in windows:
            try:
                window_result = self.process_temporal_window(start_win, end_win, max_workers)
                window_results.append(window_result)
                
                # Add a small delay between windows
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Failed to process window {start_win}-{end_win}: {e}")
                window_results.append({
                    'window': f"{start_win}-{end_win}",
                    'error': str(e),
                    'total_papers': 0,
                    'processed_papers': 0,
                    'failed_papers': 0
                })
        
        # Calculate final statistics
        total_time = time.time() - start_time
        self.stats['processing_time'] = total_time
        
        # Generate comprehensive report
        report = {
            'processing_info': {
                'start_year': start_year,
                'end_year': end_year,
                'total_windows': len(windows),
                'max_workers': max_workers,
                'ollama_model': self.ollama_model,
                'extraction_type': 'methodology_only',
                'total_processing_time': total_time
            },
            'overall_statistics': self.stats,
            'window_results': window_results,
            'summary': {
                'total_papers_found': sum(w['total_papers'] for w in window_results),
                'total_papers_processed': sum(w['processed_papers'] for w in window_results),
                'total_papers_failed': sum(w['failed_papers'] for w in window_results),
                'success_rate': self._calculate_success_rate(),
                'methodology_breakdown': {
                    'quantitative': self.stats['quantitative_methods'],
                    'qualitative': self.stats['qualitative_methods'],
                    'mixed': self.stats['mixed_methods'],
                    'other': self.stats['other_methods']
                }
            }
        }
        
        # Save detailed report
        self._save_report(report)
        
        logger.info("🎉 Methodology-ONLY extraction completed!")
        logger.info(f"Total papers processed: {self.stats['processed_papers']}")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        logger.info(f"Success rate: {self._calculate_success_rate():.2f}%")
        
        return report
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.stats['total_papers'] == 0:
            return 0.0
        return (self.stats['processed_papers'] / self.stats['total_papers']) * 100
    
    def _save_report(self, report: Dict[str, Any]):
        """Save processing report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"methodology_only_extraction_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Detailed report saved to: {report_file}")
    
    def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get current knowledge graph statistics"""
        try:
            with self.processor.ingester.driver.session() as session:
                # Get counts for methodology-related nodes
                stats = {}
                
                node_types = ['Paper', 'Methodology']
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    stats[node_type.lower()] = result.single()['count']
                
                # Get methodology type breakdown
                result = session.run("MATCH (m:Methodology) RETURN m.type as type, count(m) as count")
                methodology_types = {record['type']: record['count'] for record in result}
                stats['methodology_types'] = methodology_types
                
                # Get relationship count
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                stats['relationships'] = result.single()['count']
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get knowledge graph stats: {e}")
            return {}

def main():
    """Main function to run methodology-only extraction"""
    # Configuration
    BASE_DIR = Path(".")  # Current directory since we're already in Strategic Management Journal
    START_YEAR = 1985
    END_YEAR = 1994
    MAX_WORKERS = 2
    OLLAMA_MODEL = "codellama:7b"
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Check if base directory exists
    if not BASE_DIR.exists():
        logger.error(f"Base directory not found: {BASE_DIR}")
        return
    
    # Initialize batch processor
    processor = MethodologyOnlyBatchProcessor(BASE_DIR, ollama_model=OLLAMA_MODEL)
    
    # Get initial knowledge graph stats
    logger.info("📊 Initial Knowledge Graph Statistics:")
    initial_stats = processor.get_knowledge_graph_stats()
    for key, value in initial_stats.items():
        logger.info(f"  {key}: {value}")
    
    # Process all windows
    try:
        report = processor.process_all_windows(START_YEAR, END_YEAR, MAX_WORKERS)
        
        # Get final knowledge graph stats
        logger.info("\n📊 Final Knowledge Graph Statistics:")
        final_stats = processor.get_knowledge_graph_stats()
        for key, value in final_stats.items():
            logger.info(f"  {key}: {value}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 METHODOLOGY-ONLY EXTRACTION COMPLETED!")
        print("="*60)
        print(f"📅 Period: {START_YEAR}-{END_YEAR}")
        print(f"🤖 Model: {OLLAMA_MODEL}")
        print(f"🔍 Extraction Type: METHODOLOGY ONLY")
        print(f"📄 Papers Found: {report['summary']['total_papers_found']}")
        print(f"✅ Papers Processed: {report['summary']['total_papers_processed']}")
        print(f"❌ Papers Failed: {report['summary']['total_papers_failed']}")
        print(f"📊 Success Rate: {report['summary']['success_rate']:.2f}%")
        print(f"⏱️  Total Time: {report['processing_info']['total_processing_time']:.2f} seconds")
        print("\n📈 Methodology Breakdown:")
        for method_type, count in report['summary']['methodology_breakdown'].items():
            print(f"  {method_type}: {count}")
        
    except Exception as e:
        logger.error(f"Methodology-only extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
