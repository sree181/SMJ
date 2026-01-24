#!/usr/bin/env python3
"""
Monitor ingestion progress for 2020-2024 papers
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

def monitor_ingestion():
    """Monitor ingestion progress"""
    
    uri = 'neo4j+s://fe285b91.databases.neo4j.io'
    user = 'neo4j'
    password = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Count papers from 2020-2024
        papers_2020_2024 = session.run('''
            MATCH (p:Paper)
            WHERE p.year >= 2020 AND p.year <= 2024
            RETURN count(p) as count
        ''').single()['count']
        
        # Count methodologies for 2020-2024
        methodologies_2020_2024 = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            RETURN count(m) as count
        ''').single()['count']
        
        # Average confidence for 2020-2024
        avg_confidence = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            AND m.confidence IS NOT NULL
            RETURN avg(m.confidence) as avg_conf
        ''').single()['avg_conf'] or 0.0
        
        # Papers with software
        papers_with_software = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            AND size(m.software) > 0
            RETURN count(p) as count
        ''').single()['count']
        
        # Papers with quant methods
        papers_with_quant = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            AND size(m.quant_methods) > 0
            RETURN count(p) as count
        ''').single()['count']
        
        # Papers with qual methods
        papers_with_qual = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            AND size(m.qual_methods) > 0
            RETURN count(p) as count
        ''').single()['count']
        
        # SAME_METHOD relationships for 2020-2024
        same_method_rels = session.run('''
            MATCH (p1:Paper)-[r:SAME_METHOD]->(p2:Paper)
            WHERE p1.year >= 2020 AND p1.year <= 2024
            RETURN count(r) as count
        ''').single()['count']
        
        # Get recent papers
        recent_papers = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.year >= 2020 AND p.year <= 2024
            RETURN p.paper_id as id, p.title as title, p.year as year, m.confidence as confidence
            ORDER BY p.year DESC
            LIMIT 10
        ''')
        
        print('📊 INGESTION PROGRESS: 2020-2024')
        print('=' * 60)
        print(f'📄 Papers ingested: {papers_2020_2024}/158 ({papers_2020_2024/158*100:.1f}%)')
        print(f'🔬 Methodologies: {methodologies_2020_2024}')
        print(f'📊 Average confidence: {avg_confidence:.2f}')
        print(f'💻 Papers with software: {papers_with_software}')
        print(f'📈 Papers with quant methods: {papers_with_quant}')
        print(f'📝 Papers with qual methods: {papers_with_qual}')
        print(f'🔗 SAME_METHOD relationships: {same_method_rels}')
        print()
        
        if papers_2020_2024 > 0:
            print('📋 Recent papers ingested:')
            for i, record in enumerate(recent_papers, 1):
                title = record['title'][:55] if record['title'] else 'No title'
                conf = record['confidence'] or 0.0
                print(f'  {i}. {record["id"]}: {title}... (Conf: {conf:.2f})')
        else:
            print('⏳ No papers ingested yet. Process is running...')
    
    driver.close()

if __name__ == "__main__":
    monitor_ingestion()
