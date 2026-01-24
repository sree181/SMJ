#!/usr/bin/env python3
"""
Clean up the progress file by removing duplicates and papers that should be retried
"""

import json
from pathlib import Path

def main():
    progress_file = Path("batch_extraction_progress.json")
    resume_file = Path("resume_ingestion_list.json")
    
    # Load current progress
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {"processed_papers": [], "failed_papers": []}
    
    # Load resume list to see what should be retried
    if resume_file.exists():
        with open(resume_file, 'r') as f:
            resume_data = json.load(f)
        
        should_retry = set(resume_data.get("should_retry", []))
        processed_but_missing = set(resume_data.get("processed_but_missing", []))
    else:
        should_retry = set()
        processed_but_missing = set()
    
    # Clean up: remove duplicates
    processed = list(set(progress.get("processed_papers", [])))
    failed = list(set(progress.get("failed_papers", [])))
    
    # Remove papers that should be retried from processed list
    # (they were marked as processed but failed or are missing)
    papers_to_remove_from_processed = should_retry | processed_but_missing
    processed = [p for p in processed if p not in papers_to_remove_from_processed]
    
    # Remove papers that should be retried from failed list
    # (we'll retry them, so clear their failed status)
    failed = [p for p in failed if p not in should_retry]
    
    # Create cleaned progress
    cleaned_progress = {
        "processed_papers": sorted(processed),
        "failed_papers": sorted(failed),
        "note": "Cleaned progress file - removed duplicates and papers marked for retry"
    }
    
    # Save cleaned progress
    backup_file = Path("batch_extraction_progress.json.backup")
    if progress_file.exists():
        import shutil
        shutil.copy(progress_file, backup_file)
        print(f"✅ Backed up original to: {backup_file}")
    
    with open(progress_file, 'w') as f:
        json.dump(cleaned_progress, f, indent=2)
    
    print(f"✅ Cleaned progress file saved")
    print(f"   Processed: {len(cleaned_progress['processed_papers'])} (removed {len(progress.get('processed_papers', [])) - len(cleaned_progress['processed_papers'])})")
    print(f"   Failed: {len(cleaned_progress['failed_papers'])} (removed {len(progress.get('failed_papers', [])) - len(cleaned_progress['failed_papers'])})")
    print()
    print(f"📝 Papers removed from processed (will be retried): {len(papers_to_remove_from_processed)}")
    print(f"📝 Papers removed from failed (will be retried): {len(should_retry)}")

if __name__ == "__main__":
    main()
