#!/usr/bin/env python3
"""
Test script to improve Paper node extraction
Tests different prompt strategies and shows what's being extracted
"""

from redesigned_methodology_extractor import RedesignedOllamaExtractor, RedesignedPDFProcessor
from pathlib import Path
import json

def test_paper_extraction(pdf_path: Path):
    """Test paper metadata extraction"""
    
    extractor = RedesignedOllamaExtractor(model='llama3.1:8b')
    pdf_processor = RedesignedPDFProcessor()
    
    paper_id = pdf_path.stem
    print(f"\n{'='*70}")
    print(f"Testing Paper Extraction: {paper_id}")
    print(f"{'='*70}\n")
    
    # Extract text
    text = pdf_processor.extract_text_from_pdf(pdf_path)
    print(f"Text length: {len(text)} characters")
    print(f"\nFirst 1000 characters of paper:")
    print("-" * 70)
    print(text[:1000])
    print("-" * 70)
    
    # Extract metadata
    print("\nExtracting metadata...")
    result = extractor.extract_paper_metadata(text, paper_id)
    
    print("\n" + "="*70)
    print("EXTRACTION RESULT")
    print("="*70)
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    
    # Analyze what was extracted
    print("\n" + "="*70)
    print("EXTRACTION ANALYSIS")
    print("="*70)
    
    paper_meta = result.get("paper_metadata", {})
    print(f"\n✅ Extracted Fields:")
    print(f"   Title: {bool(paper_meta.get('title'))} - '{paper_meta.get('title', '')[:80]}...'")
    print(f"   Abstract: {bool(paper_meta.get('abstract'))} - {len(paper_meta.get('abstract', ''))} chars")
    print(f"   Year: {paper_meta.get('publication_year', 'N/A')}")
    print(f"   Journal: {bool(paper_meta.get('journal'))} - '{paper_meta.get('journal', '')}'")
    print(f"   DOI: {bool(paper_meta.get('doi'))} - '{paper_meta.get('doi', '')}'")
    print(f"   Volume: {paper_meta.get('volume', 'N/A')}")
    print(f"   Issue: {paper_meta.get('issue', 'N/A')}")
    print(f"   Pages: {paper_meta.get('pages', 'N/A')}")
    print(f"   Keywords: {len(paper_meta.get('keywords', []))} keywords")
    print(f"   Paper Type: {paper_meta.get('paper_type', 'N/A')}")
    
    authors = result.get("authors", [])
    print(f"\n✅ Authors: {len(authors)}")
    for i, author in enumerate(authors, 1):
        print(f"   {i}. {author.get('full_name', 'N/A')} (email: {author.get('email', 'N/A')})")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path("2025-2029/2025_4359.pdf")
    
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    test_paper_extraction(pdf_path)

