#!/usr/bin/env python3
"""
Analyze why dashboard shows 751 papers but Neo4j has 1029
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_discrepancy():
    """Analyze the discrepancy between total papers and dashboard count"""
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
        
        # Papers with valid year > 0
        valid_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        # Papers with invalid year (NULL or <= 0)
        invalid_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN count(p) as count
        """).single()["count"]
        
        # Papers in dashboard range (1985-2025, year > 0)
        dashboard_range = session.run("""
            MATCH (p:Paper)
            WHERE p.year >= 1985 
              AND p.year < 2025
              AND p.year > 0
            RETURN count(p) as count
        """).single()["count"]
        
        # Papers outside dashboard range but with valid year
        outside_range = session.run("""
            MATCH (p:Paper)
            WHERE p.year > 0 
              AND (p.year < 1985 OR p.year >= 2025)
            RETURN count(p) as count
        """).single()["count"]
        
        # Year range breakdown
        min_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0
            RETURN min(p.year) as min_year
        """).single()["min_year"]
        
        max_year = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0
            RETURN max(p.year) as max_year
        """).single()["max_year"]
        
        # Papers by year range
        before_1985 = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year < 1985
            RETURN count(p) as count
        """).single()["count"]
        
        after_2024 = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year >= 2025
            RETURN count(p) as count
        """).single()["count"]
        
        print("=" * 80)
        print("📊 PAPER COUNT DISCREPANCY ANALYSIS")
        print("=" * 80)
        print()
        print(f"📄 Total papers in Neo4j: {total}")
        print()
        print("Breakdown:")
        print(f"   ✅ Papers with valid year (year > 0): {valid_year}")
        print(f"   ❌ Papers with invalid year (NULL or <= 0): {invalid_year}")
        print()
        print("Dashboard Filter (1985-2024, year > 0):")
        print(f"   📊 Papers shown in dashboard: {dashboard_range}")
        print()
        print("Papers excluded from dashboard:")
        print(f"   📅 Before 1985: {before_1985} papers")
        print(f"   📅 2025 and later: {after_2024} papers")
        print(f"   ❌ Invalid year: {invalid_year} papers")
        print(f"   📊 Total excluded: {before_1985 + after_2024 + invalid_year} papers")
        print()
        print("Verification:")
        print(f"   Dashboard count ({dashboard_range}) + Excluded ({before_1985 + after_2024 + invalid_year}) = {dashboard_range + before_1985 + after_2024 + invalid_year}")
        print(f"   Should equal total: {total}")
        print()
        
        if dashboard_range + before_1985 + after_2024 + invalid_year == total:
            print("✅ Math checks out!")
        else:
            print("⚠️  Math doesn't match - there may be an issue")
        
        print()
        print("Year range of valid papers:")
        print(f"   Earliest: {min_year}")
        print(f"   Latest: {max_year}")
        print()
        
        # Sample papers with invalid year
        print("Sample papers with invalid year:")
        invalid_samples = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NULL OR p.year <= 0
            RETURN p.paper_id as paper_id, p.title as title, p.year as year
            LIMIT 5
        """).data()
        
        for i, paper in enumerate(invalid_samples, 1):
            title = paper.get("title", "No title")[:60]
            year = paper.get("year", "NULL")
            paper_id = paper.get("paper_id", "N/A")
            print(f"   {i}. [{year}] {title}... (ID: {paper_id})")
        
        print()
        print("Sample papers before 1985:")
        before_samples = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year < 1985
            RETURN p.paper_id as paper_id, p.title as title, p.year as year
            ORDER BY p.year DESC
            LIMIT 5
        """).data()
        
        for i, paper in enumerate(before_samples, 1):
            title = paper.get("title", "No title")[:60]
            year = paper.get("year", "N/A")
            paper_id = paper.get("paper_id", "N/A")
            print(f"   {i}. [{year}] {title}... (ID: {paper_id})")
        
        print()
        print("Sample papers from 2025+:")
        after_samples = session.run("""
            MATCH (p:Paper)
            WHERE p.year IS NOT NULL AND p.year > 0 AND p.year >= 2025
            RETURN p.paper_id as paper_id, p.title as title, p.year as year
            ORDER BY p.year
            LIMIT 5
        """).data()
        
        for i, paper in enumerate(after_samples, 1):
            title = paper.get("title", "No title")[:60]
            year = paper.get("year", "N/A")
            paper_id = paper.get("paper_id", "N/A")
            print(f"   {i}. [{year}] {title}... (ID: {paper_id})")
    
    driver.close()

if __name__ == "__main__":
    analyze_discrepancy()
