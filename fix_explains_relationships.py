#!/usr/bin/env python3
"""
Fix EXPLAINS_PHENOMENON Relationships
Creates Theory-Phenomenon EXPLAINS relationships based on Paper connections
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplainsRelationshipFixer:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def create_explains_relationships(self):
        """Create EXPLAINS_PHENOMENON relationships from Paper-Theory-Phenomenon paths"""
        logger.info("=" * 80)
        logger.info("Creating EXPLAINS_PHENOMENON Relationships")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            # First, get all Theory-Phenomenon pairs from papers
            logger.info("Step 1: Finding Theory-Phenomenon pairs from papers...")
            result = session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory),
                      (p)-[r2:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WITH t, ph, 
                     collect(DISTINCT p.paper_id) as paper_ids,
                     count(DISTINCT p) as paper_count,
                     collect(DISTINCT {
                         paper_id: p.paper_id,
                         theory_role: r.role,
                         context: r2.context
                     }) as connections
                WHERE paper_count > 0
                RETURN t.name as theory_name,
                       ph.phenomenon_name as phenomenon_name,
                       paper_ids,
                       paper_count,
                       connections
                ORDER BY paper_count DESC
            """)
            
            theory_phenomenon_pairs = []
            for record in result:
                theory_phenomenon_pairs.append({
                    'theory_name': record['theory_name'],
                    'phenomenon_name': record['phenomenon_name'],
                    'paper_ids': record['paper_ids'],
                    'paper_count': record['paper_count'],
                    'connections': record['connections']
                })
            
            logger.info(f"Found {len(theory_phenomenon_pairs)} Theory-Phenomenon pairs")
            
            # Calculate connection strength for each pair
            logger.info("Step 2: Calculating connection strengths...")
            created = 0
            updated = 0
            
            for pair in theory_phenomenon_pairs:
                theory_name = pair['theory_name']
                phenomenon_name = pair['phenomenon_name']
                paper_count = pair['paper_count']
                paper_ids = pair['paper_ids']
                
                # Calculate connection strength
                # Base strength on paper count and role distribution
                connections = pair['connections']
                primary_count = sum(1 for c in connections if c.get('theory_role') == 'primary')
                supporting_count = sum(1 for c in connections if c.get('theory_role') == 'supporting')
                
                # Connection strength formula
                base_strength = min(1.0, paper_count / 10.0)  # Normalize to 0-1
                role_bonus = (primary_count * 0.2) / max(paper_count, 1)  # Primary theories get bonus
                strength = min(1.0, base_strength + role_bonus)
                
                # Create or update EXPLAINS_PHENOMENON relationship
                result = session.run("""
                    MATCH (t:Theory {name: $theory_name})
                    MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                    MERGE (t)-[r:EXPLAINS_PHENOMENON]->(ph)
                    ON CREATE SET 
                        r.connection_strength = $strength,
                        r.paper_count = $paper_count,
                        r.paper_ids = $paper_ids,
                        r.evidence_count = $paper_count,
                        r.created_at = datetime()
                    ON MATCH SET
                        r.connection_strength = $strength,
                        r.paper_count = $paper_count,
                        r.paper_ids = $paper_ids,
                        r.evidence_count = $paper_count,
                        r.updated_at = datetime()
                    RETURN r
                """, 
                theory_name=theory_name,
                phenomenon_name=phenomenon_name,
                strength=strength,
                paper_count=paper_count,
                paper_ids=paper_ids)
                
                if result.peek():
                    created += 1
                    if created % 100 == 0:
                        logger.info(f"  Created/updated {created} relationships...")
            
            logger.info(f"✓ Created/updated {created} EXPLAINS_PHENOMENON relationships")
            
            # Verify
            result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                RETURN count(r) as total
            """)
            total = result.single()['total']
            logger.info(f"✓ Total EXPLAINS_PHENOMENON relationships: {total}")
            
            return total
    
    def create_aggregated_relationships(self):
        """Create aggregated EXPLAINS_PHENOMENON_AGGREGATED relationships"""
        logger.info("\n" + "=" * 80)
        logger.info("Creating Aggregated Relationships")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, ph,
                     collect(r) as relationships,
                     avg(r.connection_strength) as avg_strength,
                     sum(r.paper_count) as total_papers,
                     collect(DISTINCT r.paper_ids) as all_paper_ids
                
                UNWIND all_paper_ids as paper_id_list
                UNWIND paper_id_list as paper_id
                WITH t, ph, relationships, avg_strength, total_papers,
                     collect(DISTINCT paper_id) as unique_paper_ids
                
                MERGE (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph)
                SET agg.avg_strength = avg_strength,
                    agg.paper_count = total_papers,
                    agg.paper_ids = unique_paper_ids,
                    agg.updated_at = datetime()
                RETURN count(agg) as created
            """)
            
            created = result.single()['created']
            logger.info(f"✓ Created {created} aggregated relationships")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    fixer = ExplainsRelationshipFixer()
    try:
        total = fixer.create_explains_relationships()
        fixer.create_aggregated_relationships()
        logger.info("\n" + "=" * 80)
        logger.info("✓ Fix complete!")
        logger.info("=" * 80)
    finally:
        fixer.close()
