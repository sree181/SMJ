#!/usr/bin/env python3
"""
Post-processing script to compute paper-to-paper relationships.
This script creates relationships based on shared theories, methods, and variables
regardless of theory role (primary, supporting, etc.).
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class PaperRelationshipComputer:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        
        self.stats = {
            "USES_SAME_THEORY": 0,
            "USES_SAME_METHOD": 0,
            "USES_SAME_VARIABLES": 0,
            "TEMPORAL_SEQUENCE": 0
        }
    
    def compute_all_relationships(self):
        """Compute all paper-to-paper relationships."""
        logger.info("=" * 70)
        logger.info("Computing Paper-to-Paper Relationships")
        logger.info("=" * 70)
        
        with self.driver.session() as session:
            # 1. USES_SAME_THEORY: Find papers using same PRIMARY theories (STRICT)
            # Only create relationships if papers share PRIMARY theories
            # Exclude very common theories that appear in most papers (they're not meaningful connections)
            logger.info("\n1. Computing USES_SAME_THEORY relationships...")
            logger.info("   Criteria: Papers must share PRIMARY theories (most restrictive)")
            logger.info("   Note: Supporting theories excluded - too many false positives")
            
            # Common theories that appear in most SMJ papers (exclude from relationships)
            common_theories = [
                "Resource-Based View", "RBV", "Resource-Based View (RBV)",
                "Upper Echelons Theory", "Organizational Learning Theory"
            ]
            
            # First, create relationships for papers sharing PRIMARY theories (excluding common ones)
            result_primary = session.run("""
                MATCH (p1:Paper)-[r1:USES_THEORY {role: "primary"}]->(t:Theory)<-[r2:USES_THEORY {role: "primary"}]-(p2:Paper)
                WHERE p1 <> p2 
                AND p1.paper_id IS NOT NULL 
                AND p2.paper_id IS NOT NULL
                AND NOT t.name IN $common_theories
                AND NOT EXISTS((p1)-[:USES_SAME_THEORY]->(p2))
                WITH p1, p2, collect(DISTINCT t.name) as shared_theories,
                     abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                WHERE size(shared_theories) > 0
                MERGE (p1)-[rel:USES_SAME_THEORY {
                    shared_theories: shared_theories,
                    theory_count: size(shared_theories),
                    temporal_gap: temporal_gap,
                    relationship_type: "primary_theories"
                }]->(p2)
                RETURN count(rel) as count
            """, common_theories=common_theories).single()
            
            primary_count = result_primary["count"] if result_primary else 0
            
            # If no primary relationships, try with common theories included (but still only primary)
            if primary_count == 0:
                logger.info("   No relationships found excluding common theories, trying with all primary theories...")
                result_primary_all = session.run("""
                    MATCH (p1:Paper)-[r1:USES_THEORY {role: "primary"}]->(t:Theory)<-[r2:USES_THEORY {role: "primary"}]-(p2:Paper)
                    WHERE p1 <> p2 
                    AND p1.paper_id IS NOT NULL 
                    AND p2.paper_id IS NOT NULL
                    AND NOT EXISTS((p1)-[:USES_SAME_THEORY]->(p2))
                    WITH p1, p2, collect(DISTINCT t.name) as shared_theories,
                         abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                    WHERE size(shared_theories) > 0
                    MERGE (p1)-[rel:USES_SAME_THEORY {
                        shared_theories: shared_theories,
                        theory_count: size(shared_theories),
                        temporal_gap: temporal_gap,
                        relationship_type: "primary_theories"
                    }]->(p2)
                    RETURN count(rel) as count
                """).single()
                primary_count = result_primary_all["count"] if result_primary_all else 0
            
            supporting_count = 0  # Disabled - too many false positives
            total_count = primary_count
            
            result = {"count": total_count}
            
            if result and result["count"] > 0:
                count = result["count"]
                self.stats["USES_SAME_THEORY"] = count
                logger.info(f"   ✅ Created {count} USES_SAME_THEORY relationships")
                logger.info(f"      - {primary_count} from shared PRIMARY theories")
                logger.info(f"      - {supporting_count} from 2+ shared supporting theories")
            else:
                logger.info("   ⚠️  No USES_SAME_THEORY relationships created")
            
            # 2. USES_SAME_METHOD: Find papers using same methods
            logger.info("\n2. Computing USES_SAME_METHOD relationships...")
            result = session.run("""
                MATCH (p1:Paper)-[:USES_METHOD]->(m:Method)<-[:USES_METHOD]-(p2:Paper)
                WHERE p1 <> p2 
                AND p1.paper_id IS NOT NULL 
                AND p2.paper_id IS NOT NULL
                AND NOT EXISTS((p1)-[:USES_SAME_METHOD]->(p2))
                WITH p1, p2, collect(DISTINCT m.name) as shared_methods,
                     abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                WHERE size(shared_methods) > 0
                MERGE (p1)-[rel:USES_SAME_METHOD {
                    shared_methods: shared_methods,
                    method_count: size(shared_methods),
                    temporal_gap: temporal_gap
                }]->(p2)
                RETURN count(rel) as count
            """).single()
            
            if result:
                count = result["count"]
                self.stats["USES_SAME_METHOD"] = count
                logger.info(f"   ✅ Created {count} USES_SAME_METHOD relationships")
            else:
                logger.info("   ⚠️  No USES_SAME_METHOD relationships created")
            
            # 3. USES_SAME_VARIABLES: Find papers using 2+ shared variables
            logger.info("\n3. Computing USES_SAME_VARIABLES relationships...")
            result = session.run("""
                MATCH (p1:Paper)-[:USES_VARIABLE]->(v:Variable)<-[:USES_VARIABLE]-(p2:Paper)
                WHERE p1 <> p2 
                AND p1.paper_id IS NOT NULL 
                AND p2.paper_id IS NOT NULL
                AND NOT EXISTS((p1)-[:USES_SAME_VARIABLES]->(p2))
                WITH p1, p2, collect(DISTINCT v.variable_name) as shared_vars,
                     abs(coalesce(p1.publication_year, 0) - coalesce(p2.publication_year, 0)) as temporal_gap
                WHERE size(shared_vars) >= 2
                MERGE (p1)-[rel:USES_SAME_VARIABLES {
                    shared_variables: shared_vars,
                    variable_count: size(shared_vars),
                    temporal_gap: temporal_gap
                }]->(p2)
                RETURN count(rel) as count
            """).single()
            
            if result:
                count = result["count"]
                self.stats["USES_SAME_VARIABLES"] = count
                logger.info(f"   ✅ Created {count} USES_SAME_VARIABLES relationships")
            else:
                logger.info("   ⚠️  No USES_SAME_VARIABLES relationships created")
            
            # 4. TEMPORAL_SEQUENCE: Papers published in consecutive years
            logger.info("\n4. Computing TEMPORAL_SEQUENCE relationships...")
            result = session.run("""
                MATCH (p1:Paper), (p2:Paper)
                WHERE p1 <> p2 
                AND p1.paper_id IS NOT NULL 
                AND p2.paper_id IS NOT NULL
                AND p1.publication_year IS NOT NULL 
                AND p2.publication_year IS NOT NULL
                AND abs(p1.publication_year - p2.publication_year) = 1
                AND NOT EXISTS((p1)-[:TEMPORAL_SEQUENCE]->(p2))
                WITH p1, p2, 
                     CASE WHEN p1.publication_year < p2.publication_year 
                          THEN p1.publication_year 
                          ELSE p2.publication_year 
                     END as earlier_year,
                     CASE WHEN p1.publication_year < p2.publication_year 
                          THEN p2.publication_year 
                          ELSE p1.publication_year 
                     END as later_year
                MERGE (p1)-[rel:TEMPORAL_SEQUENCE {
                    earlier_year: earlier_year,
                    later_year: later_year,
                    sequence_type: CASE WHEN p1.publication_year < p2.publication_year 
                                         THEN 'precedes' 
                                         ELSE 'follows' 
                                    END
                }]->(p2)
                RETURN count(rel) as count
            """).single()
            
            if result:
                count = result["count"]
                self.stats["TEMPORAL_SEQUENCE"] = count
                logger.info(f"   ✅ Created {count} TEMPORAL_SEQUENCE relationships")
            else:
                logger.info("   ⚠️  No TEMPORAL_SEQUENCE relationships created")
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("Relationship Computation Summary")
        logger.info("=" * 70)
        total = sum(self.stats.values())
        logger.info(f"Total relationships created: {total}")
        for rel_type, count in self.stats.items():
            logger.info(f"  {rel_type}: {count}")
        logger.info("=" * 70)
        
        return self.stats
    
    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

if __name__ == "__main__":
    computer = PaperRelationshipComputer()
    try:
        computer.compute_all_relationships()
    finally:
        computer.close()

