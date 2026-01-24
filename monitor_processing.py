#!/usr/bin/env python3
"""
Real-time monitoring script for batch processing
Shows progress, statistics, and system health
"""

import time
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class ProcessingMonitor:
    """Monitor batch processing progress in real-time"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self.connect()
    
    def connect(self):
        """Connect to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            print("✓ Connected to Neo4j")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def get_current_stats(self):
        """Get current knowledge graph statistics"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                stats = {}
                
                # Get node counts
                node_types = ['Paper', 'ResearchQuestion', 'Methodology', 'Finding', 'Contribution', 'Entity']
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    stats[node_type.lower()] = result.single()['count']
                
                # Get relationship count
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                stats['relationships'] = result.single()['count']
                
                # Get papers by year
                result = session.run("MATCH (p:Paper) RETURN p.year as year, count(p) as count ORDER BY year")
                stats['papers_by_year'] = {str(record['year']): record['count'] for record in result}
                
                return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def get_processing_logs(self):
        """Get recent processing logs"""
        log_file = Path("batch_processing.log")
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Get last 20 lines
                return lines[-20:]
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def display_dashboard(self):
        """Display real-time dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🔍 SMJ Batch Processing Monitor")
        print("=" * 50)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get current stats
        stats = self.get_current_stats()
        
        if stats:
            print("📊 Knowledge Graph Statistics:")
            print(f"  📄 Papers: {stats.get('paper', 0)}")
            print(f"  ❓ Research Questions: {stats.get('researchquestion', 0)}")
            print(f"  🔬 Methodologies: {stats.get('methodology', 0)}")
            print(f"  📈 Findings: {stats.get('finding', 0)}")
            print(f"  🏆 Contributions: {stats.get('contribution', 0)}")
            print(f"  🏷️  Entities: {stats.get('entity', 0)}")
            print(f"  🔗 Relationships: {stats.get('relationships', 0)}")
            print()
            
            if stats.get('papers_by_year'):
                print("📅 Papers by Year:")
                for year, count in sorted(stats['papers_by_year'].items()):
                    print(f"  {year}: {count} papers")
                print()
        
        # Show recent logs
        logs = self.get_processing_logs()
        if logs:
            print("📝 Recent Processing Logs:")
            for line in logs[-10:]:  # Show last 10 lines
                print(f"  {line.strip()}")
            print()
        
        print("Press Ctrl+C to stop monitoring")
    
    def monitor(self, refresh_interval: int = 10):
        """Start monitoring with specified refresh interval"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
        finally:
            if self.driver:
                self.driver.close()

def main():
    """Main monitoring function"""
    monitor = ProcessingMonitor()
    monitor.monitor(refresh_interval=10)

if __name__ == "__main__":
    main()
