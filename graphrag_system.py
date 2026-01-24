#!/usr/bin/env python3
"""
GraphRAG System for Literature Review
Combines vector search + graph traversal for intelligent paper retrieval
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiteratureGraphRAG:
    """
    GraphRAG system for literature review
    Combines:
    - Vector search (semantic similarity)
    - Graph traversal (relationship-based)
    - Entity matching (exact matches)
    """
    
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def query(self, question: str, top_k: int = 5, similarity_threshold: float = 0.4):
        """
        Main GraphRAG query method
        
        Args:
            question: User's question
            top_k: Number of papers to retrieve
            similarity_threshold: Minimum similarity score
        
        Returns:
            Dictionary with retrieved papers, context, and relationships
        """
        logger.info(f"Query: {question}")
        
        # 1. Generate query embedding
        query_embedding = self.embedding_model.encode(question, convert_to_numpy=True)
        query_vector = query_embedding.tolist()
        
        with self.driver.session() as session:
            # 2. Vector Search: Find semantically similar papers
            logger.info("Performing vector search...")
            similar_papers = self._vector_search(session, query_vector, top_k, similarity_threshold)
            
            # 3. Graph Traversal: Find connected papers
            logger.info("Performing graph traversal...")
            connected_papers = []
            relationship_context = []
            
            if similar_papers:
                paper_ids = [p['paper_id'] for p in similar_papers]
                connected_papers = self._graph_traversal(session, paper_ids, top_k)
                relationship_context = self._get_relationship_context(session, paper_ids)
            
            # 4. Entity Matching: Extract entities from question and find papers
            logger.info("Performing entity matching...")
            entity_matches = self._entity_matching(session, question)
            
            return {
                'question': question,
                'similar_papers': similar_papers,
                'connected_papers': connected_papers,
                'entity_matches': entity_matches,
                'relationship_context': relationship_context,
                'total_papers': len(set(
                    [p['paper_id'] for p in similar_papers] +
                    [p['paper_id'] for p in connected_papers] +
                    [p['paper_id'] for p in entity_matches]
                ))
            }
    
    def _vector_search(self, session, query_vector: List[float], top_k: int, threshold: float):
        """Vector search for similar papers"""
        # Get all papers with embeddings
        papers = session.run("""
            MATCH (p:Paper)
            WHERE p.embedding IS NOT NULL
            RETURN p.paper_id as paper_id,
                   p.title as title,
                   p.abstract as abstract,
                   p.embedding as embedding
        """).data()
        
        if not papers:
            return []
        
        # Compute similarities
        similarities = []
        for paper in papers:
            if paper['embedding']:
                similarity = self.cosine_similarity(query_vector, paper['embedding'])
                if similarity >= threshold:
                    similarities.append({
                        'paper_id': paper['paper_id'],
                        'title': paper['title'],
                        'abstract': paper['abstract'],
                        'similarity': similarity
                    })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _graph_traversal(self, session, paper_ids: List[str], top_k: int):
        """Find papers connected via graph relationships"""
        if not paper_ids:
            return []
        
        result = session.run("""
            MATCH (p1:Paper)-[r]->(entity)<-[r2]-(p2:Paper)
            WHERE p1.paper_id IN $paper_ids
            AND p1 <> p2
            AND p2.paper_id IS NOT NULL
            WITH p2, 
                 count(DISTINCT entity) as connection_strength,
                 collect(DISTINCT type(r)) as relationship_types
            RETURN p2.paper_id as paper_id,
                   p2.title as title,
                   p2.abstract as abstract,
                   connection_strength,
                   relationship_types
            ORDER BY connection_strength DESC
            LIMIT $top_k
        """, paper_ids=paper_ids, top_k=top_k).data()
        
        return result
    
    def _get_relationship_context(self, session, paper_ids: List[str]):
        """Get relationship context between papers"""
        if not paper_ids:
            return []
        
        result = session.run("""
            MATCH (p1:Paper)-[r]->(p2:Paper)
            WHERE p1.paper_id IN $paper_ids
            RETURN p1.paper_id as paper1,
                   p2.paper_id as paper2,
                   type(r) as relationship_type,
                   properties(r) as properties
            LIMIT 20
        """, paper_ids=paper_ids).data()
        
        return result
    
    def _entity_matching(self, session, question: str):
        """Extract entities from question and find matching papers"""
        # Simple keyword matching (can be enhanced with NER)
        keywords = question.lower().split()
        
        # Look for theory names, method names, etc.
        entity_matches = []
        
        # Check for theories
        theories = session.run("""
            MATCH (t:Theory)
            WHERE toLower(t.name) CONTAINS $keyword
            WITH t
            MATCH (p:Paper)-[:USES_THEORY]->(t)
            RETURN DISTINCT p.paper_id as paper_id,
                   p.title as title,
                   p.abstract as abstract,
                   'theory_match' as match_type
            LIMIT 5
        """, keyword=keywords[0] if keywords else "").data()
        
        entity_matches.extend(theories)
        
        return entity_matches[:5]  # Limit to 5
    
    def generate_answer(self, query_result: Dict, use_llm: bool = False):
        """
        Generate answer from retrieved context
        
        Args:
            query_result: Result from query() method
            use_llm: Whether to use LLM for answer generation
        
        Returns:
            Formatted answer string
        """
        if use_llm:
            # Use OLLAMA or OpenAI to generate answer
            # This would integrate with your LLM
            pass
        
        # Simple answer generation (can be enhanced with LLM)
        answer_parts = []
        
        answer_parts.append(f"Found {query_result['total_papers']} relevant papers.\n")
        
        if query_result['similar_papers']:
            answer_parts.append("\n📄 Semantically Similar Papers:")
            for paper in query_result['similar_papers'][:3]:
                answer_parts.append(
                    f"  - {paper['title']} (similarity: {paper['similarity']:.2f})"
                )
        
        if query_result['connected_papers']:
            answer_parts.append("\n🔗 Connected Papers:")
            for paper in query_result['connected_papers'][:3]:
                answer_parts.append(
                    f"  - {paper['title']} ({paper['connection_strength']} connections)"
                )
        
        if query_result['relationship_context']:
            answer_parts.append("\n📊 Relationships:")
            for rel in query_result['relationship_context'][:3]:
                answer_parts.append(
                    f"  - {rel['paper1']} -[{rel['relationship_type']}]-> {rel['paper2']}"
                )
        
        return "\n".join(answer_parts)
    
    def ask(self, question: str, use_llm: bool = False):
        """
        Complete GraphRAG pipeline: Query + Generate Answer
        
        Args:
            question: User's question
            use_llm: Whether to use LLM for answer generation
        
        Returns:
            Complete answer with sources
        """
        # 1. Retrieve context
        query_result = self.query(question)
        
        # 2. Generate answer
        answer = self.generate_answer(query_result, use_llm=use_llm)
        
        return {
            'answer': answer,
            'sources': query_result['similar_papers'],
            'connections': query_result['connected_papers'],
            'context': query_result['relationship_context']
        }
    
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()

# Example usage
if __name__ == "__main__":
    graphrag = LiteratureGraphRAG()
    
    try:
        # Example queries
        questions = [
            "What papers use Resource-Based View theory?",
            "Find papers similar to my research on dynamic capabilities",
            "What are the research gaps in strategic management?",
        ]
        
        for question in questions:
            print("\n" + "=" * 70)
            print(f"Question: {question}")
            print("=" * 70)
            
            result = graphrag.ask(question)
            print(result['answer'])
            print(f"\nTotal papers found: {result['sources']}")
    
    finally:
        graphrag.close()

