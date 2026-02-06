#!/usr/bin/env python3
"""
Fix missing year values in Railway Neo4j database
This script can be run locally but connects to the same Neo4j database that Railway uses
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def fix_railway_database():
    """Set year to 2025 for papers with year = 0 or NULL in Railway's Neo4j database"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, password]):
        print("❌ Neo4j credentials not found in .env file")
        print("   Make sure NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are set")
        return
    
    print("=" * 80)
    print("🔧 FIXING RAILWAY NEO4J DATABASE")
    print("=" * 80)
    print()
    print(f"📡 Connecting to: {uri}")
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Check current status
            total = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            invalid_year = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NULL OR p.year <= 0
                RETURN count(p) as count
            """).single()["count"]
            
            dashboard_count = session.run("""
                MATCH (p:Paper)
                WHERE p.year >= 1985 
                  AND p.year < 2026
                  AND p.year > 0
                RETURN count(p) as count
            """).single()["count"]
            
            print(f"📊 Current Status:")
            print(f"   Total papers: {total}")
            print(f"   Papers with invalid year: {invalid_year}")
            print(f"   Papers in dashboard range: {dashboard_count}")
            print()
            
            if invalid_year == 0:
                print("✅ All papers already have valid year values!")
                print(f"✅ Dashboard should show {dashboard_count} papers")
                driver.close()
                return
            
            # Show sample papers before fixing
            print(f"📋 Sample papers to be fixed ({invalid_year} total):")
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
            total_after = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            valid_year_after = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL AND p.year > 0
                RETURN count(p) as count
            """).single()["count"]
            
            dashboard_count_after = session.run("""
                MATCH (p:Paper)
                WHERE p.year >= 1985 
                  AND p.year < 2026
                  AND p.year > 0
                RETURN count(p) as count
            """).single()["count"]
            
            print("📊 Updated Statistics:")
            print(f"   Total papers: {total_after}")
            print(f"   Papers with valid year: {valid_year_after}")
            print(f"   Papers in dashboard range (1985-2026): {dashboard_count_after}")
            print()
            
            if dashboard_count_after == total_after:
                print("✅ SUCCESS! Railway dashboard will now show all papers!")
                print()
                print("📝 Next Steps:")
                print("   1. Railway should automatically pick up the database changes")
                print("   2. If dashboard still shows 0, try refreshing the page")
                print("   3. If still 0, check Railway logs for connection issues")
            else:
                print(f"⚠️  Dashboard will show {dashboard_count_after} out of {total_after} papers")
        
        driver.close()
        print()
        print("✅ Database fix complete!")
        
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        print()
        print("🔍 Troubleshooting:")
        print("   1. Check that NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD are correct in .env")
        print("   2. Verify the Neo4j database is accessible")
        print("   3. Make sure you're using the same database that Railway connects to")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_railway_database()
