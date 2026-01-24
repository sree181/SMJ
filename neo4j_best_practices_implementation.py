#!/usr/bin/env python3
"""
Neo4j Best Practices Implementation
- Indexes and constraints
- Entity embeddings for similarity
- Optimized batch operations
- Enhanced graph structure for agent queries
"""

import os
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jBestPractices:
    """
    Implements Neo4j best practices:
    1. Indexes and constraints
    2. Entity embeddings for similarity
    3. Optimized batch operations
    4. Enhanced graph structure
    """
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        if neo4j_user is None:
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        if neo4j_password is None:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50
        )
        
        # Initialize embedding model
        logger.info("Loading embedding model for entity similarity...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        logger.info("✓ Embedding model loaded")
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def create_indexes_and_constraints(self):
        """
        Create indexes and constraints following Neo4j best practices
        Based on: https://neo4j.com/docs/cypher-manual/current/constraints/
        """
        logger.info("Creating indexes and constraints...")
        
        with self.driver.session() as session:
            # Unique constraints (enforce uniqueness at database level)
            constraints = [
                # Paper constraints
                "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
                
                # Author constraints
                "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
                
                # Theory constraints
                "CREATE CONSTRAINT theory_name_unique IF NOT EXISTS FOR (t:Theory) REQUIRE t.name IS UNIQUE",
                
                # Method constraints (composite: name + type)
                "CREATE CONSTRAINT method_name_type_unique IF NOT EXISTS FOR (m:Method) REQUIRE (m.name, m.type) IS UNIQUE",
                
                # Software constraints
                "CREATE CONSTRAINT software_name_unique IF NOT EXISTS FOR (s:Software) REQUIRE s.software_name IS UNIQUE",
                
                # Dataset constraints
                "CREATE CONSTRAINT dataset_name_unique IF NOT EXISTS FOR (d:Dataset) REQUIRE d.dataset_name IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✓ Created constraint: {constraint.split()[-1]}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
            
            # Indexes on frequently queried properties
            indexes = [
                # Paper indexes
                "CREATE INDEX paper_year_index IF NOT EXISTS FOR (p:Paper) ON (p.year)",
                "CREATE INDEX paper_type_index IF NOT EXISTS FOR (p:Paper) ON (p.paper_type)",
                "CREATE INDEX paper_journal_index IF NOT EXISTS FOR (p:Paper) ON (p.journal)",
                
                # Composite index for common query pattern
                "CREATE INDEX paper_year_type_index IF NOT EXISTS FOR (p:Paper) ON (p.year, p.paper_type)",
                
                # Theory indexes
                "CREATE INDEX theory_domain_index IF NOT EXISTS FOR (t:Theory) ON (t.domain)",
                
                # Method indexes
                "CREATE INDEX method_type_index IF NOT EXISTS FOR (m:Method) ON (m.type)",
                
                # Author indexes
                "CREATE INDEX author_family_name_index IF NOT EXISTS FOR (a:Author) ON (a.family_name)",
                
                # Institution indexes
                "CREATE INDEX institution_country_index IF NOT EXISTS FOR (i:Institution) ON (i.country)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"✓ Created index: {index.split('ON')[0].split()[-1]}")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")
            
            # Full-text search index for paper titles and abstracts
            try:
                session.run("""
                    CREATE FULLTEXT INDEX paper_text_index IF NOT EXISTS
                    FOR (p:Paper) ON EACH [p.title, p.abstract]
                """)
                logger.info("✓ Created full-text search index for papers")
            except Exception as e:
                logger.warning(f"Full-text index may already exist: {e}")
            
            logger.info("✅ All indexes and constraints created")
    
    def generate_entity_embeddings(self):
        """
        Generate embeddings for all entity types (Theory, Method, etc.)
        Use embeddings for similarity detection instead of just string matching
        """
        logger.info("Generating entity embeddings...")
        
        entity_types = [
            ("Theory", "name", "description"),
            ("Method", "name", None),
            ("ResearchQuestion", "question", None),
            ("Variable", "variable_name", "operationalization"),
            ("Software", "software_name", None),
        ]
        
        with self.driver.session() as session:
            for entity_type, name_prop, desc_prop in entity_types:
                # Get all entities without embeddings
                result = session.run(f"""
                    MATCH (e:{entity_type})
                    WHERE e.embedding IS NULL
                    RETURN e.{name_prop} as name, 
                           e.{desc_prop} as description
                """.replace("e.description", f"COALESCE(e.{desc_prop}, '')") if desc_prop else f"""
                    MATCH (e:{entity_type})
                    WHERE e.embedding IS NULL
                    RETURN e.{name_prop} as name
                """)
                
                entities = list(result)
                if not entities:
                    logger.info(f"  No {entity_type} entities need embeddings")
                    continue
                
                logger.info(f"  Generating embeddings for {len(entities)} {entity_type} entities...")
                
                # Generate embeddings
                texts = []
                for record in entities:
                    text = record["name"]
                    if desc_prop and record.get("description"):
                        text += " " + record["description"]
                    texts.append(text)
                
                embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
                
                # Store embeddings in Neo4j
                for i, record in enumerate(entities):
                    entity_name = record["name"]
                    embedding = embeddings[i].tolist()
                    
                    session.run(f"""
                        MATCH (e:{entity_type} {{{name_prop}: $name}})
                        SET e.embedding = $embedding,
                            e.embedding_model = 'all-MiniLM-L6-v2',
                            e.embedding_dim = $dim
                    """,
                    name=entity_name,
                    embedding=embedding,
                    dim=self.embedding_dim)
                
                logger.info(f"  ✓ Generated embeddings for {len(entities)} {entity_type} entities")
        
        logger.info("✅ All entity embeddings generated")
    
    def find_similar_entity_embedding(self, entity_name: str, entity_type: str, threshold: float = 0.85) -> Optional[str]:
        """
        Find similar entity using embeddings
        Returns canonical name if similarity > threshold, else None
        """
        # Generate embedding for input entity
        entity_embedding = self.embedding_model.encode([entity_name], convert_to_numpy=True)[0]
        
        with self.driver.session() as session:
            # Find similar entities using vector similarity
            if entity_type == "Theory":
                name_prop = "name"
            elif entity_type == "Method":
                name_prop = "name"
            else:
                return None
            
            # Use vector similarity search (if vector index exists)
            # Otherwise, compute cosine similarity manually
            result = session.run(f"""
                MATCH (e:{entity_type})
                WHERE e.embedding IS NOT NULL
                RETURN e.{name_prop} as name, e.embedding as embedding
                LIMIT 100
            """)
            
            best_match = None
            best_similarity = 0.0
            
            for record in result:
                existing_embedding = np.array(record["embedding"])
                similarity = np.dot(entity_embedding, existing_embedding) / (
                    np.linalg.norm(entity_embedding) * np.linalg.norm(existing_embedding)
                )
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match = record["name"]
            
            return best_match
    
    def create_entity_to_entity_relationships(self):
        """
        Create entity-to-entity relationships for complex agent queries
        - Theory co-occurrence
        - Method co-occurrence
        - Theory-Method patterns
        """
        logger.info("Creating entity-to-entity relationships...")
        
        with self.driver.session() as session:
            # Theory co-occurrence (theories used together in same papers)
            logger.info("  Creating theory co-occurrence relationships...")
            session.run("""
                MATCH (p:Paper)-[:USES_THEORY {role: 'primary'}]->(t1:Theory)
                MATCH (p)-[:USES_THEORY {role: 'primary'}]->(t2:Theory)
                WHERE t1 <> t2
                WITH t1, t2, count(DISTINCT p) as co_occurrence_count
                WHERE co_occurrence_count >= 2
                MERGE (t1)-[r:OFTEN_USED_WITH {
                    frequency: co_occurrence_count,
                    relationship_type: 'theory_co_occurrence'
                }]->(t2)
                SET r.created_at = datetime()
            """)
            
            # Method co-occurrence (methods used together in same papers)
            logger.info("  Creating method co-occurrence relationships...")
            session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m1:Method)
                MATCH (p)-[:USES_METHOD]->(m2:Method)
                WHERE m1 <> m2
                WITH m1, m2, count(DISTINCT p) as co_occurrence_count
                WHERE co_occurrence_count >= 2
                MERGE (m1)-[r:OFTEN_USED_WITH {
                    frequency: co_occurrence_count,
                    relationship_type: 'method_co_occurrence'
                }]->(m2)
                SET r.created_at = datetime()
            """)
            
            # Theory-Method patterns (common combinations)
            logger.info("  Creating theory-method pattern relationships...")
            session.run("""
                MATCH (p:Paper)-[:USES_THEORY {role: 'primary'}]->(t:Theory)
                MATCH (p)-[:USES_METHOD]->(m:Method)
                WITH t, m, count(DISTINCT p) as frequency
                WHERE frequency >= 2
                MERGE (t)-[r:COMMONLY_USED_WITH {
                    frequency: frequency,
                    relationship_type: 'theory_method_pattern'
                }]->(m)
                SET r.created_at = datetime()
            """)
            
            logger.info("✅ Entity-to-entity relationships created")
    
    def create_semantic_relationships(self):
        """
        Create semantic relationships for complex queries
        - Similar research questions
        - Related findings
        """
        logger.info("Creating semantic relationships...")
        
        with self.driver.session() as session:
            # Similar research questions (using embeddings)
            logger.info("  Creating similar research question relationships...")
            
            # Get all research questions with embeddings
            result = session.run("""
                MATCH (rq:ResearchQuestion)
                WHERE rq.embedding IS NOT NULL
                RETURN rq.question_id as id, rq.question as question, rq.embedding as embedding
            """)
            
            questions = list(result)
            
            if len(questions) > 1:
                # Compute pairwise similarity
                for i, q1 in enumerate(questions):
                    emb1 = np.array(q1["embedding"])
                    for q2 in questions[i+1:]:
                        emb2 = np.array(q2["embedding"])
                        similarity = np.dot(emb1, emb2) / (
                            np.linalg.norm(emb1) * np.linalg.norm(emb2)
                        )
                        
                        if similarity > 0.75:  # High similarity threshold
                            session.run("""
                                MATCH (rq1:ResearchQuestion {question_id: $id1})
                                MATCH (rq2:ResearchQuestion {question_id: $id2})
                                MERGE (rq1)-[r:SIMILAR_TO {
                                    similarity: $similarity,
                                    relationship_type: 'semantic_similarity'
                                }]->(rq2)
                            """,
                            id1=q1["id"],
                            id2=q2["id"],
                            similarity=float(similarity))
            
            logger.info("✅ Semantic relationships created")
    
    def create_temporal_relationships(self):
        """
        Create temporal relationships for evolution analysis
        """
        logger.info("Creating temporal relationships...")
        
        with self.driver.session() as session:
            # Temporal sequence of methods (evolution over time)
            # First, compute average time gap
            result = session.run("""
                MATCH (p1:Paper)-[:USES_METHOD]->(m1:Method)
                MATCH (p2:Paper)-[:USES_METHOD]->(m2:Method)
                WHERE p1.year < p2.year 
                  AND p2.year - p1.year <= 5
                  AND m1.name = m2.name
                  AND p1.year IS NOT NULL
                  AND p2.year IS NOT NULL
                WITH m1, m2, count(*) as sequence_count, 
                     avg(p2.year - p1.year) as avg_time_gap
                WHERE sequence_count >= 3
                RETURN m1.name as method1, m2.name as method2, 
                       sequence_count, avg_time_gap
            """)
            
            relationships_created = 0
            for record in result:
                session.run("""
                    MATCH (m1:Method {name: $method1})
                    MATCH (m2:Method {name: $method2})
                    MERGE (m1)-[r:EVOLVED_TO {
                        time_gap: $avg_time_gap,
                        frequency: $sequence_count,
                        relationship_type: 'temporal_evolution'
                    }]->(m2)
                    SET r.created_at = datetime()
                """,
                method1=record["method1"],
                method2=record["method2"],
                avg_time_gap=float(record["avg_time_gap"]),
                sequence_count=record["sequence_count"])
                relationships_created += 1
            
            logger.info(f"✅ Temporal relationships created: {relationships_created} relationships")
    
    def setup_complete(self):
        """
        Run all best practices setup
        """
        logger.info("=" * 70)
        logger.info("Setting up Neo4j Best Practices")
        logger.info("=" * 70)
        
        # Step 1: Create indexes and constraints
        self.create_indexes_and_constraints()
        
        # Step 2: Generate entity embeddings
        self.generate_entity_embeddings()
        
        # Step 3: Create entity-to-entity relationships
        self.create_entity_to_entity_relationships()
        
        # Step 4: Create semantic relationships
        self.create_semantic_relationships()
        
        # Step 5: Create temporal relationships
        self.create_temporal_relationships()
        
        logger.info("=" * 70)
        logger.info("✅ Neo4j Best Practices Setup Complete")
        logger.info("=" * 70)

if __name__ == "__main__":
    best_practices = Neo4jBestPractices()
    try:
        best_practices.setup_complete()
    finally:
        best_practices.close()

