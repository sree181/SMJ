#!/usr/bin/env python3
"""
Analyze results from high-performance pipeline run
Provides detailed analysis of extraction quality, normalization coverage, and performance metrics
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any
import statistics

def analyze_progress_file(progress_file: Path) -> Dict[str, Any]:
    """Analyze progress file"""
    if not progress_file.exists():
        return {"error": "Progress file not found"}
    
    with open(progress_file, 'r') as f:
        data = json.load(f)
    
    processed = data.get("processed_papers", [])
    stats = data.get("stats", {})
    
    return {
        "processed_count": len(processed),
        "processed_papers": processed,
        "stats": stats
    }

def analyze_stats_file(stats_file: Path) -> Dict[str, Any]:
    """Analyze statistics file"""
    if not stats_file.exists():
        return {"error": "Stats file not found"}
    
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    return stats

def analyze_log_file(log_file: Path) -> Dict[str, Any]:
    """Analyze log file for errors and patterns"""
    if not log_file.exists():
        return {"error": "Log file not found"}
    
    errors = []
    warnings = []
    completed_papers = []
    failed_papers = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if "ERROR" in line or "error" in line.lower():
                errors.append(line.strip())
            if "WARNING" in line or "warning" in line.lower():
                warnings.append(line.strip())
            if "✓ Completed" in line or "COMPLETED" in line:
                # Extract paper ID
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.startswith("2025_"):
                        completed_papers.append(part)
                        break
            if "✗ Failed" in line or "FAILED" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.startswith("2025_"):
                        failed_papers.append(part)
                        break
    
    return {
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "errors": errors[:20],  # First 20 errors
        "warnings": warnings[:20],  # First 20 warnings
        "completed_papers": list(set(completed_papers)),
        "failed_papers": list(set(failed_papers))
    }

def check_neo4j_ingestion(paper_ids: List[str]) -> Dict[str, Any]:
    """Check what was actually ingested into Neo4j"""
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            return {"error": "Neo4j credentials not found"}
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Count papers
            paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            
            # Count by year
            papers_by_year = session.run("""
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL
                RETURN p.year as year, count(p) as count
                ORDER BY year
            """).data()
            
            # Count entities
            theory_count = session.run("MATCH (t:Theory) RETURN count(t) as count").single()["count"]
            method_count = session.run("MATCH (m:Method) RETURN count(m) as count").single()["count"]
            phenomenon_count = session.run("MATCH (ph:Phenomenon) RETURN count(ph) as count").single()["count"]
            
            # Check specific papers
            found_papers = []
            for paper_id in paper_ids[:10]:  # Check first 10
                result = session.run(
                    "MATCH (p:Paper {paper_id: $paper_id}) RETURN p.paper_id as id, p.title as title",
                    paper_id=paper_id
                ).single()
                if result:
                    found_papers.append(paper_id)
        
        driver.close()
        
        return {
            "total_papers": paper_count,
            "papers_by_year": {r["year"]: r["count"] for r in papers_by_year},
            "theory_count": theory_count,
            "method_count": method_count,
            "phenomenon_count": phenomenon_count,
            "found_papers": found_papers,
            "checked_papers": len(paper_ids[:10])
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("HIGH-PERFORMANCE PIPELINE RESULTS ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze progress file
    print("📋 Analyzing progress file...")
    progress_file = Path("high_performance_progress.json")
    progress_data = analyze_progress_file(progress_file)
    
    if "error" in progress_data:
        print(f"   {progress_data['error']}")
    else:
        print(f"   ✅ Processed papers: {progress_data['processed_count']}")
        if progress_data.get("stats"):
            stats = progress_data["stats"]
            print(f"   📊 Success rate: {stats.get('success_rate', 0):.1f}%")
            print(f"   ⚡ Papers/hour: {stats.get('papers_per_hour', 0):.1f}")
            print(f"   🔍 Normalization coverage: {stats.get('normalization_coverage', 0):.1f}%")
    print()
    
    # Analyze stats file
    print("📊 Analyzing statistics file...")
    stats_file = Path("high_performance_stats.json")
    stats_data = analyze_stats_file(stats_file)
    
    if "error" in stats_data:
        print(f"   {stats_data['error']}")
    else:
        print(f"   ✅ Processed: {stats_data.get('processed', 0)}")
        print(f"   ❌ Failed: {stats_data.get('failed', 0)}")
        print(f"   ⏭️  Skipped: {stats_data.get('skipped', 0)}")
        print(f"   📈 Papers/hour: {stats_data.get('papers_per_hour', 0):.1f}")
        print(f"   ⏱️  Avg extraction time: {stats_data.get('avg_extraction_time', 0):.1f}s")
        print(f"   🔍 Normalization coverage: {stats_data.get('normalization_coverage', 0):.1f}%")
        print(f"   📦 Theories extracted: {stats_data.get('total_theories', 0)}")
        print(f"   📦 Phenomena extracted: {stats_data.get('total_phenomena', 0)}")
        print(f"   📦 Methods extracted: {stats_data.get('total_methods', 0)}")
    print()
    
    # Analyze log file
    print("📝 Analyzing log file...")
    log_file = Path("high_performance_pipeline.log")
    log_data = analyze_log_file(log_file)
    
    if "error" in log_data:
        print(f"   {log_data['error']}")
    else:
        print(f"   ✅ Completed papers: {len(log_data['completed_papers'])}")
        print(f"   ❌ Failed papers: {len(log_data['failed_papers'])}")
        print(f"   ⚠️  Errors: {log_data['total_errors']}")
        print(f"   ⚠️  Warnings: {log_data['total_warnings']}")
        
        if log_data['failed_papers']:
            print(f"\n   Failed papers:")
            for paper_id in log_data['failed_papers']:
                print(f"      - {paper_id}")
    print()
    
    # Check Neo4j ingestion
    if progress_data.get("processed_papers"):
        print("🗄️  Checking Neo4j ingestion...")
        neo4j_data = check_neo4j_ingestion(progress_data["processed_papers"])
        
        if "error" in neo4j_data:
            print(f"   ❌ {neo4j_data['error']}")
        else:
            print(f"   ✅ Total papers in Neo4j: {neo4j_data['total_papers']}")
            print(f"   📊 Theories: {neo4j_data['theory_count']}")
            print(f"   📊 Methods: {neo4j_data['method_count']}")
            print(f"   📊 Phenomena: {neo4j_data['phenomenon_count']}")
            
            if neo4j_data.get('papers_by_year'):
                print(f"\n   Papers by year:")
                for year, count in sorted(neo4j_data['papers_by_year'].items()):
                    print(f"      {year}: {count}")
            
            print(f"\n   Verified papers in Neo4j: {len(neo4j_data.get('found_papers', []))}/{neo4j_data.get('checked_papers', 0)}")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if progress_data.get("processed_count", 0) > 0:
        print(f"✅ Successfully processed: {progress_data['processed_count']} papers")
        
        if stats_data.get("papers_per_hour", 0) > 0:
            print(f"⚡ Processing rate: {stats_data['papers_per_hour']:.1f} papers/hour")
        
        if stats_data.get("normalization_coverage", 0) > 0:
            print(f"🔍 Normalization coverage: {stats_data['normalization_coverage']:.1f}%")
        
        if log_data.get("total_errors", 0) > 0:
            print(f"⚠️  Errors encountered: {log_data['total_errors']}")
            print(f"   Review log file for details: {log_file}")
    else:
        print("⏳ No papers processed yet. Check if pipeline is still running.")
    
    print()

if __name__ == "__main__":
    main()
