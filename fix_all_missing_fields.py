#!/usr/bin/env python3
"""
Comprehensive Pipeline to Fix All Missing Fields
Runs extraction and ingestion for all papers with missing data
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

class MissingFieldsFixer:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.pipeline = HighPerformancePipeline()
    
    def find_papers_missing_data(self) -> List[Dict[str, Any]]:
        """Find all papers with missing data"""
        papers_to_process = []
        
        with self.driver.session() as session:
            # Papers missing titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN p.paper_id, 'title' as missing_field
            """)
            for record in result:
                papers_to_process.append({
                    "paper_id": record["p.paper_id"],
                    "missing_fields": ["title"]
                })
            
            # Papers missing authors
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT EXISTS((p)<-[:AUTHORED]-()) AND NOT EXISTS((p)-[:AUTHORED_BY]->())
                RETURN p.paper_id, 'authors' as missing_field
            """)
            for record in result:
                paper_id = record["p.paper_id"]
                # Add to existing or create new
                existing = next((p for p in papers_to_process if p["paper_id"] == paper_id), None)
                if existing:
                    if "authors" not in existing["missing_fields"]:
                        existing["missing_fields"].append("authors")
                else:
                    papers_to_process.append({
                        "paper_id": paper_id,
                        "missing_fields": ["authors"]
                    })
            
            # Papers missing theories
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_THEORY]->()
                RETURN p.paper_id, 'theories' as missing_field
            """)
            for record in result:
                paper_id = record["p.paper_id"]
                existing = next((p for p in papers_to_process if p["paper_id"] == paper_id), None)
                if existing:
                    if "theories" not in existing["missing_fields"]:
                        existing["missing_fields"].append("theories")
                else:
                    papers_to_process.append({
                        "paper_id": paper_id,
                        "missing_fields": ["theories"]
                    })
            
            # Papers missing methods
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_METHOD]->()
                RETURN p.paper_id, 'methods' as missing_field
            """)
            for record in result:
                paper_id = record["p.paper_id"]
                existing = next((p for p in papers_to_process if p["paper_id"] == paper_id), None)
                if existing:
                    if "methods" not in existing["missing_fields"]:
                        existing["missing_fields"].append("methods")
                else:
                    papers_to_process.append({
                        "paper_id": paper_id,
                        "missing_fields": ["methods"]
                    })
            
            # Papers missing phenomena
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:STUDIES_PHENOMENON]->()
                RETURN p.paper_id, 'phenomena' as missing_field
            """)
            for record in result:
                paper_id = record["p.paper_id"]
                existing = next((p for p in papers_to_process if p["paper_id"] == paper_id), None)
                if existing:
                    if "phenomena" not in existing["missing_fields"]:
                        existing["missing_fields"].append("phenomena")
                else:
                    papers_to_process.append({
                        "paper_id": paper_id,
                        "missing_fields": ["phenomena"]
                    })
            
            # Papers missing research questions
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:ADDRESSES]->()
                RETURN p.paper_id, 'research_questions' as missing_field
            """)
            for record in result:
                paper_id = record["p.paper_id"]
                existing = next((p for p in papers_to_process if p["paper_id"] == paper_id), None)
                if existing:
                    if "research_questions" not in existing["missing_fields"]:
                        existing["missing_fields"].append("research_questions")
                else:
                    papers_to_process.append({
                        "paper_id": paper_id,
                        "missing_fields": ["research_questions"]
                    })
        
        return papers_to_process
    
    def find_pdf_path(self, paper_id: str) -> Path:
        """Find PDF file for a paper_id"""
        patterns = [
            f"{paper_id}.pdf",
            f"**/{paper_id}.pdf",
            f"**/*{paper_id}*.pdf"
        ]
        
        for pattern in patterns:
            matches = list(Path(".").glob(pattern))
            if matches:
                return matches[0]
        
        return None
    
    async def process_all_papers(self, limit: int = None):
        """Process all papers with missing data"""
        papers = self.find_papers_missing_data()
        
        if limit:
            papers = papers[:limit]
        
        logger.info(f"Found {len(papers)} papers with missing data")
        
        # Group by missing fields for summary
        field_counts = {}
        for paper in papers:
            for field in paper["missing_fields"]:
                field_counts[field] = field_counts.get(field, 0) + 1
        
        logger.info("\nMissing Fields Summary:")
        for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {field}: {count} papers")
        
        # Find PDFs
        papers_with_pdfs = []
        papers_without_pdfs = []
        
        for paper in papers:
            pdf_path = self.find_pdf_path(paper["paper_id"])
            if pdf_path and pdf_path.exists():
                paper["pdf_path"] = pdf_path
                papers_with_pdfs.append(paper)
            else:
                papers_without_pdfs.append(paper)
        
        logger.info(f"\nPapers with PDFs: {len(papers_with_pdfs)}")
        logger.info(f"Papers without PDFs: {len(papers_without_pdfs)}")
        
        if papers_without_pdfs:
            logger.warning("\nPapers without PDFs (first 10):")
            for paper in papers_without_pdfs[:10]:
                logger.warning(f"  {paper['paper_id']}: {', '.join(paper['missing_fields'])}")
        
        # Process papers with PDFs
        if papers_with_pdfs:
            logger.info(f"\nProcessing {len(papers_with_pdfs)} papers...")
            
            # Use the high-performance pipeline
            pdf_paths = [p["pdf_path"] for p in papers_with_pdfs]
            
            # Run pipeline
            await self.pipeline.process_papers(pdf_paths)
            
            logger.info("\n" + "=" * 80)
            logger.info("PROCESSING COMPLETE")
            logger.info("=" * 80)
        else:
            logger.warning("No papers with PDFs found to process")
    
    def close(self):
        self.driver.close()
        if hasattr(self.pipeline, 'close'):
            self.pipeline.close()

async def main():
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Processing first {limit} papers...")
    
    fixer = MissingFieldsFixer()
    try:
        await fixer.process_all_papers(limit=limit)
    finally:
        fixer.close()

if __name__ == "__main__":
    asyncio.run(main())
