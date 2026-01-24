#!/usr/bin/env python3
"""
Setup Graph RAG System
Creates vector indexes and sets up hybrid search (vector + graph) for comprehensive Q&A
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphRAGSetup:
    """Setup Graph RAG system with vector indexes and hybrid search"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize embedding model for query encoding
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        logger.info("✓ Embedding model loaded")
    
    def check_neo4j_version(self) -> bool:
        """Check if Neo4j version supports vector indexes"""
        try:
            with self.driver.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
                for record in result:
                    if record['name'] == 'Neo4j Kernel':
                        version = record['versions'][0]
                        major_version = int(version.split('.')[0])
                        if major_version >= 5:
                            logger.info(f"✓ Neo4j version {version} supports vector indexes")
                            return True
                        else:
                            logger.warning(f"⚠️  Neo4j version {version} may not support vector indexes (requires 5.x+)")
                            return False
        except Exception as e:
            logger.warning(f"Could not check Neo4j version: {e}")
            return False
    
    def create_vector_indexes(self):
        """Create vector indexes for all entities with embeddings"""
        logger.info("=" * 80)
        logger.info("CREATING VECTOR INDEXES")
        logger.info("=" * 80)
        
        supports_vector_index = self.check_neo4j_version()
        
        entity_configs = [
            {'label': 'Paper', 'property': 'embedding', 'index_name': 'paper_embedding_index'},
            {'label': 'Theory', 'property': 'embedding', 'index_name': 'theory_embedding_index'},
            {'label': 'Phenomenon', 'property': 'embedding', 'index_name': 'phenomenon_embedding_index'},
            {'label': 'Method', 'property': 'embedding', 'index_name': 'method_embedding_index'},
            {'label': 'ResearchQuestion', 'property': 'embedding', 'index_name': 'research_question_embedding_index'},
        ]
        
        created = 0
        skipped = 0
        
        with self.driver.session() as session:
            for config in entity_configs:
                label = config['label']
                property_name = config['property']
                index_name = config['index_name']
                
                # Check if entities with embeddings exist
                result = session.run(f"""
                    MATCH (n:{label})
                    WHERE n.{property_name} IS NOT NULL
                    RETURN count(n) as count
                """)
                count = result.single()['count']
                
                if count == 0:
                    logger.info(f"  ⚠️  Skipping {label}: No entities with embeddings")
                    skipped += 1
                    continue
                
                logger.info(f"  Creating index for {label} ({count} entities)...")
                
                if supports_vector_index:
                    # Try to create vector index (Neo4j 5.x+)
                    try:
                        session.run(f"""
                            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                            FOR (n:{label})
                            ON n.{property_name}
                            OPTIONS {{
                                indexConfig: {{
                                    `vector.dimensions`: {self.embedding_dim},
                                    `vector.similarity_function`: 'cosine'
                                }}
                            }}
                        """)
                        logger.info(f"    ✓ Created vector index: {index_name}")
                        created += 1
                    except Exception as e:
                        logger.warning(f"    ⚠️  Could not create vector index (may not be supported): {e}")
                        logger.info(f"    → Embeddings stored as properties, can use similarity search")
                else:
                    logger.info(f"    → Embeddings stored as properties (vector index not supported)")
        
        logger.info(f"\n✓ Vector index setup complete: {created} created, {skipped} skipped")
    
    def verify_embeddings(self):
        """Verify embeddings are present"""
        logger.info("\n" + "=" * 80)
        logger.info("VERIFYING EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            entity_types = ['Paper', 'Theory', 'Phenomenon', 'Method', 'ResearchQuestion']
            
            for entity_type in entity_types:
                result = session.run(f"""
                    MATCH (n:{entity_type})
                    WHERE n.embedding IS NOT NULL
                    RETURN count(n) as count
                """)
                count = result.single()['count']
                
                result_total = session.run(f"MATCH (n:{entity_type}) RETURN count(n) as count")
                total = result_total.single()['count']
                
                pct = (count / total * 100) if total > 0 else 0
                status = "✓" if count > 0 else "✗"
                logger.info(f"  {status} {entity_type}: {count}/{total} ({pct:.1f}%)")
    
    def test_vector_search(self):
        """Test vector search functionality"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING VECTOR SEARCH")
        logger.info("=" * 80)
        
        test_query = "resource-based view competitive advantage"
        logger.info(f"Test query: '{test_query}'")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(test_query, convert_to_numpy=True)
        query_vector = query_embedding.tolist()
        
        with self.driver.session() as session:
            # Test paper search
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                RETURN p.paper_id, p.title, p.embedding
                LIMIT 10
            """)
            
            papers = list(result)
            if papers:
                logger.info(f"  Found {len(papers)} papers with embeddings")
                
                # Compute similarity for first paper
                if papers[0]['p.embedding']:
                    paper_emb = np.array(papers[0]['p.embedding'])
                    query_emb = np.array(query_vector)
                    similarity = float(np.dot(paper_emb, query_emb) / (np.linalg.norm(paper_emb) * np.linalg.norm(query_emb)))
                    logger.info(f"  ✓ Vector similarity computation works (sample: {similarity:.3f})")
            else:
                logger.warning("  ⚠️  No papers with embeddings found")
    
    def setup_complete(self):
        """Complete setup and verification"""
        logger.info("\n" + "=" * 80)
        logger.info("GRAPH RAG SETUP COMPLETE")
        logger.info("=" * 80)
        
        self.verify_embeddings()
        self.create_vector_indexes()
        self.test_vector_search()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Graph RAG system is ready!")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("1. Use GraphRAGQuerySystem for hybrid search queries")
        logger.info("2. Integrate with /api/query endpoint")
        logger.info("3. Test with comprehensive questions")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    setup = GraphRAGSetup()
    try:
        setup.setup_complete()
    finally:
        setup.close()
