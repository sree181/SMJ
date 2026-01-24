#!/usr/bin/env python3
"""
Re-extract Titles for Papers Missing Titles
Extracts titles from PDFs for papers that don't have titles in Neo4j
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path
from enhanced_gpt4_extractor import EnhancedGPT4Extractor
import asyncio

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TitleReExtractor:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.extractor = EnhancedGPT4Extractor()
        self.pdf_base_path = Path("pdfs")  # Adjust if needed
    
    def find_papers_without_titles(self):
        """Find all papers without titles"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN p.paper_id, p.year
                ORDER BY p.paper_id
            """)
            papers = [{"paper_id": record["p.paper_id"], "year": record["p.year"]} 
                     for record in result]
            return papers
    
    def find_pdf_path(self, paper_id: str) -> Path:
        """Find PDF file for a paper_id"""
        # Try different patterns
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
    
    async def extract_title_from_pdf(self, paper_id: str, pdf_path: Path) -> str:
        """Extract title from PDF"""
        try:
            # Extract just metadata (including title)
            result = await self.extractor.extract_paper_async(pdf_path)
            if result and result.metadata:
                title = result.metadata.get("title", "")
                if title and title.strip():
                    return title.strip()
        except Exception as e:
            logger.error(f"Error extracting title for {paper_id}: {e}")
        return None
    
    def update_title_in_neo4j(self, paper_id: str, title: str):
        """Update title in Neo4j"""
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                SET p.title = $title, p.updated_at = datetime()
            """, paper_id=paper_id, title=title)
            logger.info(f"Updated title for {paper_id}: {title[:50]}...")
    
    async def process_papers(self, limit: int = None):
        """Process papers without titles"""
        papers = self.find_papers_without_titles()
        
        if limit:
            papers = papers[:limit]
        
        logger.info(f"Found {len(papers)} papers without titles")
        
        updated = 0
        not_found = 0
        failed = 0
        
        for i, paper in enumerate(papers, 1):
            paper_id = paper["paper_id"]
            logger.info(f"[{i}/{len(papers)}] Processing {paper_id}...")
            
            # Find PDF
            pdf_path = self.find_pdf_path(paper_id)
            if not pdf_path or not pdf_path.exists():
                logger.warning(f"  PDF not found for {paper_id}")
                not_found += 1
                continue
            
            # Extract title
            title = await self.extract_title_from_pdf(paper_id, pdf_path)
            if title:
                self.update_title_in_neo4j(paper_id, title)
                updated += 1
            else:
                logger.warning(f"  Could not extract title for {paper_id}")
                failed += 1
        
        logger.info("\n" + "=" * 80)
        logger.info("RE-EXTRACTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total papers processed: {len(papers)}")
        logger.info(f"Titles updated: {updated}")
        logger.info(f"PDFs not found: {not_found}")
        logger.info(f"Extraction failed: {failed}")
    
    def close(self):
        self.driver.close()

async def main():
    import sys
    
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
        print(f"Processing first {limit} papers...")
    
    extractor = TitleReExtractor()
    try:
        await extractor.process_papers(limit=limit)
    finally:
        extractor.close()

if __name__ == "__main__":
    asyncio.run(main())
