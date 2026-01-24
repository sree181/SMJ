#!/usr/bin/env python3
"""
Automated Multi-Bucket Processing Script
Processes all 5-year buckets sequentially with resume capability
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

from high_performance_pipeline import HighPerformancePipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_all_buckets.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def discover_buckets(base_path: Path) -> List[Dict[str, Any]]:
    """
    Discover all year bucket directories
    
    Returns:
        List of bucket info dicts with path, name, and paper count
    """
    buckets = []
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        return buckets
    
    # Look for directories matching year patterns (e.g., 2015-2019, 2020-2024)
    for item in base_path.iterdir():
        if item.is_dir() and any(char.isdigit() for char in item.name):
            # Check if it contains PDFs
            pdf_count = len(list(item.glob("*.pdf")))
            if pdf_count > 0:
                buckets.append({
                    "name": item.name,
                    "path": item,
                    "paper_count": pdf_count
                })
    
    # Sort by name (which should sort chronologically)
    buckets.sort(key=lambda x: x["name"])
    
    return buckets


def get_bucket_progress(bucket_name: str, progress_file: Path) -> Dict[str, Any]:
    """
    Get progress for a specific bucket
    
    Returns:
        Dict with processed count, total count, and completion status
    """
    if not progress_file.exists():
        return {"processed": 0, "total": 0, "completed": False}
    
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
        
        processed_papers = set(data.get("processed_papers", []))
        
        # Filter papers for this bucket (papers starting with bucket years)
        bucket_papers = [p for p in processed_papers if p.startswith(bucket_name.split("-")[0][:4])]
        
        return {
            "processed": len(bucket_papers),
            "total": len(processed_papers),
            "completed": False  # Will be determined by comparing with actual paper count
        }
    except Exception as e:
        logger.warning(f"Error reading progress file: {e}")
        return {"processed": 0, "total": 0, "completed": False}


async def process_bucket(bucket: Dict[str, Any], 
                        workers: int = 5,
                        progress_file: Path = None) -> Dict[str, Any]:
    """
    Process a single bucket
    
    Returns:
        Dict with processing results
    """
    bucket_name = bucket["name"]
    bucket_path = bucket["path"]
    total_papers = bucket["paper_count"]
    
    logger.info("=" * 80)
    logger.info(f"PROCESSING BUCKET: {bucket_name}")
    logger.info("=" * 80)
    logger.info(f"Path: {bucket_path}")
    logger.info(f"Total papers: {total_papers}")
    
    start_time = datetime.now()
    
    try:
        # Initialize pipeline for this bucket
        pipeline = HighPerformancePipeline(
            max_workers=workers,
            progress_file=progress_file or Path("high_performance_progress.json"),
            gpt4_model="gpt-4-turbo-preview"
        )
        
        # Run pipeline with resume enabled
        stats = await pipeline.run(
            base_dir=bucket_path,
            year_range=None,  # Process all years in the bucket
            resume=True  # Always resume to skip already processed papers
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60  # minutes
        
        result = {
            "bucket": bucket_name,
            "status": "completed",
            "total_papers": total_papers,
            "processed": stats.processed,
            "failed": stats.failed,
            "skipped": stats.skipped,
            "duration_minutes": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "stats": stats.to_dict()
        }
        
        logger.info(f"✓ Bucket {bucket_name} completed: {stats.processed} processed, {stats.failed} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Error processing bucket {bucket_name}: {e}")
        return {
            "bucket": bucket_name,
            "status": "failed",
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat()
        }


async def process_all_buckets(base_path: Path = None,
                             workers: int = 5,
                             start_from: str = None,
                             skip_completed: bool = True):
    """
    Process all year buckets sequentially
    
    Args:
        base_path: Base directory containing bucket folders (default: current directory)
        workers: Number of concurrent workers per bucket
        start_from: Bucket name to start from (skip earlier buckets)
        skip_completed: Skip buckets that are already fully processed
    """
    if base_path is None:
        base_path = Path(".")
    
    logger.info("=" * 80)
    logger.info("AUTOMATED MULTI-BUCKET PROCESSING")
    logger.info("=" * 80)
    logger.info(f"Base path: {base_path.absolute()}")
    logger.info(f"Workers per bucket: {workers}")
    logger.info(f"Start from: {start_from or 'first bucket'}")
    logger.info("=" * 80)
    
    # Discover all buckets
    buckets = discover_buckets(base_path)
    
    if not buckets:
        logger.error("No buckets found!")
        return
    
    logger.info(f"Found {len(buckets)} buckets:")
    for bucket in buckets:
        logger.info(f"  - {bucket['name']}: {bucket['paper_count']} papers")
    
    # Filter buckets based on start_from
    if start_from:
        start_index = next((i for i, b in enumerate(buckets) if b["name"] == start_from), None)
        if start_index is not None:
            buckets = buckets[start_index:]
            logger.info(f"Starting from bucket: {start_from}")
        else:
            logger.warning(f"Bucket {start_from} not found, processing all buckets")
    
    # Process each bucket
    results = []
    progress_file = Path("high_performance_progress.json")
    
    for i, bucket in enumerate(buckets, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"BUCKET {i}/{len(buckets)}: {bucket['name']}")
        logger.info(f"{'='*80}")
        
        # Check if bucket is already completed (if skip_completed is True)
        if skip_completed:
            progress = get_bucket_progress(bucket["name"], progress_file)
            # Estimate completion (if processed count is close to total, consider it done)
            # This is a heuristic - you might want to improve this logic
            if progress["processed"] > 0 and progress["processed"] >= bucket["paper_count"] * 0.95:
                logger.info(f"⏭️  Skipping {bucket['name']} (appears to be completed: {progress['processed']}/{bucket['paper_count']})")
                results.append({
                    "bucket": bucket["name"],
                    "status": "skipped",
                    "reason": "already_completed"
                })
                continue
        
        # Process bucket
        result = await process_bucket(bucket, workers=workers, progress_file=progress_file)
        results.append(result)
        
        # Save intermediate results
        results_file = Path("bucket_processing_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Intermediate results saved to: {results_file}")
        
        # Brief pause between buckets
        if i < len(buckets):
            logger.info("Waiting 5 seconds before next bucket...")
            await asyncio.sleep(5)
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("ALL BUCKETS PROCESSING COMPLETE")
    logger.info("=" * 80)
    
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    
    logger.info(f"Total buckets: {len(buckets)}")
    logger.info(f"✅ Completed: {completed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⏭️  Skipped: {skipped}")
    
    total_processed = sum(r.get("processed", 0) for r in results if r.get("status") == "completed")
    total_failed = sum(r.get("failed", 0) for r in results if r.get("status") == "completed")
    
    logger.info(f"\nTotal papers processed: {total_processed}")
    logger.info(f"Total papers failed: {total_failed}")
    
    # Save final results
    results_file = Path("bucket_processing_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Final results saved to: {results_file}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated Multi-Bucket Processing Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all buckets from current directory
  python process_all_buckets.py
  
  # Process with custom worker count
  python process_all_buckets.py --workers 10
  
  # Start from a specific bucket
  python process_all_buckets.py --start-from 2020-2024
  
  # Process all buckets including completed ones
  python process_all_buckets.py --no-skip-completed
        """
    )
    
    parser.add_argument(
        "base_path",
        nargs="?",
        default=".",
        help="Base directory containing bucket folders (default: current directory)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent workers per bucket (default: 5)"
    )
    parser.add_argument(
        "--start-from",
        type=str,
        help="Bucket name to start from (e.g., '2020-2024')"
    )
    parser.add_argument(
        "--no-skip-completed",
        action="store_true",
        help="Process all buckets even if they appear completed"
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path)
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)
    
    await process_all_buckets(
        base_path=base_path,
        workers=args.workers,
        start_from=args.start_from,
        skip_completed=not args.no_skip_completed
    )


if __name__ == "__main__":
    asyncio.run(main())
