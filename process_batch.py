#!/usr/bin/env python3
"""
Process papers in small batches with user control
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

def extract_research_questions(text: str, section: str, paper_id: str, llm_client):
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

def extract_methodology(text: str, section: str, paper_id: str, llm_client):
    """Extract methodology using LLM"""
    if len(text) > 3000:
        text = text[:3000] + "..."
    
    prompt = f"""
    Analyze this text from the {section} section of a research paper and identify methodology details.

    Text: {text}

    Extract methodology information in this JSON format:
    {{
        "methodologies": [
            {{
                "method_type": "quantitative|qualitative|mixed|experimental|case_study",
                "data_source": "description of data source",
                "sample_size": number or null,
                "analysis_technique": "specific analysis techniques used",
                "research_design": "description of research design",
                "context": "brief context"
            }}
        ]
    }}

    Only return valid JSON, no additional text. If no methodology is found, return {{"methodologies": []}}.
    """
    
    try:
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content.strip())
        return data.get("methodologies", [])
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
        return False
    
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
    questions = extract_research_questions(intro_text, "introduction", paper_id, llm_client)
    
    # Extract methodology
    logger.info("Extracting methodology...")
    methodologies = extract_methodology(intro_text, "introduction", paper_id, llm_client)
    
    logger.info(f"Found {len(questions)} research questions and {len(methodologies)} methodologies")
    
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
        
        # Create methodology nodes
        for m in methodologies:
            method_id = f"{paper_id}_m_{hash(m['method_type']) % 10000}"
            session.run("""
                MERGE (meth:Methodology {id: $method_id})
                SET meth.method_type = $method_type, meth.data_source = $data_source,
                    meth.sample_size = $sample_size, meth.analysis_technique = $analysis_technique,
                    meth.research_design = $research_design, meth.context = $context
            """, method_id=method_id, method_type=m['method_type'], 
                 data_source=m['data_source'], sample_size=m.get('sample_size'),
                 analysis_technique=m['analysis_technique'], research_design=m['research_design'],
                 context=m['context'])
            
            # Link to paper
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (meth:Methodology {id: $method_id})
                MERGE (p)-[:USES_METHODOLOGY]->(meth)
            """, paper_id=paper_id, method_id=method_id)
    
    logger.info(f"✓ Completed processing {pdf_path.name}")
    return True

def process_bucket(bucket_path: Path, llm_client, neo4j_driver, max_papers=5):
    """Process papers in a bucket with limit"""
    logger.info(f"Processing bucket: {bucket_path.name} (max {max_papers} papers)")
    
    pdf_files = list(bucket_path.glob("*.pdf"))[:max_papers]  # Limit to max_papers
    processed = 0
    
    for pdf_file in pdf_files:
        try:
            if process_single_paper(pdf_file, llm_client, neo4j_driver):
                processed += 1
                logger.info(f"Progress: {processed}/{len(pdf_files)} papers processed")
                
                # Small delay to avoid rate limiting
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
    
    logger.info(f"✓ Completed bucket {bucket_path.name}: {processed} papers processed")
    return processed

def main():
    """Main function to process papers in batches"""
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
    
    # Find bucket directories
    bucket_dirs = [d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith("19") or d.name.startswith("20")]
    bucket_dirs.sort()
    
    print(f"\nFound {len(bucket_dirs)} buckets:")
    for i, bucket in enumerate(bucket_dirs, 1):
        pdf_count = len(list(bucket.glob("*.pdf")))
        print(f"  {i}. {bucket.name}: {pdf_count} papers")
    
    # Ask user which bucket to process
    try:
        choice = input(f"\nWhich bucket to process? (1-{len(bucket_dirs)}, or 'all' for all buckets): ").strip()
        
        if choice.lower() == 'all':
            # Process all buckets with limit
            max_per_bucket = int(input("How many papers per bucket? (default 3): ") or "3")
            total_processed = 0
            
            for bucket in bucket_dirs:
                processed = process_bucket(bucket, llm_client, neo4j_driver, max_per_bucket)
                total_processed += processed
                
                # Ask if user wants to continue
                if bucket != bucket_dirs[-1]:  # Not the last bucket
                    continue_choice = input(f"\nContinue to next bucket? (y/n): ").strip().lower()
                    if continue_choice != 'y':
                        break
            
            print(f"\n✓ Total papers processed: {total_processed}")
        else:
            # Process specific bucket
            bucket_index = int(choice) - 1
            if 0 <= bucket_index < len(bucket_dirs):
                bucket = bucket_dirs[bucket_index]
                max_papers = int(input(f"How many papers from {bucket.name}? (default 5): ") or "5")
                processed = process_bucket(bucket, llm_client, neo4j_driver, max_papers)
                print(f"\n✓ Processed {processed} papers from {bucket.name}")
            else:
                print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        neo4j_driver.close()
        print("✓ Neo4j connection closed")

if __name__ == "__main__":
    main()
