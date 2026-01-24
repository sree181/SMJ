#!/usr/bin/env python3
"""
Test script for ResearchQuestion and Variable extraction
"""

from redesigned_methodology_extractor import RedesignedOllamaExtractor, RedesignedPDFProcessor
from pathlib import Path
import json
import sys

def test_extraction(pdf_path: Path):
    """Test research question and variable extraction"""
    
    extractor = RedesignedOllamaExtractor(model='llama3.1:8b')
    pdf_processor = RedesignedPDFProcessor()
    
    paper_id = pdf_path.stem
    print(f"\n{'='*70}")
    print(f"Testing ResearchQuestion & Variable Extraction: {paper_id}")
    print(f"{'='*70}\n")
    
    # Extract text
    text = pdf_processor.extract_text_from_pdf(pdf_path)
    print(f"Text length: {len(text)} characters\n")
    
    # Extract research questions
    print("Extracting research questions...")
    research_questions = extractor.extract_research_questions(text, paper_id)
    print(f"✓ Extracted {len(research_questions)} research questions\n")
    
    # Extract variables
    print("Extracting variables...")
    variables = extractor.extract_variables(text, paper_id)
    print(f"✓ Extracted {len(variables)} variables\n")
    
    # Display results
    print("="*70)
    print("RESEARCH QUESTIONS")
    print("="*70)
    for i, rq in enumerate(research_questions, 1):
        print(f"\n{i}. {rq.get('question', 'N/A')}")
        print(f"   Type: {rq.get('question_type', 'N/A')}")
        print(f"   Section: {rq.get('section', 'N/A')}")
        print(f"   Domain: {rq.get('domain', 'N/A')}")
    
    print("\n" + "="*70)
    print("VARIABLES")
    print("="*70)
    
    # Group by type
    by_type = {}
    for var in variables:
        var_type = var.get('variable_type', 'unknown')
        if var_type not in by_type:
            by_type[var_type] = []
        by_type[var_type].append(var)
    
    for var_type, vars_list in by_type.items():
        print(f"\n{var_type.upper()} Variables ({len(vars_list)}):")
        for i, var in enumerate(vars_list, 1):
            print(f"  {i}. {var.get('variable_name', 'N/A')}")
            if var.get('measurement'):
                print(f"     Measurement: {var.get('measurement')}")
            if var.get('operationalization'):
                print(f"     Operationalization: {var.get('operationalization')}")
    
    # Save to JSON
    output = {
        "paper_id": paper_id,
        "research_questions": research_questions,
        "variables": variables
    }
    
    output_file = Path(f"extraction_test_{paper_id}.json")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path("2025-2029/2025_4359.pdf")
    
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    test_extraction(pdf_path)

