#!/usr/bin/env python3
"""
Complete Pipeline Execution for All Missing Fields
Runs the high-performance pipeline on all papers with missing data
"""

import os
import logging
import asyncio
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any
from high_performance_pipeline import HighPerformancePipeline

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompletePipelineRunner:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def find_papers_missing_data(self) -> List[Dict[str, Any]]:
        """Find all papers with missing data"""
        papers_to_process = set()
        
        with self.driver.session() as session:
            # Papers missing titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
            
            # Papers missing authors
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT EXISTS((p)<-[:AUTHORED]-()) AND NOT EXISTS((p)-[:AUTHORED_BY]->())
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
            
            # Papers missing theories
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_THEORY]->()
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
            
            # Papers missing methods
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_METHOD]->()
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
            
            # Papers missing phenomena
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:STUDIES_PHENOMENON]->()
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
            
            # Papers missing research questions
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:ADDRESSES]->()
                RETURN DISTINCT p.paper_id
            """)
            for record in result:
                papers_to_process.add(record["p.paper_id"])
        
        return list(papers_to_process)
    
    def find_pdf_path(self, paper_id: str) -> Path:
        """Find PDF file for a paper_id"""
        # Try different patterns
        patterns = [
            f"{paper_id}.pdf",
            f"**/{paper_id}.pdf",
            f"**/*{paper_id}*.pdf",
            f"pdfs/{paper_id}.pdf",
            f"pdfs/**/{paper_id}.pdf"
        ]
        
        for pattern in patterns:
            matches = list(Path(".").glob(pattern))
            if matches:
                return matches[0]
        
        return None
    
    async def run_complete_pipeline(self, limit: int = None):
        """Run complete pipeline for all papers with missing data"""
        paper_ids = self.find_papers_missing_data()
        
        if limit:
            paper_ids = paper_ids[:limit]
        
        logger.info(f"Found {len(paper_ids)} papers with missing data")
        
        # Find PDFs
        pdf_paths = []
        papers_without_pdfs = []
        
        for paper_id in paper_ids:
            pdf_path = self.find_pdf_path(paper_id)
            if pdf_path and pdf_path.exists():
                pdf_paths.append(pdf_path)
            else:
                papers_without_pdfs.append(paper_id)
        
        logger.info(f"Papers with PDFs: {len(pdf_paths)}")
        logger.info(f"Papers without PDFs: {len(papers_without_pdfs)}")
        
        if papers_without_pdfs:
            logger.warning(f"\nFirst 10 papers without PDFs: {papers_without_pdfs[:10]}")
        
        # Run pipeline
        if pdf_paths:
            logger.info(f"\nStarting pipeline for {len(pdf_paths)} papers...")
            
            pipeline = HighPerformancePipeline(max_workers=10)  # Reduced for stability
            
            # Discover papers (this will add them to the pipeline)
            pipeline.discover_papers(pdf_paths)
            
            # Run the pipeline
            await pipeline.run()
            
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE EXECUTION COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Processed: {pipeline.stats.processed}")
            logger.info(f"Failed: {pipeline.stats.failed}")
            logger.info(f"Skipped: {pipeline.stats.skipped}")
        else:
            logger.warning("No papers with PDFs found to process")
    
    def close(self):
        self.driver.close()

async def main():
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Processing first {limit} papers...")
    
    runner = CompletePipelineRunner()
    try:
        await runner.run_complete_pipeline(limit=limit)
    finally:
        runner.close()

if __name__ == "__main__":
    asyncio.run(main())
