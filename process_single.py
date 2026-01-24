#!/usr/bin/env python3
"""
Process a single PDF article and test the extraction
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
import fitz
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_with_llm(text: str, section: str, paper_id: str, llm_client):
    """Extract research questions using LLM"""
    if len(text) > 3000:
        text = text[:3000] + "..."
    
    prompt = f"""
    Analyze this text from the {section} section of a research paper and identify all research questions.

    Text: {text}

    Extract research questions in this JSON format:
    {{
        "questions": [
            {{
                "question": "the exact research question text",
                "question_type": "what|how|why|when|where|which",
                "context": "brief context around the question"
            }}
        ]
    }}

    Only return valid JSON, no additional text. If no research questions are found, return {{"questions": []}}.
    """
    
    try:
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content.strip())
        return data.get("questions", [])
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}")
        return []

def process_single_paper(pdf_path: Path, llm_client, neo4j_driver):
    """Process a single PDF paper"""
    logger.info(f"Processing: {pdf_path.name}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text:
        logger.warning(f"No text extracted from {pdf_path}")
        return
    
    # Extract metadata from filename
    import re
    match = re.match(r'(\d{4})_(\d+)(?:_(\d+))?\.pdf', pdf_path.name)
    if match:
        year = int(match.group(1))
        volume = match.group(2)
        issue = match.group(3) if match.group(3) else None
    else:
        year = 0
        volume = None
        issue = None
    
    paper_id = pdf_path.stem
    
    # Simple section extraction (first 2000 chars as introduction)
    intro_text = text[:2000] if len(text) > 2000 else text
    
    # Extract research questions using LLM
    logger.info("Extracting research questions...")
    questions = extract_with_llm(intro_text, "introduction", paper_id, llm_client)
    
    logger.info(f"Found {len(questions)} research questions")
    for i, q in enumerate(questions, 1):
        logger.info(f"  Q{i}: {q['question'][:100]}...")
    
    # Store in Neo4j
    with neo4j_driver.session() as session:
        # Create paper node
        session.run("""
            MERGE (p:Paper {paper_id: $paper_id})
            SET p.year = $year, p.volume = $volume, p.issue = $issue
        """, paper_id=paper_id, year=year, volume=volume, issue=issue)
        
        # Create research question nodes
        for q in questions:
            question_id = f"{paper_id}_q_{hash(q['question']) % 10000}"
            session.run("""
                MERGE (rq:ResearchQuestion {id: $question_id})
                SET rq.question = $question, rq.question_type = $question_type, rq.context = $context
            """, question_id=question_id, question=q['question'], 
                 question_type=q['question_type'], context=q['context'])
            
            # Link to paper
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (rq:ResearchQuestion {id: $question_id})
                MERGE (p)-[:HAS_RESEARCH_QUESTION]->(rq)
            """, paper_id=paper_id, question_id=question_id)
    
    logger.info(f"✓ Completed processing {pdf_path.name}")

def main():
    """Main function to process a single paper"""
    load_dotenv()
    
    # Initialize clients
    llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    # Test connection
    with neo4j_driver.session() as session:
        result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
        print(f"✓ {result.single()['message']}")
    
    # Process a single PDF
    pdf_files = list(Path(".").glob("*/1988_305.pdf"))
    if pdf_files:
        pdf_path = pdf_files[0]
        print(f"\nProcessing single paper: {pdf_path}")
        process_single_paper(pdf_path, llm_client, neo4j_driver)
    else:
        print("No test PDF found")
    
    neo4j_driver.close()
    print("\n✓ Single paper processing completed!")

if __name__ == "__main__":
    main()
