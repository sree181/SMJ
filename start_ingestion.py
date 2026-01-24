#!/usr/bin/env python3
"""
Start ingestion process - begin with a small test batch, then continue
"""

import subprocess
import sys
from pathlib import Path

def check_prerequisites():
    """Check if prerequisites are met"""
    print("=" * 80)
    print("CHECKING PREREQUISITES")
    print("=" * 80)
    print()
    
    # Check if batch processor exists
    batch_script = Path("batch_process_complete_extraction.py")
    if not batch_script.exists():
        print("❌ batch_process_complete_extraction.py not found")
        return False
    print("✅ Batch processor script found")
    
    # Check if year folders exist
    year_folders = list(Path(".").glob("20*"))
    if not year_folders:
        print("❌ No year folders found (2020-2024, 2025-2029, etc.)")
        return False
    print(f"✅ Found {len(year_folders)} year folders")
    
    # Check if progress file exists
    progress_file = Path("batch_extraction_progress.json")
    if progress_file.exists():
        print("✅ Progress file exists")
    else:
        print("⚠️  Progress file not found (will be created)")
    
    print()
    return True

def start_ingestion(folder_name=None, background=False):
    """Start ingestion process"""
    
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please fix issues above.")
        return
    
    # Default to 2025-2029 (smallest batch for testing)
    if not folder_name:
        folder_name = "2025-2029"
    
    folder_path = Path(folder_name)
    if not folder_path.exists():
        print(f"❌ Folder '{folder_name}' not found")
        print(f"Available folders: {', '.join([f.name for f in Path('.').glob('20*') if f.is_dir()])}")
        return
    
    # Count PDFs in folder
    pdf_count = len(list(folder_path.glob("*.pdf")))
    print(f"📁 Found {pdf_count} PDFs in {folder_name}")
    print()
    
    # Build command
    cmd = ["python3", "batch_process_complete_extraction.py", folder_name]
    
    if background:
        print("🚀 Starting ingestion in background...")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Log file: batch_extraction_output.log")
        print()
        print("To monitor progress:")
        print("   tail -f batch_extraction_output.log")
        print()
        
        # Start in background
        with open("batch_extraction_output.log", "w") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=Path.cwd()
            )
        print(f"✅ Process started with PID: {process.pid}")
        print(f"   To stop: kill {process.pid}")
    else:
        print("🚀 Starting ingestion...")
        print(f"   Command: {' '.join(cmd)}")
        print()
        print("Press Ctrl+C to stop (progress will be saved)")
        print()
        
        # Run in foreground
        try:
            subprocess.run(cmd, cwd=Path.cwd())
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted. Progress has been saved.")
            print("   Run again to resume from where it left off.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Start paper ingestion process")
    parser.add_argument(
        "folder",
        nargs="?",
        default="2025-2029",
        help="Year folder to process (default: 2025-2029)"
    )
    parser.add_argument(
        "-b", "--background",
        action="store_true",
        help="Run in background"
    )
    
    args = parser.parse_args()
    
    start_ingestion(args.folder, args.background)

if __name__ == "__main__":
    main()
