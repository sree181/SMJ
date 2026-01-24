#!/usr/bin/env python3
"""
Advanced Paper-to-Paper Features Implementation
Implements embeddings, semantic similarity, centrality, and community detection
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedPaperFeatures:
    """
    Advanced paper-to-paper features using embeddings, graph analytics, and network science
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
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, 384-dim
        # For better quality, use: 'sentence-transformers/all-mpnet-base-v2' (768-dim, slower)
        logger.info("✓ Embedding model loaded")
    
    def generate_embeddings(self):
        """
        Generate embeddings for all papers and store in Neo4j
        Uses: abstract + introduction (first 2000 chars) + conclusion (first 1000 chars)
        """
        logger.info("=" * 70)
        logger.info("Generating Paper Embeddings")
        logger.info("=" * 70)
        
        with self.driver.session() as session:
            # Get all papers with their text
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.abstract IS NOT NULL
                RETURN p.paper_id as paper_id, 
                       p.abstract as abstract,
                       p.title as title
                ORDER BY p.paper_id
            """).data()
            
            logger.info(f"Found {len(papers)} papers to process")
            
            processed = 0
            for paper in papers:
                paper_id = paper['paper_id']
                if not paper_id:
                    continue
                
                # Combine text for embedding
                abstract = paper.get('abstract', '') or ''
                title = paper.get('title', '') or ''
                paper_text = f"{title}. {abstract}"[:3000]  # Limit to 3000 chars for speed
                
                if not paper_text.strip():
                    logger.warning(f"⚠️  Skipping {paper_id}: No text available")
                    continue
                
                # Generate embedding
                try:
                    embedding = self.embedding_model.encode(paper_text, convert_to_numpy=True)
                    embedding_list = embedding.tolist()
                    
                    # Store in Neo4j
                    session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        SET p.embedding = $embedding,
                            p.embedding_model = 'all-MiniLM-L6-v2',
                            p.embedding_dim = 384
                    """, paper_id=paper_id, embedding=embedding_list)
                    
                    processed += 1
                    if processed % 10 == 0:
                        logger.info(f"  Processed {processed}/{len(papers)} papers...")
                
                except Exception as e:
                    logger.error(f"✗ Error processing {paper_id}: {e}")
                    continue
            
            logger.info(f"✅ Generated embeddings for {processed} papers")
    
    def compute_semantic_similarity(self, threshold: float = 0.25):
        """
        Compute semantic similarity between papers based on embeddings
        Creates SEMANTIC_SIMILARITY relationships
        """
        logger.info("=" * 70)
        logger.info("Computing Semantic Similarity")
        logger.info("=" * 70)
        
        with self.driver.session() as session:
            # Get all papers with embeddings
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL AND p.paper_id IS NOT NULL
                RETURN p.paper_id as paper_id, p.embedding as embedding
                ORDER BY p.paper_id
            """).data()
            
            logger.info(f"Found {len(papers)} papers with embeddings")
            
            if len(papers) < 2:
                logger.warning("⚠️  Need at least 2 papers with embeddings")
                return
            
            # Convert to numpy arrays for efficient computation
            paper_ids = [p['paper_id'] for p in papers]
            embeddings = np.array([p['embedding'] for p in papers])
            
            # Compute pairwise cosine similarity
            logger.info("Computing pairwise similarities...")
            similarity_matrix = cosine_similarity(embeddings)
            
            # Create relationships for pairs above threshold
            relationships_created = 0
            for i, paper_id_1 in enumerate(paper_ids):
                for j, paper_id_2 in enumerate(paper_ids):
                    if i >= j:  # Only upper triangle (avoid duplicates)
                        continue
                    
                    similarity = float(similarity_matrix[i, j])
                    
                    if similarity >= threshold:
                        # Create bidirectional relationship
                        session.run("""
                            MATCH (p1:Paper {paper_id: $paper_id_1})
                            MATCH (p2:Paper {paper_id: $paper_id_2})
                            WHERE NOT EXISTS((p1)-[:SEMANTIC_SIMILARITY]->(p2))
                            MERGE (p1)-[r:SEMANTIC_SIMILARITY {
                                similarity_score: $similarity,
                                threshold: $threshold,
                                computed_at: datetime()
                            }]->(p2)
                            RETURN count(r) as count
                        """, paper_id_1=paper_id_1, paper_id_2=paper_id_2, 
                            similarity=similarity, threshold=threshold)
                        
                        relationships_created += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"  Processed {i + 1}/{len(paper_ids)} papers...")
            
            logger.info(f"✅ Created {relationships_created} semantic similarity relationships")
    
    def compute_centrality(self):
        """
        Compute graph centrality measures for papers
        Uses NetworkX for computation, stores results in Neo4j
        """
        logger.info("=" * 70)
        logger.info("Computing Graph Centrality Measures")
        logger.info("=" * 70)
        
        # Build NetworkX graph from Neo4j
        G = nx.DiGraph()
        
        with self.driver.session() as session:
            # Get all papers
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_id IS NOT NULL
                RETURN p.paper_id as paper_id
            """).data()
            
            paper_ids = [p['paper_id'] for p in papers]
            G.add_nodes_from(paper_ids)
            
            # Get all relationships
            relationships = session.run("""
                MATCH (p1:Paper)-[r]->(p2:Paper)
                WHERE p1.paper_id IS NOT NULL AND p2.paper_id IS NOT NULL
                RETURN p1.paper_id as source, p2.paper_id as target, type(r) as rel_type
            """).data()
            
            for rel in relationships:
                G.add_edge(rel['source'], rel['target'])
            
            logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            # Compute centrality measures
            logger.info("Computing PageRank...")
            pagerank = nx.pagerank(G)
            
            logger.info("Computing Betweenness Centrality...")
            betweenness = nx.betweenness_centrality(G)
            
            logger.info("Computing Closeness Centrality...")
            closeness = nx.closeness_centrality(G)
            
            logger.info("Computing Degree Centrality...")
            degree = nx.degree_centrality(G)
            
            # Store in Neo4j
            logger.info("Storing centrality measures in Neo4j...")
            for paper_id in paper_ids:
                session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})
                    SET p.pagerank = $pagerank,
                        p.betweenness = $betweenness,
                        p.closeness = $closeness,
                        p.degree_centrality = $degree,
                        p.centrality_computed_at = datetime()
                """, paper_id=paper_id,
                    pagerank=pagerank.get(paper_id, 0.0),
                    betweenness=betweenness.get(paper_id, 0.0),
                    closeness=closeness.get(paper_id, 0.0),
                    degree=degree.get(paper_id, 0.0))
            
            logger.info("✅ Centrality measures computed and stored")
            
            # Print top papers by each measure
            logger.info("\n📊 Top Papers by Centrality:")
            logger.info("PageRank:")
            for paper_id, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"  {paper_id}: {score:.4f}")
            
            logger.info("\nBetweenness Centrality:")
            for paper_id, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"  {paper_id}: {score:.4f}")
    
    def detect_communities(self):
        """
        Detect research communities using Louvain algorithm
        Stores community_id in Neo4j
        """
        logger.info("=" * 70)
        logger.info("Detecting Research Communities")
        logger.info("=" * 70)
        
        # Build undirected graph for community detection
        G = nx.Graph()
        
        with self.driver.session() as session:
            # Get all papers
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_id IS NOT NULL
                RETURN p.paper_id as paper_id
            """).data()
            
            paper_ids = [p['paper_id'] for p in papers]
            G.add_nodes_from(paper_ids)
            
            # Get all relationships (undirected)
            relationships = session.run("""
                MATCH (p1:Paper)-[r]->(p2:Paper)
                WHERE p1.paper_id IS NOT NULL AND p2.paper_id IS NOT NULL
                RETURN p1.paper_id as source, p2.paper_id as target
            """).data()
            
            for rel in relationships:
                G.add_edge(rel['source'], rel['target'])
            
            logger.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
            
            # Detect communities using Louvain algorithm
            try:
                import community.community_louvain as community_louvain
                communities = community_louvain.best_partition(G)
            except ImportError:
                logger.warning("⚠️  python-louvain not installed, using NetworkX greedy_modularity")
                from networkx.algorithms import community
                communities_dict = community.greedy_modularity_communities(G)
                communities = {}
                for comm_id, comm in enumerate(communities_dict):
                    for node in comm:
                        communities[node] = comm_id
            
            logger.info(f"Found {len(set(communities.values()))} communities")
            
            # Store in Neo4j
            logger.info("Storing community assignments in Neo4j...")
            for paper_id, community_id in communities.items():
                session.run("""
                    MATCH (p:Paper {paper_id: $paper_id})
                    SET p.community_id = $community_id,
                        p.community_detected_at = datetime()
                """, paper_id=paper_id, community_id=community_id)
            
            logger.info("✅ Community detection complete")
            
            # Print community sizes
            from collections import Counter
            community_sizes = Counter(communities.values())
            logger.info("\n📊 Community Sizes:")
            for comm_id, size in sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
                logger.info(f"  Community {comm_id}: {size} papers")
    
    def identify_research_gaps(self):
        """
        Identify research gaps using network analysis
        """
        logger.info("=" * 70)
        logger.info("Identifying Research Gaps")
        logger.info("=" * 70)
        
        with self.driver.session() as session:
            # 1. Isolated papers (few connections)
            isolated = session.run("""
                MATCH (p:Paper)-[r]->(:Paper)
                WITH p, count(r) as connections
                WHERE connections < 2
                RETURN p.paper_id as paper_id, connections
                ORDER BY connections
            """).data()
            
            logger.info(f"\n📊 Isolated Papers (few connections): {len(isolated)}")
            for paper in isolated[:10]:
                logger.info(f"  {paper['paper_id']}: {paper['connections']} connections")
            
            # 2. Theory-Method gaps
            gaps = session.run("""
                MATCH (t:Theory), (m:Method)
                WHERE NOT EXISTS {
                    MATCH (p:Paper)-[:USES_THEORY]->(t)
                    MATCH (p)-[:USES_METHOD]->(m)
                }
                WITH t, m, 
                     count{(p:Paper)-[:USES_THEORY]->(t)} as theory_usage,
                     count{(p:Paper)-[:USES_METHOD]->(m)} as method_usage
                WHERE theory_usage > 0 AND method_usage > 0
                RETURN t.name as theory, m.name as method, theory_usage, method_usage
                ORDER BY theory_usage * method_usage DESC
                LIMIT 10
            """).data()
            
            logger.info(f"\n📊 Theory-Method Gaps (potential research opportunities): {len(gaps)}")
            for gap in gaps:
                logger.info(f"  Theory: {gap['theory']}, Method: {gap['method']}")
                logger.info(f"    Theory used in {gap['theory_usage']} papers, Method in {gap['method_usage']} papers")
    
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()

if __name__ == "__main__":
    features = AdvancedPaperFeatures()
    
    try:
        # Run all features
        features.generate_embeddings()
        features.compute_semantic_similarity(threshold=0.7)
        features.compute_centrality()
        features.detect_communities()
        features.identify_research_gaps()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ All advanced features computed successfully!")
        logger.info("=" * 70)
    
    finally:
        features.close()

