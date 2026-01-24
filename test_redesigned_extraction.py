#!/usr/bin/env python3
"""
Test the redesigned extraction framework
Compares old vs new approach
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Test both systems
from enhanced_methodology_extractor import EnhancedMethodologyProcessor as OldProcessor
from redesigned_methodology_extractor import RedesignedMethodologyProcessor as NewProcessor

load_dotenv()

def test_comparison():
    """Compare old vs new extraction"""
    
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Test papers
    test_papers = [
        Path('2020-2024/2020_1103.pdf'),
        Path('2020-2024/2020_1313.pdf'),
        Path('2020-2024/2020_1773.pdf')
    ]
    
    print("🔬 COMPARING OLD vs NEW EXTRACTION")
    print("=" * 70)
    
    old_processor = OldProcessor(ollama_model='codellama:7b')
    new_processor = NewProcessor(ollama_model='codellama:7b')
    
    for pdf_path in test_papers:
        if not pdf_path.exists():
            continue
        
        print(f"\n📄 Testing: {pdf_path.name}")
        print("-" * 70)
        
        # Old system
        print("\n[OLD SYSTEM]")
        try:
            old_result = old_processor.process_paper(pdf_path)
            old_methodology = old_result['methodology_data'].get('methodology', {})
            print(f"  Quant methods: {old_methodology.get('quant_methods', [])}")
            print(f"  Qual methods: {old_methodology.get('qual_methods', [])}")
            print(f"  Software: {old_methodology.get('software', [])}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # New system
        print("\n[NEW SYSTEM]")
        try:
            new_result = new_processor.process_paper(pdf_path)
            methods_data = new_result.get('methods_data', [])
            print(f"  Methods extracted: {len(methods_data)}")
            for method in methods_data:
                print(f"    - {method.get('method_name')} ({method.get('method_type')})")
                print(f"      Software: {method.get('software', [])}")
                print(f"      Confidence: {method.get('confidence', 0.0):.2f}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_comparison()
