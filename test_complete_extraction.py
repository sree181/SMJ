#!/usr/bin/env python3
"""
Test complete extraction pipeline on one paper
Tests all node types: Paper, Method, Theory, ResearchQuestion, Variable, Finding, Contribution, Software, Dataset
"""

from redesigned_methodology_extractor import RedesignedMethodologyProcessor
from pathlib import Path
import json
import sys

def test_complete_extraction(pdf_path: Path):
    """Test complete extraction pipeline"""
    
    processor = RedesignedMethodologyProcessor()
    paper_id = pdf_path.stem
    
    print(f"\n{'='*70}")
    print(f"Testing COMPLETE Extraction Pipeline: {paper_id}")
    print(f"{'='*70}\n")
    
    try:
        result = processor.process_paper(pdf_path)
        
        print("="*70)
        print("EXTRACTION SUMMARY")
        print("="*70)
        
        paper_meta = result.get("paper_metadata", {})
        print(f"\n✅ Paper Metadata:")
        print(f"   Title: {bool(paper_meta.get('title'))}")
        print(f"   Abstract: {bool(paper_meta.get('abstract'))}")
        print(f"   Authors: {len(result.get('authors', []))}")
        print(f"   Year: {paper_meta.get('publication_year', 'N/A')}")
        print(f"   DOI: {bool(paper_meta.get('doi'))}")
        
        print(f"\n✅ Methods: {len(result.get('methods', []))}")
        print(f"✅ Theories: {len(result.get('theories', []))}")
        print(f"✅ Research Questions: {len(result.get('research_questions', []))}")
        print(f"✅ Variables: {len(result.get('variables', []))}")
        print(f"✅ Findings: {len(result.get('findings', []))}")
        print(f"✅ Contributions: {len(result.get('contributions', []))}")
        print(f"✅ Software: {len(result.get('software', []))}")
        print(f"✅ Datasets: {len(result.get('datasets', []))}")
        
        # Save to JSON
        output_file = Path(f"complete_extraction_{paper_id}.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n{'='*70}")
        print(f"✅ Complete extraction successful!")
        print(f"Results saved to: {output_file}")
        print(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path("2025-2029/2025_4359.pdf")
    
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    test_complete_extraction(pdf_path)

