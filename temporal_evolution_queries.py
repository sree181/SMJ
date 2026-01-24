#!/usr/bin/env python3
"""
Temporal Evolution Queries
Example queries for analyzing field evolution across time periods
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class TemporalEvolutionQueries:
    """Example queries for temporal evolution analysis"""
    
    def __init__(self):
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
    
    def close(self):
        self.driver.close()
    
    def query_theory_evolution(self, theory_name: str):
        """
        Query: How has a theory's usage evolved across time periods?
        
        Example: "How has Resource-Based View usage changed from 2020-2024 vs 2015-2019?"
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tp:TimePeriod)-[r:HAS_THEORY_USAGE]->(t:Theory {name: $theory_name})
                RETURN tp.period_name as period,
                       tp.start_year as start_year,
                       tp.end_year as end_year,
                       r.paper_count as paper_count,
                       r.usage_frequency as frequency
                ORDER BY tp.start_year DESC
            """, theory_name=theory_name)
            
            print(f"\nTheory Evolution: {theory_name}")
            print("=" * 70)
            for record in result:
                print(f"{record['period']} ({record['start_year']}-{record['end_year']}): "
                      f"{record['paper_count']} papers")
    
    def query_method_evolution(self, method_name: str):
        """
        Query: How has a method's usage evolved across time periods?
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tp:TimePeriod)-[r:HAS_METHOD_USAGE]->(m:Method {name: $method_name})
                RETURN tp.period_name as period,
                       tp.start_year as start_year,
                       tp.end_year as end_year,
                       r.paper_count as paper_count
                ORDER BY tp.start_year DESC
            """, method_name=method_name)
            
            print(f"\nMethod Evolution: {method_name}")
            print("=" * 70)
            for record in result:
                print(f"{record['period']} ({record['start_year']}-{record['end_year']}): "
                      f"{record['paper_count']} papers")
    
    def query_emerging_theories(self, period: str = "2020-2024"):
        """
        Query: What theories are emerging (increasing usage) in a period?
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tp1:TimePeriod {period_name: $period})-[evol:EVOLVES_TO]->(tp2:TimePeriod)
                WHERE evol.entity_type = 'theory'
                  AND evol.evolution_type = 'increasing'
                  AND evol.change_percentage > 50
                RETURN evol.entity_name as theory_name,
                       evol.period1_count as previous_count,
                       evol.period2_count as current_count,
                       evol.change_percentage as change_pct
                ORDER BY evol.change_percentage DESC
                LIMIT 10
            """, period=period)
            
            print(f"\nEmerging Theories in {period}")
            print("=" * 70)
            for record in result:
                print(f"{record['theory_name']}: "
                      f"{record['previous_count']} → {record['current_count']} "
                      f"(+{record['change_pct']:.1f}%)")
    
    def query_declining_theories(self, period: str = "2020-2024"):
        """
        Query: What theories are declining (decreasing usage) in a period?
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tp1:TimePeriod {period_name: $period})-[evol:EVOLVES_TO]->(tp2:TimePeriod)
                WHERE evol.entity_type = 'theory'
                  AND evol.evolution_type = 'decreasing'
                  AND evol.change_percentage < -30
                RETURN evol.entity_name as theory_name,
                       evol.period1_count as previous_count,
                       evol.period2_count as current_count,
                       evol.change_percentage as change_pct
                ORDER BY evol.change_percentage ASC
                LIMIT 10
            """, period=period)
            
            print(f"\nDeclining Theories in {period}")
            print("=" * 70)
            for record in result:
                print(f"{record['theory_name']}: "
                      f"{record['previous_count']} → {record['current_count']} "
                      f"({record['change_pct']:.1f}%)")
    
    def query_period_comparison(self, period1: str, period2: str, entity_type: str = "theory"):
        """
        Query: Compare entity usage between two periods
        
        Example: "Compare theory usage in 2020-2024 vs 2015-2019"
        """
        with self.driver.session() as session:
            if entity_type == "theory":
                result = session.run("""
                    MATCH (tp1:TimePeriod {period_name: $period1})-[r1:HAS_THEORY_USAGE]->(t:Theory)
                    MATCH (tp2:TimePeriod {period_name: $period2})-[r2:HAS_THEORY_USAGE]->(t)
                    RETURN t.name as theory_name,
                           r1.paper_count as period1_count,
                           r2.paper_count as period2_count,
                           r2.paper_count - r1.paper_count as change,
                           ((r2.paper_count - r1.paper_count) / r1.paper_count * 100.0) as change_pct
                    ORDER BY abs(r2.paper_count - r1.paper_count) DESC
                    LIMIT 20
                """, period1=period1, period2=period2)
            else:
                result = session.run("""
                    MATCH (tp1:TimePeriod {period_name: $period1})-[r1:HAS_METHOD_USAGE]->(m:Method)
                    MATCH (tp2:TimePeriod {period_name: $period2})-[r2:HAS_METHOD_USAGE]->(m)
                    RETURN m.name as method_name,
                           r1.paper_count as period1_count,
                           r2.paper_count as period2_count,
                           r2.paper_count - r1.paper_count as change,
                           ((r2.paper_count - r1.paper_count) / r1.paper_count * 100.0) as change_pct
                    ORDER BY abs(r2.paper_count - r1.paper_count) DESC
                    LIMIT 20
                """, period1=period1, period2=period2)
            
            print(f"\n{entity_type.title()} Comparison: {period1} vs {period2}")
            print("=" * 70)
            for record in result:
                name = record.get('theory_name') or record.get('method_name')
                print(f"{name}: "
                      f"{record['period1_count']} → {record['period2_count']} "
                      f"({record['change']:+d}, {record['change_pct']:+.1f}%)")
    
    def query_temporal_trends(self, trend_type: str = "emerging"):
        """
        Query: What are the overall temporal trends?
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tt:TemporalTrend {trend_type: $trend_type})
                WHERE tt.entity_type = 'theory'
                RETURN tt.entity_name as entity_name,
                       tt.total_increase as total_change,
                       size(tt.trends) as trend_count
                ORDER BY tt.total_increase DESC
                LIMIT 10
            """, trend_type=trend_type)
            
            print(f"\n{trend_type.title()} Trends")
            print("=" * 70)
            for record in result:
                print(f"{record['entity_name']}: "
                      f"{record['total_change']:.1f}% increase across {record['trend_count']} periods")
    
    def query_method_theory_coevolution(self, period1: str, period2: str):
        """
        Query: How do method-theory combinations evolve?
        Example: "How has OLS + RBV usage changed over time?"
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p1:Paper)-[:BELONGS_TO_PERIOD]->(tp1:TimePeriod {period_name: $period1})
                MATCH (p1)-[:USES_THEORY {role: 'primary'}]->(t:Theory)
                MATCH (p1)-[:USES_METHOD]->(m:Method)
                
                MATCH (p2:Paper)-[:BELONGS_TO_PERIOD]->(tp2:TimePeriod {period_name: $period2})
                MATCH (p2)-[:USES_THEORY {role: 'primary'}]->(t)
                MATCH (p2)-[:USES_METHOD]->(m)
                
                WITH t.name as theory_name, m.name as method_name,
                     count(DISTINCT p1) as period1_count,
                     count(DISTINCT p2) as period2_count
                WHERE period1_count > 0 OR period2_count > 0
                RETURN theory_name, method_name, period1_count, period2_count,
                       period2_count - period1_count as change
                ORDER BY abs(period2_count - period1_count) DESC
                LIMIT 20
            """, period1=period1, period2=period2)
            
            print(f"\nMethod-Theory Co-evolution: {period1} vs {period2}")
            print("=" * 70)
            for record in result:
                print(f"{record['theory_name']} + {record['method_name']}: "
                      f"{record['period1_count']} → {record['period2_count']} "
                      f"({record['change']:+d})")

if __name__ == "__main__":
    queries = TemporalEvolutionQueries()
    try:
        # Example queries
        queries.query_theory_evolution("Resource-Based View")
        queries.query_emerging_theories("2020-2024")
        queries.query_period_comparison("2020-2024", "2015-2019", "theory")
    finally:
        queries.close()

