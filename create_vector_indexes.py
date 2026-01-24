#!/usr/bin/env python3
"""
Create Vector Indexes for Embeddings
Enables fast similarity search using Neo4j vector indexes
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIndexCreator:
    """Create vector indexes for entity embeddings"""
    
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
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def check_neo4j_version(self):
        """Check if Neo4j version supports vector indexes"""
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
                        logger.warning(f"⚠️ Neo4j version {version} may not support vector indexes (requires 5.x+)")
                        return False
        return False
    
    def create_vector_indexes(self):
        """Create vector indexes for all entities with embeddings"""
        logger.info("Creating vector indexes for embeddings...")
        
        # Check Neo4j version
        if not self.check_neo4j_version():
            logger.warning("Vector indexes may not be supported. Continuing with fallback...")
        
        with self.driver.session() as session:
            # Entity types with embeddings
            entity_configs = [
                {
                    'label': 'Theory',
                    'property': 'embedding',
                    'dimensions': 384,
                    'index_name': 'theory_embedding_index'
                },
                {
                    'label': 'Method',
                    'property': 'embedding',
                    'dimensions': 384,
                    'index_name': 'method_embedding_index'
                },
                {
                    'label': 'ResearchQuestion',
                    'property': 'embedding',
                    'dimensions': 384,
                    'index_name': 'research_question_embedding_index'
                },
                {
                    'label': 'Variable',
                    'property': 'embedding',
                    'dimensions': 384,
                    'index_name': 'variable_embedding_index'
                },
                {
                    'label': 'Paper',
                    'property': 'embedding',
                    'dimensions': 384,
                    'index_name': 'paper_embedding_index'
                }
            ]
            
            for config in entity_configs:
                try:
                    # Check if entities with embeddings exist
                    count_result = session.run(f"""
                        MATCH (e:{config['label']})
                        WHERE e.{config['property']} IS NOT NULL
                        RETURN count(e) as count
                    """)
                    
                    count_record = count_result.single()
                    entity_count = count_record['count'] if count_record else 0
                    
                    if entity_count == 0:
                        logger.info(f"  No {config['label']} entities with embeddings found, skipping index")
                        continue
                    
                    logger.info(f"  Creating vector index for {config['label']} ({entity_count} entities)...")
                    
                    # Try to create vector index (Neo4j 5.x+)
                    try:
                        session.run(f"""
                            CREATE VECTOR INDEX {config['index_name']} IF NOT EXISTS
                            FOR (e:{config['label']}) ON e.{config['property']}
                            OPTIONS {{
                                indexConfig: {{
                                    `vector.dimensions`: {config['dimensions']},
                                    `vector.similarity_function`: 'cosine'
                                }}
                            }}
                        """)
                        logger.info(f"  ✓ Created vector index: {config['index_name']}")
                    except Exception as e:
                        # Fallback: Create regular index if vector index not supported
                        if "vector" in str(e).lower() or "unknown" in str(e).lower():
                            logger.warning(f"  Vector index not supported, creating regular index instead")
                            session.run(f"""
                                CREATE INDEX {config['index_name']}_fallback IF NOT EXISTS
                                FOR (e:{config['label']}) ON (e.{config['property']})
                            """)
                            logger.info(f"  ✓ Created fallback index: {config['index_name']}_fallback")
                        else:
                            raise e
                
                except Exception as e:
                    logger.error(f"  ✗ Error creating index for {config['label']}: {e}")
                    # Continue with other indexes
                    continue
        
        logger.info("✅ Vector index creation complete")
    
    def verify_indexes(self):
        """Verify that indexes were created successfully"""
        logger.info("Verifying indexes...")
        
        with self.driver.session() as session:
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            
            vector_indexes = [idx for idx in indexes if 'vector' in str(idx.get('type', '')).lower() or 'embedding' in str(idx.get('name', '')).lower()]
            
            if vector_indexes:
                logger.info(f"✓ Found {len(vector_indexes)} vector/embedding indexes:")
                for idx in vector_indexes:
                    logger.info(f"  - {idx.get('name', 'unknown')}")
            else:
                logger.warning("⚠️ No vector indexes found (may be using fallback indexes)")
            
            # Check regular indexes
            regular_indexes = [idx for idx in indexes if 'embedding' in str(idx.get('name', '')).lower()]
            if regular_indexes:
                logger.info(f"✓ Found {len(regular_indexes)} embedding-related indexes:")
                for idx in regular_indexes:
                    logger.info(f"  - {idx.get('name', 'unknown')}")

if __name__ == "__main__":
    creator = VectorIndexCreator()
    try:
        creator.create_vector_indexes()
        creator.verify_indexes()
    finally:
        creator.close()

