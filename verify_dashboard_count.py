#!/usr/bin/env python3
"""
Verify that dashboard will now show 1029 papers
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def verify_dashboard_count():
    """Verify dashboard query returns all papers"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, password]):
        print("❌ Neo4j credentials not found")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Total papers
        total = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
        
        # Simulate dashboard query (1985-2026, year > 0)
        dashboard_count = 0
        start_year = 1985
        end_year = 2026
        
        current_start = start_year
        while current_start < end_year:
            current_end = min(current_start + 5, end_year)
            
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.year >= $start_year 
                  AND p.year < $end_year
                  AND p.year > 0
                RETURN count(p) as count
            """, start_year=current_start, end_year=current_end)
            
            count = result.single()["count"]
            dashboard_count += count
            print(f"   Interval {current_start}-{current_end-1}: {count} papers")
            
            current_start = current_end
        
        print()
        print("=" * 80)
        print("📊 DASHBOARD COUNT VERIFICATION")
        print("=" * 80)
        print()
        print(f"📄 Total papers in Neo4j: {total}")
        print(f"📊 Papers in dashboard (1985-2026): {dashboard_count}")
        print()
        
        if dashboard_count == total:
            print("✅ SUCCESS! Dashboard will now show all papers!")
        else:
            print(f"⚠️  Dashboard shows {dashboard_count} out of {total} papers")
            print(f"   Missing: {total - dashboard_count} papers")
        
        # Check for any papers still excluded
        excluded = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0 OR p.year < 1985 OR p.year >= 2026
            RETURN count(p) as count
        """).single()["count"]
        
        if excluded > 0:
            print(f"   ⚠️  {excluded} papers still excluded")
        else:
            print("   ✅ No papers excluded")
    
    driver.close()

if __name__ == "__main__":
    verify_dashboard_count()
