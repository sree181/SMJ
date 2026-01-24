#!/usr/bin/env python3
"""
SMJ Literature Agent with OLLAMA Integration
Cost-effective research paper analysis using local OLLAMA models
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

import fitz  # PyMuPDF
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Import our OLLAMA client
from ollama_client import OllamaClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data structures
@dataclass
class ResearchEntity:
    id: str
    name: str
    type: str
    context: str
    paper_id: str
    section: str

@dataclass
class ResearchQuestion:
    id: str
    question: str
    question_type: str
    context: str
    paper_id: str
    section: str

@dataclass
class Methodology:
    id: str
    methodology: str
    method_type: str
    context: str
    paper_id: str
    section: str

@dataclass
class Finding:
    id: str
    finding: str
    finding_type: str
    context: str
    paper_id: str
    section: str

@dataclass
class Contribution:
    id: str
    contribution: str
    contribution_type: str
    context: str
    paper_id: str
    section: str

@dataclass
class Relationship:
    id: str
    source: str
    target: str
    relationship_type: str
    context: str
    paper_id: str
    section: str

@dataclass
class PaperMetadata:
    paper_id: str
    year: int
    volume: Optional[str]
    issue: Optional[str]
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    doi: Optional[str]

class PDFProcessor:
    """Handles PDF text extraction and section identification using OLLAMA"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def identify_sections_ollama(self, text: str) -> Dict[str, str]:
        """Use OLLAMA to identify and extract sections from paper text"""
        if len(text) > 15000:  # Truncate very long texts
            text = text[:15000] + "..."
        
        try:
            sections = self.ollama_client.identify_sections(text)
            # Filter out null values and clean up
            return {k: v for k, v in sections.items() if v and v != "null"}
        except Exception as e:
            logger.warning(f"Failed to identify sections with OLLAMA: {e}")
            return {"full_text": text}
    
    def extract_metadata_from_filename(self, filename: str) -> Tuple[int, Optional[str], Optional[str]]:
        """Extract year, volume, issue from filename like '1988_305.pdf'"""
        match = re.match(r'(\d{4})_(\d+)(?:_(\d+))?\.pdf', filename)
        if match:
            year = int(match.group(1))
            volume = match.group(2)
            issue = match.group(3) if match.group(3) else None
            return year, volume, issue
        return None, None, None

