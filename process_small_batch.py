#!/usr/bin/env python3
"""
Process a small batch of papers (3-5 papers) for testing
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

def extract_with_llm(text: str, section: str, paper_id: str, llm_client, extraction_type="questions"):
    """Extract information using LLM"""
    if len(text) > 3000:
        text = text[:3000] + "..."
    
    if extraction_type == "questions":
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
    elif extraction_type == "methodology":
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
    elif extraction_type == "findings":
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify research findings.

        Text: {text}

        Extract findings in this JSON format:
        {{
            "findings": [
                {{
                    "finding": "description of the finding",
                    "finding_type": "positive|negative|neutral|mixed|significant|non_significant",
                    "significance": "statistical significance if mentioned or null",
                    "context": "brief context"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no findings are found, return {{"findings": []}}.
        """
    
    try:
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content.strip())
        if extraction_type == "questions":
            return data.get("questions", [])
        elif extraction_type == "methodology":
            return data.get("methodologies", [])
        elif extraction_type == "findings":
            return data.get("findings", [])
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
    
    # Extract different types of information
    logger.info("Extracting research questions...")
    questions = extract_with_llm(intro_text, "introduction", paper_id, llm_client, "questions")
    
    logger.info("Extracting methodology...")
    methodologies = extract_with_llm(intro_text, "introduction", paper_id, llm_client, "methodology")
    
    logger.info("Extracting findings...")
    findings = extract_with_llm(intro_text, "introduction", paper_id, llm_client, "findings")
    
    logger.info(f"Found: {len(questions)} questions, {len(methodologies)} methodologies, {len(findings)} findings")
    
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
            
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (meth:Methodology {id: $method_id})
                MERGE (p)-[:USES_METHODOLOGY]->(meth)
            """, paper_id=paper_id, method_id=method_id)
        
        # Create finding nodes
        for f in findings:
            finding_id = f"{paper_id}_f_{hash(f['finding']) % 10000}"
            session.run("""
                MERGE (find:Finding {id: $finding_id})
                SET find.finding = $finding, find.finding_type = $finding_type,
                    find.significance = $significance, find.context = $context
            """, finding_id=finding_id, finding=f['finding'], 
                 finding_type=f['finding_type'], significance=f.get('significance'),
                 context=f['context'])
            
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH (find:Finding {id: $finding_id})
                MERGE (p)-[:REPORTS_FINDING]->(find)
            """, paper_id=paper_id, finding_id=finding_id)
    
    logger.info(f"✓ Completed processing {pdf_path.name}")
    return True

def main():
    """Process a small batch of papers"""
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
    
    # Process 3 papers from 1985-1989 bucket
    bucket_path = Path("1985-1989")
    pdf_files = list(bucket_path.glob("*.pdf"))[:3]  # Only first 3 papers
    
    print(f"\nProcessing {len(pdf_files)} papers from {bucket_path.name}:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    processed = 0
    for pdf_file in pdf_files:
        try:
            if process_single_paper(pdf_file, llm_client, neo4j_driver):
                processed += 1
                print(f"\nProgress: {processed}/{len(pdf_files)} papers completed")
                time.sleep(2)  # Small delay between papers
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
    
    print(f"\n✓ Batch processing completed: {processed} papers processed")
    
    # Show results
    with neo4j_driver.session() as session:
        result = session.run("MATCH (p:Paper) RETURN count(p) as total")
        total_papers = result.single()["total"]
        print(f"📊 Total papers in database: {total_papers}")
    
    neo4j_driver.close()

if __name__ == "__main__":
    main()
