#!/usr/bin/env python3
"""
LLM-based methodology extraction test with raw text capture
Tests LLM approaches on 2025-2029 bucket and saves raw methodology text
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from enhanced_methodology_extractor import EnhancedMethodologyProcessor
from methodology_only_extractor import OllamaMethodologyOnlyExtractor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_methodology_with_raw_text():
    """Test LLM-based methodology extraction with raw text capture"""
    
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    # Initialize processors
    enhanced_processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    methodology_only_extractor = OllamaMethodologyOnlyExtractor(model='codellama:7b')
    
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
            'approach': 'llm_based_with_raw_text'
        },
        'papers': []
    }
    
    print("\n🧪 TESTING LLM-BASED METHODOLOGY EXTRACTION WITH RAW TEXT")
    print("=" * 70)
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n📄 Testing {i}/{len(pdf_files)}: {pdf_path.name}")
        print("-" * 60)
        
        paper_result = {
            'paper_id': pdf_path.stem,
            'pdf_path': str(pdf_path),
            'extraction_results': {}
        }
        
        try:
            # Extract text from PDF
            text = enhanced_processor.pdf_processor.extract_text_from_pdf(pdf_path)
            print(f"  📊 Text length: {len(text)} characters")
            paper_result['text_length'] = len(text)
            
            # Test 1: Extract raw methodology section using LLM
            print("  🔍 Extracting raw methodology section...")
            raw_methodology_section = methodology_only_extractor.extract_methodology_section(text)
            print(f"    Raw methodology section length: {len(raw_methodology_section)} chars")
            
            paper_result['extraction_results']['raw_methodology_section'] = {
                'section_length': len(raw_methodology_section),
                'section_text': raw_methodology_section,
                'has_content': len(raw_methodology_section) > 100,
                'preview': raw_methodology_section[:300] + "..." if len(raw_methodology_section) > 300 else raw_methodology_section
            }
            
            # Test 2: Extract structured methodology data
            print("  🤖 Extracting structured methodology data...")
            structured_methodology = enhanced_processor.extractor.extract_detailed_methodology(text, pdf_path.stem)
            methodology = structured_methodology.get('methodology', {})
            
            print(f"    Methodology type: {methodology.get('type', 'unknown')}")
            print(f"    Quant methods: {methodology.get('quant_methods', [])}")
            print(f"    Qual methods: {methodology.get('qual_methods', [])}")
            print(f"    Software: {methodology.get('software', [])}")
            print(f"    Confidence: {methodology.get('confidence', 0.0)}")
            
            paper_result['extraction_results']['structured_methodology'] = {
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
            
            # Test 3: Paper metadata extraction
            print("  📄 Extracting paper metadata...")
            metadata = enhanced_processor.extractor.extract_paper_metadata(text, pdf_path.stem)
            
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
            has_raw_section = len(raw_methodology_section) > 100
            has_structured_data = methodology.get('type', '') not in ['', 'unknown', 'other']
            has_quant_methods = len(methodology.get('quant_methods', [])) > 0
            has_qual_methods = len(methodology.get('qual_methods', [])) > 0
            has_software = len(methodology.get('software', [])) > 0
            confidence = methodology.get('confidence', 0.0)
            
            print(f"  📈 Analysis:")
            print(f"    Has raw methodology section: {has_raw_section}")
            print(f"    Has structured methodology: {has_structured_data}")
            print(f"    Has quant methods: {has_quant_methods}")
            print(f"    Has qual methods: {has_qual_methods}")
            print(f"    Has software: {has_software}")
            print(f"    Confidence: {confidence}")
            
            paper_result['analysis'] = {
                'has_raw_section': has_raw_section,
                'has_structured_data': has_structured_data,
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
    print("=" * 70)
    
    total_papers = len(results['papers'])
    successful_extractions = sum(1 for p in results['papers'] if p.get('extraction_results', {}).get('structured_methodology', {}).get('success', False))
    has_raw_sections = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_raw_section', False))
    has_structured_data = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_structured_data', False))
    has_quant_methods = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_quant_methods', False))
    has_qual_methods = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_qual_methods', False))
    has_software = sum(1 for p in results['papers'] if p.get('analysis', {}).get('has_software', False))
    
    # Quality analysis
    high_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'high')
    medium_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'medium')
    low_quality = sum(1 for p in results['papers'] if p.get('analysis', {}).get('extraction_quality') == 'low')
    
    print(f"📄 Total papers tested: {total_papers}")
    print(f"✅ Successful extractions: {successful_extractions}/{total_papers} ({successful_extractions/total_papers*100:.1f}%)")
    print(f"📝 Papers with raw methodology sections: {has_raw_sections}/{total_papers} ({has_raw_sections/total_papers*100:.1f}%)")
    print(f"🔬 Papers with structured methodology: {has_structured_data}/{total_papers} ({has_structured_data/total_papers*100:.1f}%)")
    print(f"📊 Papers with quant methods: {has_quant_methods}/{total_papers} ({has_quant_methods/total_papers*100:.1f}%)")
    print(f"📝 Papers with qual methods: {has_qual_methods}/{total_papers} ({has_qual_methods/total_papers*100:.1f}%)")
    print(f"💻 Papers with software: {has_software}/{total_papers} ({has_software/total_papers*100:.1f}%)")
    
    print(f"\n📈 Extraction Quality:")
    print(f"  High quality: {high_quality}/{total_papers} ({high_quality/total_papers*100:.1f}%)")
    print(f"  Medium quality: {medium_quality}/{total_papers} ({medium_quality/total_papers*100:.1f}%)")
    print(f"  Low quality: {low_quality}/{total_papers} ({low_quality/total_papers*100:.1f}%)")
    
    # Raw section length analysis
    raw_section_lengths = [p.get('extraction_results', {}).get('raw_methodology_section', {}).get('section_length', 0) for p in results['papers']]
    avg_raw_length = sum(raw_section_lengths) / len(raw_section_lengths) if raw_section_lengths else 0
    max_raw_length = max(raw_section_lengths) if raw_section_lengths else 0
    min_raw_length = min(raw_section_lengths) if raw_section_lengths else 0
    
    print(f"\n📏 Raw Methodology Section Lengths:")
    print(f"  Average: {avg_raw_length:.0f} characters")
    print(f"  Maximum: {max_raw_length} characters")
    print(f"  Minimum: {min_raw_length} characters")
    
    # Add summary to results
    results['summary'] = {
        'total_papers': total_papers,
        'successful_extractions': successful_extractions,
        'success_rate': successful_extractions/total_papers*100,
        'has_raw_sections_rate': has_raw_sections/total_papers*100,
        'has_structured_data_rate': has_structured_data/total_papers*100,
        'has_quant_methods_rate': has_quant_methods/total_papers*100,
        'has_qual_methods_rate': has_qual_methods/total_papers*100,
        'has_software_rate': has_software/total_papers*100,
        'quality_distribution': {
            'high': high_quality,
            'medium': medium_quality,
            'low': low_quality
        },
        'raw_section_lengths': {
            'average': avg_raw_length,
            'maximum': max_raw_length,
            'minimum': min_raw_length
        }
    }
    
    # Save results to JSON
    output_file = f"methodology_extraction_with_raw_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"📊 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    
    return results

if __name__ == "__main__":
    test_methodology_with_raw_text()