class OllamaExtractor:
    """Uses OLLAMA to extract research entities, questions, methodology, findings, and contributions"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    def extract_research_questions(self, text: str, section: str, paper_id: str) -> List[ResearchQuestion]:
        """Extract research questions using OLLAMA"""
        try:
            questions_data = self.ollama_client.extract_research_questions(text, section, paper_id)
            questions = []
            
            for i, q_data in enumerate(questions_data):
                question = ResearchQuestion(
                    id=f"{paper_id}_q_{hash(q_data.get('question', '')) % 10000}",
                    question=q_data.get('question', ''),
                    question_type=q_data.get('question_type', 'what'),
                    context=q_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                questions.append(question)
            
            return questions
        except Exception as e:
            logger.error(f"Error extracting research questions: {e}")
            return []
    
    def extract_methodology(self, text: str, section: str, paper_id: str) -> List[Methodology]:
        """Extract methodology using OLLAMA"""
        try:
            methodologies_data = self.ollama_client.extract_methodology(text, section, paper_id)
            methodologies = []
            
            for i, m_data in enumerate(methodologies_data):
                methodology = Methodology(
                    id=f"{paper_id}_m_{hash(m_data.get('methodology', '')) % 10000}",
                    methodology=m_data.get('methodology', ''),
                    method_type=m_data.get('method_type', 'mixed'),
                    context=m_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                methodologies.append(methodology)
            
            return methodologies
        except Exception as e:
            logger.error(f"Error extracting methodology: {e}")
            return []
    
    def extract_findings(self, text: str, section: str, paper_id: str) -> List[Finding]:
        """Extract findings using OLLAMA"""
        try:
            findings_data = self.ollama_client.extract_findings(text, section, paper_id)
            findings = []
            
            for i, f_data in enumerate(findings_data):
                finding = Finding(
                    id=f"{paper_id}_f_{hash(f_data.get('finding', '')) % 10000}",
                    finding=f_data.get('finding', ''),
                    finding_type=f_data.get('finding_type', 'empirical'),
                    context=f_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                findings.append(finding)
            
            return findings
        except Exception as e:
            logger.error(f"Error extracting findings: {e}")
            return []
    
    def extract_contributions(self, text: str, section: str, paper_id: str) -> List[Contribution]:
        """Extract contributions using OLLAMA"""
        try:
            contributions_data = self.ollama_client.extract_contributions(text, section, paper_id)
            contributions = []
            
            for i, c_data in enumerate(contributions_data):
                contribution = Contribution(
                    id=f"{paper_id}_c_{hash(c_data.get('contribution', '')) % 10000}",
                    contribution=c_data.get('contribution', ''),
                    contribution_type=c_data.get('contribution_type', 'theoretical'),
                    context=c_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                contributions.append(contribution)
            
            return contributions
        except Exception as e:
            logger.error(f"Error extracting contributions: {e}")
            return []
    
    def extract_entities(self, text: str, section: str, paper_id: str) -> List[ResearchEntity]:
        """Extract entities using OLLAMA"""
        try:
            entities_data = self.ollama_client.extract_entities(text, section, paper_id)
            entities = []
            
            for i, e_data in enumerate(entities_data):
                entity = ResearchEntity(
                    id=f"{paper_id}_e_{hash(e_data.get('name', '')) % 10000}",
                    name=e_data.get('name', ''),
                    type=e_data.get('type', 'concept'),
                    context=e_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                entities.append(entity)
            
            return entities
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def extract_relationships(self, text: str, section: str, paper_id: str) -> List[Relationship]:
        """Extract relationships using OLLAMA"""
        try:
            relationships_data = self.ollama_client.extract_relationships(text, section, paper_id)
            relationships = []
            
            for i, r_data in enumerate(relationships_data):
                relationship = Relationship(
                    id=f"{paper_id}_r_{i}",
                    source=r_data.get('source', ''),
                    target=r_data.get('target', ''),
                    relationship_type=r_data.get('relationship_type', 'relates_to'),
                    context=r_data.get('context', ''),
                    paper_id=paper_id,
                    section=section
                )
                relationships.append(relationship)
            
            return relationships
        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []

class KnowledgeGraphBuilder:
    """Builds and manages the Neo4j knowledge graph"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        """Close the database connection"""
        self.driver.close()
    
    def add_paper(self, metadata: PaperMetadata):
        """Add a paper to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (p:Paper {paper_id: $paper_id})
                SET p.year = $year, p.volume = $volume, p.issue = $issue,
                    p.title = $title, p.authors = $authors, p.abstract = $abstract,
                    p.keywords = $keywords, p.doi = $doi
            """, paper_id=metadata.paper_id, year=metadata.year, volume=metadata.volume,
                issue=metadata.issue, title=metadata.title, authors=metadata.authors,
                abstract=metadata.abstract, keywords=metadata.keywords, doi=metadata.doi)
    
    def add_research_question(self, question: ResearchQuestion):
        """Add a research question to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (q:ResearchQuestion {id: $id})
                SET q.question = $question, q.question_type = $question_type,
                    q.context = $context, q.paper_id = $paper_id, q.section = $section
                WITH q
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (q)-[:HAS_QUESTION]->(p)
            """, id=question.id, question=question.question, question_type=question.question_type,
                context=question.context, paper_id=question.paper_id, section=question.section)
    
    def add_methodology(self, methodology: Methodology):
        """Add a methodology to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (m:Methodology {id: $id})
                SET m.methodology = $methodology, m.method_type = $method_type,
                    m.context = $context, m.paper_id = $paper_id, m.section = $section
                WITH m
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (m)-[:HAS_METHODOLOGY]->(p)
            """, id=methodology.id, methodology=methodology.methodology, 
                method_type=methodology.method_type, context=methodology.context,
                paper_id=methodology.paper_id, section=methodology.section)
    
    def add_finding(self, finding: Finding):
        """Add a finding to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (f:Finding {id: $id})
                SET f.finding = $finding, f.finding_type = $finding_type,
                    f.context = $context, f.paper_id = $paper_id, f.section = $section
                WITH f
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (f)-[:HAS_FINDING]->(p)
            """, id=finding.id, finding=finding.finding, finding_type=finding.finding_type,
                context=finding.context, paper_id=finding.paper_id, section=finding.section)
    
    def add_contribution(self, contribution: Contribution):
        """Add a contribution to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Contribution {id: $id})
                SET c.contribution = $contribution, c.contribution_type = $contribution_type,
                    c.context = $context, c.paper_id = $paper_id, c.section = $section
                WITH c
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (c)-[:HAS_CONTRIBUTION]->(p)
            """, id=contribution.id, contribution=contribution.contribution,
                contribution_type=contribution.contribution_type, context=contribution.context,
                paper_id=contribution.paper_id, section=contribution.section)
    
    def add_entity(self, entity: ResearchEntity):
        """Add an entity to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MERGE (e:Entity {id: $id})
                SET e.name = $name, e.type = $type, e.context = $context,
                    e.paper_id = $paper_id, e.section = $section
                WITH e
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (e)-[:HAS_ENTITY]->(p)
            """, id=entity.id, name=entity.name, type=entity.type, context=entity.context,
                paper_id=entity.paper_id, section=entity.section)
    
    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the knowledge graph"""
        with self.driver.session() as session:
            session.run("""
                MATCH (source:Entity {name: $source})
                MATCH (target:Entity {name: $target})
                MERGE (source)-[r:RELATES_TO {id: $id}]->(target)
                SET r.relationship_type = $relationship_type, r.context = $context,
                    r.paper_id = $paper_id, r.section = $section
            """, id=relationship.id, source=relationship.source, target=relationship.target,
                relationship_type=relationship.relationship_type, context=relationship.context,
                paper_id=relationship.paper_id, section=relationship.section)

