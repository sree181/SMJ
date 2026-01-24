#!/usr/bin/env python3
"""
Comprehensive test for methodology section extraction
Tests both rule-based and LLM-based approaches on 2025-2029 bucket
Saves results to JSON for analysis
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

def test_methodology_extraction_comprehensive():
    """Comprehensive test of methodology section extraction"""
    
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
            'approaches_tested': ['rule_based', 'llm_based', 'hybrid']
        },
        'papers': []
    }
    
    print("\n🧪 TESTING METHODOLOGY SECTION EXTRACTION")
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
            text = enhanced_processor.pdf_processor.extract_text_from_pdf(pdf_path)
            print(f"  📊 Text length: {len(text)} characters")
            paper_result['text_length'] = len(text)
            
            # Test 1: Rule-based methodology section extraction
            print("  🔍 Testing rule-based extraction...")
            rule_based_section = enhanced_processor.extractor._extract_methodology_section(text)
            print(f"    Rule-based section length: {len(rule_based_section)} chars")
            
            paper_result['extraction_results']['rule_based'] = {
                'section_length': len(rule_based_section),
                'section_preview': rule_based_section[:200] + "..." if len(rule_based_section) > 200 else rule_based_section,
                'has_content': len(rule_based_section) > 100,
                'section_text': rule_based_section
            }
            
            # Test 2: LLM-based methodology section extraction
            print("  🤖 Testing LLM-based extraction...")
            llm_section = methodology_only_extractor.extract_methodology_section(text)
            print(f"    LLM-based section length: {len(llm_section)} chars")
            
            paper_result['extraction_results']['llm_based'] = {
                'section_length': len(llm_section),
                'section_preview': llm_section[:200] + "..." if len(llm_section) > 200 else llm_section,
                'has_content': len(llm_section) > 100,
                'section_text': llm_section
            }
            
            # Test 3: Hybrid approach (use LLM if rule-based is too short)
            print("  🔄 Testing hybrid approach...")
            if len(rule_based_section) > 500:
                hybrid_section = rule_based_section
                hybrid_method = 'rule_based'
            else:
                hybrid_section = llm_section
                hybrid_method = 'llm_based'
            
            print(f"    Hybrid section length: {len(hybrid_section)} chars (method: {hybrid_method})")
            
            paper_result['extraction_results']['hybrid'] = {
                'section_length': len(hybrid_section),
                'section_preview': hybrid_section[:200] + "..." if len(hybrid_section) > 200 else hybrid_section,
                'has_content': len(hybrid_section) > 100,
                'method_used': hybrid_method,
                'section_text': hybrid_section
            }
            
            # Test 4: Full methodology extraction using hybrid section
            print("  📊 Testing full methodology extraction...")
            if len(hybrid_section) > 100:
                methodology_data = enhanced_processor.extractor.extract_detailed_methodology(hybrid_section, pdf_path.stem)
                methodology = methodology_data.get('methodology', {})
                
                paper_result['extraction_results']['full_extraction'] = {
                    'methodology_type': methodology.get('type', 'unknown'),
                    'quant_methods': methodology.get('quant_methods', []),
                    'qual_methods': methodology.get('qual_methods', []),
                    'software': methodology.get('software', []),
                    'sample_size': methodology.get('sample_size', ''),
                    'confidence': methodology.get('confidence', 0.0),
                    'extraction_notes': methodology.get('extraction_notes', ''),
                    'success': True
                }
                
                print(f"    Methodology type: {methodology.get('type', 'unknown')}")
                print(f"    Quant methods: {methodology.get('quant_methods', [])}")
                print(f"    Confidence: {methodology.get('confidence', 0.0)}")
            else:
                paper_result['extraction_results']['full_extraction'] = {
                    'success': False,
                    'reason': 'No methodology section found'
                }
                print("    ❌ No methodology section found")
            
            # Analysis
            rule_has_content = len(rule_based_section) > 100
            llm_has_content = len(llm_section) > 100
            hybrid_has_content = len(hybrid_section) > 100
            
            print(f"  📈 Analysis:")
            print(f"    Rule-based found content: {rule_has_content}")
            print(f"    LLM-based found content: {llm_has_content}")
            print(f"    Hybrid found content: {hybrid_has_content}")
            
            paper_result['analysis'] = {
                'rule_based_success': rule_has_content,
                'llm_based_success': llm_has_content,
                'hybrid_success': hybrid_has_content,
                'best_method': 'rule_based' if rule_has_content and len(rule_based_section) > len(llm_section) else 'llm_based' if llm_has_content else 'none'
            }
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
            paper_result['error'] = str(e)
        
        results['papers'].append(paper_result)
    
    # Summary analysis
    print("\n📊 SUMMARY ANALYSIS")
    print("=" * 60)
    
    total_papers = len(results['papers'])
    rule_based_success = sum(1 for p in results['papers'] if p.get('analysis', {}).get('rule_based_success', False))
    llm_based_success = sum(1 for p in results['papers'] if p.get('analysis', {}).get('llm_based_success', False))
    hybrid_success = sum(1 for p in results['papers'] if p.get('analysis', {}).get('hybrid_success', False))
    
    print(f"📄 Total papers tested: {total_papers}")
    print(f"🔍 Rule-based success: {rule_based_success}/{total_papers} ({rule_based_success/total_papers*100:.1f}%)")
    print(f"🤖 LLM-based success: {llm_based_success}/{total_papers} ({llm_based_success/total_papers*100:.1f}%)")
    print(f"🔄 Hybrid success: {hybrid_success}/{total_papers} ({hybrid_success/total_papers*100:.1f}%)")
    
    # Best method analysis
    best_methods = [p.get('analysis', {}).get('best_method', 'none') for p in results['papers']]
    method_counts = {method: best_methods.count(method) for method in set(best_methods)}
    print(f"\n🏆 Best method distribution:")
    for method, count in method_counts.items():
        print(f"  {method}: {count}/{total_papers} ({count/total_papers*100:.1f}%)")
    
    # Add summary to results
    results['summary'] = {
        'total_papers': total_papers,
        'rule_based_success_rate': rule_based_success/total_papers*100,
        'llm_based_success_rate': llm_based_success/total_papers*100,
        'hybrid_success_rate': hybrid_success/total_papers*100,
        'best_method_distribution': method_counts
    }
    
    # Save results to JSON
    output_file = f"methodology_extraction_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"📊 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    
    return results

if __name__ == "__main__":
    test_methodology_extraction_comprehensive()
