#!/usr/bin/env python3
"""
Graph RAG Query System
Hybrid search combining vector similarity + graph traversal for comprehensive Q&A
"""

import os
import logging
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from collections import defaultdict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphRAGQuerySystem:
    """
    Graph RAG system for comprehensive question answering
    Combines:
    1. Vector search (semantic similarity)
    2. Graph traversal (relationship-based)
    3. Entity matching (exact matches)
    4. Context assembly (rich relationship paths)
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def query(self, question: str, top_k: int = 10, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Main Graph RAG query method
        
        Args:
            question: User's question
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
        
        Returns:
            Dictionary with retrieved context, papers, entities, and relationships
        """
        logger.info(f"Graph RAG Query: '{question}'")
        
        # 1. Generate query embedding
        query_embedding = self.embedding_model.encode(question, convert_to_numpy=True)
        query_vector = query_embedding.tolist()
        
        try:
            with self.driver.session() as session:
                # 2. Vector Search: Find semantically similar papers
                similar_papers = self._vector_search_papers(session, query_vector, top_k, similarity_threshold) or []
                
                # 3. Vector Search: Find similar theories, phenomena, methods
                similar_theories = self._vector_search_theories(session, query_vector, top_k=5, threshold=similarity_threshold) or []
                similar_phenomena = self._vector_search_phenomena(session, query_vector, top_k=5, threshold=similarity_threshold) or []
                similar_methods = self._vector_search_methods(session, query_vector, top_k=5, threshold=similarity_threshold) or []
                
                # 4. Graph Traversal: Find connected papers
                paper_ids = [p.get('paper_id') for p in similar_papers if p and p.get('paper_id')]
                connected_papers = self._graph_traversal(session, paper_ids, top_k) if paper_ids else []
                if connected_papers is None:
                    connected_papers = []
                
                # 5. Entity Matching: Extract entities and find papers
                entity_matches = self._entity_matching(session, question) or []
                
                # 6. Build relationship context
                # Safely extract paper_ids from all sources
                connected_paper_ids = [p.get('paper_id') for p in connected_papers if p and p.get('paper_id')]
                entity_paper_ids = [p.get('paper_id') for p in entity_matches if p and p.get('paper_id')]
                all_paper_ids = list(set(paper_ids + connected_paper_ids + entity_paper_ids))
                relationship_context = self._get_relationship_context(session, all_paper_ids[:20]) if all_paper_ids else []
                if relationship_context is None:
                    relationship_context = []
                
                # 7. Build comprehensive context
                context = self._build_context(
                    similar_papers,
                    connected_papers,
                    similar_theories,
                    similar_phenomena,
                    similar_methods,
                    entity_matches,
                    relationship_context
                )
                
                return {
                    'question': question,
                    'context': context or '',
                    'papers': (similar_papers or [])[:top_k],
                    'connected_papers': (connected_papers or [])[:top_k],
                    'theories': similar_theories or [],
                    'phenomena': similar_phenomena or [],
                    'methods': similar_methods or [],
                    'entity_matches': entity_matches or [],
                    'relationships': relationship_context or [],
                    'total_papers': len(set(all_paper_ids)) if all_paper_ids else 0
                }
        except Exception as e:
            logger.error(f"Error in Graph RAG query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty result instead of None
            return {
                'question': question,
                'context': '',
                'papers': [],
                'connected_papers': [],
                'theories': [],
                'phenomena': [],
                'methods': [],
                'entity_matches': [],
                'relationships': [],
                'total_papers': 0
            }
    
    def _vector_search_papers(self, session, query_vector: List[float], top_k: int, threshold: float) -> List[Dict]:
        """Vector search for similar papers"""
        papers = session.run("""
            MATCH (p:Paper)
            WHERE p.embedding IS NOT NULL
            RETURN p.paper_id as paper_id,
                   p.title as title,
                   p.abstract as abstract,
                   p.year as year,
                   p.embedding as embedding
        """).data()
        
        if not papers:
            return []
        
        similarities = []
        for paper in papers:
            if not paper:
                continue
            embedding = paper.get('embedding')
            if embedding:
                try:
                    similarity = self.cosine_similarity(query_vector, embedding)
                    if similarity >= threshold:
                        similarities.append({
                            'paper_id': paper.get('paper_id'),
                            'title': paper.get('title', ''),
                            'abstract': paper.get('abstract', ''),
                            'year': paper.get('year'),
                            'similarity': similarity,
                            'source': 'vector_search'
                        })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for paper {paper.get('paper_id')}: {e}")
                    continue
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _vector_search_theories(self, session, query_vector: List[float], top_k: int, threshold: float) -> List[Dict]:
        """Vector search for similar theories"""
        theories = session.run("""
            MATCH (t:Theory)
            WHERE t.embedding IS NOT NULL
            RETURN t.name as name,
                   t.description as description,
                   t.embedding as embedding
        """).data()
        
        if not theories:
            return []
        
        similarities = []
        for theory in theories:
            if not theory:
                continue
            embedding = theory.get('embedding')
            if embedding:
                try:
                    similarity = self.cosine_similarity(query_vector, embedding)
                    if similarity >= threshold:
                        similarities.append({
                            'name': theory.get('name', ''),
                            'description': theory.get('description', ''),
                            'similarity': similarity
                        })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for theory {theory.get('name')}: {e}")
                    continue
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _vector_search_phenomena(self, session, query_vector: List[float], top_k: int, threshold: float) -> List[Dict]:
        """Vector search for similar phenomena"""
        phenomena = session.run("""
            MATCH (ph:Phenomenon)
            WHERE ph.embedding IS NOT NULL
            RETURN ph.phenomenon_name as name,
                   ph.description as description,
                   ph.embedding as embedding
        """).data()
        
        if not phenomena:
            return []
        
        similarities = []
        for phenomenon in phenomena:
            if not phenomenon:
                continue
            embedding = phenomenon.get('embedding')
            if embedding:
                try:
                    similarity = self.cosine_similarity(query_vector, embedding)
                    if similarity >= threshold:
                        similarities.append({
                            'name': phenomenon.get('name', ''),
                            'description': phenomenon.get('description', ''),
                            'similarity': similarity
                        })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for phenomenon {phenomenon.get('name')}: {e}")
                    continue
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _vector_search_methods(self, session, query_vector: List[float], top_k: int, threshold: float) -> List[Dict]:
        """Vector search for similar methods"""
        methods = session.run("""
            MATCH (m:Method)
            WHERE m.embedding IS NOT NULL
            RETURN m.name as name,
                   m.type as type,
                   m.embedding as embedding
        """).data()
        
        if not methods:
            return []
        
        similarities = []
        for method in methods:
            if not method:
                continue
            embedding = method.get('embedding')
            if embedding:
                try:
                    similarity = self.cosine_similarity(query_vector, embedding)
                    if similarity >= threshold:
                        similarities.append({
                            'name': method.get('name', ''),
                            'type': method.get('type', ''),
                            'similarity': similarity
                        })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for method {method.get('name')}: {e}")
                    continue
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _graph_traversal(self, session, paper_ids: List[str], top_k: int) -> List[Dict]:
        """Find papers connected via graph relationships"""
        if not paper_ids:
            return []
        
        result = session.run("""
            MATCH (p1:Paper)-[r]->(entity)
            WHERE p1.paper_id IN $paper_ids
            AND entity IS NOT NULL
            WITH DISTINCT entity
            MATCH (p2:Paper)-[r2]->(entity)
            WHERE p2.paper_id IS NOT NULL
            AND NOT p2.paper_id IN $paper_ids
            WITH p2, 
                 count(DISTINCT entity) as connection_strength,
                 collect(DISTINCT CASE WHEN size(labels(entity)) > 0 THEN labels(entity)[0] ELSE 'Unknown' END) as entity_types
            RETURN p2.paper_id as paper_id,
                   p2.title as title,
                   p2.abstract as abstract,
                   p2.year as year,
                   connection_strength,
                   entity_types
            ORDER BY connection_strength DESC
            LIMIT $top_k
        """, paper_ids=paper_ids, top_k=top_k).data()
        
        return [{
            'paper_id': r.get('paper_id'),
            'title': r.get('title', ''),
            'abstract': r.get('abstract', ''),
            'year': r.get('year'),
            'connection_strength': r.get('connection_strength', 0),
            'entity_types': r.get('entity_types', []),
            'source': 'graph_traversal'
        } for r in result if r and r.get('paper_id')]
    
    def _entity_matching(self, session, question: str) -> List[Dict]:
        """Extract entities from question and find matching papers"""
        question_lower = question.lower()
        keywords = [w for w in question_lower.split() if len(w) > 3]  # Filter short words
        
        matches = []
        
        # Check for theories
        for keyword in keywords[:3]:  # Limit to first 3 keywords
            result = session.run("""
                MATCH (t:Theory)
                WHERE toLower(t.name) CONTAINS $keyword
                WITH t
                MATCH (p:Paper)-[:USES_THEORY]->(t)
                RETURN DISTINCT p.paper_id as paper_id,
                       p.title as title,
                       p.abstract as abstract,
                       p.year as year,
                       t.name as theory_name,
                       'theory_match' as match_type
                LIMIT 5
            """, keyword=keyword).data()
            matches.extend(result)
        
        # Check for phenomena
        for keyword in keywords[:3]:
            result = session.run("""
                MATCH (ph:Phenomenon)
                WHERE toLower(ph.phenomenon_name) CONTAINS $keyword
                WITH ph
                MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph)
                RETURN DISTINCT p.paper_id as paper_id,
                       p.title as title,
                       p.abstract as abstract,
                       p.year as year,
                       ph.phenomenon_name as phenomenon_name,
                       'phenomenon_match' as match_type
                LIMIT 5
            """, keyword=keyword).data()
            matches.extend(result)
        
        # Deduplicate
        seen = set()
        unique_matches = []
        for match in matches:
            if not match:
                continue
            paper_id = match.get('paper_id')
            if paper_id and paper_id not in seen:
                seen.add(paper_id)
                unique_matches.append({
                    'paper_id': paper_id,
                    'title': match.get('title', ''),
                    'abstract': match.get('abstract', ''),
                    'year': match.get('year'),
                    'match_type': match.get('match_type', 'entity_match'),
                    'source': 'entity_matching'
                })
        
        return unique_matches[:10]  # Limit to 10 matches
    
    def _get_relationship_context(self, session, paper_ids: List[str]) -> List[Dict]:
        """Get relationship context for papers"""
        if not paper_ids:
            return []
        
        result = session.run("""
            MATCH (p1:Paper)-[r]->(entity)
            WHERE p1.paper_id IN $paper_ids
            AND entity IS NOT NULL
            WITH p1, entity, type(r) as rel_type, r
            OPTIONAL MATCH (p2:Paper)-[r2]->(entity)
            WHERE p2.paper_id IS NOT NULL AND p2.paper_id <> p1.paper_id
            WITH p1, entity, rel_type, count(DISTINCT p2) as connected_papers,
                 CASE WHEN size(labels(entity)) > 0 THEN labels(entity)[0] ELSE 'Unknown' END as entity_type,
                 CASE 
                     WHEN size(labels(entity)) > 0 AND labels(entity)[0] = 'Theory' THEN entity.name
                     WHEN size(labels(entity)) > 0 AND labels(entity)[0] = 'Phenomenon' THEN entity.phenomenon_name
                     WHEN size(labels(entity)) > 0 AND labels(entity)[0] = 'Method' THEN entity.name
                     ELSE ''
                 END as entity_name
            RETURN p1.paper_id as paper_id,
                   entity_type,
                   entity_name,
                   rel_type,
                   connected_papers
            ORDER BY connected_papers DESC
            LIMIT 50
        """, paper_ids=paper_ids).data()
        
        return [dict(r) for r in result if r]
    
    def _build_context(self, similar_papers: List[Dict], connected_papers: List[Dict],
                      theories: List[Dict], phenomena: List[Dict], methods: List[Dict],
                      entity_matches: List[Dict], relationships: List[Dict]) -> str:
        """Build comprehensive context string for LLM"""
        context_parts = []
        
        # Papers from vector search
        if similar_papers:
            context_parts.append("SEMANTICALLY SIMILAR PAPERS:")
            for paper in similar_papers[:5]:
                if paper and paper.get('title'):
                    context_parts.append(f"- {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})")
                    if paper.get('abstract'):
                        context_parts.append(f"  Abstract: {str(paper.get('abstract', ''))[:200]}...")
                    context_parts.append(f"  Similarity: {paper.get('similarity', 0):.3f}")
        
        # Connected papers
        if connected_papers:
            context_parts.append("\nGRAPH-CONNECTED PAPERS:")
            for paper in connected_papers[:5]:
                if paper and paper.get('title'):
                    context_parts.append(f"- {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})")
                    entity_types = paper.get('entity_types', [])
                    if entity_types:
                        context_parts.append(f"  Connected via: {', '.join(str(et) for et in entity_types if et)}")
        
        # Relevant theories
        if theories:
            context_parts.append("\nRELEVANT THEORIES:")
            for theory in theories[:5]:
                if theory and theory.get('name'):
                    desc = theory.get('description', '') or ''
                    context_parts.append(f"- {theory.get('name', 'Unknown')}: {desc[:100]}")
        
        # Relevant phenomena
        if phenomena:
            context_parts.append("\nRELEVANT PHENOMENA:")
            for phenomenon in phenomena[:5]:
                if phenomenon and phenomenon.get('name'):
                    desc = phenomenon.get('description', '') or ''
                    context_parts.append(f"- {phenomenon.get('name', 'Unknown')}: {desc[:100]}")
        
        # Relevant methods
        if methods:
            context_parts.append("\nRELEVANT METHODS:")
            for method in methods[:5]:
                if method and method.get('name'):
                    context_parts.append(f"- {method.get('name', 'Unknown')} ({method.get('type', 'N/A')})")
        
        # Relationship context
        if relationships:
            context_parts.append("\nKEY RELATIONSHIPS:")
            theory_phenomenon = [r for r in relationships if r.get('entity_type') == 'Theory' and 'Phenomenon' in str(r)]
            if theory_phenomenon:
                context_parts.append(f"- {len(theory_phenomenon)} Theory-Phenomenon connections found")
        
        return "\n".join(context_parts)
    
    def generate_answer(self, query_result: Dict[str, Any], use_llm: bool = True) -> str:
        """Generate answer using LLM with Graph RAG context"""
        if not query_result:
            logger.error("query_result is None or empty")
            return "I'm sorry, I couldn't retrieve enough context to answer your question. Please try rephrasing it."
        
        if not use_llm:
            return self._generate_summary(query_result)
        
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, falling back to summary")
            return self._generate_summary(query_result)
        
        client = OpenAI(api_key=api_key)
        
        context = query_result.get('context', '') if query_result else ''
        question = query_result.get('question', '') if query_result else ''
        
        # Check if context is meaningful (lowered threshold to allow more attempts)
        if not context or len(context.strip()) < 20:
            logger.warning(f"Context too short ({len(context)} chars), falling back to summary")
            return self._generate_summary(query_result)
        
        logger.info(f"Generating LLM answer with context length: {len(context)} characters")
        
        prompt = f"""You are an expert research assistant analyzing Strategic Management Journal literature.

User Question: {question}

Retrieved Context:
{context}

Based on the retrieved context, provide a comprehensive answer that:
1. Directly addresses the question
2. Cites specific papers, theories, and phenomena
3. Explains relationships and connections
4. Identifies patterns and trends
5. Suggests areas for further research if applicable

Be specific, well-structured, and cite paper IDs when referencing studies."""

        try:
            logger.info("Calling OpenAI API for answer generation...")
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and len(content.strip()) > 50:
                    logger.info(f"Successfully generated LLM answer (length: {len(content)} chars)")
                    return content.strip()
                else:
                    logger.warning(f"OpenAI API returned short/empty content (length: {len(content) if content else 0}), falling back to summary")
            else:
                logger.warning("OpenAI API returned invalid response structure, falling back to summary")
            return self._generate_summary(query_result)
        except Exception as e:
            logger.error(f"Error generating answer with OpenAI: {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("Falling back to summary due to OpenAI API error")
            return self._generate_summary(query_result)
    
    def _generate_summary(self, query_result: Dict[str, Any]) -> str:
        """Generate summary without LLM - this should only be used as fallback"""
        papers = query_result.get('papers', []) or []
        connected_papers = query_result.get('connected_papers', []) or []
        theories = query_result.get('theories', []) or []
        phenomena = query_result.get('phenomena', []) or []
        methods = query_result.get('methods', []) or []
        
        total_papers = len(papers) + len(connected_papers)
        
        summary = f"I found {total_papers} relevant papers"
        if theories:
            summary += f", {len(theories)} relevant theories"
        if phenomena:
            summary += f", {len(phenomena)} relevant phenomena"
        if methods:
            summary += f", {len(methods)} relevant methods"
        
        summary += " in the knowledge graph.\n\n"
        summary += "To provide a more detailed answer, I would need access to an LLM service. "
        summary += "The current data shows research activity across multiple papers, but I cannot "
        summary += "synthesize a comprehensive response without additional processing capabilities.\n\n"
        summary += "Available data includes research questions, methods, findings, theories, and phenomena "
        summary += "from various Strategic Management Journal papers."
        
        return summary
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    # Test the system
    system = GraphRAGQuerySystem()
    try:
        result = system.query("What theories explain resource allocation patterns?")
        print("\n" + "=" * 80)
        print("QUERY RESULT")
        print("=" * 80)
        print(f"Papers found: {len(result['papers'])}")
        print(f"Connected papers: {len(result['connected_papers'])}")
        print(f"Theories: {len(result['theories'])}")
        print(f"Phenomena: {len(result['phenomena'])}")
        print("\nContext preview:")
        print(result['context'][:500] + "...")
    finally:
        system.close()
