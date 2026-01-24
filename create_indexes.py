#!/usr/bin/env python3
"""
Create Database Indexes for Performance
Creates indexes on frequently queried properties
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexCreator:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def create_all_indexes(self):
        """Create all critical indexes"""
        logger.info("=" * 80)
        logger.info("Creating Database Indexes")
        logger.info("=" * 80)
        
        indexes = [
            # Paper indexes
            ("CREATE INDEX paper_id_index IF NOT EXISTS FOR (p:Paper) ON (p.paper_id)", "Paper.paper_id"),
            ("CREATE INDEX paper_year_index IF NOT EXISTS FOR (p:Paper) ON (p.year)", "Paper.year"),
            ("CREATE INDEX paper_title_index IF NOT EXISTS FOR (p:Paper) ON (p.title)", "Paper.title"),
            
            # Theory indexes
            ("CREATE INDEX theory_name_index IF NOT EXISTS FOR (t:Theory) ON (t.name)", "Theory.name"),
            ("CREATE INDEX theory_domain_index IF NOT EXISTS FOR (t:Theory) ON (t.domain)", "Theory.domain"),
            
            # Method indexes
            ("CREATE INDEX method_name_index IF NOT EXISTS FOR (m:Method) ON (m.name)", "Method.name"),
            ("CREATE INDEX method_type_index IF NOT EXISTS FOR (m:Method) ON (m.type)", "Method.type"),
            
            # Phenomenon indexes
            ("CREATE INDEX phenomenon_name_index IF NOT EXISTS FOR (ph:Phenomenon) ON (ph.phenomenon_name)", "Phenomenon.phenomenon_name"),
            ("CREATE INDEX phenomenon_type_index IF NOT EXISTS FOR (ph:Phenomenon) ON (ph.phenomenon_type)", "Phenomenon.phenomenon_type"),
            
            # Author indexes (for when authors are added)
            ("CREATE INDEX author_id_index IF NOT EXISTS FOR (a:Author) ON (a.author_id)", "Author.author_id"),
            ("CREATE INDEX author_name_index IF NOT EXISTS FOR (a:Author) ON (a.full_name)", "Author.full_name"),
            
            # ResearchQuestion indexes
            ("CREATE INDEX research_question_id_index IF NOT EXISTS FOR (q:ResearchQuestion) ON (q.question_id)", "ResearchQuestion.question_id"),
        ]
        
        with self.driver.session() as session:
            created = 0
            failed = 0
            
            for cypher, description in indexes:
                try:
                    result = session.run(cypher)
                    result.consume()  # Consume result
                    logger.info(f"  ✓ Created index: {description}")
                    created += 1
                except Exception as e:
                    # Index might already exist or node type might not exist yet
                    if "already exists" in str(e).lower() or "unknown label" in str(e).lower():
                        logger.info(f"  ⚠️  Skipped (already exists or label missing): {description}")
                    else:
                        logger.warning(f"  ✗ Failed to create {description}: {e}")
                        failed += 1
            
            logger.info(f"\n✓ Created {created} indexes")
            if failed > 0:
                logger.warning(f"⚠️  {failed} indexes failed to create")
            
            # Verify indexes
            result = session.run("SHOW INDEXES")
            indexes_list = list(result)
            logger.info(f"✓ Total indexes in database: {len(indexes_list)}")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    creator = IndexCreator()
    try:
        creator.create_all_indexes()
        logger.info("\n" + "=" * 80)
        logger.info("✓ Index creation complete!")
        logger.info("=" * 80)
    finally:
        creator.close()
