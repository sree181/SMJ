#!/usr/bin/env python3
"""
Test the redesigned extraction system with Neo4j ingestion
Processes papers from 2025-2029 folder and ingests into Neo4j
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from redesigned_methodology_extractor import RedesignedMethodologyProcessor

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_redesigned_ingestion(test_dir: Path, max_papers: int = 5, model: str = "llama3.1:8b"):
    """Test redesigned extraction system with Neo4j ingestion"""
    
    logger.info(f"\n{'='*70}")
    logger.info("TESTING REDESIGNED EXTRACTION SYSTEM WITH NEO4J INGESTION")
    logger.info(f"{'='*70}\n")
    
    # Get Neo4j credentials
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://fe285b91.databases.neo4j.io")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw")
    
    logger.info(f"📊 Model: {model}")
    logger.info(f"📁 Directory: {test_dir}")
    logger.info(f"📄 Max papers: {max_papers}")
    logger.info(f"🔗 Neo4j URI: {neo4j_uri}\n")
    
    # Initialize processor
    processor = RedesignedMethodologyProcessor(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        ollama_model=model
    )
    
    # Find PDF files
    pdf_files = list(test_dir.glob("*.pdf"))[:max_papers]
    if not pdf_files:
        logger.error(f"❌ No PDF files found in {test_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process\n")
    
    # Process each paper
    successful = 0
    failed = 0
    total_methods = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        paper_id = pdf_path.stem
        logger.info(f"\n{'='*70}")
        logger.info(f"[{i}/{len(pdf_files)}] Processing: {paper_id}")
        logger.info(f"{'='*70}\n")
        
        try:
            result = processor.process_paper(pdf_path)
            
            methods_count = len(result.get("methods_data", []))
            total_methods += methods_count
            
            logger.info(f"\n✅ Successfully processed {paper_id}")
            logger.info(f"   Methods extracted: {methods_count}")
            
            if methods_count > 0:
                for method in result.get("methods_data", []):
                    logger.info(f"   - {method.get('method_name', 'Unknown')} (confidence: {method.get('confidence', 0.0):.2f})")
            
            successful += 1
            
        except Exception as e:
            logger.error(f"\n❌ Failed to process {paper_id}: {e}")
            failed += 1
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("PROCESSING SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"✅ Successful: {successful}/{len(pdf_files)}")
    logger.info(f"❌ Failed: {failed}/{len(pdf_files)}")
    logger.info(f"📊 Total methods extracted: {total_methods}")
    if successful > 0:
        logger.info(f"📊 Avg methods per paper: {total_methods/successful:.1f}")
    logger.info(f"{'='*70}\n")
    
    # Check Neo4j status
    logger.info("Checking Neo4j status...")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session() as session:
            # Count papers
            paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()['count']
            # Count methods
            method_count = session.run("MATCH (m:Method) RETURN count(m) as count").single()['count']
            # Count relationships
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            logger.info(f"\n📊 Neo4j Status:")
            logger.info(f"   Papers: {paper_count}")
            logger.info(f"   Methods: {method_count}")
            logger.info(f"   Relationships: {rel_count}")
        
        driver.close()
    except Exception as e:
        logger.error(f"Error checking Neo4j status: {e}")
    
    # Close processor
    processor.ingester.close()
    
    logger.info("\n✅ Test complete!")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test redesigned extraction with Neo4j ingestion")
    parser.add_argument("--dir", type=str, default="2025-2029", help="Directory with PDFs")
    parser.add_argument("--max-papers", type=int, default=5, help="Maximum number of papers to process")
    parser.add_argument("--model", type=str, default="llama3.1:8b", help="OLLAMA model to use")
    
    args = parser.parse_args()
    
    test_dir = Path(args.dir)
    if not test_dir.exists():
        logger.error(f"Directory not found: {test_dir}")
        return
    
    test_redesigned_ingestion(test_dir, max_papers=args.max_papers, model=args.model)


if __name__ == "__main__":
    main()

