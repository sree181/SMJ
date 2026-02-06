#!/usr/bin/env python3
"""
Fix missing year values: Set year to 2025 for papers with year = 0 or NULL
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def fix_missing_years():
    """Set year to 2025 for papers with year = 0 or NULL"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, password]):
        print("❌ Neo4j credentials not found")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # First, check how many papers need fixing
        count_result = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN count(p) as count
        """).single()
        
        count = count_result["count"]
        print(f"📊 Found {count} papers with missing/invalid year")
        print()
        
        if count == 0:
            print("✅ No papers need fixing!")
            driver.close()
            return
        
        # Show sample papers before fixing
        print("Sample papers to be fixed:")
        samples = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN p.paper_id as paper_id, p.title as title, p.year as year
            LIMIT 10
        """).data()
        
        for i, paper in enumerate(samples, 1):
            title = paper.get("title", "No title")[:60]
            year = paper.get("year", "NULL")
            paper_id = paper.get("paper_id", "N/A")
            print(f"   {i}. [{year}] {title}... (ID: {paper_id})")
        print()
        
        # Update papers with year = 0 or NULL to 2025
        print("🔄 Updating year to 2025 for papers with missing/invalid year...")
        result = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            SET p.year = 2025
            RETURN count(p) as updated_count
        """)
        
        updated_count = result.single()["updated_count"]
        print(f"✅ Updated {updated_count} papers to year = 2025")
        print()
        
        # Verify the update
        print("🔍 Verifying update...")
        remaining = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN count(p) as count
        """).single()["count"]
        
        if remaining == 0:
            print("✅ All papers now have valid year values!")
        else:
            print(f"⚠️  Warning: {remaining} papers still have invalid year")
        
        print()
        
        # Show updated statistics
        total = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
        valid_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        year_2025 = session.run("""
            MATCH (p:Paper)
            WHERE p.year = 2025
            RETURN count(p) as count
        """).single()["count"]
        
        dashboard_range = session.run("""
            MATCH (p:Paper)
            WHERE p.year >= 1985 
              AND p.year <= 2025
              AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        print("📊 Updated Statistics:")
        print(f"   Total papers: {total}")
        print(f"   Papers with valid year: {valid_year}")
        print(f"   Papers with year = 2025: {year_2025}")
        print(f"   Papers in dashboard range (1985-2025): {dashboard_range}")
        print()
        
        if dashboard_range == total:
            print("✅ Dashboard will now show all papers!")
        else:
            print(f"⚠️  Dashboard will show {dashboard_range} out of {total} papers")
    
    driver.close()
    print()
    print("✅ Year fix complete!")

if __name__ == "__main__":
    fix_missing_years()
