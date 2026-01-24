#!/usr/bin/env python3
"""
LLM-based methodology section extraction test
Tests only LLM approaches on 2025-2029 bucket
Saves results to JSON for analysis
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from enhanced_methodology_extractor import EnhancedMethodologyProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llm_methodology_extraction():
    """Test LLM-based methodology section extraction"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Initialize processor
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Get all papers in 2025-2029 bucket
    bucket_dir = Path('2025-2029')
    if not bucket_dir.exists():
        print(f"❌ Bucket directory not found: {bucket_dir}")
        return
    
    pdf_files = list(bucket_dir.glob('*.pdf'))
    print(f"📁 Found {len(pdf_files)} papers in {bucket_dir}")
    
    results = {
        'test_info': {
            'bucket': '2025-2029',
            'total_papers': len(pdf_files),
            'test_timestamp': datetime.now().isoformat(),
            'approach': 'llm_based_only'
        },
        'papers': []
    }
    
    print("\n🧪 TESTING LLM-BASED METHODOLOGY EXTRACTION")
    print("=" * 60)
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n📄 Testing {i}/{len(pdf_files)}: {pdf_path.name}")
        print("-" * 50)
        
        paper_result = {
            'paper_id': pdf_path.stem,
            'pdf_path': str(pdf_path),
            'extraction_results': {}
        }
        
        try:
            # Extract text from PDF
            text = processor.pdf_processor.extract_text_from_pdf(pdf_path)
            print(f"  📊 Text length: {len(text)} characters")
            paper_result['text_length'] = len(text)
            
            # Test 1: LLM-based methodology section extraction
            print("  🤖 Testing LLM-based methodology section extraction...")
            llm_section = processor.extractor.extract_detailed_methodology(text, pdf_path.stem)
            methodology = llm_section.get('methodology', {})
            
            print(f"    Methodology type: {methodology.get('type', 'unknown')}")
            print(f"    Quant methods: {methodology.get('quant_methods', [])}")
            print(f"    Qual methods: {methodology.get('qual_methods', [])}")
            print(f"    Software: {methodology.get('software', [])}")
            print(f"    Confidence: {methodology.get('confidence', 0.0)}")
            
            paper_result['extraction_results']['llm_methodology'] = {
                'methodology_type': methodology.get('type', 'unknown'),
                'design': methodology.get('design', []),
                'quant_methods': methodology.get('quant_methods', []),
                'qual_methods': methodology.get('qual_methods', []),
                'software': methodology.get('software', []),
                'sample_size': methodology.get('sample_size', ''),
                'data_sources': methodology.get('data_sources', []),
                'analysis_techniques': methodology.get('analysis_techniques', []),
                'statistical_tests': methodology.get('statistical_tests', []),
                'confidence': methodology.get('confidence', 0.0),
                'extraction_notes': methodology.get('extraction_notes', ''),
                'success': True
            }
            
            # Test 2: Paper metadata extraction
            print("  📄 Testing paper metadata extraction...")
            metadata = processor.extractor.extract_paper_metadata(text, pdf_path.stem)
            
            print(f"    Title: {metadata.get('title', 'No title')[:60]}...")
            print(f"    Authors: {metadata.get('authors', [])}")
            print(f"    Year: {metadata.get('year', 'Unknown')}")
            
            paper_result['extraction_results']['metadata'] = {
                'title': metadata.get('title', ''),
                'abstract': metadata.get('abstract', ''),
                'authors': metadata.get('authors', []),
                'year': metadata.get('year', 0),
                'email': metadata.get('email', ''),
                'journal': metadata.get('journal', ''),
                'doi': metadata.get('doi', ''),
                'keywords': metadata.get('keywords', []),
                'success': True
            }
            
            # Analysis
            has_methodology = methodology.get('type', '') not in ['', 'unknown', 'other']
            has_quant_methods = len(methodology.get('quant_methods', [])) > 0
            has_qual_methods = len(methodology.get('qual_methods', [])) > 0
            has_software = len(methodology.get('software', [])) > 0
            confidence = methodology.get('confidence', 0.0)
            
            print(f"  📈 Analysis:")
            print(f"    Has methodology: {has_methodology}")
            print(f"    Has quant methods: {has_quant_methods}")
            print(f"    Has qual methods: {has_qual_methods}")
            print(f"    Has software: {has_software}")
            print(f"    Confidence: {confidence}")
            
            paper_result['analysis'] = {
                'has_methodology': has_methodology,
                'has_quant_methods': has_quant_methods,
                'has_qual_methods': has_qual_methods,
                'has_software': has_software,
                'confidence': confidence,
                'extraction_quality': 'high' if confidence > 0.7 and (has_quant_methods or has_qual_methods) else 'medium' if confidence > 0.4 else 'low'
            }
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
            paper_result['error'] = str(e)
            paper_result['extraction_results'] = {'success': False, 'error': str(e)}
        
        results['papers'].append(paper_result)
    
    # Summary analysis
    print("\n📊 SUMMARY ANALYSIS")
    print("=" * 60)
    
    total_papers = len(results['papers'])
    successful_extractions = sum(1 for p in results['papers'] if p.get('extraction_results', {}).get('llm_methodology', {}).get('success', False))
    has_methodology = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_methodology', False))
    has_quant_methods = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_quant_methods', False))
    has_qual_methods = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_qual_methods', False))
    has_software = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_software', False))
    
    # Quality analysis
    high_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'high')
    medium_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'medium')
    low_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'low')
    
    print(f"📄 Total papers tested: {total_papers}")
    print(f"✅ Successful extractions: {successful_extractions}/{total_papers} ({successful_extractions/total_papers*100:.1f}%)")
    print(f"🔬 Papers with methodology: {has_methodology}/{total_papers} ({has_methodology/total_papers*100:.1f}%)")
    print(f"📊 Papers with quant methods: {has_quant_methods}/{total_papers} ({has_quant_methods/total_papers*100:.1f}%)")
    print(f"📝 Papers with qual methods: {has_qual_methods}/{total_papers} ({has_qual_methods/total_papers*100:.1f}%)")
    print(f"💻 Papers with software: {has_software}/{total_papers} ({has_software/total_papers*100:.1f}%)")
    
    print(f"\n📈 Extraction Quality:")
    print(f"  High quality: {high_quality}/{total_papers} ({high_quality/total_papers*100:.1f}%)")
    print(f"  Medium quality: {medium_quality}/{total_papers} ({medium_quality/total_papers*100:.1f}%)")
    print(f"  Low quality: {low_quality}/{total_papers} ({low_quality/total_papers*100:.1f}%)")
    
    # Methodology types
    methodology_types = [p.get('extraction_results', {}).get('llm_methodology', {}).get('methodology_type', 'unknown') for p in results['papers']]
    type_counts = {method_type: methodology_types.count(method_type) for method_type in set(methodology_types)}
    print(f"\n🔬 Methodology Types Found:")
    for method_type, count in type_counts.items():
        print(f"  {method_type}: {count}/{total_papers} ({count/total_papers*100:.1f}%)")
    
    # Add summary to results
    results['summary'] = {
        'total_papers': total_papers,
        'successful_extractions': successful_extractions,
        'success_rate': successful_extractions/total_papers*100,
        'has_methodology_rate': has_methodology/total_papers*100,
        'has_quant_methods_rate': has_quant_methods/total_papers*100,
        'has_qual_methods_rate': has_qual_methods/total_papers*100,
        'has_software_rate': has_software/total_papers*100,
        'quality_distribution': {
            'high': high_quality,
            'medium': medium_quality,
            'low': low_quality
        },
        'methodology_types': type_counts
    }
    
    # Save results to JSON
    output_file = f"llm_methodology_extraction_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"📊 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    
    return results

if __name__ == "__main__":
    test_llm_methodology_extraction()
