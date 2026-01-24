#!/usr/bin/env python3
"""
Investigate Author Ingestion Issue
Checks extraction, normalization, and ingestion pipeline
"""

import os
import json
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_extraction_results():
    """Check if authors are in extraction results"""
    print("=" * 80)
    print("1. CHECKING EXTRACTION RESULTS")
    print("=" * 80)
    
    # Check if we have any extraction result files
    result_files = list(Path(".").glob("**/extraction_results/*.json"))
    if not result_files:
        result_files = list(Path(".").glob("**/*extraction*.json"))
    
    if result_files:
        print(f"Found {len(result_files)} extraction result files")
        sample_file = result_files[0]
        print(f"\nChecking sample file: {sample_file}")
        
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        if "authors" in data:
            authors = data["authors"]
            print(f"  ✓ Authors found in extraction: {len(authors)}")
            if authors:
                print(f"  Sample author: {authors[0]}")
        else:
            print("  ✗ No 'authors' key in extraction result")
    else:
        print("  ⚠️  No extraction result files found")
    
    # Check pipeline progress files
    progress_files = list(Path(".").glob("**/*progress*.json"))
    if progress_files:
        print(f"\nFound {len(progress_files)} progress files")
        for pf in progress_files[:3]:
            print(f"  - {pf}")

def check_neo4j_authors():
    """Check authors in Neo4j"""
    print("\n" + "=" * 80)
    print("2. CHECKING NEO4J DATABASE")
    print("=" * 80)
    
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
    )
    
    try:
        with driver.session() as session:
            # Check Author nodes
            result = session.run("MATCH (a:Author) RETURN count(a) as count")
            author_count = result.single()['count']
            print(f"Author nodes: {author_count}")
            
            # Check AUTHORED relationships
            result = session.run("MATCH (a:Author)-[r:AUTHORED]->(p:Paper) RETURN count(r) as count")
            authored_count = result.single()['count']
            print(f"AUTHORED relationships: {authored_count}")
            
            # Check AUTHORED_BY relationships (opposite direction)
            result = session.run("MATCH (p:Paper)-[r:AUTHORED_BY]->(a:Author) RETURN count(r) as count")
            authored_by_count = result.single()['count']
            print(f"AUTHORED_BY relationships: {authored_by_count}")
            
            # Check papers with author info in metadata
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.authors IS NOT NULL OR p.author_names IS NOT NULL
                RETURN count(p) as count
            """)
            papers_with_author_metadata = result.single()['count']
            print(f"Papers with author metadata: {papers_with_author_metadata}")
            
            # Sample a paper to see its structure
            result = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id, keys(p) as keys
                LIMIT 1
            """)
            if result.peek():
                record = result.single()
                print(f"\nSample paper structure:")
                print(f"  Paper ID: {record['p.paper_id']}")
                print(f"  Properties: {record['keys']}")
    
    finally:
        driver.close()

def check_validation_issue():
    """Check if validation is the issue"""
    print("\n" + "=" * 80)
    print("3. CHECKING VALIDATION LOGIC")
    print("=" * 80)
    
    from data_validator import DataValidator
    
    validator = DataValidator()
    
    # Test with sample author data (as extracted)
    sample_author = {
        "full_name": "John Smith",
        "given_name": "John",
        "family_name": "Smith",
        "position": 1,
        "corresponding_author": False
    }
    
    print("Testing validation with sample author (without author_id):")
    print(f"  Input: {sample_author}")
    
    validated = validator.validate_author(sample_author)
    
    if validated:
        print(f"  ✓ Validation passed: {validated}")
    else:
        print("  ✗ Validation FAILED - This is the issue!")
        print("  The AuthorData model requires 'author_id' but extraction doesn't provide it")

if __name__ == "__main__":
    check_extraction_results()
    check_neo4j_authors()
    check_validation_issue()
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
