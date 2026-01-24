#!/usr/bin/env python3
"""
Test comprehensive extraction on a sample paper
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from enhanced_methodology_extractor import EnhancedMethodologyProcessor

load_dotenv()

def test_comprehensive_extraction():
    """Test comprehensive extraction on a sample paper"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    print("🧪 TESTING COMPREHENSIVE EXTRACTION")
    print("=" * 60)
    print()
    
    # Initialize processor
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test with a paper from 2020-2024 that hasn't been processed yet
    test_paper = Path('2020-2024/2022_1963.pdf')
    
    if not test_paper.exists():
        # Try another paper
        pdf_files = list(Path('2020-2024').glob('*.pdf'))
        if pdf_files:
            test_paper = pdf_files[0]
        else:
            print("❌ No test papers found in 2020-2024")
            return
    
    print(f"📄 Testing with: {test_paper.name}")
    print()
    
    try:
        # Process the paper
        print("🔍 Processing paper with comprehensive extraction...")
        result = processor.process_paper(test_paper)
        
        methodology = result['methodology_data'].get('methodology', {})
        
        print()
        print("✅ EXTRACTION RESULTS")
        print("=" * 60)
        print(f"Methodology Type: {methodology.get('type', 'unknown')}")
        print(f"Confidence: {methodology.get('confidence', 0.0):.2f}")
        print()
        
        # Check comprehensive fields
        print("📊 COMPREHENSIVE FIELDS")
        print("-" * 60)
        
        # Variables
        variables = methodology.get('variables', {})
        if isinstance(variables, dict):
            dep_vars = variables.get('dependent', [])
            ind_vars = variables.get('independent', [])
            control_vars = variables.get('control', [])
            
            if dep_vars:
                print(f"✓ Dependent variables: {dep_vars}")
            if ind_vars:
                print(f"✓ Independent variables: {ind_vars}")
            if control_vars:
                print(f"✓ Control variables: {control_vars}")
            if not dep_vars and not ind_vars and not control_vars:
                print("✗ Variables: Not extracted")
        else:
            print("✗ Variables: Not extracted")
        
        # Validity/Reliability
        validity_reliability = methodology.get('validity_reliability', {})
        if isinstance(validity_reliability, dict):
            rel_measures = validity_reliability.get('reliability_measures', [])
            val_measures = validity_reliability.get('validity_measures', [])
            
            if rel_measures:
                print(f"✓ Reliability measures: {rel_measures}")
            if val_measures:
                print(f"✓ Validity measures: {val_measures}")
            if not rel_measures and not val_measures:
                print("✗ Validity/Reliability: Not extracted")
        else:
            print("✗ Validity/Reliability: Not extracted")
        
        # Assumptions
        assumptions = methodology.get('assumptions_checked', [])
        if assumptions:
            print(f"✓ Assumptions checked: {assumptions}")
        else:
            print("✗ Assumptions: Not extracted")
        
        # Limitations
        limitations = methodology.get('limitations', [])
        if limitations:
            print(f"✓ Limitations: {limitations}")
        else:
            print("✗ Limitations: Not extracted")
        
        # Time period
        time_period = methodology.get('time_period', '')
        if time_period:
            print(f"✓ Time period: {time_period}")
        else:
            print("✗ Time period: Not extracted")
        
        # Data collection
        data_collection = methodology.get('data_collection', [])
        if data_collection:
            print(f"✓ Data collection: {data_collection}")
        else:
            print("✗ Data collection: Not extracted")
        
        # Hypotheses
        hypotheses_count = methodology.get('hypotheses_count', 0)
        if hypotheses_count > 0:
            print(f"✓ Hypotheses count: {hypotheses_count}")
        else:
            print("✗ Hypotheses count: Not extracted")
        
        print()
        print("📋 STANDARD FIELDS")
        print("-" * 60)
        print(f"Quant methods: {methodology.get('quant_methods', [])}")
        print(f"Qual methods: {methodology.get('qual_methods', [])}")
        print(f"Software: {methodology.get('software', [])}")
        print(f"Sample size: {methodology.get('sample_size', '')}")
        
        # Save results to JSON for inspection
        output_file = f"comprehensive_extraction_test_{test_paper.stem}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"💾 Full results saved to: {output_file}")
        print()
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_extraction()
