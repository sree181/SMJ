#!/usr/bin/env python3
"""
Check current ingestion status
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def check_status():
    """Check current ingestion status"""
    
    # Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'neo4j+s://fe285b91.databases.neo4j.io')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw')
    
    # Count PDFs in bucket
    bucket_dir = Path('2025-2029')
    pdf_files = list(bucket_dir.glob('*.pdf')) if bucket_dir.exists() else []
    total_papers = len(pdf_files)
    
    print('📊 CURRENT INGESTION STATUS')
    print('=' * 50)
    print()
    print('📁 Files in 2025-2029 bucket:')
    print(f'  Total PDFs: {total_papers}')
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Count papers
            paper_count = session.run('MATCH (p:Paper) RETURN count(p) as count').single()['count']
            progress = (paper_count/total_papers*100) if total_papers > 0 else 0
            print(f'📄 Papers ingested: {paper_count}/{total_papers} ({progress:.1f}%)')
            
            # Count methodologies
            method_count = session.run('MATCH (m:Methodology) RETURN count(m) as count').single()['count']
            print(f'🔬 Methodologies: {method_count}')
            
            # Count relationships
            rel_count = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()['count']
            print(f'🔗 Total Relationships: {rel_count}')
            
            # Count SAME_METHOD relationships
            same_method_count = session.run('MATCH ()-[r:SAME_METHOD]->() RETURN count(r) as count').single()['count']
            print(f'🔗 SAME_METHOD relationships: {same_method_count}')
            
            print()
            print('🔬 Methodology Types:')
            methods = session.run('MATCH (m:Methodology) RETURN m.type as type, count(m) as count ORDER BY count DESC')
            for record in methods:
                print(f'  - {record["type"]}: {record["count"]}')
            
            print()
            print('📋 Recent Papers:')
            papers = session.run('MATCH (p:Paper) RETURN p.title as title, p.year as year, p.paper_id as id ORDER BY p.year DESC LIMIT 5')
            for i, record in enumerate(papers, 1):
                title = record['title'][:70] if record['title'] else 'No title'
                print(f'  {i}. {title}... (ID: {record["id"]}, Year: {record["year"]})')
            
            print()
            print('📊 Papers with Quant Methods:')
            quant_papers = session.run('''
                MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
                WHERE size(m.quant_methods) > 0
                RETURN count(p) as count
            ''').single()['count']
            print(f'  {quant_papers} papers')
            
            print()
            print('📊 Papers with Qual Methods:')
            qual_papers = session.run('''
                MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
                WHERE size(m.qual_methods) > 0
                RETURN count(p) as count
            ''').single()['count']
            print(f'  {qual_papers} papers')
            
            print()
            print('💻 Papers with Software:')
            software_papers = session.run('''
                MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
                WHERE size(m.software) > 0
                RETURN count(p) as count
            ''').single()['count']
            print(f'  {software_papers} papers')
        
        driver.close()
        
    except Exception as e:
        print(f'❌ Error connecting to Neo4j: {e}')
        print('   Please check your connection and credentials.')

if __name__ == "__main__":
    check_status()
