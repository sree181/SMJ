#!/usr/bin/env python3
"""
Temporal Evolution System
Captures field evolution across 5-year periods (2020-2024, 2015-2019, etc.)
Enables analysis of how theories, methods, and research questions evolve over time
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemporalEvolutionSystem:
    """System for capturing and analyzing temporal evolution of research field"""
    
    def __init__(self):
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_uri or not neo4j_password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50
        )
        
        # Define time periods (5-year buckets)
        self.time_periods = [
            (2020, 2024, "2020-2024"),
            (2015, 2019, "2015-2019"),
            (2010, 2014, "2010-2014"),
            (2005, 2009, "2005-2009"),
            (2000, 2004, "2000-2004"),
            (1995, 1999, "1995-1999"),
            (1990, 1994, "1990-1994"),
            (1985, 1989, "1985-1989")
        ]
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def create_time_period_nodes(self):
        """Create TimePeriod nodes for each 5-year bucket"""
        logger.info("Creating time period nodes...")
        
        with self.driver.session() as session:
            for start_year, end_year, period_name in self.time_periods:
                session.run("""
                    MERGE (tp:TimePeriod {period_name: $period_name})
                    SET tp.start_year = $start_year,
                        tp.end_year = $end_year,
                        tp.duration_years = $end_year - $start_year + 1,
                        tp.created_at = datetime()
                """,
                period_name=period_name,
                start_year=start_year,
                end_year=end_year)
            
            logger.info(f"✅ Created {len(self.time_periods)} time period nodes")
    
    def link_papers_to_time_periods(self):
        """Link papers to their time period nodes"""
        logger.info("Linking papers to time periods...")
        
        with self.driver.session() as session:
            for start_year, end_year, period_name in self.time_periods:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.publication_year >= $start_year 
                      AND p.publication_year <= $end_year
                    MATCH (tp:TimePeriod {period_name: $period_name})
                    MERGE (p)-[r:BELONGS_TO_PERIOD {
                        period_name: $period_name,
                        year: p.publication_year
                    }]->(tp)
                    RETURN count(r) as count
                """,
                start_year=start_year,
                end_year=end_year,
                period_name=period_name).single()
                
                if result:
                    logger.info(f"  Linked {result['count']} papers to {period_name}")
        
        logger.info("✅ Paper-time period links created")
    
    def compute_temporal_entity_usage(self):
        """
        Compute entity usage statistics per time period
        Creates aggregated statistics for theories, methods, etc. per period
        """
        logger.info("Computing temporal entity usage statistics...")
        
        with self.driver.session() as session:
            # Theory usage over time
            logger.info("  Computing theory usage over time...")
            session.run("""
                MATCH (tp:TimePeriod)
                MATCH (p:Paper)-[:BELONGS_TO_PERIOD]->(tp)
                MATCH (p)-[:USES_THEORY]->(t:Theory)
                WITH tp, t, count(DISTINCT p) as paper_count
                MERGE (tp)-[r:HAS_THEORY_USAGE {
                    theory_name: t.name,
                    paper_count: paper_count,
                    usage_frequency: paper_count
                }]->(t)
                SET r.updated_at = datetime()
            """)
            
            # Method usage over time
            logger.info("  Computing method usage over time...")
            session.run("""
                MATCH (tp:TimePeriod)
                MATCH (p:Paper)-[:BELONGS_TO_PERIOD]->(tp)
                MATCH (p)-[:USES_METHOD]->(m:Method)
                WITH tp, m, count(DISTINCT p) as paper_count
                MERGE (tp)-[r:HAS_METHOD_USAGE {
                    method_name: m.name,
                    paper_count: paper_count,
                    usage_frequency: paper_count
                }]->(m)
                SET r.updated_at = datetime()
            """)
            
            # Research question frequency over time
            logger.info("  Computing research question frequency over time...")
            session.run("""
                MATCH (tp:TimePeriod)
                MATCH (p:Paper)-[:BELONGS_TO_PERIOD]->(tp)
                MATCH (p)-[:ADDRESSES]->(rq:ResearchQuestion)
                WITH tp, rq, count(DISTINCT p) as paper_count
                MERGE (tp)-[r:HAS_RESEARCH_QUESTION_USAGE {
                    question_id: rq.question_id,
                    paper_count: paper_count,
                    usage_frequency: paper_count
                }]->(rq)
                SET r.updated_at = datetime()
            """)
            
            logger.info("✅ Temporal entity usage statistics computed")
    
    def create_evolution_relationships(self):
        """
        Create evolution relationships between time periods
        Tracks how entities evolve from one period to the next
        """
        logger.info("Creating evolution relationships between time periods...")
        
        with self.driver.session() as session:
            # Theory evolution between periods
            logger.info("  Creating theory evolution relationships...")
            session.run("""
                MATCH (tp1:TimePeriod)-[r1:HAS_THEORY_USAGE]->(t:Theory)<-[r2:HAS_THEORY_USAGE]-(tp2:TimePeriod)
                WHERE tp1.start_year < tp2.start_year
                  AND tp2.start_year - tp1.end_year <= 1
                  AND r1.paper_count > 0 
                  AND r2.paper_count > 0
                WITH tp1, tp2, t, r1.paper_count as count1, r2.paper_count as count2
                MERGE (tp1)-[evol:EVOLVES_TO {
                    entity_type: 'theory',
                    entity_name: t.name,
                    period1_count: count1,
                    period2_count: count2,
                    change: count2 - count1,
                    change_percentage: ((count2 - count1) / count1 * 100.0),
                    evolution_type: CASE 
                        WHEN count2 > count1 * 1.2 THEN 'increasing'
                        WHEN count2 < count1 * 0.8 THEN 'decreasing'
                        ELSE 'stable'
                    END
                }]->(tp2)
            """)
            
            # Method evolution between periods
            logger.info("  Creating method evolution relationships...")
            session.run("""
                MATCH (tp1:TimePeriod)-[r1:HAS_METHOD_USAGE]->(m:Method)<-[r2:HAS_METHOD_USAGE]-(tp2:TimePeriod)
                WHERE tp1.start_year < tp2.start_year
                  AND tp2.start_year - tp1.end_year <= 1
                  AND r1.paper_count > 0 
                  AND r2.paper_count > 0
                WITH tp1, tp2, m, r1.paper_count as count1, r2.paper_count as count2
                MERGE (tp1)-[evol:EVOLVES_TO {
                    entity_type: 'method',
                    entity_name: m.name,
                    period1_count: count1,
                    period2_count: count2,
                    change: count2 - count1,
                    change_percentage: ((count2 - count1) / count1 * 100.0),
                    evolution_type: CASE 
                        WHEN count2 > count1 * 1.2 THEN 'increasing'
                        WHEN count2 < count1 * 0.8 THEN 'decreasing'
                        ELSE 'stable'
                    END
                }]->(tp2)
            """)
            
            logger.info("✅ Evolution relationships created")
    
    def create_temporal_trends(self):
        """
        Create temporal trend nodes that aggregate patterns across periods
        """
        logger.info("Creating temporal trend analysis...")
        
        with self.driver.session() as session:
            # Identify emerging theories (increasing usage)
            logger.info("  Identifying emerging theories...")
            session.run("""
                MATCH (tp1:TimePeriod)-[evol:EVOLVES_TO]->(tp2:TimePeriod)
                WHERE evol.entity_type = 'theory'
                  AND evol.evolution_type = 'increasing'
                  AND evol.change_percentage > 50
                WITH evol.entity_name as theory_name, 
                     collect({
                         period1: tp1.period_name,
                         period2: tp2.period_name,
                         change: evol.change_percentage
                     }) as trends
                WHERE size(trends) >= 2
                MERGE (tt:TemporalTrend {
                    entity_type: 'theory',
                    entity_name: theory_name,
                    trend_type: 'emerging'
                })
                SET tt.trends = trends,
                    tt.total_increase = reduce(sum = 0, t in trends | sum + t.change),
                    tt.created_at = datetime()
            """)
            
            # Identify declining theories
            logger.info("  Identifying declining theories...")
            session.run("""
                MATCH (tp1:TimePeriod)-[evol:EVOLVES_TO]->(tp2:TimePeriod)
                WHERE evol.entity_type = 'theory'
                  AND evol.evolution_type = 'decreasing'
                  AND evol.change_percentage < -30
                WITH evol.entity_name as theory_name,
                     collect({
                         period1: tp1.period_name,
                         period2: tp2.period_name,
                         change: evol.change_percentage
                     }) as trends
                WHERE size(trends) >= 2
                MERGE (tt:TemporalTrend {
                    entity_type: 'theory',
                    entity_name: theory_name,
                    trend_type: 'declining'
                })
                SET tt.trends = trends,
                    tt.total_decrease = reduce(sum = 0, t in trends | sum + abs(t.change)),
                    tt.created_at = datetime()
            """)
            
            logger.info("✅ Temporal trends created")
    
    def add_temporal_properties_to_relationships(self):
        """
        Add temporal properties to existing relationships
        Enables time-based filtering and analysis
        """
        logger.info("Adding temporal properties to relationships...")
        
        with self.driver.session() as session:
            # Add year to USES_THEORY relationships
            session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE p.publication_year IS NOT NULL
                  AND r.year IS NULL
                SET r.year = p.publication_year,
                    r.period = CASE
                        WHEN p.publication_year >= 2020 AND p.publication_year <= 2024 THEN '2020-2024'
                        WHEN p.publication_year >= 2015 AND p.publication_year <= 2019 THEN '2015-2019'
                        WHEN p.publication_year >= 2010 AND p.publication_year <= 2014 THEN '2010-2014'
                        WHEN p.publication_year >= 2005 AND p.publication_year <= 2009 THEN '2005-2009'
                        WHEN p.publication_year >= 2000 AND p.publication_year <= 2004 THEN '2000-2004'
                        ELSE 'other'
                    END
            """)
            
            # Add year to USES_METHOD relationships
            session.run("""
                MATCH (p:Paper)-[r:USES_METHOD]->(m:Method)
                WHERE p.publication_year IS NOT NULL
                  AND r.year IS NULL
                SET r.year = p.publication_year,
                    r.period = CASE
                        WHEN p.publication_year >= 2020 AND p.publication_year <= 2024 THEN '2020-2024'
                        WHEN p.publication_year >= 2015 AND p.publication_year <= 2019 THEN '2015-2019'
                        WHEN p.publication_year >= 2010 AND p.publication_year <= 2014 THEN '2010-2014'
                        WHEN p.publication_year >= 2005 AND p.publication_year <= 2009 THEN '2005-2009'
                        WHEN p.publication_year >= 2000 AND p.publication_year <= 2004 THEN '2000-2004'
                        ELSE 'other'
                    END
            """)
            
            logger.info("✅ Temporal properties added to relationships")
    
    def setup_complete(self):
        """Run complete temporal evolution setup"""
        logger.info("=" * 70)
        logger.info("TEMPORAL EVOLUTION SYSTEM SETUP")
        logger.info("=" * 70)
        
        # Step 1: Create time period nodes
        self.create_time_period_nodes()
        
        # Step 2: Link papers to time periods
        self.link_papers_to_time_periods()
        
        # Step 3: Add temporal properties to relationships
        self.add_temporal_properties_to_relationships()
        
        # Step 4: Compute entity usage per period
        self.compute_temporal_entity_usage()
        
        # Step 5: Create evolution relationships
        self.create_evolution_relationships()
        
        # Step 6: Create temporal trends
        self.create_temporal_trends()
        
        logger.info("=" * 70)
        logger.info("✅ TEMPORAL EVOLUTION SYSTEM SETUP COMPLETE")
        logger.info("=" * 70)
    
    def analyze_temporal_evolution(self, entity_type: str, entity_name: str) -> Dict[str, Any]:
        """
        Analyze temporal evolution of a specific entity
        
        Args:
            entity_type: "theory", "method", "research_question"
            entity_name: Name of the entity
        
        Returns:
            Evolution analysis with trends across periods
        """
        with self.driver.session() as session:
            if entity_type == "theory":
                result = session.run("""
                    MATCH (tp:TimePeriod)-[r:HAS_THEORY_USAGE]->(t:Theory {name: $entity_name})
                    RETURN tp.period_name as period,
                           tp.start_year as start_year,
                           tp.end_year as end_year,
                           r.paper_count as paper_count,
                           r.usage_frequency as frequency
                    ORDER BY tp.start_year
                """, entity_name=entity_name)
            elif entity_type == "method":
                result = session.run("""
                    MATCH (tp:TimePeriod)-[r:HAS_METHOD_USAGE]->(m:Method {name: $entity_name})
                    RETURN tp.period_name as period,
                           tp.start_year as start_year,
                           tp.end_year as end_year,
                           r.paper_count as paper_count,
                           r.usage_frequency as frequency
                    ORDER BY tp.start_year
                """, entity_name=entity_name)
            else:
                return {}
            
            periods = []
            for record in result:
                periods.append({
                    'period': record['period'],
                    'start_year': record['start_year'],
                    'end_year': record['end_year'],
                    'paper_count': record['paper_count'],
                    'frequency': record['frequency']
                })
            
            # Calculate trends
            trends = []
            for i in range(len(periods) - 1):
                p1 = periods[i]
                p2 = periods[i + 1]
                change = p2['paper_count'] - p1['paper_count']
                change_pct = (change / p1['paper_count'] * 100) if p1['paper_count'] > 0 else 0
                trends.append({
                    'from_period': p1['period'],
                    'to_period': p2['period'],
                    'change': change,
                    'change_percentage': change_pct,
                    'trend': 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable'
                })
            
            return {
                'entity_type': entity_type,
                'entity_name': entity_name,
                'periods': periods,
                'trends': trends,
                'total_papers': sum(p['paper_count'] for p in periods),
                'peak_period': max(periods, key=lambda x: x['paper_count'])['period'] if periods else None
            }

if __name__ == "__main__":
    system = TemporalEvolutionSystem()
    try:
        system.setup_complete()
    finally:
        system.close()

