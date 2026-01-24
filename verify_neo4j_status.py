#!/usr/bin/env python3
"""
Complete verification of Neo4j status - check what papers are actually ingested
"""

import json
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

def get_papers_in_neo4j():
    """Get all papers currently in Neo4j with details"""
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("⚠️  Neo4j credentials not found in environment")
        return {}
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session() as session:
            # Get all papers
            result = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, p.title as title, p.year as year
                ORDER BY p.year DESC, p.paper_id
            """)
            
            papers = {}
            for record in result:
                paper_id = record["paper_id"]
                papers[paper_id] = {
                    "title": record["title"],
                    "year": record["year"]
                }
            
            # Get statistics
            stats = {}
            
            # Count by year
            year_result = session.run("""
                MATCH (p:Paper)
                RETURN p.year as year, count(p) as count
                ORDER BY year
            """)
            stats["by_year"] = {record["year"]: record["count"] for record in year_result}
            
            # Count nodes
            node_counts = {}
            node_types = ["Paper", "Theory", "Method", "Phenomenon", "Author", "Variable", "Finding"]
            for node_type in node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                node_counts[node_type] = result.single()["count"]
            stats["node_counts"] = node_counts
            
            # Count relationships
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            stats["relationships"] = {record["rel_type"]: record["count"] for record in rel_result}
        
        driver.close()
        return papers, stats
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        return {}, {}

def main():
    print("=" * 80)
    print("COMPLETE NEO4J VERIFICATION")
    print("=" * 80)
    print()
    
    # Get papers in Neo4j
    print("🗄️  Connecting to Neo4j and retrieving all papers...")
    neo4j_papers, stats = get_papers_in_neo4j()
    
    if not neo4j_papers:
        print("❌ Could not connect to Neo4j or no papers found")
        print("   Check your .env file and Neo4j connection")
        return
    
    print(f"✅ Found {len(neo4j_papers)} papers in Neo4j")
    print()
    
    # Display statistics
    print("=" * 80)
    print("NEO4J STATISTICS")
    print("=" * 80)
    print()
    
    if stats.get("node_counts"):
        print("📊 Node Counts:")
        for node_type, count in stats["node_counts"].items():
            print(f"   {node_type}: {count}")
        print()
    
    if stats.get("by_year"):
        print("📅 Papers by Year:")
        for year in sorted(stats["by_year"].keys()):
            count = stats["by_year"][year]
            print(f"   {year}: {count} papers")
        print()
    
    if stats.get("relationships"):
        print("🔗 Top Relationships:")
        for rel_type, count in list(stats["relationships"].items())[:10]:
            print(f"   {rel_type}: {count}")
        print()
    
    # Save to file
    output_file = Path("neo4j_verification.json")
    with open(output_file, 'w') as f:
        json.dump({
            "total_papers": len(neo4j_papers),
            "papers": neo4j_papers,
            "statistics": stats
        }, f, indent=2, default=str)
    
    print(f"💾 Full verification saved to: {output_file}")
    print()
    
    # Compare with folder papers
    print("=" * 80)
    print("COMPARISON WITH FOLDER PAPERS")
    print("=" * 80)
    print()
    
    # Get papers in folders
    base_dir = Path(".")
    folder_papers = set()
    for year_folder in sorted(base_dir.glob("20*")):
        if year_folder.is_dir():
            for pdf_file in year_folder.glob("*.pdf"):
                folder_papers.add(pdf_file.stem)
    
    for pdf_file in base_dir.glob("*.pdf"):
        folder_papers.add(pdf_file.stem)
    
    neo4j_paper_ids = set(neo4j_papers.keys())
    missing_in_neo4j = folder_papers - neo4j_paper_ids
    extra_in_neo4j = neo4j_paper_ids - folder_papers
    
    print(f"📁 Papers in folders: {len(folder_papers)}")
    print(f"🗄️  Papers in Neo4j: {len(neo4j_paper_ids)}")
    print(f"❌ Missing in Neo4j: {len(missing_in_neo4j)}")
    print(f"⚠️  Extra in Neo4j (not in folders): {len(extra_in_neo4j)}")
    print()
    
    if missing_in_neo4j:
        print(f"📝 Papers to process: {len(missing_in_neo4j)}")
        print("   Sample (first 20):")
        for paper_id in sorted(list(missing_in_neo4j))[:20]:
            print(f"      {paper_id}")
        if len(missing_in_neo4j) > 20:
            print(f"      ... and {len(missing_in_neo4j) - 20} more")
        print()
    
    if extra_in_neo4j:
        print(f"⚠️  Papers in Neo4j but not in folders: {len(extra_in_neo4j)}")
        print("   Sample (first 10):")
        for paper_id in sorted(list(extra_in_neo4j))[:10]:
            print(f"      {paper_id}")
        print()

if __name__ == "__main__":
    main()
