#!/usr/bin/env python3
"""
Validation script to check extraction consistency across multiple papers
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

def validate_extraction():
    """Validate extraction consistency"""
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'neo4j+s://fe285b91.databases.neo4j.io'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'))
    )
    
    with driver.session() as session:
        print('='*70)
        print('EXTRACTION CONSISTENCY VALIDATION REPORT')
        print('='*70)
        
        # Count papers
        paper_count = session.run('MATCH (p:Paper) RETURN count(p) as count').single()['count']
        print(f'\n📄 Papers Processed: {paper_count}')
        
        if paper_count == 0:
            print('\n⚠️  No papers found in Neo4j')
            driver.close()
            return
        
        # Paper details
        papers = session.run('''
            MATCH (p:Paper)
            RETURN p.paper_id as id, p.title as title, p.year as year, 
                   p.journal as journal, p.doi as doi,
                   size(p.keywords) as keyword_count,
                   p.abstract IS NOT NULL AND p.abstract <> "" as has_abstract
            ORDER BY p.paper_id
        ''').data()
        
        print('\n📊 Paper Extraction Details:')
        for p in papers:
            print(f'\n  {p["id"]}:')
            print(f'    Title: {"✓" if p["title"] else "✗"} {p["title"][:60] if p["title"] else "Missing"}...')
            print(f'    Abstract: {"✓" if p["has_abstract"] else "✗"}')
            print(f'    Journal: {"✓" if p["journal"] else "✗"} {p["journal"] or "Missing"}')
            print(f'    DOI: {"✓" if p["doi"] else "✗"} {p["doi"] or "Missing"}')
            print(f'    Keywords: {p["keyword_count"]} keywords')
        
        # Author extraction
        author_stats = session.run('''
            MATCH (a:Author)-[:AUTHORED]->(p:Paper)
            WITH p.paper_id as paper_id, count(a) as author_count, 
                 collect(a.full_name) as author_names
            RETURN paper_id, author_count, author_names
            ORDER BY paper_id
        ''').data()
        
        print('\n👤 Author Extraction:')
        for stat in author_stats:
            print(f'  {stat["paper_id"]}: {stat["author_count"]} authors')
            for name in stat["author_names"][:3]:  # Show first 3
                print(f'    - {name}')
            if len(stat["author_names"]) > 3:
                print(f'    ... and {len(stat["author_names"]) - 3} more')
        
        # Method extraction
        method_stats = session.run('''
            MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
            WITH p.paper_id as paper_id, count(m) as method_count, collect(m.name) as methods
            RETURN paper_id, method_count, methods
            ORDER BY paper_id
        ''').data()
        
        print('\n🔬 Method Extraction:')
        for stat in method_stats:
            print(f'  {stat["paper_id"]}: {stat["method_count"]} methods')
            for method in stat["methods"]:
                print(f'    - {method}')
        
        # Extraction consistency analysis
        print('\n' + '='*70)
        print('CONSISTENCY ANALYSIS')
        print('='*70)
        
        # Title extraction rate
        title_count = session.run('MATCH (p:Paper) WHERE p.title IS NOT NULL AND p.title <> "" RETURN count(p) as count').single()['count']
        print(f'\n✅ Title Extraction: {title_count}/{paper_count} papers ({title_count/paper_count*100:.1f}%)')
        
        # Abstract extraction rate
        abstract_count = session.run('MATCH (p:Paper) WHERE p.abstract IS NOT NULL AND p.abstract <> "" RETURN count(p) as count').single()['count']
        print(f'✅ Abstract Extraction: {abstract_count}/{paper_count} papers ({abstract_count/paper_count*100:.1f}%)')
        
        # Journal extraction rate
        journal_count = session.run('MATCH (p:Paper) WHERE p.journal IS NOT NULL AND p.journal <> "" RETURN count(p) as count').single()['count']
        print(f'✅ Journal Extraction: {journal_count}/{paper_count} papers ({journal_count/paper_count*100:.1f}%)')
        
        # DOI extraction rate
        doi_count = session.run('MATCH (p:Paper) WHERE p.doi IS NOT NULL AND p.doi <> "" RETURN count(p) as count').single()['count']
        print(f'✅ DOI Extraction: {doi_count}/{paper_count} papers ({doi_count/paper_count*100:.1f}%)')
        
        # Keywords extraction rate
        keywords_count = session.run('MATCH (p:Paper) WHERE p.keywords IS NOT NULL AND size(p.keywords) > 0 RETURN count(p) as count').single()['count']
        print(f'✅ Keywords Extraction: {keywords_count}/{paper_count} papers ({keywords_count/paper_count*100:.1f}%)')
        
        # Author extraction rate
        papers_with_authors = session.run('''
            MATCH (p:Paper)
            OPTIONAL MATCH (a:Author)-[:AUTHORED]->(p)
            WITH p.paper_id as paper_id, count(a) as author_count
            WHERE author_count > 0
            RETURN count(paper_id) as count
        ''').single()['count']
        print(f'✅ Author Extraction: {papers_with_authors}/{paper_count} papers ({papers_with_authors/paper_count*100:.1f}%)')
        
        # Method extraction rate
        papers_with_methods = session.run('''
            MATCH (p:Paper)
            OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
            WITH p.paper_id as paper_id, count(m) as method_count
            WHERE method_count > 0
            RETURN count(paper_id) as count
        ''').single()['count']
        print(f'✅ Method Extraction: {papers_with_methods}/{paper_count} papers ({papers_with_methods/paper_count*100:.1f}%)')
        
        # Average methods per paper
        avg_methods_result = session.run('''
            MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
            WITH p.paper_id as paper_id, count(m) as method_count
            RETURN avg(method_count) as avg
        ''').single()['avg']
        if avg_methods_result:
            print(f'\n📊 Average Methods per Paper: {avg_methods_result:.1f}')
        
        # Average authors per paper
        avg_authors_result = session.run('''
            MATCH (a:Author)-[:AUTHORED]->(p:Paper)
            WITH p.paper_id as paper_id, count(a) as author_count
            RETURN avg(author_count) as avg
        ''').single()['avg']
        if avg_authors_result:
            print(f'📊 Average Authors per Paper: {avg_authors_result:.1f}')
        
        # Graph structure summary
        print('\n' + '='*70)
        print('GRAPH STRUCTURE SUMMARY')
        print('='*70)
        
        node_counts = session.run('''
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        ''').data()
        
        print('\n📊 Node Counts:')
        for nc in node_counts:
            print(f'  {nc["label"]}: {nc["count"]}')
        
        rel_counts = session.run('''
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        ''').data()
        
        print('\n🔗 Relationship Counts:')
        for rc in rel_counts:
            print(f'  {rc["rel_type"]}: {rc["count"]}')
        
        print('\n' + '='*70)
    
    driver.close()

if __name__ == "__main__":
    validate_extraction()

