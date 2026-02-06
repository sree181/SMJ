#!/usr/bin/env python3
"""
Test the exact query used by the dashboard to see why it shows 751 instead of 1029
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def test_dashboard_query():
    """Test the exact query logic used by get_paper_counts_by_interval"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, password]):
        print("❌ Neo4j credentials not found")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Simulate the exact logic from get_paper_counts_by_interval
        start_year = 1985
        end_year = 2026
        intervals = []
        current_start = start_year
        total_count = 0
        
        print("=" * 80)
        print("🔍 TESTING DASHBOARD QUERY LOGIC")
        print("=" * 80)
        print()
        print(f"Start year: {start_year}, End year: {end_year}")
        print()
        
        while current_start < end_year:
            current_end = min(current_start + 5, end_year)
            
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.year >= $start_year 
                  AND p.year < $end_year
                  AND p.year > 0
                RETURN count(p) as count,
                       collect(p.paper_id) as paper_ids
            """, start_year=current_start, end_year=current_end)
            
            record = result.single()
            count = record['count'] if record else 0
            paper_ids = record['paper_ids'] if record else []
            
            intervals.append({
                'interval': f"{current_start}-{current_end-1}",
                'start_year': current_start,
                'end_year': current_end - 1,
                'count': count,
                'paper_ids': paper_ids
            })
            
            total_count += count
            print(f"Interval {current_start}-{current_end-1}: {count} papers")
            
            # Check for papers in 2025 specifically
            if current_start == 2025:
                year_2025_count = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year = 2025
                    RETURN count(p) as count
                """).single()["count"]
                print(f"   (Papers with year=2025: {year_2025_count})")
            
            current_start = current_end
        
        print()
        print("=" * 80)
        print(f"📊 TOTAL COUNT FROM INTERVALS: {total_count}")
        print("=" * 80)
        print()
        
        # Verify total papers
        total_papers = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
        print(f"📄 Total papers in database: {total_papers}")
        print()
        
        # Check papers excluded
        excluded = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0 OR p.year < 1985 OR p.year >= 2026
            RETURN count(p) as count
        """).single()["count"]
        
        print(f"❌ Papers excluded from query: {excluded}")
        print()
        
        # Check papers by year range
        before_1985 = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year < 1985
            RETURN count(p) as count
        """).single()["count"]
        
        after_2025 = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year >= 2026
            RETURN count(p) as count
        """).single()["count"]
        
        invalid_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN count(p) as count
        """).single()["count"]
        
        print("Breakdown of excluded papers:")
        print(f"   Before 1985: {before_1985}")
        print(f"   After 2025 (>= 2026): {after_2025}")
        print(f"   Invalid year (NULL or <= 0): {invalid_year}")
        print()
        
        # Check 2025 papers specifically
        papers_2025 = session.run("""
            MATCH (p:Paper)
            WHERE p.year = 2025
            RETURN count(p) as count
        """).single()["count"]
        
        print(f"📅 Papers with year = 2025: {papers_2025}")
        print()
        
        # Check what the 2020-2024 interval actually contains
        interval_2020_2024 = session.run("""
            MATCH (p:Paper)
            WHERE p.year >= 2020 
              AND p.year < 2025
              AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        interval_2025 = session.run("""
            MATCH (p:Paper)
            WHERE p.year >= 2025 
              AND p.year < 2026
              AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        print(f"📊 Interval 2020-2024: {interval_2020_2024} papers")
        print(f"📊 Interval 2025: {interval_2025} papers")
        print()
        
        if total_count == total_papers:
            print("✅ SUCCESS! Query returns all papers")
        else:
            print(f"⚠️  MISMATCH: Query returns {total_count} but database has {total_papers}")
            print(f"   Missing: {total_papers - total_count} papers")
            print()
            print("🔍 Investigating missing papers...")
            
            # Find papers not in any interval
            all_paper_ids = set()
            for interval in intervals:
                all_paper_ids.update(interval['paper_ids'])
            
            missing_papers = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p.year >= 1985 AND p.year < 2026 AND p.year > 0)
                RETURN p.paper_id as paper_id, p.year as year, p.title as title
                LIMIT 10
            """).data()
            
            if missing_papers:
                print("Sample papers not included in query:")
                for paper in missing_papers:
                    print(f"   [{paper['year']}] {paper.get('paper_id', 'N/A')}: {paper.get('title', 'No title')[:50]}")
    
    driver.close()

if __name__ == "__main__":
    test_dashboard_query()
