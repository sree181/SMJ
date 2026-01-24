#!/usr/bin/env python3
"""
Advanced Multi-Dimensional Knowledge Graph Connector
Production-grade system for connecting papers across multiple dimensions
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import networkx as nx
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetadata:
    """Metadata for paper connections"""
    connection_id: str
    source_paper: str
    target_paper: str
    connection_type: str
    strength: float
    confidence: float
    evidence: List[str]
    context: str
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class EntityNode:
    """Normalized entity for cross-paper connections"""
    entity_id: str
    name: str
    entity_type: str
    normalized_name: str
    aliases: List[str]
    description: str
    first_appearance: str
    frequency: int
    papers: List[str]

class AdvancedKnowledgeConnector:
    """Advanced system for creating multi-dimensional paper connections"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, openai_api_key: str):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.openai_api_key = openai_api_key
        
        # Initialize connections
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.llm_client = OpenAI(api_key=openai_api_key)
        
        # Initialize ML components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2
        )
        
        # Connection tracking
        self.connection_cache = {}
        self.entity_registry = {}
        
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def normalize_entity_name(self, name: str) -> str:
        """Normalize entity names for consistent matching"""
        # Remove special characters and normalize
        normalized = name.lower().strip()
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())
        return normalized
    
    def extract_entities_advanced(self, text: str, paper_id: str) -> List[EntityNode]:
        """Advanced entity extraction using LLM with normalization"""
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        prompt = f"""
        Extract and normalize all important entities from this research text. 
        Focus on theories, concepts, methodologies, frameworks, and key terms.
        
        Text: {text}
        
        For each entity, provide:
        1. Original name as it appears
        2. Normalized name (standardized form)
        3. Entity type (theory, concept, methodology, framework, construct, variable)
        4. Brief description
        5. Alternative names/aliases
        
        Return in this JSON format:
        {{
            "entities": [
                {{
                    "original_name": "exact text as it appears",
                    "normalized_name": "standardized form",
                    "entity_type": "theory|concept|methodology|framework|construct|variable",
                    "description": "brief description",
                    "aliases": ["alt1", "alt2"]
                }}
            ]
        }}
        
        Only return valid JSON, no additional text.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            
            data = json.loads(response.choices[0].message.content.strip())
            entities = []
            
            for entity_data in data.get("entities", []):
                entity = EntityNode(
                    entity_id=hashlib.md5(
                        f"{entity_data['normalized_name']}_{entity_data['entity_type']}".encode()
                    ).hexdigest()[:12],
                    name=entity_data['original_name'],
                    entity_type=entity_data['entity_type'],
                    normalized_name=entity_data['normalized_name'],
                    aliases=entity_data.get('aliases', []),
                    description=entity_data['description'],
                    first_appearance=paper_id,
                    frequency=1,
                    papers=[paper_id]
                )
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.warning(f"Entity extraction failed for {paper_id}: {e}")
            return []
    
    def merge_entities(self, entities: List[EntityNode]) -> Dict[str, EntityNode]:
        """Merge similar entities across papers"""
        entity_registry = {}
        
        for entity in entities:
            # Check for exact matches
            if entity.normalized_name in entity_registry:
                existing = entity_registry[entity.normalized_name]
                existing.frequency += 1
                existing.papers.extend(entity.papers)
                existing.aliases.extend(entity.aliases)
                existing.aliases = list(set(existing.aliases))  # Remove duplicates
            else:
                # Check for fuzzy matches
                found_match = False
                for existing_name, existing_entity in entity_registry.items():
                    if self.calculate_entity_similarity(entity, existing_entity) > 0.8:
                        existing_entity.frequency += 1
                        existing_entity.papers.extend(entity.papers)
                        existing_entity.aliases.append(entity.normalized_name)
                        existing_entity.aliases = list(set(existing_entity.aliases))
                        found_match = True
                        break
                
                if not found_match:
                    entity_registry[entity.normalized_name] = entity
        
        return entity_registry
    
    def calculate_entity_similarity(self, entity1: EntityNode, entity2: EntityNode) -> float:
        """Calculate similarity between two entities"""
        # Check if they're the same type
        if entity1.entity_type != entity2.entity_type:
            return 0.0
        
        # Check name similarity
        name1 = entity1.normalized_name.lower()
        name2 = entity2.normalized_name.lower()
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return 0.9
        
        # Check aliases
        for alias1 in entity1.aliases:
            for alias2 in entity2.aliases:
                if alias1.lower() == alias2.lower():
                    return 0.8
        
        # Use TF-IDF similarity for partial matches
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([name1, name2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.0
    
    def create_entity_connections(self):
        """Phase 1: Create entity-level connections across papers"""
        logger.info("Phase 1: Creating entity-level connections")
        
        with self.driver.session() as session:
            # Get all papers with their content
            result = session.run("""
                MATCH (p:Paper)
                OPTIONAL MATCH (p)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                OPTIONAL MATCH (p)-[:USES_METHODOLOGY]->(m:Methodology)
                OPTIONAL MATCH (p)-[:REPORTS_FINDING]->(f:Finding)
                RETURN p.paper_id as paper_id, p.year as year,
                       collect(DISTINCT rq.question) as questions,
                       collect(DISTINCT m.method_type) as methods,
                       collect(DISTINCT f.finding) as findings
            """)
            
            all_entities = []
            paper_entities = {}
            
            for record in result:
                paper_id = record['paper_id']
                year = record['year']
                
                # Combine all text content
                combined_text = " ".join([
                    " ".join(record['questions'] or []),
                    " ".join(record['methods'] or []),
                    " ".join(record['findings'] or [])
                ])
                
                if combined_text.strip():
                    # Extract entities
                    entities = self.extract_entities_advanced(combined_text, paper_id)
                    all_entities.extend(entities)
                    paper_entities[paper_id] = entities
            
            # Merge similar entities
            logger.info(f"Extracted {len(all_entities)} entities, merging similar ones...")
            entity_registry = self.merge_entities(all_entities)
            logger.info(f"Created {len(entity_registry)} unique entities")
            
            # Store entities in Neo4j
            for entity in entity_registry.values():
                session.run("""
                    MERGE (e:Entity {entity_id: $entity_id})
                    SET e.name = $name,
                        e.entity_type = $entity_type,
                        e.normalized_name = $normalized_name,
                        e.aliases = $aliases,
                        e.description = $description,
                        e.frequency = $frequency,
                        e.papers = $papers
                """, entity_id=entity.entity_id,
                     name=entity.name,
                     entity_type=entity.entity_type,
                     normalized_name=entity.normalized_name,
                     aliases=entity.aliases,
                     description=entity.description,
                     frequency=entity.frequency,
                     papers=entity.papers)
            
            # Create paper-entity connections
            for paper_id, entities in paper_entities.items():
                for entity in entities:
                    # Find the merged entity
                    merged_entity = None
                    for merged in entity_registry.values():
                        if entity.normalized_name == merged.normalized_name:
                            merged_entity = merged
                            break
                    
                    if merged_entity:
                        session.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            MATCH (e:Entity {entity_id: $entity_id})
                            MERGE (p)-[:CONTAINS_ENTITY {
                                original_name: $original_name,
                                context: $context
                            }]->(e)
                        """, paper_id=paper_id,
                             entity_id=merged_entity.entity_id,
                             original_name=entity.name,
                             context="extracted")
            
            # Create entity-entity connections (shared entities)
            for entity1 in entity_registry.values():
                for entity2 in entity_registry.values():
                    if entity1.entity_id != entity2.entity_id:
                        # Check if they appear in same papers
                        shared_papers = set(entity1.papers) & set(entity2.papers)
                        if shared_papers:
                            similarity = self.calculate_entity_similarity(entity1, entity2)
                            if similarity > 0.7:
                                session.run("""
                                    MATCH (e1:Entity {entity_id: $entity1_id})
                                    MATCH (e2:Entity {entity_id: $entity2_id})
                                    MERGE (e1)-[r:RELATED_ENTITY {
                                        similarity: $similarity,
                                        shared_papers: $shared_papers,
                                        connection_type: 'co_occurrence'
                                    }]->(e2)
                                """, entity1_id=entity1.entity_id,
                                     entity2_id=entity2.entity_id,
                                     similarity=similarity,
                                     shared_papers=list(shared_papers))
    
    def create_conceptual_connections(self):
        """Phase 2: Create conceptual connections between papers"""
        logger.info("Phase 2: Creating conceptual connections")
        
        with self.driver.session() as session:
            # Get papers with their entities
            result = session.run("""
                MATCH (p:Paper)-[:CONTAINS_ENTITY]->(e:Entity)
                RETURN p.paper_id as paper_id, p.year as year,
                       collect(DISTINCT e.entity_id) as entity_ids,
                       collect(DISTINCT e.entity_type) as entity_types
            """)
            
            paper_entities = {}
            for record in result:
                paper_entities[record['paper_id']] = {
                    'year': record['year'],
                    'entities': record['entity_ids'],
                    'types': record['entity_types']
                }
            
            # Create paper-to-paper connections based on shared entities
            paper_list = list(paper_entities.keys())
            connections_created = 0
            
            for i, paper1 in enumerate(paper_list):
                for paper2 in paper_list[i+1:]:
                    entities1 = set(paper_entities[paper1]['entities'])
                    entities2 = set(paper_entities[paper2]['entities'])
                    
                    shared_entities = entities1 & entities2
                    if shared_entities:
                        # Calculate conceptual similarity
                        jaccard_similarity = len(shared_entities) / len(entities1 | entities2)
                        
                        if jaccard_similarity > 0.1:  # Threshold for meaningful connection
                            connection_id = f"conceptual_{paper1}_{paper2}_{int(jaccard_similarity * 100)}"
                            
                            session.run("""
                                MATCH (p1:Paper {paper_id: $paper1})
                                MATCH (p2:Paper {paper_id: $paper2})
                                MERGE (p1)-[r:CONCEPTUALLY_RELATED {
                                    connection_id: $connection_id,
                                    similarity: $similarity,
                                    shared_entities: $shared_entities,
                                    connection_type: 'conceptual',
                                    strength: $strength,
                                    created_at: datetime()
                                }]->(p2)
                            """, paper1=paper1, paper2=paper2,
                                 connection_id=connection_id,
                                 similarity=jaccard_similarity,
                                 shared_entities=list(shared_entities),
                                 strength=jaccard_similarity)
                            
                            connections_created += 1
            
            logger.info(f"Created {connections_created} conceptual connections")
    
    def create_methodological_connections(self):
        """Phase 3: Create methodological connections"""
        logger.info("Phase 3: Creating methodological connections")
        
        with self.driver.session() as session:
            # Get papers with their methodologies
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                RETURN p.paper_id as paper_id, p.year as year,
                       collect(DISTINCT m.method_type) as method_types,
                       collect(DISTINCT m.analysis_technique) as techniques
            """)
            
            paper_methods = {}
            for record in result:
                paper_methods[record['paper_id']] = {
                    'year': record['year'],
                    'methods': record['method_types'],
                    'techniques': record['techniques']
                }
            
            # Create methodological connections
            paper_list = list(paper_methods.keys())
            connections_created = 0
            
            for i, paper1 in enumerate(paper_list):
                for paper2 in paper_list[i+1:]:
                    methods1 = set(paper_methods[paper1]['methods'])
                    methods2 = set(paper_methods[paper2]['methods'])
                    techniques1 = set(paper_methods[paper1]['techniques'])
                    techniques2 = set(paper_methods[paper2]['techniques'])
                    
                    # Calculate methodological similarity
                    method_similarity = len(methods1 & methods2) / len(methods1 | methods2) if (methods1 | methods2) else 0
                    technique_similarity = len(techniques1 & techniques2) / len(techniques1 | techniques2) if (techniques1 | techniques2) else 0
                    
                    overall_similarity = (method_similarity + technique_similarity) / 2
                    
                    if overall_similarity > 0.2:
                        connection_id = f"methodological_{paper1}_{paper2}_{int(overall_similarity * 100)}"
                        
                        session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})
                            MATCH (p2:Paper {paper_id: $paper2})
                            MERGE (p1)-[r:METHODOLOGICALLY_RELATED {
                                connection_id: $connection_id,
                                method_similarity: $method_similarity,
                                technique_similarity: $technique_similarity,
                                overall_similarity: $overall_similarity,
                                shared_methods: $shared_methods,
                                shared_techniques: $shared_techniques,
                                connection_type: 'methodological',
                                strength: $strength,
                                created_at: datetime()
                            }]->(p2)
                        """, paper1=paper1, paper2=paper2,
                             connection_id=connection_id,
                             method_similarity=method_similarity,
                             technique_similarity=technique_similarity,
                             overall_similarity=overall_similarity,
                             shared_methods=list(methods1 & methods2),
                             shared_techniques=list(techniques1 & techniques2),
                             strength=overall_similarity)
                        
                        connections_created += 1
            
            logger.info(f"Created {connections_created} methodological connections")
    
    def create_temporal_connections(self):
        """Phase 4: Create temporal connections based on research evolution"""
        logger.info("Phase 4: Creating temporal connections")
        
        with self.driver.session() as session:
            # Get papers ordered by year
            result = session.run("""
                MATCH (p:Paper)
                RETURN p.paper_id as paper_id, p.year as year
                ORDER BY p.year
            """)
            
            papers_by_year = defaultdict(list)
            for record in result:
                papers_by_year[record['year']].append(record['paper_id'])
            
            # Create temporal connections
            years = sorted(papers_by_year.keys())
            connections_created = 0
            
            for i in range(len(years) - 1):
                current_year = years[i]
                next_year = years[i + 1]
                
                current_papers = papers_by_year[current_year]
                next_papers = papers_by_year[next_year]
                
                # Connect papers from consecutive years
                for paper1 in current_papers:
                    for paper2 in next_papers:
                        # Check if they share entities or methodologies
                        shared_check = session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})-[:CONTAINS_ENTITY]->(e:Entity)<-[:CONTAINS_ENTITY]-(p2:Paper {paper_id: $paper2})
                            RETURN count(e) as shared_entities
                        """, paper1=paper1, paper2=paper2)
                        
                        shared_entities = shared_check.single()['shared_entities']
                        
                        if shared_entities > 0:
                            connection_id = f"temporal_{paper1}_{paper2}_{current_year}_{next_year}"
                            
                            session.run("""
                                MATCH (p1:Paper {paper_id: $paper1})
                                MATCH (p2:Paper {paper_id: $paper2})
                                MERGE (p1)-[r:TEMPORALLY_RELATED {
                                    connection_id: $connection_id,
                                    year_gap: $year_gap,
                                    shared_entities: $shared_entities,
                                    connection_type: 'temporal',
                                    strength: $strength,
                                    created_at: datetime()
                                }]->(p2)
                            """, paper1=paper1, paper2=paper2,
                                 connection_id=connection_id,
                                 year_gap=next_year - current_year,
                                 shared_entities=shared_entities,
                                 strength=min(shared_entities / 5.0, 1.0))
                            
                            connections_created += 1
            
            logger.info(f"Created {connections_created} temporal connections")
    
    def create_semantic_connections(self):
        """Phase 5: Create semantic connections using text similarity"""
        logger.info("Phase 5: Creating semantic connections")
        
        with self.driver.session() as session:
            # Get all paper content
            result = session.run("""
                MATCH (p:Paper)
                OPTIONAL MATCH (p)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                OPTIONAL MATCH (p)-[:USES_METHODOLOGY]->(m:Methodology)
                OPTIONAL MATCH (p)-[:REPORTS_FINDING]->(f:Finding)
                RETURN p.paper_id as paper_id,
                       collect(DISTINCT rq.question) as questions,
                       collect(DISTINCT m.method_type) as methods,
                       collect(DISTINCT f.finding) as findings
            """)
            
            paper_texts = {}
            paper_ids = []
            
            for record in result:
                paper_id = record['paper_id']
                combined_text = " ".join([
                    " ".join(record['questions'] or []),
                    " ".join(record['methods'] or []),
                    " ".join(record['findings'] or [])
                ])
                
                if combined_text.strip():
                    paper_texts[paper_id] = combined_text
                    paper_ids.append(paper_id)
            
            if len(paper_ids) < 2:
                logger.warning("Not enough papers for semantic analysis")
                return
            
            # Create TF-IDF vectors
            texts = [paper_texts[pid] for pid in paper_ids]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Create semantic connections
            connections_created = 0
            for i, paper1 in enumerate(paper_ids):
                for j, paper2 in enumerate(paper_ids[i+1:], i+1):
                    similarity = similarity_matrix[i][j]
                    
                    if similarity > 0.3:  # Threshold for semantic similarity
                        connection_id = f"semantic_{paper1}_{paper2}_{int(similarity * 100)}"
                        
                        session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})
                            MATCH (p2:Paper {paper_id: $paper2})
                            MERGE (p1)-[r:SEMANTICALLY_RELATED {
                                connection_id: $connection_id,
                                similarity: $similarity,
                                connection_type: 'semantic',
                                strength: $strength,
                                created_at: datetime()
                            }]->(p2)
                        """, paper1=paper1, paper2=paper2,
                             connection_id=connection_id,
                             similarity=similarity,
                             strength=similarity)
                        
                        connections_created += 1
            
            logger.info(f"Created {connections_created} semantic connections")
    
    def create_network_analysis(self):
        """Phase 6: Create network-level analysis and clusters"""
        logger.info("Phase 6: Creating network analysis")
        
        with self.driver.session() as session:
            # Build network graph
            G = nx.Graph()
            
            # Add nodes (papers)
            result = session.run("MATCH (p:Paper) RETURN p.paper_id as paper_id, p.year as year")
            for record in result:
                G.add_node(record['paper_id'], year=record['year'])
            
            # Add edges (connections)
            result = session.run("""
                MATCH (p1:Paper)-[r]->(p2:Paper)
                WHERE r.connection_type IN ['conceptual', 'methodological', 'temporal', 'semantic']
                RETURN p1.paper_id as paper1, p2.paper_id as paper2, 
                       r.connection_type as connection_type, r.strength as strength
            """)
            
            for record in result:
                G.add_edge(record['paper1'], record['paper2'], 
                          connection_type=record['connection_type'],
                          strength=record['strength'])
            
            # Calculate network metrics
            if G.number_of_nodes() > 0:
                # Centrality measures
                degree_centrality = nx.degree_centrality(G)
                betweenness_centrality = nx.betweenness_centrality(G)
                closeness_centrality = nx.closeness_centrality(G)
                
                # Store centrality measures
                for paper_id, centrality in degree_centrality.items():
                    session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        SET p.degree_centrality = $centrality
                    """, paper_id=paper_id, centrality=centrality)
                
                for paper_id, centrality in betweenness_centrality.items():
                    session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        SET p.betweenness_centrality = $centrality
                    """, paper_id=paper_id, centrality=centrality)
                
                for paper_id, centrality in closeness_centrality.items():
                    session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        SET p.closeness_centrality = $centrality
                    """, paper_id=paper_id, centrality=centrality)
                
                # Community detection
                try:
                    communities = nx.community.greedy_modularity_communities(G)
                    for i, community in enumerate(communities):
                        for paper_id in community:
                            session.run("""
                                MATCH (p:Paper {paper_id: $paper_id})
                                SET p.community_id = $community_id
                            """, paper_id=paper_id, community_id=i)
                except:
                    logger.warning("Community detection failed")
                
                logger.info(f"Network analysis completed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    def run_full_connection_analysis(self):
        """Run all phases of connection analysis"""
        logger.info("Starting full multi-dimensional connection analysis")
        
        try:
            self.create_entity_connections()
            self.create_conceptual_connections()
            self.create_methodological_connections()
            self.create_temporal_connections()
            self.create_semantic_connections()
            self.create_network_analysis()
            
            logger.info("✅ Full connection analysis completed successfully")
            
            # Generate summary report
            self.generate_connection_report()
            
        except Exception as e:
            logger.error(f"Connection analysis failed: {e}")
            raise
    
    def generate_connection_report(self):
        """Generate a comprehensive connection report"""
        with self.driver.session() as session:
            # Get connection statistics
            result = session.run("""
                MATCH ()-[r]->()
                WHERE r.connection_type IN ['conceptual', 'methodological', 'temporal', 'semantic']
                RETURN r.connection_type as type, count(r) as count
            """)
            
            connection_stats = {}
            for record in result:
                connection_stats[record['type']] = record['count']
            
            # Get entity statistics
            result = session.run("MATCH (e:Entity) RETURN count(e) as entity_count")
            entity_count = result.single()['entity_count']
            
            # Get paper statistics
            result = session.run("MATCH (p:Paper) RETURN count(p) as paper_count")
            paper_count = result.single()['paper_count']
            
            logger.info("\n" + "="*60)
            logger.info("📊 CONNECTION ANALYSIS REPORT")
            logger.info("="*60)
            logger.info(f"📄 Total Papers: {paper_count}")
            logger.info(f"🔗 Total Entities: {entity_count}")
            logger.info(f"🔗 Total Connections: {sum(connection_stats.values())}")
            logger.info("\nConnection Types:")
            for conn_type, count in connection_stats.items():
                logger.info(f"  - {conn_type.title()}: {count}")
            logger.info("="*60)

def main():
    load_dotenv()
    
    # Initialize connector
    connector = AdvancedKnowledgeConnector(
        neo4j_uri=os.getenv("NEO4J_URI"),
        neo4j_user=os.getenv("NEO4J_USER"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    try:
        # Test connection
        with connector.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        # Run full connection analysis
        connector.run_full_connection_analysis()
        
    finally:
        connector.close()

if __name__ == "__main__":
    main()
