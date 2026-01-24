#!/usr/bin/env python3
"""
Real-time monitoring script for batch processing
Shows progress, recent papers, and Neo4j status
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def get_progress_status():
    """Get current progress from progress file"""
    progress_file = Path("batch_extraction_progress.json")
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {"processed_papers": [], "failed_papers": []}

def get_log_tail(log_file: Path, lines: int = 20):
    """Get last N lines from log file"""
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except:
        return []

def get_neo4j_status():
    """Get current Neo4j statistics"""
    try:
        uri = os.getenv('NEO4J_URI')
        user = os.getenv('NEO4J_USER')
        password = os.getenv('NEO4J_PASSWORD')
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Paper count
            paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()["count"]
            
            # Recent papers (last 5)
            recent_papers = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, 
                       p.title as title,
                       p.publication_year as year
                ORDER BY p.paper_id DESC
                LIMIT 5
            """).data()
            
            # Node counts
            node_counts = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """).data()
            
            # Relationship counts
            rel_counts = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """).data()
        
        driver.close()
        
        return {
            "paper_count": paper_count,
            "recent_papers": recent_papers,
            "node_counts": node_counts,
            "rel_counts": rel_counts
        }
    except Exception as e:
        return {"error": str(e)}

def print_status():
    """Print current status"""
    print("\n" + "=" * 80)
    print("  BATCH PROCESSING STATUS MONITOR")
    print("=" * 80)
    
    # Progress file status
    progress = get_progress_status()
    processed = len(progress.get("processed_papers", []))
    failed = len(progress.get("failed_papers", []))
    
    print(f"\n📊 Progress File Status:")
    print(f"   ✅ Processed: {processed} papers")
    print(f"   ❌ Failed: {failed} papers")
    
    if processed > 0:
        print(f"\n   Recent processed papers:")
        for paper_id in progress.get("processed_papers", [])[-5:]:
            print(f"      • {paper_id}")
    
    if failed > 0:
        print(f"\n   Failed papers:")
        for paper_id in progress.get("failed_papers", [])[-5:]:
            print(f"      • {paper_id}")
    
    # Neo4j status
    print(f"\n📊 Neo4j Database Status:")
    neo4j_status = get_neo4j_status()
    
    if "error" in neo4j_status:
        print(f"   ⚠️  Error connecting to Neo4j: {neo4j_status['error']}")
    else:
        print(f"   ✅ Total Papers: {neo4j_status['paper_count']}")
        
        if neo4j_status.get("recent_papers"):
            print(f"\n   Recent papers in Neo4j:")
            for paper in neo4j_status["recent_papers"]:
                title = paper.get("title", "N/A")[:60]
                year = paper.get("year", "N/A")
                print(f"      • {paper['paper_id']} ({year}): {title}...")
        
        if neo4j_status.get("node_counts"):
            print(f"\n   Top Node Types:")
            for node in neo4j_status["node_counts"][:5]:
                print(f"      • {node['label']}: {node['count']}")
        
        if neo4j_status.get("rel_counts"):
            print(f"\n   Top Relationship Types:")
            for rel in neo4j_status["rel_counts"][:5]:
                print(f"      • {rel['type']}: {rel['count']}")
    
    # Log file status
    log_file = Path("batch_extraction.log")
    if log_file.exists():
        log_size = log_file.stat().st_size
        print(f"\n📄 Log File Status:")
        print(f"   ✅ batch_extraction.log exists ({log_size / 1024:.1f} KB)")
        
        # Show last few log lines
        log_lines = get_log_tail(log_file, 10)
        if log_lines:
            print(f"\n   Last 10 log lines:")
            for line in log_lines:
                print(f"      {line.rstrip()}")
    else:
        print(f"\n📄 Log File Status:")
        print(f"   ⚠️  batch_extraction.log not found")
    
    print("\n" + "=" * 80)
    print(f"  Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

def monitor_loop(interval: int = 30):
    """Monitor in a loop"""
    print("Starting batch processing monitor...")
    print(f"Update interval: {interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            print_status()
            print(f"\n⏳ Waiting {interval} seconds for next update...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        monitor_loop(interval)
    else:
        print_status()

