#!/usr/bin/env python3
"""
Check paper counts: Compare source PDFs with papers in Neo4j
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from pathlib import Path
from collections import defaultdict

load_dotenv()

def count_source_pdfs():
    """Count PDF files in year folders"""
    base_dir = Path(".")
    pdf_counts = defaultdict(int)
    all_pdfs = []
    
    # Check year folders (2020-2024, 2015-2019, etc.)
    year_folders = sorted([d for d in base_dir.glob("20*") if d.is_dir()])
    
    for year_folder in year_folders:
        pdf_files = list(year_folder.glob("*.pdf"))
        pdf_counts[year_folder.name] = len(pdf_files)
        all_pdfs.extend(pdf_files)
    
    # Also check root directory
    root_pdfs = list(base_dir.glob("*.pdf"))
    if root_pdfs:
        pdf_counts["root"] = len(root_pdfs)
        all_pdfs.extend(root_pdfs)
    
    return pdf_counts, all_pdfs

def get_neo4j_paper_counts():
    """Get paper counts from Neo4j"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, password]):
        print("❌ Neo4j credentials not found in environment")
        return None
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Total paper count
            total_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            
            # Count by year
            year_result = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL AND p.year > 0
                RETURN p.year as year, count(p) as count
                ORDER BY year
            """)
            
            papers_by_year = {}
            for record in year_result:
                papers_by_year[record["year"]] = record["count"]
            
            # Count papers without year
            no_year_count = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NULL OR p.year <= 0
                RETURN count(p) as count
            """).single()["count"]
            
            # Count papers with relationships
            papers_with_theories = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->()
                RETURN count(DISTINCT p) as count
            """).single()["count"]
            
            papers_with_phenomena = session.run("""
                MATCH (p:Paper)-[:STUDIES_PHENOMENON]->()
                RETURN count(DISTINCT p) as count
            """).single()["count"]
            
            papers_with_authors = session.run("""
                MATCH (p:Paper)<-[:AUTHORED]-(:Author)
                RETURN count(DISTINCT p) as count
            """).single()["count"]
            
            # Year range
            year_range = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL AND p.year > 0
                RETURN min(p.year) as min_year, max(p.year) as max_year
            """).single()
            
            min_year = year_range["min_year"]
            max_year = year_range["max_year"]
            
            # Get sample paper IDs
            sample_papers = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, p.title as title, p.year as year
                ORDER BY p.year DESC
                LIMIT 5
            """).data()
        
        driver.close()
        
        return {
            "total": total_count,
            "by_year": papers_by_year,
            "no_year": no_year_count,
            "with_theories": papers_with_theories,
            "with_phenomena": papers_with_phenomena,
            "with_authors": papers_with_authors,
            "min_year": min_year,
            "max_year": max_year,
            "sample_papers": sample_papers
        }
        
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 80)
    print("📊 PAPER COUNT COMPARISON: SOURCE PDFs vs NEO4J")
    print("=" * 80)
    print()
    
    # Count source PDFs
    print("📁 Counting source PDF files...")
    pdf_counts, all_pdfs = count_source_pdfs()
    total_source = len(all_pdfs)
    
    print(f"   Total PDF files found: {total_source}")
    print()
    print("   Breakdown by folder:")
    for folder, count in sorted(pdf_counts.items()):
        print(f"      {folder}: {count} PDFs")
    print()
    
    # Get Neo4j counts
    print("🔍 Querying Neo4j...")
    neo4j_data = get_neo4j_paper_counts()
    
    if neo4j_data:
        print()
        print("=" * 80)
        print("📊 NEO4J PAPER STATISTICS")
        print("=" * 80)
        print()
        
        total_neo4j = neo4j_data["total"]
        print(f"📄 Total papers in Neo4j: {total_neo4j}")
        print()
        
        if neo4j_data["min_year"] and neo4j_data["max_year"]:
            print(f"📅 Year range: {neo4j_data['min_year']} - {neo4j_data['max_year']}")
        print()
        
        print("📊 Papers by year (top 20):")
        sorted_years = sorted(neo4j_data["by_year"].items(), key=lambda x: x[1], reverse=True)[:20]
        for year, count in sorted_years:
            print(f"   {year}: {count} papers")
        
        if neo4j_data["no_year"] > 0:
            print(f"   (No year or invalid year: {neo4j_data['no_year']} papers)")
        print()
        
        print("🔗 Papers with relationships:")
        print(f"   With Theories: {neo4j_data['with_theories']} papers")
        print(f"   With Phenomena: {neo4j_data['with_phenomena']} papers")
        print(f"   With Authors: {neo4j_data['with_authors']} papers")
        print()
        
        print("📋 Sample papers (most recent):")
        for i, paper in enumerate(neo4j_data["sample_papers"], 1):
            title = paper.get("title", "No title")[:60]
            year = paper.get("year", "N/A")
            paper_id = paper.get("paper_id", "N/A")
            print(f"   {i}. [{year}] {title}... (ID: {paper_id})")
        print()
        
        # Comparison
        print("=" * 80)
        print("📊 COMPARISON")
        print("=" * 80)
        print()
        print(f"   Source PDFs: {total_source}")
        print(f"   Papers in Neo4j: {total_neo4j}")
        print()
        
        if total_source > 0:
            ingestion_rate = (total_neo4j / total_source * 100) if total_source > 0 else 0
            print(f"   Ingestion rate: {ingestion_rate:.1f}%")
            
            if total_neo4j < total_source:
                missing = total_source - total_neo4j
                print(f"   ⚠️  {missing} PDFs not yet ingested")
            elif total_neo4j > total_source:
                extra = total_neo4j - total_source
                print(f"   ℹ️  {extra} more papers in Neo4j than source PDFs (may include duplicates or different sources)")
            else:
                print(f"   ✅ All source PDFs are in Neo4j")
        print()
    else:
        print("❌ Could not retrieve data from Neo4j")
        print()

if __name__ == "__main__":
    main()