class LiteratureAgentOllama:
    """Main literature agent using OLLAMA for cost-effective processing"""
    
    def __init__(self, neo4j_uri: str = None,
                 neo4j_user: str = None, neo4j_password: str = None,
                 ollama_model: str = "llama3.1:8b"):
        
        # Use environment variables if not provided
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        if neo4j_user is None:
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        if neo4j_password is None:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize OLLAMA client
        self.ollama_client = OllamaClient(model=ollama_model)
        
        # Initialize components
        self.pdf_processor = PDFProcessor(self.ollama_client)
        self.entity_extractor = OllamaExtractor(self.ollama_client)
        self.knowledge_graph = KnowledgeGraphBuilder(neo4j_uri, neo4j_user, neo4j_password)
    
    def process_single_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single paper with comprehensive extraction"""
        paper_id = pdf_path.stem
        logger.info(f"Processing paper: {paper_id}")
        
        # Extract text
        text = self.pdf_processor.extract_text_from_pdf(pdf_path)
        if not text:
            raise Exception(f"Failed to extract text from {pdf_path}")
        
        # Identify sections
        sections = self.pdf_processor.identify_sections_ollama(text)
        
        # Extract metadata
        year, volume, issue = self.pdf_processor.extract_metadata_from_filename(pdf_path.name)
        
        metadata = PaperMetadata(
            paper_id=paper_id,
            year=year or 0,
            volume=volume,
            issue=issue,
            title="",  # Could be enhanced with title extraction
            authors=[],  # Could be enhanced with author extraction
            abstract=sections.get('abstract', ''),
            keywords=[],  # Could be enhanced with keyword extraction
            doi=None
        )
        
        # Extract entities and relationships using OLLAMA
        all_questions = []
        all_methodologies = []
        all_findings = []
        all_contributions = []
        all_entities = []
        all_relationships = []
        
        for section_name, section_text in sections.items():
            logger.info(f"Extracting from {section_name} section...")
            
            # Extract research questions
            questions = self.entity_extractor.extract_research_questions(section_text, section_name, paper_id)
            all_questions.extend(questions)
            
            # Extract methodology
            methodologies = self.entity_extractor.extract_methodology(section_text, section_name, paper_id)
            all_methodologies.extend(methodologies)
            
            # Extract findings
            findings = self.entity_extractor.extract_findings(section_text, section_name, paper_id)
            all_findings.extend(findings)
            
            # Extract contributions
            contributions = self.entity_extractor.extract_contributions(section_text, section_name, paper_id)
            all_contributions.extend(contributions)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(section_text, section_name, paper_id)
            all_entities.extend(entities)
            
            # Extract relationships
            relationships = self.entity_extractor.extract_relationships(section_text, section_name, paper_id)
            all_relationships.extend(relationships)
        
        return {
            'metadata': metadata,
            'questions': all_questions,
            'methodologies': all_methodologies,
            'findings': all_findings,
            'contributions': all_contributions,
            'entities': all_entities,
            'relationships': all_relationships
        }
    
    def build_knowledge_graph(self, extraction_result: Dict[str, Any]):
        """Add extracted data to the knowledge graph"""
        metadata = extraction_result['metadata']
        
        # Add paper
        self.knowledge_graph.add_paper(metadata)
        
        # Add all entities
        for question in extraction_result['questions']:
            self.knowledge_graph.add_research_question(question)
        
        for methodology in extraction_result['methodologies']:
            self.knowledge_graph.add_methodology(methodology)
        
        for finding in extraction_result['findings']:
            self.knowledge_graph.add_finding(finding)
        
        for contribution in extraction_result['contributions']:
            self.knowledge_graph.add_contribution(contribution)
        
        for entity in extraction_result['entities']:
            self.knowledge_graph.add_entity(entity)
        
        for relationship in extraction_result['relationships']:
            self.knowledge_graph.add_relationship(relationship)
    
    def process_and_ingest(self, pdf_path: Path):
        """Process a paper and ingest into knowledge graph"""
        try:
            result = self.process_single_paper(pdf_path)
            self.build_knowledge_graph(result)
            logger.info(f"✓ Successfully processed and ingested {pdf_path.name}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to process {pdf_path.name}: {e}")
            raise

def main():
    """Test the OLLAMA-based literature agent"""
    # Test OLLAMA connection
    if not OllamaClient().extract_with_retry("Test connection"):
        print("❌ OLLAMA not available. Please install and start OLLAMA first.")
        return
    
    # Initialize agent
    agent = LiteratureAgentOllama()
    
    # Test with a sample paper
    pdf_files = list(Path(".").glob("*.pdf"))
    if pdf_files:
        test_paper = pdf_files[0]
        print(f"Testing with: {test_paper.name}")
        
        try:
            result = agent.process_and_ingest(test_paper)
            print(f"✓ Successfully processed {test_paper.name}")
            print(f"  Questions: {len(result['questions'])}")
            print(f"  Methodologies: {len(result['methodologies'])}")
            print(f"  Findings: {len(result['findings'])}")
            print(f"  Contributions: {len(result['contributions'])}")
            print(f"  Entities: {len(result['entities'])}")
            print(f"  Relationships: {len(result['relationships'])}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("No PDF files found for testing")

if __name__ == "__main__":
    main()
