#!/usr/bin/env python3
"""
Test the full pipeline: extract methodology and ingest into Neo4j
"""

import os
import sys
from pathlib import Path
from enhanced_methodology_extractor import EnhancedMethodologyProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_full_pipeline():
    """Test the complete pipeline with a few papers"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Initialize processor
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test with 3 papers
    test_papers = [
        '1990-1994/1990_319.pdf',  # Has good text content
        '1990-1994/1990_382.pdf',  # Qualitative paper
        '1985-1989/1988_305.pdf'   # Different time period
    ]
    
    print("🧪 TESTING FULL PIPELINE")
    print("=" * 50)
    
    for paper_path in test_papers:
        pdf_path = Path(paper_path)
        if not pdf_path.exists():
            print(f"❌ {paper_path} not found")
            continue
            
        print(f"\n📄 Processing: {pdf_path.name}")
        print("-" * 40)
        
        try:
            # Process the paper (metadata + methodology + ingestion)
            result = processor.process_paper(pdf_path)
            
            # Display results
            paper_metadata = result['paper_metadata']
            methodology_data = result['methodology_data']
            methodology = methodology_data.get('methodology', {})
            
            print(f"  📄 Title: {paper_metadata.get('title', 'No title')[:60]}...")
            print(f"  👥 Authors: {paper_metadata.get('authors', [])}")
            print(f"  📊 Methodology Type: {methodology.get('type', 'unknown')}")
            print(f"  🔬 Quant Methods: {methodology.get('quant_methods', [])}")
            print(f"  📝 Qual Methods: {methodology.get('qual_methods', [])}")
            print(f"  💻 Software: {methodology.get('software', [])}")
            print(f"  📝 Notes: {methodology.get('extraction_notes', '')[:80]}...")
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
    
    # Check what's in Neo4j
    print("\n📊 CHECKING NEO4J DATABASE")
    print("-" * 40)
    
    with processor.ingester.driver.session() as session:
        # Check papers
        result = session.run('MATCH (p:Paper) RETURN count(p) as count')
        paper_count = result.single()['count']
        print(f"📄 Total Papers: {paper_count}")
        
        # Check methodology nodes
        result = session.run('MATCH (m:Methodology) RETURN count(m) as count')
        methodology_count = result.single()['count']
        print(f"📊 Total Methodology Nodes: {methodology_count}")
        
        # Check recent papers with methodology
        result = session.run('''
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            RETURN p.paper_id as paper_id, p.title as title, m.type as type, 
                   m.quant_methods as quant_methods, m.qual_methods as qual_methods
            ORDER BY p.paper_id
            LIMIT 10
        ''')
        
        print("\n📋 Recent Papers with Methodology:")
        for record in result:
            title = record['title'] if record['title'] else 'No title'
            print(f"  {record['paper_id']}: {record['type']} - {record['quant_methods']} / {record['qual_methods']}")
            print(f"    Title: {title[:50]}...")

if __name__ == "__main__":
    test_full_pipeline()
