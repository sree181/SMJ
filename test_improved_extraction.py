#!/usr/bin/env python3
"""
Test the improved methodology extraction with all enhancements:
1. Better prompts for accuracy
2. Fixed confidence scoring
3. Enhanced software detection
4. Increased text limits
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from enhanced_methodology_extractor import EnhancedMethodologyProcessor

load_dotenv()

def test_improved_extraction():
    """Test the improved extraction on a sample paper"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    print("🧪 TESTING IMPROVED METHODOLOGY EXTRACTION")
    print("=" * 60)
    print()
    
    # Initialize processor
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test with a paper from 2025-2029 bucket
    test_paper = Path('2025-2029/2025_4359.pdf')
    
    if not test_paper.exists():
        print(f"❌ Test paper not found: {test_paper}")
        return
    
    print(f"📄 Testing with: {test_paper.name}")
    print()
    
    try:
        # Extract text to check length
        text = processor.pdf_processor.extract_text_from_pdf(test_paper)
        print(f"📊 Paper text length: {len(text)} characters")
        print(f"   (Previous limit: 20,000, New limit: 50,000)")
        print()
        
        # Extract methodology
        print("🔍 Extracting methodology with improved prompts...")
        methodology_data = processor.extractor.extract_detailed_methodology(text, test_paper.stem)
        
        methodology = methodology_data.get('methodology', {})
        
        print()
        print("📊 EXTRACTION RESULTS:")
        print("=" * 60)
        print(f"Methodology Type: {methodology.get('type', 'unknown')}")
        print(f"Confidence: {methodology.get('confidence', 0.0):.2f}")
        print()
        
        print("🔬 Quantitative Methods:")
        quant_methods = methodology.get('quant_methods', [])
        if quant_methods:
            for i, method in enumerate(quant_methods, 1):
                print(f"  {i}. {method}")
        else:
            print("  (none)")
        print()
        
        print("📝 Qualitative Methods:")
        qual_methods = methodology.get('qual_methods', [])
        if qual_methods:
            for i, method in enumerate(qual_methods, 1):
                print(f"  {i}. {method}")
        else:
            print("  (none)")
        print()
        
        print("💻 Software:")
        software = methodology.get('software', [])
        if software:
            for i, sw in enumerate(software, 1):
                print(f"  {i}. {sw}")
        else:
            print("  (none)")
        print()
        
        print("📐 Research Design:")
        design = methodology.get('design', [])
        if design:
            for i, d in enumerate(design, 1):
                print(f"  {i}. {d}")
        else:
            print("  (none)")
        print()
        
        print("📊 Sample Size:")
        sample_size = methodology.get('sample_size', '')
        print(f"  {sample_size if sample_size else '(not specified)'}")
        print()
        
        print("📚 Data Sources:")
        data_sources = methodology.get('data_sources', [])
        if data_sources:
            for i, source in enumerate(data_sources, 1):
                print(f"  {i}. {source}")
        else:
            print("  (none)")
        print()
        
        print("📝 Extraction Notes:")
        notes = methodology.get('extraction_notes', '')
        print(f"  {notes if notes else '(none)'}")
        print()
        
        # Analysis
        print("📈 QUALITY ANALYSIS:")
        print("=" * 60)
        confidence = methodology.get('confidence', 0.0)
        
        if confidence >= 0.9:
            quality = "Excellent"
        elif confidence >= 0.7:
            quality = "Good"
        elif confidence >= 0.5:
            quality = "Fair"
        elif confidence >= 0.3:
            quality = "Poor"
        else:
            quality = "Very Poor"
        
        print(f"Confidence Score: {confidence:.2f} ({quality})")
        print(f"Has Specific Methods: {len(quant_methods) > 0 or len(qual_methods) > 0}")
        print(f"Has Software Info: {len(software) > 0}")
        print(f"Has Sample Size: {bool(sample_size)}")
        print(f"Has Data Sources: {len(data_sources) > 0}")
        print(f"Has Design Info: {len(design) > 0}")
        
        print()
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_extraction()
