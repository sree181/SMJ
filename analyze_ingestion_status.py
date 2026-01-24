#!/usr/bin/env python3
"""
Analyze ingestion status and determine where to resume
"""

import json
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

def get_papers_in_folders():
    """Get all PDF files in year folders"""
    base_dir = Path(".")
    papers = {}
    
    # Check year folders (2020-2024, 2025-2029, etc.)
    for year_folder in sorted(base_dir.glob("20*")):
        if year_folder.is_dir():
            for pdf_file in year_folder.glob("*.pdf"):
                paper_id = pdf_file.stem
                papers[paper_id] = {
                    "path": str(pdf_file),
                    "folder": year_folder.name,
                    "year": paper_id.split("_")[0] if "_" in paper_id else None
                }
    
    # Also check root directory
    for pdf_file in base_dir.glob("*.pdf"):
        paper_id = pdf_file.stem
        if paper_id not in papers:
            papers[paper_id] = {
                "path": str(pdf_file),
                "folder": "root",
                "year": paper_id.split("_")[0] if "_" in paper_id else None
            }
    
    return papers

def get_papers_in_neo4j():
    """Get all papers currently in Neo4j"""
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("⚠️  Neo4j credentials not found in environment")
        return {}
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, p.title as title, p.year as year
            """)
            
            papers = {}
            for record in result:
                paper_id = record["paper_id"]
                papers[paper_id] = {
                    "title": record["title"],
                    "year": record["year"]
                }
        
        driver.close()
        return papers
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        return {}

def analyze_progress_file():
    """Analyze the progress file"""
    progress_file = Path("batch_extraction_progress.json")
    
    if not progress_file.exists():
        return {"processed_papers": [], "failed_papers": []}
    
    with open(progress_file, 'r') as f:
        data = json.load(f)
    
    # Remove duplicates
    processed = list(set(data.get("processed_papers", [])))
    failed = list(set(data.get("failed_papers", [])))
    
    return {
        "processed_papers": processed,
        "failed_papers": failed
    }

def main():
    print("=" * 80)
    print("INGESTION STATUS ANALYSIS")
    print("=" * 80)
    print()
    
    # Get papers in folders
    print("📁 Scanning PDF files in folders...")
    folder_papers = get_papers_in_folders()
    print(f"   Found {len(folder_papers)} PDF files")
    print()
    
    # Get papers in Neo4j
    print("🗄️  Checking papers in Neo4j...")
    neo4j_papers = get_papers_in_neo4j()
    print(f"   Found {len(neo4j_papers)} papers in Neo4j")
    print()
    
    # Get progress file status
    print("📋 Analyzing progress file...")
    progress = analyze_progress_file()
    print(f"   Marked as processed: {len(progress['processed_papers'])}")
    print(f"   Marked as failed: {len(progress['failed_papers'])}")
    print()
    
    # Analysis
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    
    # Papers that exist in folders but not in Neo4j
    missing_in_neo4j = set(folder_papers.keys()) - set(neo4j_papers.keys())
    
    # Papers marked as processed but not in Neo4j
    processed_but_missing = set(progress["processed_papers"]) - set(neo4j_papers.keys())
    
    # Papers marked as failed
    failed_papers = set(progress["failed_papers"])
    
    # Papers that need processing (not in Neo4j and not marked as processed)
    need_processing = missing_in_neo4j - set(progress["processed_papers"])
    
    # Papers that should be retried (marked as failed but not in Neo4j)
    should_retry = failed_papers - set(neo4j_papers.keys())
    
    print(f"📊 Summary:")
    print(f"   Total PDFs found: {len(folder_papers)}")
    print(f"   Papers in Neo4j: {len(neo4j_papers)}")
    print(f"   Missing in Neo4j: {len(missing_in_neo4j)}")
    print(f"   Need processing: {len(need_processing)}")
    print(f"   Should retry (failed): {len(should_retry)}")
    print(f"   Processed but missing: {len(processed_but_missing)}")
    print()
    
    # Group by year
    print("📅 Breakdown by year:")
    year_stats = defaultdict(lambda: {"total": 0, "in_neo4j": 0, "missing": 0})
    
    for paper_id, info in folder_papers.items():
        year = info.get("year", "unknown")
        year_stats[year]["total"] += 1
        if paper_id in neo4j_papers:
            year_stats[year]["in_neo4j"] += 1
        else:
            year_stats[year]["missing"] += 1
    
    for year in sorted(year_stats.keys()):
        stats = year_stats[year]
        pct = (stats["in_neo4j"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"   {year}: {stats['in_neo4j']}/{stats['total']} ({pct:.1f}%)")
    print()
    
    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    if len(need_processing) > 0:
        print(f"✅ {len(need_processing)} papers need to be processed")
        print(f"   These are new papers not yet ingested")
        print()
    
    if len(should_retry) > 0:
        print(f"🔄 {len(should_retry)} papers should be retried")
        print(f"   These were marked as failed but are not in Neo4j")
        print(f"   Sample: {', '.join(list(should_retry)[:5])}")
        print()
    
    if len(processed_but_missing) > 0:
        print(f"⚠️  {len(processed_but_missing)} papers marked as processed but missing from Neo4j")
        print(f"   These may need to be reprocessed")
        print(f"   Sample: {', '.join(list(processed_but_missing)[:5])}")
        print()
    
    # Create resume list
    papers_to_process = sorted(list(need_processing | should_retry))
    
    if papers_to_process:
        print("=" * 80)
        print("RESUME PLAN")
        print("=" * 80)
        print()
        print(f"📝 Total papers to process: {len(papers_to_process)}")
        print()
        print("Papers to process (first 20):")
        for i, paper_id in enumerate(papers_to_process[:20], 1):
            folder = folder_papers[paper_id]["folder"]
            print(f"   {i}. {paper_id} ({folder})")
        
        if len(papers_to_process) > 20:
            print(f"   ... and {len(papers_to_process) - 20} more")
        print()
        
        # Save resume list
        resume_file = Path("resume_ingestion_list.json")
        with open(resume_file, 'w') as f:
            json.dump({
                "papers_to_process": papers_to_process,
                "total": len(papers_to_process),
                "need_processing": list(need_processing),
                "should_retry": list(should_retry),
                "processed_but_missing": list(processed_but_missing)
            }, f, indent=2)
        
        print(f"💾 Resume list saved to: {resume_file}")
        print()
        print("To resume ingestion:")
        print(f"   python batch_process_complete_extraction.py <folder>")
        print()
        print("Or process specific papers by updating batch_extraction_progress.json")
        print("   (remove papers from 'processed_papers' to reprocess them)")
    else:
        print("✅ All papers appear to be processed!")
        print()

if __name__ == "__main__":
    main()
