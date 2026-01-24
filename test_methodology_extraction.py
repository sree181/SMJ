#!/usr/bin/env python3
"""
Simple test script to verify methodology extraction is working correctly
Tests multiple papers to ensure different methodologies are extracted
"""

import os
import sys
from pathlib import Path
from enhanced_methodology_extractor import EnhancedMethodologyProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_methodology_extraction():
    """Test methodology extraction on multiple papers"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Initialize processor
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test papers
    test_papers = [
        '1990-1994/1990_295.pdf',
        '1990-1994/1990_319.pdf', 
        '1990-1994/1990_358.pdf',
        '1990-1994/1990_382.pdf',
        '1985-1989/1988_305.pdf'
    ]
    
    print("🧪 TESTING METHODOLOGY EXTRACTION")
    print("=" * 50)
    
    results = []
    
    for paper_path in test_papers:
        pdf_path = Path(paper_path)
        if not pdf_path.exists():
            print(f"❌ {paper_path} not found")
            continue
            
        print(f"\n📄 Testing: {pdf_path.name}")
        print("-" * 30)
        
        try:
            # Extract text
            text = processor.pdf_processor.extract_text_from_pdf(pdf_path)
            print(f"  📊 Text length: {len(text)} characters")
            
            # Extract methodology
            methodology_data = processor.extractor.extract_detailed_methodology(text, pdf_path.stem)
            methodology = methodology_data.get('methodology', {})
            
            # Display results
            print(f"  📋 Type: {methodology.get('type', 'unknown')}")
            print(f"  🔬 Quant methods: {methodology.get('quant_methods', [])}")
            print(f"  📝 Qual methods: {methodology.get('qual_methods', [])}")
            print(f"  💻 Software: {methodology.get('software', [])}")
            print(f"  📝 Notes: {methodology.get('extraction_notes', '')[:100]}...")
            
            results.append({
                'paper_id': pdf_path.stem,
                'type': methodology.get('type', 'unknown'),
                'quant_methods': methodology.get('quant_methods', []),
                'qual_methods': methodology.get('qual_methods', []),
                'software': methodology.get('software', []),
                'notes': methodology.get('extraction_notes', '')
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'paper_id': pdf_path.stem,
                'error': str(e)
            })
    
    # Analyze results
    print("\n📊 ANALYSIS")
    print("=" * 50)
    
    # Check for identical methodologies
    types = [r.get('type', 'unknown') for r in results if 'error' not in r]
    quant_methods = [r.get('quant_methods', []) for r in results if 'error' not in r]
    
    print(f"📋 Methodology types found: {set(types)}")
    print(f"🔬 Unique quant methods: {set(str(m) for m in quant_methods)}")
    
    # Check if all are identical
    if len(set(types)) == 1 and len(set(str(quant_methods) for quant_methods in quant_methods)) == 1:
        print("❌ PROBLEM: All papers have identical methodology!")
        print("   This indicates the extraction is still not working correctly.")
    else:
        print("✅ SUCCESS: Different methodologies extracted for different papers!")
    
    # Show detailed comparison
    print("\n📋 DETAILED COMPARISON")
    print("-" * 30)
    for result in results:
        if 'error' not in result:
            print(f"{result['paper_id']}: {result['type']} - {result['quant_methods']}")
        else:
            print(f"{result['paper_id']}: ERROR - {result['error']}")
    
    return results

if __name__ == "__main__":
    test_methodology_extraction()
