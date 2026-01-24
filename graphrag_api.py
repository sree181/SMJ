#!/usr/bin/env python3
"""
FastAPI Backend for GraphRAG
Provides REST API endpoints for frontend integration
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from neo4j_graphrag_official import OfficialNeo4jGraphRAG

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Neo4j GraphRAG API",
    description="GraphRAG API for Literature Review Knowledge Graph",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global GraphRAG instance
graphrag_instance: Optional[OfficialNeo4jGraphRAG] = None

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    return_context: bool = False
    use_cypher: bool = False

class QueryResponse(BaseModel):
    answer: str
    query: str
    sources_count: int
    context: Optional[list] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    vector_index_exists: bool
    papers_count: int

@app.on_event("startup")
async def startup_event():
    """Initialize GraphRAG on startup"""
    global graphrag_instance
    logger.info("Initializing GraphRAG...")
    try:
        graphrag_instance = OfficialNeo4jGraphRAG()
        graphrag_instance.setup_complete_pipeline()
        logger.info("✅ GraphRAG initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize GraphRAG: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global graphrag_instance
    if graphrag_instance:
        graphrag_instance.close()
        logger.info("GraphRAG closed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Neo4j GraphRAG API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/query": "POST - Query the knowledge graph",
            "/docs": "API documentation"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global graphrag_instance
    
    if not graphrag_instance:
        raise HTTPException(status_code=503, detail="GraphRAG not initialized")
    
    try:
        # Check Neo4j connection and get stats
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        with driver.session() as session:
            # Check vector index
            index_exists = False
            try:
                result = session.run("""
                    SHOW INDEXES
                    WHERE name = 'paper-embeddings'
                """).data()
                index_exists = len(result) > 0
            except:
                pass
            
            # Count papers
            result = session.run("MATCH (p:Paper) RETURN count(p) as count").single()
            papers_count = result['count'] if result else 0
        
        driver.close()
        
        return HealthResponse(
            status="healthy",
            message="GraphRAG API is running",
            vector_index_exists=index_exists,
            papers_count=papers_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_graphrag(request: QueryRequest):
    """
    Query the GraphRAG system
    
    Args:
        request: QueryRequest with query text and options
    
    Returns:
        QueryResponse with answer and metadata
    """
    global graphrag_instance
    
    if not graphrag_instance:
        raise HTTPException(status_code=503, detail="GraphRAG not initialized")
    
    try:
        # If use_cypher is requested, reinitialize with VectorCypherRetriever
        if request.use_cypher:
            logger.info("Reinitializing with VectorCypherRetriever...")
            graphrag_instance.initialize_graphrag(use_cypher=True)
        
        # Perform search
        response = graphrag_instance.search(
            query=request.query,
            top_k=request.top_k,
            return_context=request.return_context
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="No response from GraphRAG")
        
        # Extract context if available
        context = None
        if request.return_context and hasattr(response, 'context'):
            context = response.context
        
        # Count sources (approximate from context)
        sources_count = len(context) if context else request.top_k
        
        return QueryResponse(
            answer=response.answer,
            query=request.query,
            sources_count=sources_count,
            context=context
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get knowledge graph statistics"""
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        with driver.session() as session:
            # Get counts
            stats = {}
            
            # Papers
            result = session.run("MATCH (p:Paper) RETURN count(p) as count").single()
            stats['papers'] = result['count'] if result else 0
            
            # Papers with embeddings
            result = session.run("MATCH (p:Paper) WHERE p.embedding IS NOT NULL RETURN count(p) as count").single()
            stats['papers_with_embeddings'] = result['count'] if result else 0
            
            # Theories
            result = session.run("MATCH (t:Theory) RETURN count(t) as count").single()
            stats['theories'] = result['count'] if result else 0
            
            # Methods
            result = session.run("MATCH (m:Method) RETURN count(m) as count").single()
            stats['methods'] = result['count'] if result else 0
            
            # Relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()
            stats['relationships'] = result['count'] if result else 0
        
        driver.close()
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

