#!/usr/bin/env python3
"""
Generate Embeddings for All Nodes
Creates vector embeddings for Papers, Theories, Phenomena, Methods, Research Questions, etc.
Prepares the database for Graph RAG
"""

import os
import logging
import numpy as np
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from tqdm import tqdm

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate and store embeddings for all entity types"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        self.embedding_dim = 384
        logger.info("✓ Embedding model loaded")
    
    def generate_paper_embeddings(self, batch_size: int = 100):
        """Generate embeddings for all papers"""
        logger.info("=" * 80)
        logger.info("GENERATING PAPER EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            # Get all papers
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NOT NULL OR p.abstract IS NOT NULL
                RETURN p.paper_id as paper_id,
                       COALESCE(p.title, '') as title,
                       COALESCE(p.abstract, '') as abstract
            """)
            
            papers = list(result)
            logger.info(f"Found {len(papers)} papers to process")
            
            processed = 0
            skipped = 0
            
            for i in range(0, len(papers), batch_size):
                batch = papers[i:i+batch_size]
                
                # Prepare texts for embedding
                texts = []
                paper_ids = []
                
                for record in batch:
                    paper_id = record['paper_id']
                    title = record['title'] or ''
                    abstract = record['abstract'] or ''
                    
                    # Combine title and abstract (limit to 3000 chars for efficiency)
                    paper_text = f"{title}. {abstract}"[:3000].strip()
                    
                    if paper_text:
                        texts.append(paper_text)
                        paper_ids.append(paper_id)
                    else:
                        skipped += 1
                
                if not texts:
                    continue
                
                # Generate embeddings in batch
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    # Store in Neo4j
                    for j, paper_id in enumerate(paper_ids):
                        embedding_list = embeddings[j].tolist()
                        
                        session.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            SET p.embedding = $embedding,
                                p.embedding_model = 'all-MiniLM-L6-v2',
                                p.embedding_dim = $dim,
                                p.embedding_updated_at = datetime()
                        """, 
                        paper_id=paper_id,
                        embedding=embedding_list,
                        dim=self.embedding_dim)
                        
                        processed += 1
                    
                    if (i + batch_size) % 500 == 0:
                        logger.info(f"  Processed {processed}/{len(papers)} papers...")
                
                except Exception as e:
                    logger.error(f"Error processing batch {i}: {e}")
                    continue
            
            logger.info(f"✓ Generated embeddings for {processed} papers")
            if skipped > 0:
                logger.info(f"  Skipped {skipped} papers (no text)")
    
    def generate_theory_embeddings(self, batch_size: int = 100):
        """Generate embeddings for all theories"""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING THEORY EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)
                RETURN t.name as name,
                       COALESCE(t.description, '') as description
            """)
            
            theories = list(result)
            logger.info(f"Found {len(theories)} theories to process")
            
            processed = 0
            
            for i in range(0, len(theories), batch_size):
                batch = theories[i:i+batch_size]
                
                texts = []
                theory_names = []
                
                for record in batch:
                    name = record['name'] or ''
                    description = record['description'] or ''
                    theory_text = f"{name}. {description}".strip()
                    
                    if theory_text:
                        texts.append(theory_text)
                        theory_names.append(name)
                
                if not texts:
                    continue
                
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    for j, theory_name in enumerate(theory_names):
                        embedding_list = embeddings[j].tolist()
                        
                        session.run("""
                            MATCH (t:Theory {name: $name})
                            SET t.embedding = $embedding,
                                t.embedding_model = 'all-MiniLM-L6-v2',
                                t.embedding_dim = $dim,
                                t.embedding_updated_at = datetime()
                        """,
                        name=theory_name,
                        embedding=embedding_list,
                        dim=self.embedding_dim)
                        
                        processed += 1
                
                except Exception as e:
                    logger.error(f"Error processing batch {i}: {e}")
                    continue
            
            logger.info(f"✓ Generated embeddings for {processed} theories")
    
    def generate_phenomenon_embeddings(self, batch_size: int = 100):
        """Generate embeddings for all phenomena"""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING PHENOMENON EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (ph:Phenomenon)
                RETURN ph.phenomenon_name as name,
                       COALESCE(ph.description, '') as description,
                       COALESCE(ph.context, '') as context
            """)
            
            phenomena = list(result)
            logger.info(f"Found {len(phenomena)} phenomena to process")
            
            processed = 0
            
            for i in range(0, len(phenomena), batch_size):
                batch = phenomena[i:i+batch_size]
                
                texts = []
                phenomenon_names = []
                
                for record in batch:
                    name = record['name'] or ''
                    description = record['description'] or ''
                    context = record['context'] or ''
                    phenomenon_text = f"{name}. {description}. {context}".strip()
                    
                    if phenomenon_text:
                        texts.append(phenomenon_text)
                        phenomenon_names.append(name)
                
                if not texts:
                    continue
                
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    for j, phenomenon_name in enumerate(phenomenon_names):
                        embedding_list = embeddings[j].tolist()
                        
                        session.run("""
                            MATCH (ph:Phenomenon {phenomenon_name: $name})
                            SET ph.embedding = $embedding,
                                ph.embedding_model = 'all-MiniLM-L6-v2',
                                ph.embedding_dim = $dim,
                                ph.embedding_updated_at = datetime()
                        """,
                        name=phenomenon_name,
                        embedding=embedding_list,
                        dim=self.embedding_dim)
                        
                        processed += 1
                
                except Exception as e:
                    logger.error(f"Error processing batch {i}: {e}")
                    continue
            
            logger.info(f"✓ Generated embeddings for {processed} phenomena")
    
    def generate_method_embeddings(self, batch_size: int = 100):
        """Generate embeddings for all methods"""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING METHOD EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Method)
                RETURN m.name as name,
                       COALESCE(m.type, '') as type,
                       COALESCE(m.sample_size, '') as sample_size,
                       COALESCE(m.time_period, '') as time_period
            """)
            
            methods = list(result)
            logger.info(f"Found {len(methods)} methods to process")
            
            processed = 0
            
            for i in range(0, len(methods), batch_size):
                batch = methods[i:i+batch_size]
                
                texts = []
                method_names = []
                
                for record in batch:
                    name = record['name'] or ''
                    method_type = record['type'] or ''
                    sample_size = record['sample_size'] or ''
                    time_period = record['time_period'] or ''
                    method_text = f"{name}. Type: {method_type}. Sample: {sample_size}. Period: {time_period}".strip()
                    
                    if method_text:
                        texts.append(method_text)
                        method_names.append(name)
                
                if not texts:
                    continue
                
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    for j, method_name in enumerate(method_names):
                        embedding_list = embeddings[j].tolist()
                        
                        session.run("""
                            MATCH (m:Method {name: $name})
                            SET m.embedding = $embedding,
                                m.embedding_model = 'all-MiniLM-L6-v2',
                                m.embedding_dim = $dim,
                                m.embedding_updated_at = datetime()
                        """,
                        name=method_name,
                        embedding=embedding_list,
                        dim=self.embedding_dim)
                        
                        processed += 1
                
                except Exception as e:
                    logger.error(f"Error processing batch {i}: {e}")
                    continue
            
            logger.info(f"✓ Generated embeddings for {processed} methods")
    
    def generate_research_question_embeddings(self, batch_size: int = 100):
        """Generate embeddings for all research questions"""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING RESEARCH QUESTION EMBEDDINGS")
        logger.info("=" * 80)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (rq:ResearchQuestion)
                WHERE rq.question IS NOT NULL AND rq.question <> ""
                RETURN rq.question_id as question_id,
                       rq.question as question
            """)
            
            questions = list(result)
            logger.info(f"Found {len(questions)} research questions to process")
            
            processed = 0
            
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                
                texts = []
                question_ids = []
                
                for record in batch:
                    question = record['question'] or ''
                    if question:
                        texts.append(question)
                        question_ids.append(record['question_id'])
                
                if not texts:
                    continue
                
                try:
                    embeddings = self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                    
                    for j, question_id in enumerate(question_ids):
                        embedding_list = embeddings[j].tolist()
                        
                        session.run("""
                            MATCH (rq:ResearchQuestion {question_id: $question_id})
                            SET rq.embedding = $embedding,
                                rq.embedding_model = 'all-MiniLM-L6-v2',
                                rq.embedding_dim = $dim,
                                rq.embedding_updated_at = datetime()
                        """,
                        question_id=question_id,
                        embedding=embedding_list,
                        dim=self.embedding_dim)
                        
                        processed += 1
                
                except Exception as e:
                    logger.error(f"Error processing batch {i}: {e}")
                    continue
            
            logger.info(f"✓ Generated embeddings for {processed} research questions")
    
    def generate_all_embeddings(self):
        """Generate embeddings for all entity types"""
        logger.info("=" * 80)
        logger.info("GENERATING EMBEDDINGS FOR ALL ENTITIES")
        logger.info("=" * 80)
        
        self.generate_paper_embeddings()
        self.generate_theory_embeddings()
        self.generate_phenomenon_embeddings()
        self.generate_method_embeddings()
        self.generate_research_question_embeddings()
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL EMBEDDINGS GENERATED")
        logger.info("=" * 80)
        
        # Summary
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                RETURN count(p) as count
            """)
            papers_with_emb = result.single()['count']
            
            result = session.run("""
                MATCH (t:Theory)
                WHERE t.embedding IS NOT NULL
                RETURN count(t) as count
            """)
            theories_with_emb = result.single()['count']
            
            result = session.run("""
                MATCH (ph:Phenomenon)
                WHERE ph.embedding IS NOT NULL
                RETURN count(ph) as count
            """)
            phenomena_with_emb = result.single()['count']
            
            result = session.run("""
                MATCH (m:Method)
                WHERE m.embedding IS NOT NULL
                RETURN count(m) as count
            """)
            methods_with_emb = result.single()['count']
            
            result = session.run("""
                MATCH (rq:ResearchQuestion)
                WHERE rq.embedding IS NOT NULL
                RETURN count(rq) as count
            """)
            questions_with_emb = result.single()['count']
            
            logger.info(f"\nEmbeddings Summary:")
            logger.info(f"  Papers: {papers_with_emb}")
            logger.info(f"  Theories: {theories_with_emb}")
            logger.info(f"  Phenomena: {phenomena_with_emb}")
            logger.info(f"  Methods: {methods_with_emb}")
            logger.info(f"  Research Questions: {questions_with_emb}")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    generator = EmbeddingGenerator()
    try:
        generator.generate_all_embeddings()
    finally:
        generator.close()
