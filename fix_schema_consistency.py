#!/usr/bin/env python3
"""
Fix Schema Consistency Issues
Standardizes year field usage across the database
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaConsistencyFixer:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def standardize_year_field(self):
        """Standardize on 'year' field - copy publication_year to year if needed"""
        logger.info("=" * 80)
        logger.info("Standardizing Year Field")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            # Check current state
            result = session.run('''
                MATCH (p:Paper)
                WHERE p.year IS NULL AND p.publication_year IS NOT NULL
                RETURN count(p) as count
            ''')
            papers_to_fix = result.single()['count']
            logger.info(f"Papers with publication_year but no year: {papers_to_fix}")
            
            if papers_to_fix > 0:
                # Copy publication_year to year
                result = session.run('''
                    MATCH (p:Paper)
                    WHERE p.year IS NULL AND p.publication_year IS NOT NULL
                    SET p.year = p.publication_year
                    RETURN count(p) as updated
                ''')
                updated = result.single()['updated']
                logger.info(f"✓ Updated {updated} papers: copied publication_year to year")
            
            # Check for papers with both fields (keep year, remove publication_year)
            result = session.run('''
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL AND p.publication_year IS NOT NULL
                RETURN count(p) as count
            ''')
            papers_both = result.single()['count']
            logger.info(f"Papers with both year and publication_year: {papers_both}")
            
            if papers_both > 0:
                # Remove publication_year if year exists and matches
                result = session.run('''
                    MATCH (p:Paper)
                    WHERE p.year IS NOT NULL AND p.publication_year IS NOT NULL
                      AND p.year = p.publication_year
                    REMOVE p.publication_year
                    RETURN count(p) as removed
                ''')
                removed = result.single()['removed']
                logger.info(f"✓ Removed redundant publication_year from {removed} papers")
            
            # Final check
            result = session.run('''
                MATCH (p:Paper)
                WHERE p.year IS NULL
                RETURN count(p) as count
            ''')
            papers_no_year = result.single()['count']
            logger.info(f"Papers still missing year: {papers_no_year}")
    
    def ensure_relationship_properties(self):
        """Ensure all relationships have required properties"""
        logger.info("\n" + "=" * 80)
        logger.info("Ensuring Relationship Properties")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            # Fix USES_THEORY relationships missing 'role'
            result = session.run('''
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE r.role IS NULL
                SET r.role = 'supporting'
                RETURN count(r) as updated
            ''')
            updated = result.single()['updated']
            if updated > 0:
                logger.info(f"✓ Set default 'role' for {updated} USES_THEORY relationships")
            
            # Ensure EXPLAINS_PHENOMENON has required properties
            result = session.run('''
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WHERE r.connection_strength IS NULL
                SET r.connection_strength = 0.5
                RETURN count(r) as updated
            ''')
            updated = result.single()['updated']
            if updated > 0:
                logger.info(f"✓ Set default 'connection_strength' for {updated} EXPLAINS_PHENOMENON relationships")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    fixer = SchemaConsistencyFixer()
    try:
        fixer.standardize_year_field()
        fixer.ensure_relationship_properties()
        logger.info("\n" + "=" * 80)
        logger.info("✓ Schema consistency fix complete!")
        logger.info("=" * 80)
    finally:
        fixer.close()
