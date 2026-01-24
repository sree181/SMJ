#!/usr/bin/env python3
"""
Test script for immediate fixes:
1. Citation extraction
2. Source text validation
3. Quality monitoring
4. Vector indexes
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from redesigned_methodology_extractor import RedesignedOllamaExtractor, RedesignedNeo4jIngester
from quality_monitor import QualityMonitor

load_dotenv()

def test_citation_extraction():
    """Test citation extraction"""
    print("\n" + "="*70)
    print("TEST 1: Citation Extraction")
    print("="*70)
    
    extractor = RedesignedOllamaExtractor()
    
    # Sample text with references section
    sample_text = """
    This paper builds on previous work in strategic management.
    
    References:
    Barney, J. (1991). Firm resources and sustained competitive advantage. Journal of Management, 17(1), 99-120.
    Teece, D. J., Pisano, G., & Shuen, A. (1997). Dynamic capabilities and strategic management. Strategic Management Journal, 18(7), 509-533.
    """
    
    citations = extractor.extract_citations(sample_text, "test_paper")
    
    print(f"✓ Extracted {len(citations)} citations")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. {citation.get('cited_title', 'N/A')[:60]}...")
        print(f"     Authors: {citation.get('cited_authors', [])}")
        print(f"     Year: {citation.get('cited_year', 'N/A')}")
    
    return len(citations) > 0

def test_source_validation():
    """Test source text validation"""
    print("\n" + "="*70)
    print("TEST 2: Source Text Validation")
    print("="*70)
    
    extractor = RedesignedOllamaExtractor()
    
    source_text = "This paper uses Resource-Based View (RBV) as its main theoretical framework. We also draw on Agency Theory to support our arguments."
    
    # Test theory validation
    theory_entity = {"theory_name": "Resource-Based View"}
    is_valid, confidence, status = extractor.validate_entity_against_source(
        theory_entity, source_text, "theory"
    )
    
    print(f"✓ Theory validation test:")
    print(f"  Entity: {theory_entity['theory_name']}")
    print(f"  Valid: {is_valid}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Status: {status}")
    
    # Test invalid theory (completely different name)
    invalid_theory = {"theory_name": "Quantum Mechanics Framework"}
    is_valid2, confidence2, status2 = extractor.validate_entity_against_source(
        invalid_theory, source_text, "theory"
    )
    
    print(f"\n✓ Invalid theory test:")
    print(f"  Entity: {invalid_theory['theory_name']}")
    print(f"  Valid: {is_valid2}")
    print(f"  Confidence: {confidence2:.2f}")
    print(f"  Status: {status2}")
    
    return is_valid and not is_valid2

def test_quality_monitor():
    """Test quality monitoring"""
    print("\n" + "="*70)
    print("TEST 3: Quality Monitoring")
    print("="*70)
    
    monitor = QualityMonitor(metrics_file=Path("test_quality_metrics.json"))
    
    # Simulate some extractions
    test_results = [
        {
            'methods': [{'method_name': 'OLS Regression', 'confidence': 0.9}],
            'theories': [{'theory_name': 'RBV', 'confidence': 0.85}],
            'research_questions': [{'question': 'Test question'}],
            'variables': [{'variable_name': 'Performance'}]
        },
        {
            'methods': [{'method_name': 'Case Study', 'confidence': 0.8}],
            'theories': [],
            'research_questions': [],
            'variables': []
        },
        {
            'methods': [{'method_name': 'Panel Data', 'confidence': 0.95}],
            'theories': [{'theory_name': 'Agency Theory', 'confidence': 0.9}],
            'research_questions': [{'question': 'Another question'}],
            'variables': [{'variable_name': 'ROA'}]
        }
    ]
    
    for i, result in enumerate(test_results, 1):
        monitor.track_extraction(f"test_paper_{i}", result, extraction_time=2.5 + i * 0.1)
        time.sleep(0.1)
    
    # Generate report
    report = monitor.generate_report()
    
    print(f"✓ Quality monitoring test:")
    print(f"  Total papers: {report['summary']['total_papers']}")
    print(f"  Success rate: {report['summary']['extraction_success_rate']:.2%}")
    print(f"  Average confidence: {report['summary']['average_confidence']:.2f}")
    print(f"  Status: {report['status']}")
    
    monitor.print_summary()
    
    # Cleanup
    if Path("test_quality_metrics.json").exists():
        Path("test_quality_metrics.json").unlink()
    
    return report['summary']['total_papers'] == 3

def test_vector_indexes():
    """Test vector indexes"""
    print("\n" + "="*70)
    print("TEST 4: Vector Indexes")
    print("="*70)
    
    from neo4j import GraphDatabase
    from create_vector_indexes import VectorIndexCreator
    
    creator = VectorIndexCreator()
    
    try:
        creator.verify_indexes()
        print("✓ Vector indexes verified")
        return True
    except Exception as e:
        print(f"✗ Error verifying indexes: {e}")
        return False
    finally:
        creator.close()

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TESTING IMMEDIATE FIXES")
    print("="*70)
    
    results = {
        'citation_extraction': test_citation_extraction(),
        'source_validation': test_source_validation(),
        'quality_monitor': test_quality_monitor(),
        'vector_indexes': test_vector_indexes()
    }
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

