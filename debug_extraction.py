#!/usr/bin/env python3
"""
Debug why methodologies are the same across papers
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from enhanced_methodology_extractor import EnhancedMethodologyProcessor

load_dotenv()

def debug_extraction():
    """Debug extraction for multiple papers"""
    
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test with 3 different papers
    test_papers = [
        Path('2020-2024/2020_1103.pdf'),
        Path('2020-2024/2020_1313.pdf'),
        Path('2020-2024/2020_1773.pdf')
    ]
    
    for pdf_path in test_papers:
        if not pdf_path.exists():
            continue
        
        print(f"\n{'='*70}")
        print(f"📄 Testing: {pdf_path.name}")
        print('='*70)
        
        # Extract text
        text = processor.pdf_processor.extract_text_from_pdf(pdf_path)
        print(f"📊 Full text length: {len(text)} characters")
        
        # Extract methodology section
        methodology_section = processor.extractor._extract_methodology_section(text)
        print(f"🔍 Methodology section length: {len(methodology_section)} characters")
        
        if methodology_section:
            print(f"📝 Methodology section preview (first 300 chars):")
            print(methodology_section[:300])
            print("...")
        else:
            print("⚠️  No methodology section found!")
        
        # Check what text will be sent to LLM
        methodology_text = methodology_section[:5000] if methodology_section else ""
        full_text_sample = text[:15000]
        
        print(f"\n📤 Text sent to LLM:")
        print(f"  Methodology section: {len(methodology_text)} chars")
        print(f"  Full text sample: {len(full_text_sample)} chars")
        
        # Check if methodology section is in the full text sample
        if methodology_section and methodology_section[:500] not in full_text_sample:
            print("⚠️  WARNING: Methodology section is NOT in the full text sample!")
            print("   This means LLM won't see the methodology section!")
        
        # Extract methodology
        print(f"\n🤖 Extracting methodology...")
        try:
            methodology_data = processor.extractor.extract_detailed_methodology(text, pdf_path.stem)
            methodology = methodology_data.get('methodology', {})
            
            print(f"✅ Extracted:")
            print(f"  Type: {methodology.get('type')}")
            print(f"  Quant methods: {methodology.get('quant_methods', [])}")
            print(f"  Qual methods: {methodology.get('qual_methods', [])}")
            print(f"  Software: {methodology.get('software', [])}")
            print(f"  Confidence: {methodology.get('confidence', 0.0)}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_extraction()
