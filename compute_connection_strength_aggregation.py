#!/usr/bin/env python3
"""
Compute Aggregated Connection Strength Across Papers
Phase 2 Fix #1: Strength aggregation for research insights
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionStrengthAggregator:
    """Aggregate connection strength statistics across papers"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50
        )
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def compute_aggregations(self):
        """
        Compute aggregated connection strength statistics
        Creates EXPLAINS_PHENOMENON_AGGREGATED relationships
        """
        logger.info("Computing aggregated connection strength statistics...")
        
        with self.driver.session() as session:
            # Count existing connections
            result = session.run("""
                MATCH ()-[r:EXPLAINS_PHENOMENON]->()
                RETURN count(r) as total_connections
            """).single()
            
            total_connections = result["total_connections"] if result else 0
            logger.info(f"Found {total_connections} EXPLAINS_PHENOMENON relationships")
            
            if total_connections == 0:
                logger.warning("No connections found. Run paper extraction first.")
                return
            
            # Compute aggregations
            logger.info("\nComputing aggregated statistics...")
            result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, ph,
                     avg(r.connection_strength) as avg_strength,
                     count(r) as paper_count,
                     collect(DISTINCT r.paper_id) as paper_ids,
                     max(r.connection_strength) as max_strength,
                     min(r.connection_strength) as min_strength,
                     stDev(r.connection_strength) as std_strength,
                     
                     // Aggregate factor scores
                     avg(r.role_weight) as avg_role_weight,
                     avg(r.section_score) as avg_section_score,
                     avg(r.keyword_score) as avg_keyword_score,
                     avg(r.semantic_score) as avg_semantic_score,
                     avg(r.explicit_bonus) as avg_explicit_bonus,
                     
                     // Collect all unique theory roles
                     collect(DISTINCT r.theory_role) as roles_used,
                     
                     // Collect all unique sections
                     collect(DISTINCT r.section) as sections_used
                
                WHERE paper_count > 0
                
                MERGE (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph)
                SET agg.avg_strength = round(avg_strength, 3),
                    agg.paper_count = paper_count,
                    agg.paper_ids = paper_ids,
                    agg.max_strength = round(max_strength, 3),
                    agg.min_strength = round(min_strength, 3),
                    agg.std_strength = round(coalesce(std_strength, 0), 3),
                    agg.avg_role_weight = round(avg_role_weight, 3),
                    agg.avg_section_score = round(avg_section_score, 3),
                    agg.avg_keyword_score = round(avg_keyword_score, 3),
                    agg.avg_semantic_score = round(avg_semantic_score, 3),
                    agg.avg_explicit_bonus = round(avg_explicit_bonus, 3),
                    agg.roles_used = roles_used,
                    agg.sections_used = sections_used,
                    agg.last_updated = datetime()
                
                RETURN count(agg) as aggregated_count
            """).single()
            
            aggregated_count = result["aggregated_count"] if result else 0
            logger.info(f"✅ Created/updated {aggregated_count} aggregated relationships")
            
            # Show statistics
            logger.info("\n📊 Aggregation Statistics:")
            stats = session.run("""
                MATCH ()-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->()
                WITH 
                    count(agg) as total_aggregated,
                    avg(agg.avg_strength) as overall_avg_strength,
                    avg(agg.paper_count) as avg_papers_per_connection,
                    max(agg.paper_count) as max_papers_per_connection,
                    min(agg.paper_count) as min_papers_per_connection
                RETURN total_aggregated, 
                       round(overall_avg_strength, 3) as overall_avg_strength,
                       round(avg_papers_per_connection, 2) as avg_papers_per_connection,
                       max_papers_per_connection,
                       min_papers_per_connection
            """).single()
            
            if stats:
                logger.info(f"  Total aggregated connections: {stats['total_aggregated']}")
                logger.info(f"  Overall average strength: {stats['overall_avg_strength']}")
                logger.info(f"  Average papers per connection: {stats['avg_papers_per_connection']}")
                logger.info(f"  Max papers per connection: {stats['max_papers_per_connection']}")
                logger.info(f"  Min papers per connection: {stats['min_papers_per_connection']}")
            
            # Show top connections by average strength
            logger.info("\n🏆 Top 10 Connections by Average Strength:")
            top_connections = session.run("""
                MATCH (t:Theory)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                WHERE agg.paper_count >= 2
                RETURN t.name as theory,
                       ph.phenomenon_name as phenomenon,
                       agg.avg_strength as avg_strength,
                       agg.paper_count as paper_count,
                       agg.max_strength as max_strength,
                       agg.min_strength as min_strength
                ORDER BY agg.avg_strength DESC
                LIMIT 10
            """).data()
            
            for i, conn in enumerate(top_connections, 1):
                logger.info(f"  {i}. {conn['theory']} → {conn['phenomenon']}")
                logger.info(f"     Strength: {conn['avg_strength']:.3f} (papers: {conn['paper_count']}, "
                          f"range: {conn['min_strength']:.3f}-{conn['max_strength']:.3f})")
            
            logger.info("\n✅ Aggregation complete!")
    
    def update_aggregations(self):
        """
        Update existing aggregations (can be called after new papers are processed)
        """
        logger.info("Updating aggregated connection strength statistics...")
        self.compute_aggregations()

def main():
    """Main function"""
    aggregator = ConnectionStrengthAggregator()
    try:
        aggregator.compute_aggregations()
    finally:
        aggregator.close()

if __name__ == "__main__":
    main()

