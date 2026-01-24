#!/usr/bin/env python3
"""
Test OLLAMA extraction without Neo4j connection
"""

import os
from pathlib import Path
from Kb_ollama import PDFProcessor, OllamaExtractor, OllamaClient

def test_ollama_extraction():
    """Test OLLAMA extraction without Neo4j"""
    print("🧪 Testing OLLAMA Extraction (No Neo4j)")
    print("=" * 50)
    
    # Initialize OLLAMA client
    ollama_client = OllamaClient(model="llama3.1:8b")
    
    # Initialize components
    pdf_processor = PDFProcessor(ollama_client)
    entity_extractor = OllamaExtractor(ollama_client)
    
    # Test with a sample paper
    test_paper = Path('./1995-1999/1995_811.pdf')
    if not test_paper.exists():
        print("❌ Test paper not found")
        return
    
    print(f"📄 Testing with: {test_paper.name}")
    
    try:
        # Extract text
        print("📖 Extracting text from PDF...")
        text = pdf_processor.extract_text_from_pdf(test_paper)
        if not text:
            print("❌ Failed to extract text")
            return
        
        print(f"✓ Extracted {len(text)} characters")
        
        # Identify sections
        print("🔍 Identifying sections...")
        sections = pdf_processor.identify_sections_ollama(text)
        print(f"✓ Found sections: {list(sections.keys())}")
        
        # Extract entities from each section
        all_questions = []
        all_methodologies = []
        all_findings = []
        all_contributions = []
        all_entities = []
        all_relationships = []
        
        paper_id = test_paper.stem
        
        for section_name, section_text in sections.items():
            if not section_text or section_text == "null":
                continue
                
            print(f"\\n📝 Processing {section_name} section...")
            
            # Extract research questions
            questions = entity_extractor.extract_research_questions(section_text, section_name, paper_id)
            all_questions.extend(questions)
            print(f"  ❓ Questions: {len(questions)}")
            
            # Extract methodology
            methodologies = entity_extractor.extract_methodology(section_text, section_name, paper_id)
            all_methodologies.extend(methodologies)
            print(f"  🔬 Methodologies: {len(methodologies)}")
            
            # Extract findings
            findings = entity_extractor.extract_findings(section_text, section_name, paper_id)
            all_findings.extend(findings)
            print(f"  📈 Findings: {len(findings)}")
            
            # Extract contributions
            contributions = entity_extractor.extract_contributions(section_text, section_name, paper_id)
            all_contributions.extend(contributions)
            print(f"  🏆 Contributions: {len(contributions)}")
            
            # Extract entities
            entities = entity_extractor.extract_entities(section_text, section_name, paper_id)
            all_entities.extend(entities)
            print(f"  🏷️  Entities: {len(entities)}")
            
            # Extract relationships
            relationships = entity_extractor.extract_relationships(section_text, section_name, paper_id)
            all_relationships.extend(relationships)
            print(f"  🔗 Relationships: {len(relationships)}")
        
        # Print summary
        print("\\n" + "="*50)
        print("📊 EXTRACTION SUMMARY")
        print("="*50)
        print(f"📄 Paper: {test_paper.name}")
        print(f"📊 Questions: {len(all_questions)}")
        print(f"🔬 Methodologies: {len(all_methodologies)}")
        print(f"📈 Findings: {len(all_findings)}")
        print(f"🏆 Contributions: {len(all_contributions)}")
        print(f"🏷️  Entities: {len(all_entities)}")
        print(f"🔗 Relationships: {len(all_relationships)}")
        
        # Show samples
        if all_questions:
            print(f"\\n📝 Sample Question: {all_questions[0].question[:150]}...")
        if all_methodologies:
            print(f"🔬 Sample Methodology: {all_methodologies[0].methodology[:150]}...")
        if all_findings:
            print(f"📈 Sample Finding: {all_findings[0].finding[:150]}...")
        if all_entities:
            print(f"🏷️  Sample Entity: {all_entities[0].name} ({all_entities[0].type})")
        
        print("\\n✅ OLLAMA extraction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama_extraction()
