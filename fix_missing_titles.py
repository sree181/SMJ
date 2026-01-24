#!/usr/bin/env python3
"""
Fix Missing Titles
Investigates and fixes papers missing titles
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investigate_missing_titles():
    """Investigate papers missing titles"""
    print("=" * 80)
    print("INVESTIGATING MISSING TITLES")
    print("=" * 80)
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
    )
    
    try:
        with driver.session() as session:
            # Count papers without titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN count(p) as count
            """)
            no_title_count = result.single()['count']
            print(f"\nPapers without titles: {no_title_count}")
            
            # Get sample papers without titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN p.paper_id, keys(p) as keys
                LIMIT 5
            """)
            
            print("\nSample papers without titles:")
            for record in result:
                paper_id = record['p.paper_id']
                keys = record['keys']
                print(f"\n  Paper ID: {paper_id}")
                print(f"  Properties: {keys}")
            
            # Check if papers have other identifying info
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN count(p) as count,
                       sum(CASE WHEN p.abstract IS NOT NULL THEN 1 ELSE 0 END) as with_abstract,
                       sum(CASE WHEN p.doi IS NOT NULL THEN 1 ELSE 0 END) as with_doi
            """)
            stats = result.single()
            print(f"\nPapers without titles:")
            print(f"  Total: {stats['count']}")
            print(f"  With abstract: {stats['with_abstract']}")
            print(f"  With DOI: {stats['with_doi']}")
            
            # Check year distribution
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN p.year, count(p) as count
                ORDER BY p.year
            """)
            print("\nYear distribution of papers without titles:")
            for record in result:
                year = record['p.year']
                count = record['count']
                print(f"  {year}: {count}")
    
    finally:
        driver.close()

def check_extraction_logs():
    """Check if we can find extraction logs"""
    print("\n" + "=" * 80)
    print("CHECKING EXTRACTION LOGS")
    print("=" * 80)
    
    # Look for log files
    log_files = list(Path(".").glob("**/*.log"))
    if log_files:
        print(f"Found {len(log_files)} log files")
        for lf in log_files[:5]:
            print(f"  - {lf}")
    else:
        print("No log files found")
    
    # Look for progress files that might have extraction info
    progress_files = list(Path(".").glob("**/*progress*.json"))
    if progress_files:
        print(f"\nFound {len(progress_files)} progress files")
        import json
        for pf in progress_files[:1]:
            try:
                with open(pf, 'r') as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'failed' in data:
                    failed = data.get('failed', [])
                    print(f"\n  {pf.name}: {len(failed)} failed extractions")
                    if failed:
                        print(f"    Sample failed: {failed[0]}")
            except:
                pass

if __name__ == "__main__":
    investigate_missing_titles()
    check_extraction_logs()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print("\nRECOMMENDATIONS:")
    print("1. If titles are in PDFs but not extracted: Re-run extraction for affected papers")
    print("2. If titles are missing from PDFs: Check source data quality")
    print("3. If extraction failed: Review extraction logs and improve error handling")
