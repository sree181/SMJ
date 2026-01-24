#!/usr/bin/env python3
"""
Official Neo4j GraphRAG Implementation
Using neo4j-graphrag package for production-grade GraphRAG
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Neo4j GraphRAG imports
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_vector_index, upsert_vectors
from neo4j_graphrag.types import EntityType

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfficialNeo4jGraphRAG:
    """
    Official Neo4j GraphRAG implementation using neo4j-graphrag package
    """
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        
        # Initialize embedding model (sentence-transformers compatible with neo4j-graphrag)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded")
        
        # Vector index configuration
        self.index_name = "paper-embeddings"
        self.embedding_dim = 384
        
        # Initialize LLM (OLLAMA)
        logger.info("Initializing OLLAMA LLM...")
        self.llm = OllamaLLM(
            model_name="llama3.1:8b",
            host="http://localhost:11434"
        )
        logger.info("✓ OLLAMA LLM initialized")
    
    def create_vector_index(self):
        """
        Create vector index in Neo4j using official neo4j-graphrag utilities
        """
        logger.info("=" * 70)
        logger.info("Creating Vector Index")
        logger.info("=" * 70)
        
        try:
            # Correct API signature: driver first, then index_name
            create_vector_index(
                self.driver,
                self.index_name,
                label="Paper",
                embedding_property="embedding",
                dimensions=self.embedding_dim,
                similarity_fn="cosine"
            )
            logger.info(f"✅ Vector index '{self.index_name}' created successfully")
            return True
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "exist" in error_msg.lower():
                logger.info(f"ℹ️  Vector index '{self.index_name}' already exists")
                return True
            else:
                logger.warning(f"⚠️  Could not create vector index: {error_msg}")
                logger.info("   This might be because:")
                logger.info("   1. Neo4j version doesn't support vector indexes (need 5.x+)")
                logger.info("   2. Vector index syntax differs in your Neo4j version")
                logger.info("   Continuing with manual similarity search...")
                return False
    
    def populate_vector_index(self):
        """
        Populate vector index with paper embeddings
        Uses official neo4j-graphrag upsert_vectors function
        """
        logger.info("=" * 70)
        logger.info("Populating Vector Index")
        logger.info("=" * 70)
        
        with self.driver.session() as session:
            # Get all papers with embeddings
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL AND p.paper_id IS NOT NULL
                RETURN id(p) as node_id, p.paper_id as paper_id, p.embedding as embedding
            """).data()
            
            if not papers:
                logger.warning("⚠️  No papers with embeddings found")
                logger.info("   Run advanced_paper_features.py first to generate embeddings")
                return
            
            logger.info(f"Found {len(papers)} papers with embeddings")
            
            # Prepare data for upsert
            node_ids = [str(paper['node_id']) for paper in papers]
            embeddings = [paper['embedding'] for paper in papers]
            
            try:
                # Upsert vectors using official function
                upsert_vectors(
                    driver=self.driver,
                    ids=node_ids,
                    embedding_property="embedding",
                    embeddings=embeddings,
                    entity_type=EntityType.NODE
                )
                logger.info(f"✅ Populated vector index with {len(papers)} papers")
            except Exception as e:
                logger.warning(f"⚠️  Could not populate vector index: {e}")
                logger.info("   Embeddings are already stored as node properties")
                logger.info("   Vector index population may not be necessary")
    
    def initialize_retriever(self, use_cypher: bool = False):
        """
        Initialize retriever for GraphRAG
        
        Args:
            use_cypher: If True, use VectorCypherRetriever (includes graph traversal)
                      If False, use VectorRetriever (vector search only)
        """
        logger.info("Initializing retriever...")
        
        # Create embedder wrapper (neo4j-graphrag compatible)
        # neo4j-graphrag expects embedder with embed_query and embed_documents methods
        class SentenceTransformerEmbedder:
            def __init__(self, model):
                self.model = model
            
            def embed_query(self, text: str) -> list[float]:
                """Embed a query text"""
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                """Embed multiple documents"""
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
        
        embedder = SentenceTransformerEmbedder(self.embedding_model)
        
        if use_cypher:
            # VectorCypherRetriever: Vector search + graph traversal
            # The retrieval_query receives $nodes as a list of node objects from vector search
            # neo4j-graphrag handles UNWIND internally, so we just match on the nodes directly
            retrieval_query = """
            MATCH (p:Paper)
            WHERE p IN $nodes
            OPTIONAL MATCH (p)-[r]->(entity)
            WITH p, collect(DISTINCT {type: type(r), entity: labels(entity)[0]}) as relationships
            RETURN p.paper_id as paper_id,
                   p.title as title,
                   p.abstract as abstract,
                   relationships
            """
            
            self.retriever = VectorCypherRetriever(
                driver=self.driver,
                index_name=self.index_name,
                retrieval_query=retrieval_query,
                embedder=embedder
            )
            logger.info("✓ VectorCypherRetriever initialized (vector + graph traversal)")
        else:
            # VectorRetriever: Vector search only
            self.retriever = VectorRetriever(
                driver=self.driver,
                index_name=self.index_name,
                embedder=embedder
            )
            logger.info("✓ VectorRetriever initialized (vector search)")
        
        return self.retriever
    
    def initialize_graphrag(self, use_cypher: bool = False):
        """
        Initialize complete GraphRAG pipeline
        
        Args:
            use_cypher: If True, use VectorCypherRetriever for graph-aware retrieval
        """
        logger.info("=" * 70)
        logger.info("Initializing GraphRAG Pipeline")
        logger.info("=" * 70)
        
        # Initialize retriever
        retriever = self.initialize_retriever(use_cypher=use_cypher)
        
        # Initialize GraphRAG
        self.rag = GraphRAG(
            retriever=retriever,
            llm=self.llm
        )
        
        logger.info("✅ GraphRAG pipeline initialized")
        logger.info(f"   Retriever: {'VectorCypherRetriever' if use_cypher else 'VectorRetriever'}")
        logger.info(f"   LLM: OLLAMA (llama3.1:8b)")
    
    def search(self, query: str, top_k: int = 5, return_context: bool = False):
        """
        Perform GraphRAG search
        
        Args:
            query: User's question
            top_k: Number of results to retrieve
            return_context: If True, return retrieved context along with answer
        
        Returns:
            GraphRAG response with answer and optionally context
        """
        if not hasattr(self, 'rag'):
            logger.error("GraphRAG not initialized. Call initialize_graphrag() first.")
            return None
        
        logger.info(f"Query: {query}")
        
        try:
            response = self.rag.search(
                query_text=query,
                retriever_config={"top_k": top_k},
                return_context=return_context
            )
            
            return response
        except Exception as e:
            logger.error(f"Error during search: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def setup_complete_pipeline(self):
        """
        Complete setup: Create index, populate, initialize GraphRAG
        """
        logger.info("=" * 70)
        logger.info("Complete GraphRAG Setup")
        logger.info("=" * 70)
        
        # 1. Create vector index
        index_created = self.create_vector_index()
        
        # 2. Populate vector index (if created)
        if index_created:
            self.populate_vector_index()
        
        # 3. Initialize GraphRAG
        # Start with VectorRetriever (works reliably)
        # Can switch to VectorCypherRetriever later for graph traversal
        self.initialize_graphrag(use_cypher=False)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ GraphRAG Pipeline Ready!")
        logger.info("=" * 70)
        logger.info("\nYou can now query using:")
        logger.info("  graphrag.search('your question here')")
    
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()

# Example usage
if __name__ == "__main__":
    graphrag = OfficialNeo4jGraphRAG()
    
    try:
        # Complete setup
        graphrag.setup_complete_pipeline()
        
        # Example queries
        queries = [
            "What papers use Resource-Based View theory?",
            "Find papers similar to research on dynamic capabilities",
            "What are the main research methods used in strategic management?",
        ]
        
        print("\n" + "=" * 70)
        print("Testing GraphRAG Queries")
        print("=" * 70)
        
        for query in queries:
            print(f"\n📝 Question: {query}")
            print("-" * 70)
            
            response = graphrag.search(query, top_k=3, return_context=True)
            
            if response:
                print(f"\n💡 Answer:")
                print(response.answer)
                
                if hasattr(response, 'context') and response.context:
                    print(f"\n📚 Context retrieved: {len(response.context)} items")
            else:
                print("⚠️  No response generated")
    
    finally:
        graphrag.close()

