#!/usr/bin/env python3
"""
Create LLM-based method relationships for existing papers in Neo4j
This script retroactively creates SAME_METHOD relationships using LLM-based semantic matching
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
from enhanced_methodology_extractor import EnhancedOllamaExtractor, EnhancedNeo4jIngester

load_dotenv()

def create_llm_relationships():
    """Create LLM-based relationships for all existing papers"""
    
    # Neo4j connection
    uri = os.getenv('NEO4J_URI', 'neo4j+s://fe285b91.databases.neo4j.io')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw')
    
    print("🔗 Connecting to Neo4j...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # Initialize LLM extractor
    print("🤖 Initializing LLM extractor...")
    extractor = EnhancedOllamaExtractor(model='codellama:7b')
    ingester = EnhancedNeo4jIngester(uri, user, password, extractor=extractor)
    
    with driver.session() as session:
        # Get all papers with methodologies
        print("\n📊 Fetching all papers with methodologies...")
        papers_query = session.run("""
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            RETURN p.paper_id as paper_id,
                   m.quant_methods as quant_methods,
                   m.qual_methods as qual_methods
            ORDER BY p.paper_id
        """)
        
        papers_data = []
        for record in papers_query:
            papers_data.append({
                'paper_id': record['paper_id'],
                'quant_methods': record['quant_methods'] or [],
                'qual_methods': record['qual_methods'] or []
            })
        
        print(f"Found {len(papers_data)} papers with methodologies")
        
        # Clear existing SAME_METHOD relationships
        print("\n🗑️  Clearing existing SAME_METHOD relationships...")
        session.run("MATCH ()-[r:SAME_METHOD]->() DELETE r")
        print("✅ Cleared existing relationships")
        
        # Process each paper to create relationships
        print("\n🔗 Creating LLM-based method relationships...")
        print("=" * 60)
        
        total_relationships = 0
        
        for i, paper in enumerate(papers_data, 1):
            paper_id = paper['paper_id']
            quant_methods = paper['quant_methods']
            qual_methods = paper['qual_methods']
            
            print(f"\n[{i}/{len(papers_data)}] Processing: {paper_id}")
            print(f"  Quant methods: {len(quant_methods)}")
            print(f"  Qual methods: {len(qual_methods)}")
            
            # Create methodology dict for the ingester
            methodology = {
                'quant_methods': quant_methods,
                'qual_methods': qual_methods
            }
            
            # Use the ingester's method to create relationships
            try:
                ingester._create_method_relationships(session, paper_id, methodology)
                
                # Count relationships created for this paper
                rel_count = session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[r:SAME_METHOD]->()
                    RETURN count(r) as count
                """, paper_id=paper_id).single()['count']
                
                print(f"  ✅ Created {rel_count} relationships")
                total_relationships += rel_count
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print(f"✅ Total relationships created: {total_relationships}")
        
        # Show summary
        print("\n📊 Relationship Summary:")
        summary = session.run("""
            MATCH ()-[r:SAME_METHOD]->()
            RETURN r.method_type as method_type, 
                   r.method as method, 
                   count(r) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        for record in summary:
            print(f"  {record['method_type']}: {record['method']} ({record['count']} relationships)")
    
    driver.close()
    ingester.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    create_llm_relationships()
