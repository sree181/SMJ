#!/usr/bin/env python3
"""
Test Complex Queries - Demonstrating Enhanced Graph Capabilities
Tests all new features: indexes, embeddings, entity-to-entity relationships, semantic relationships
"""

import os
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ComplexQueryTester:
    """Test complex queries demonstrating enhanced graph capabilities"""
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        
        # Initialize embedding model for similarity queries
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded\n")
    
    def close(self):
        self.driver.close()
    
    def print_section(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")
    
    def print_result(self, description: str, result: List[Dict], max_rows: int = 5):
        """Print query result in formatted way"""
        print(f"📊 {description}")
        if not result:
            print("   ⚠️  No results found\n")
            return
        
        print(f"   Found {len(result)} result(s)\n")
        for i, row in enumerate(result[:max_rows], 1):
            print(f"   {i}. {row}")
        if len(result) > max_rows:
            print(f"   ... and {len(result) - max_rows} more\n")
        else:
            print()
    
    def test_1_indexed_queries(self):
        """Test 1: Fast Indexed Queries"""
        self.print_section("TEST 1: Fast Indexed Queries (Using Indexes)")
        
        with self.driver.session() as session:
            # Query 1.1: Find papers by year (using index)
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.year >= 2020 AND p.year <= 2024
                RETURN p.paper_id, p.title, p.year
                ORDER BY p.year DESC
                LIMIT 10
            """).data()
            self.print_result("Papers from 2020-2024 (using year index)", result)
            
            # Query 1.2: Find papers by type (using index)
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_type = 'empirical_quantitative'
                RETURN p.paper_id, p.title, p.paper_type
                LIMIT 10
            """).data()
            self.print_result("Empirical quantitative papers (using type index)", result)
            
            # Query 1.3: Find theory by name (using unique constraint)
            result = session.run("""
                MATCH (t:Theory {name: "Resource-Based View"})
                RETURN t.name, t.domain, t.description
            """).data()
            self.print_result("Resource-Based View theory (using unique constraint)", result)
    
    def test_2_fulltext_search(self):
        """Test 2: Full-Text Search"""
        self.print_section("TEST 2: Full-Text Search (Title & Abstract)")
        
        with self.driver.session() as session:
            # Query 2.1: Search for "strategic management" in titles/abstracts
            result = session.run("""
                CALL db.index.fulltext.queryNodes('paper_text_index', 'strategic management', {limit: 5})
                YIELD node, score
                RETURN node.paper_id as paper_id, 
                       node.title as title, 
                       substring(node.abstract, 0, 100) as abstract_preview,
                       score
                ORDER BY score DESC
            """).data()
            self.print_result("Full-text search: 'strategic management'", result)
            
            # Query 2.2: Search for "organizational learning"
            result = session.run("""
                CALL db.index.fulltext.queryNodes('paper_text_index', 'organizational learning', {limit: 5})
                YIELD node, score
                RETURN node.paper_id as paper_id, 
                       node.title as title, 
                       score
                ORDER BY score DESC
            """).data()
            self.print_result("Full-text search: 'organizational learning'", result)
    
    def test_3_entity_to_entity_relationships(self):
        """Test 3: Entity-to-Entity Relationships"""
        self.print_section("TEST 3: Entity-to-Entity Relationships")
        
        with self.driver.session() as session:
            # Query 3.1: Theory co-occurrence
            result = session.run("""
                MATCH (t1:Theory)-[r:OFTEN_USED_WITH]->(t2:Theory)
                RETURN t1.name as theory1, 
                       t2.name as theory2, 
                       r.frequency as frequency,
                       r.relationship_type as type
                ORDER BY r.frequency DESC
                LIMIT 10
            """).data()
            self.print_result("Theory co-occurrence (theories used together)", result)
            
            # Query 3.2: Method co-occurrence
            result = session.run("""
                MATCH (m1:Method)-[r:OFTEN_USED_WITH]->(m2:Method)
                RETURN m1.name as method1, 
                       m2.name as method2, 
                       r.frequency as frequency,
                       r.relationship_type as type
                ORDER BY r.frequency DESC
                LIMIT 10
            """).data()
            self.print_result("Method co-occurrence (methods used together)", result)
            
            # Query 3.3: Theory-Method patterns
            result = session.run("""
                MATCH (t:Theory)-[r:COMMONLY_USED_WITH]->(m:Method)
                RETURN t.name as theory, 
                       m.name as method, 
                       m.type as method_type,
                       r.frequency as frequency
                ORDER BY r.frequency DESC
                LIMIT 10
            """).data()
            self.print_result("Theory-Method patterns (common combinations)", result)
    
    def test_4_semantic_relationships(self):
        """Test 4: Semantic Relationships"""
        self.print_section("TEST 4: Semantic Relationships (Similar Research Questions)")
        
        with self.driver.session() as session:
            # Query 4.1: Similar research questions
            result = session.run("""
                MATCH (rq1:ResearchQuestion)-[r:SIMILAR_TO]->(rq2:ResearchQuestion)
                WHERE r.similarity > 0.75
                RETURN rq1.question as question1,
                       rq2.question as question2,
                       r.similarity as similarity
                ORDER BY r.similarity DESC
                LIMIT 10
            """).data()
            self.print_result("Similar research questions (semantic similarity)", result)
            
            # Query 4.2: Papers addressing similar questions
            result = session.run("""
                MATCH (p1:Paper)-[:ADDRESSES]->(rq1:ResearchQuestion)-[:SIMILAR_TO]->(rq2:ResearchQuestion)<-[:ADDRESSES]-(p2:Paper)
                WHERE p1 <> p2 AND rq1 <> rq2
                RETURN DISTINCT p1.title as paper1, 
                       p2.title as paper2,
                       rq1.question as question1,
                       rq2.question as question2
                LIMIT 5
            """).data()
            self.print_result("Papers addressing similar research questions", result)
    
    def test_5_embedding_similarity(self):
        """Test 5: Embedding-Based Similarity"""
        self.print_section("TEST 5: Embedding-Based Similarity (Entity Similarity)")
        
        with self.driver.session() as session:
            # Query 5.1: Find similar theories using embeddings
            # Get a sample theory
            sample = session.run("""
                MATCH (t:Theory)
                WHERE t.embedding IS NOT NULL
                RETURN t.name as name, t.embedding as embedding
                LIMIT 1
            """).single()
            
            if sample:
                theory_name = sample["name"]
                theory_embedding = np.array(sample["embedding"])
                
                # Find similar theories
                result = session.run("""
                    MATCH (t:Theory)
                    WHERE t.embedding IS NOT NULL AND t.name <> $theory_name
                    RETURN t.name as theory_name, 
                           t.embedding as embedding
                    LIMIT 20
                """, theory_name=theory_name).data()
                
                # Compute similarities
                similarities = []
                for record in result:
                    other_embedding = np.array(record["embedding"])
                    similarity = float(np.dot(theory_embedding, other_embedding) / (
                        np.linalg.norm(theory_embedding) * np.linalg.norm(other_embedding)
                    ))
                    if similarity > 0.7:  # High similarity threshold
                        similarities.append({
                            "theory": record["theory_name"],
                            "similarity": round(similarity, 3)
                        })
                
                similarities.sort(key=lambda x: x["similarity"], reverse=True)
                print(f"📊 Theories similar to '{theory_name}' (embedding similarity > 0.7)")
                if similarities:
                    print(f"   Found {len(similarities)} similar theory(ies)\n")
                    for i, sim in enumerate(similarities[:5], 1):
                        print(f"   {i}. {sim['theory']} (similarity: {sim['similarity']})")
                else:
                    print("   ⚠️  No similar theories found (threshold: 0.7)\n")
    
    def test_6_complex_multi_hop_queries(self):
        """Test 6: Complex Multi-Hop Queries"""
        self.print_section("TEST 6: Complex Multi-Hop Queries")
        
        with self.driver.session() as session:
            # Query 6.1: Papers using same theory and method
            result = session.run("""
                MATCH (p1:Paper)-[:USES_THEORY]->(t:Theory)<-[:USES_THEORY]-(p2:Paper)
                WHERE p1 <> p2
                MATCH (p1)-[:USES_METHOD]->(m:Method)<-[:USES_METHOD]-(p2)
                RETURN DISTINCT t.name as theory,
                       m.name as method,
                       collect(DISTINCT p1.title) as papers1,
                       collect(DISTINCT p2.title) as papers2
                LIMIT 5
            """).data()
            self.print_result("Papers using same theory AND method", result)
            
            # Query 6.2: Research gap: Theories with few papers
            result = session.run("""
                MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)
                WITH t, count(DISTINCT p) as paper_count
                WHERE paper_count < 3
                RETURN t.name as theory, 
                       paper_count,
                       'Research Gap: Under-studied theory' as gap_type
                ORDER BY paper_count ASC
                LIMIT 10
            """).data()
            self.print_result("Research gaps: Under-studied theories", result)
            
            # Query 6.3: Author collaboration network
            result = session.run("""
                MATCH (a1:Author)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(a2:Author)
                WHERE a1 <> a2
                WITH a1, a2, count(DISTINCT p) as collaboration_count
                WHERE collaboration_count >= 1
                RETURN a1.full_name as author1,
                       a2.full_name as author2,
                       collaboration_count
                ORDER BY collaboration_count DESC
                LIMIT 10
            """).data()
            self.print_result("Author collaboration network", result)
    
    def test_7_aggregation_queries(self):
        """Test 7: Aggregation Queries"""
        self.print_section("TEST 7: Aggregation Queries (Statistics)")
        
        with self.driver.session() as session:
            # Query 7.1: Most used theories
            # First get total paper count
            total_papers = session.run("MATCH (p:Paper) RETURN count(p) as total").single()["total"]
            
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY {role: 'primary'}]->(t:Theory)
                WITH t, count(DISTINCT p) as paper_count
                RETURN t.name as theory,
                       paper_count
                ORDER BY paper_count DESC
                LIMIT 10
            """).data()
            
            # Add percentage calculation
            for record in result:
                record["percentage"] = round(record["paper_count"] * 100.0 / total_papers, 1) if total_papers > 0 else 0
            self.print_result("Most used theories (primary)", result)
            
            # Query 7.2: Most used methods
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WITH m, count(DISTINCT p) as paper_count
                RETURN m.name as method,
                       m.type as method_type,
                       paper_count
                ORDER BY paper_count DESC
                LIMIT 10
            """).data()
            self.print_result("Most used methods", result)
            
            # Query 7.3: Theory-Method combination frequency
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY {role: 'primary'}]->(t:Theory),
                      (p)-[:USES_METHOD]->(m:Method)
                WITH t, m, count(DISTINCT p) as frequency
                WHERE frequency >= 1
                RETURN t.name as theory,
                       m.name as method,
                       frequency
                ORDER BY frequency DESC
                LIMIT 10
            """).data()
            self.print_result("Most common theory-method combinations", result)
    
    def test_8_temporal_queries(self):
        """Test 8: Temporal Queries"""
        self.print_section("TEST 8: Temporal Queries (Evolution Over Time)")
        
        with self.driver.session() as session:
            # Query 8.1: Method usage over time
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WHERE p.year IS NOT NULL
                WITH m, p.year as year, count(*) as usage_count
                RETURN m.name as method,
                       year,
                       usage_count
                ORDER BY m.name, year
                LIMIT 15
            """).data()
            self.print_result("Method usage over time", result)
            
            # Query 8.2: Theory usage over time
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY {role: 'primary'}]->(t:Theory)
                WHERE p.year IS NOT NULL
                WITH t, p.year as year, count(*) as usage_count
                RETURN t.name as theory,
                       year,
                       usage_count
                ORDER BY t.name, year
                LIMIT 15
            """).data()
            self.print_result("Theory usage over time", result)
            
            # Query 8.3: Method evolution (if relationships exist)
            result = session.run("""
                MATCH (m1:Method)-[r:EVOLVED_TO]->(m2:Method)
                RETURN m1.name as from_method,
                       m2.name as to_method,
                       r.time_gap as avg_years,
                       r.frequency as frequency
                ORDER BY r.frequency DESC
                LIMIT 10
            """).data()
            self.print_result("Method evolution (temporal relationships)", result)
    
    def test_9_graph_statistics(self):
        """Test 9: Graph Statistics"""
        self.print_section("TEST 9: Graph Statistics")
        
        with self.driver.session() as session:
            # Overall statistics
            stats = {}
            
            # Node counts
            node_counts = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """).data()
            
            print("📊 Node Counts:")
            for record in node_counts:
                label = record["label"]
                count = record["count"]
                stats[label] = count
                print(f"   • {label}: {count}")
            
            # Relationship counts
            rel_counts = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """).data()
            
            print("\n🔗 Relationship Counts:")
            for record in rel_counts:
                rel_type = record["type"]
                count = record["count"]
                print(f"   • {rel_type}: {count}")
            
            # Papers with embeddings
            emb_count = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                RETURN count(*) as count
            """).single()["count"]
            
            print(f"\n📊 Papers with Embeddings: {emb_count}/{stats.get('Paper', 0)}")
            
            # Entities with embeddings
            entity_emb_counts = session.run("""
                MATCH (t:Theory)
                WHERE t.embedding IS NOT NULL
                RETURN count(*) as count
            """).single()["count"]
            print(f"📊 Theories with Embeddings: {entity_emb_counts}/{stats.get('Theory', 0)}")
            
            print()
    
    def run_all_tests(self):
        """Run all complex query tests"""
        print("\n" + "=" * 80)
        print("  COMPLEX QUERY TESTING - Enhanced Graph Capabilities")
        print("=" * 80)
        
        try:
            self.test_1_indexed_queries()
            self.test_2_fulltext_search()
            self.test_3_entity_to_entity_relationships()
            self.test_4_semantic_relationships()
            self.test_5_embedding_similarity()
            self.test_6_complex_multi_hop_queries()
            self.test_7_aggregation_queries()
            self.test_8_temporal_queries()
            self.test_9_graph_statistics()
            
            print("\n" + "=" * 80)
            print("  ✅ ALL TESTS COMPLETED")
            print("=" * 80 + "\n")
            
        except Exception as e:
            logger.error(f"Error during testing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    tester = ComplexQueryTester()
    try:
        tester.run_all_tests()
    finally:
        tester.close()

