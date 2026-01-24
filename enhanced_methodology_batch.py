#!/usr/bin/env python3
"""
Enhanced Methodology Batch Processor
Processes papers with comprehensive metadata extraction and method relationships
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import time

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from enhanced_methodology_extractor import EnhancedMethodologyProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedMethodologyBatchProcessor:
    """Batch processor for enhanced methodology extraction"""
    
    def __init__(self, ollama_model: str = "codellama:7b"):
        # Set environment variables
        os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
        os.environ['NEO4J_USER'] = 'neo4j'
        os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
        
        # Initialize processor
        self.processor = EnhancedMethodologyProcessor(ollama_model=ollama_model)
        
        # Define time windows
        self.time_windows = [
            (1985, 1989),
            (1990, 1994),
            (1995, 1999),
            (2000, 2004),
            (2005, 2009),
            (2010, 2014),
            (2015, 2019),
            (2020, 2024)
        ]
    
    def get_papers_in_window(self, start_year: int, end_year: int) -> List[Path]:
        """Get all papers in a time window"""
        papers = []
        
        # Check for the 5-year window directory (e.g., 1985-1989)
        window_dir = Path(f"{start_year}-{end_year}")
        if window_dir.exists():
            pdf_files = list(window_dir.glob("*.pdf"))
            papers.extend(pdf_files)
            logger.info(f"Found {len(pdf_files)} papers in {window_dir}")
        else:
            logger.warning(f"Window directory not found: {window_dir}")
        
        return sorted(papers)
    
    def process_window(self, start_year: int, end_year: int) -> Dict[str, Any]:
        """Process all papers in a time window"""
        logger.info(f"🚀 Processing enhanced methodology window: {start_year}-{end_year}")
        
        papers = self.get_papers_in_window(start_year, end_year)
        logger.info(f"Found {len(papers)} papers in window {start_year}-{end_year}")
        
        if not papers:
            logger.warning(f"No papers found in window {start_year}-{end_year}")
            return {"successful": 0, "failed": 0, "papers": []}
        
        successful = 0
        failed = 0
        processed_papers = []
        
        # Process papers with progress bar
        for pdf_path in tqdm(papers, desc=f"Processing {start_year}-{end_year}"):
            try:
                logger.info(f"Processing enhanced extraction for: {pdf_path.stem}")
                start_time = time.time()
                
                result = self.processor.process_paper(pdf_path)
                
                processing_time = time.time() - start_time
                logger.info(f"✓ Successfully processed enhanced extraction for {pdf_path.stem} in {processing_time:.2f}s")
                
                successful += 1
                processed_papers.append({
                    "paper_id": pdf_path.stem,
                    "title": result["paper_metadata"].get("title", ""),
                    "methodology_type": result["methodology_data"]["methodology"].get("type", ""),
                    "quant_methods": result["methodology_data"]["methodology"].get("quant_methods", []),
                    "processing_time": processing_time
                })
                
            except Exception as e:
                logger.error(f"✗ Failed to process {pdf_path.stem}: {e}")
                failed += 1
        
        logger.info(f"✓ Completed window {start_year}-{end_year}: {successful} successful, {failed} failed")
        
        return {
            "successful": successful,
            "failed": failed,
            "papers": processed_papers
        }
    
    def process_all_windows(self) -> Dict[str, Any]:
        """Process all time windows"""
        logger.info("🚀 Starting Enhanced Methodology Extraction Process")
        logger.info("=" * 60)
        
        total_successful = 0
        total_failed = 0
        all_results = {}
        
        for start_year, end_year in self.time_windows:
            try:
                window_result = self.process_window(start_year, end_year)
                all_results[f"{start_year}-{end_year}"] = window_result
                
                total_successful += window_result["successful"]
                total_failed += window_result["failed"]
                
                # Brief pause between windows
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"✗ Failed to process window {start_year}-{end_year}: {e}")
                all_results[f"{start_year}-{end_year}"] = {"successful": 0, "failed": 0, "error": str(e)}
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 ENHANCED METHODOLOGY EXTRACTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total successful: {total_successful}")
        logger.info(f"Total failed: {total_failed}")
        logger.info(f"Success rate: {total_successful/(total_successful+total_failed)*100:.1f}%")
        
        # Window-by-window summary
        for window, result in all_results.items():
            if "error" in result:
                logger.info(f"{window}: ERROR - {result['error']}")
            else:
                logger.info(f"{window}: {result['successful']} successful, {result['failed']} failed")
        
        return {
            "total_successful": total_successful,
            "total_failed": total_failed,
            "window_results": all_results
        }
    
    def process_specific_window(self, start_year: int, end_year: int) -> Dict[str, Any]:
        """Process a specific time window"""
        logger.info(f"🚀 Processing specific window: {start_year}-{end_year}")
        return self.process_window(start_year, end_year)
    
    def process_single_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single paper"""
        logger.info(f"🚀 Processing single paper: {pdf_path}")
        try:
            result = self.processor.process_paper(pdf_path)
            logger.info(f"✓ Successfully processed {pdf_path.stem}")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"✗ Failed to process {pdf_path.stem}: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Main function for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Methodology Batch Processor")
    parser.add_argument("--window", help="Process specific window (e.g., '1985-1989')")
    parser.add_argument("--paper", help="Process single paper (path to PDF)")
    parser.add_argument("--model", default="codellama:7b", help="OLLAMA model to use")
    parser.add_argument("--all", action="store_true", help="Process all windows")
    
    args = parser.parse_args()
    
    processor = EnhancedMethodologyBatchProcessor(ollama_model=args.model)
    
    if args.paper:
        # Process single paper
        pdf_path = Path(args.paper)
        if not pdf_path.exists():
            logger.error(f"Paper not found: {pdf_path}")
            return
        
        result = processor.process_single_paper(pdf_path)
        if result["success"]:
            print("✅ Paper processed successfully!")
            print(f"Title: {result['result']['paper_metadata']['title']}")
            print(f"Authors: {result['result']['paper_metadata']['authors']}")
            print(f"Methodology: {result['result']['methodology_data']['methodology']['type']}")
        else:
            print(f"❌ Failed to process paper: {result['error']}")
    
    elif args.window:
        # Process specific window
        try:
            start_year, end_year = map(int, args.window.split('-'))
            result = processor.process_specific_window(start_year, end_year)
            print(f"✅ Window {args.window} processed: {result['successful']} successful, {result['failed']} failed")
        except ValueError:
            logger.error("Invalid window format. Use 'YYYY-YYYY' (e.g., '1985-1989')")
    
    elif args.all:
        # Process all windows
        result = processor.process_all_windows()
        print(f"✅ All windows processed: {result['total_successful']} successful, {result['total_failed']} failed")
    
    else:
        # Default: process 1985-1989 window
        print("🚀 Starting Enhanced Methodology Extraction (1985-1989)")
        result = processor.process_specific_window(1985, 1989)
        print(f"✅ Window processed: {result['successful']} successful, {result['failed']} failed")

if __name__ == "__main__":
    main()
