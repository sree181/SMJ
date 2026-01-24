#!/usr/bin/env python3
"""
Clear all data from Neo4j Aura instance
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_neo4j():
    """Clear all nodes and relationships from Neo4j"""
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://fe285b91.databases.neo4j.io')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw')
    
    print(f"🔗 Connecting to Neo4j: {uri}")
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Get current counts
            print("\n📊 Current data in Neo4j:")
            
            # Count nodes by label
            node_counts = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC")
            total_nodes = 0
            for record in node_counts:
                labels = record['labels']
                count = record['count']
                total_nodes += count
                print(f"  {labels}: {count}")
            
            # Count relationships
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            print(f"  Relationships: {rel_count}")
            print(f"  Total nodes: {total_nodes}")
            
            if total_nodes == 0:
                print("✅ Neo4j is already empty!")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: About to delete ALL data from Neo4j!")
            print(f"   - {total_nodes} nodes")
            print(f"   - {rel_count} relationships")
            
            response = input("\nAre you sure you want to proceed? (yes/no): ").lower().strip()
            
            if response != 'yes':
                print("❌ Operation cancelled.")
                return
            
            print("\n🗑️  Deleting all data...")
            
            # Delete all relationships first
            print("  Deleting relationships...")
            result = session.run("MATCH ()-[r]->() DELETE r")
            print(f"  Deleted relationships")
            
            # Delete all nodes
            print("  Deleting nodes...")
            result = session.run("MATCH (n) DELETE n")
            print(f"  Deleted nodes")
            
            # Verify deletion
            print("\n✅ Verifying deletion...")
            remaining_nodes = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            remaining_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            print(f"  Remaining nodes: {remaining_nodes}")
            print(f"  Remaining relationships: {remaining_rels}")
            
            if remaining_nodes == 0 and remaining_rels == 0:
                print("✅ Neo4j successfully cleared!")
            else:
                print("⚠️  Some data may still remain")
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error clearing Neo4j: {e}")

if __name__ == "__main__":
    clear_neo4j()

