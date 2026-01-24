"""
Literature Agent for Strategic Management Journal Analysis
Uses LLM-based extraction to analyze research papers section by section,
extract entities and relationships, and build a knowledge graph in Neo4j.
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import time

# PDF processing
import fitz  # PyMuPDF

# LLM Integration
import openai
from openai import OpenAI

# Knowledge Graph
from neo4j import GraphDatabase

# Data processing
import pandas as pd
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ResearchEntity:
    """Represents a research entity (theory, concept, methodology, etc.)"""
    name: str
    entity_type: str  # 'theory', 'methodology', 'concept', 'construct', 'variable', 'framework'
    description: str
    context: str
    section: str
    paper_id: str


@dataclass
class ResearchQuestion:
    """Represents a research question"""
    question: str
    question_type: str  # 'what', 'how', 'why', 'when', 'where', 'which'
    context: str
    section: str
    paper_id: str


@dataclass
class Methodology:
    """Represents research methodology details"""
    method_type: str  # 'quantitative', 'qualitative', 'mixed', 'experimental', 'case_study'
    data_source: str
    sample_size: Optional[int]
    analysis_technique: str
    research_design: str
    context: str
    section: str
    paper_id: str


@dataclass
class Finding:
    """Represents research findings"""
    finding: str
    finding_type: str  # 'positive', 'negative', 'neutral', 'mixed', 'significant', 'non_significant'
    significance: Optional[str]
    effect_size: Optional[str]
    context: str
    section: str
    paper_id: str


@dataclass
class Contribution:
    """Represents research contributions"""
    contribution: str
    contribution_type: str  # 'theoretical', 'empirical', 'methodological', 'practical', 'policy'
    impact: str
    context: str
    section: str
    paper_id: str


@dataclass
class Relationship:
    """Represents relationships between entities"""
    source_entity: str
    target_entity: str
    relationship_type: str  # 'uses', 'extends', 'contradicts', 'supports', 'builds_on'
    strength: str  # 'strong', 'moderate', 'weak'
    context: str
    section: str
    paper_id: str


@dataclass
class PaperMetadata:
    """Paper metadata extracted from filename and content"""
    paper_id: str
    year: int
    volume: Optional[str]
    issue: Optional[str]
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    doi: Optional[str]


class LLMClient:
    """Handles LLM interactions for text analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.max_retries = 3
        self.retry_delay = 1
    
    def extract_with_retry(self, prompt: str, max_tokens: int = 2000) -> str:
        """Extract information using LLM with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All LLM attempts failed: {e}")
                    return ""


class PDFProcessor:
    """Handles PDF text extraction and section identification using LLM"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
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
    
    def identify_sections_llm(self, text: str) -> Dict[str, str]:
        """Use LLM to identify and extract sections from paper text"""
        if len(text) > 15000:  # Truncate very long texts
            text = text[:15000] + "..."
        
        prompt = f"""
        Analyze this academic paper text and identify the main sections. Extract the content for each section.

        Text: {text}

        Please identify and extract the following sections (if present):
        1. Abstract
        2. Introduction
        3. Literature Review
        4. Methodology/Methods
        5. Results/Findings
        6. Discussion
        7. Conclusion

        For each section found, provide the content in this JSON format:
        {{
            "abstract": "content here or null if not found",
            "introduction": "content here or null if not found",
            "literature_review": "content here or null if not found",
            "methodology": "content here or null if not found",
            "results": "content here or null if not found",
            "discussion": "content here or null if not found",
            "conclusion": "content here or null if not found"
        }}

        Only return valid JSON, no additional text.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            sections = json.loads(response)
            # Filter out null values and clean up
            return {k: v for k, v in sections.items() if v and v != "null"}
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using fallback")
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


class LLMExtractor:
    """Uses LLM to extract research entities, questions, methodology, findings, and contributions"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def extract_research_questions(self, text: str, section: str, paper_id: str) -> List[ResearchQuestion]:
        """Extract research questions using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify all research questions.

        Text: {text}

        Extract research questions in this JSON format:
        {{
            "questions": [
                {{
                    "question": "the exact research question text",
                    "question_type": "what|how|why|when|where|which",
                    "context": "brief context around the question"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no research questions are found, return {{"questions": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            questions = []
            for q in data.get("questions", []):
                questions.append(ResearchQuestion(
                    question=q["question"],
                    question_type=q["question_type"],
                    context=q["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return questions
        except json.JSONDecodeError:
            logger.warning("Failed to parse research questions JSON")
            return []
    
    def extract_methodology(self, text: str, section: str, paper_id: str) -> List[Methodology]:
        """Extract methodology information using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify methodology details.

        Text: {text}

        Extract methodology information in this JSON format:
        {{
            "methodologies": [
                {{
                    "method_type": "quantitative|qualitative|mixed|experimental|case_study",
                    "data_source": "description of data source",
                    "sample_size": number or null,
                    "analysis_technique": "specific analysis techniques used",
                    "research_design": "description of research design",
                    "context": "brief context"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no methodology is found, return {{"methodologies": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            methodologies = []
            for m in data.get("methodologies", []):
                methodologies.append(Methodology(
                    method_type=m["method_type"],
                    data_source=m["data_source"],
                    sample_size=m.get("sample_size"),
                    analysis_technique=m["analysis_technique"],
                    research_design=m["research_design"],
                    context=m["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return methodologies
        except json.JSONDecodeError:
            logger.warning("Failed to parse methodology JSON")
            return []
    
    def extract_findings(self, text: str, section: str, paper_id: str) -> List[Finding]:
        """Extract research findings using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify research findings.

        Text: {text}

        Extract findings in this JSON format:
        {{
            "findings": [
                {{
                    "finding": "description of the finding",
                    "finding_type": "positive|negative|neutral|mixed|significant|non_significant",
                    "significance": "statistical significance if mentioned or null",
                    "effect_size": "effect size if mentioned or null",
                    "context": "brief context"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no findings are found, return {{"findings": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            findings = []
            for f in data.get("findings", []):
                findings.append(Finding(
                    finding=f["finding"],
                    finding_type=f["finding_type"],
                    significance=f.get("significance"),
                    effect_size=f.get("effect_size"),
                    context=f["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return findings
        except json.JSONDecodeError:
            logger.warning("Failed to parse findings JSON")
            return []
    
    def extract_contributions(self, text: str, section: str, paper_id: str) -> List[Contribution]:
        """Extract research contributions using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify research contributions.

        Text: {text}

        Extract contributions in this JSON format:
        {{
            "contributions": [
                {{
                    "contribution": "description of the contribution",
                    "contribution_type": "theoretical|empirical|methodological|practical|policy",
                    "impact": "description of the impact or significance",
                    "context": "brief context"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no contributions are found, return {{"contributions": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            contributions = []
            for c in data.get("contributions", []):
                contributions.append(Contribution(
                    contribution=c["contribution"],
                    contribution_type=c["contribution_type"],
                    impact=c["impact"],
                    context=c["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return contributions
        except json.JSONDecodeError:
            logger.warning("Failed to parse contributions JSON")
            return []
    
    def extract_entities(self, text: str, section: str, paper_id: str) -> List[ResearchEntity]:
        """Extract theories, concepts, and entities using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify important theories, concepts, frameworks, and entities.

        Text: {text}

        Extract entities in this JSON format:
        {{
            "entities": [
                {{
                    "name": "name of the theory/concept/entity",
                    "entity_type": "theory|concept|framework|construct|variable|methodology",
                    "description": "brief description of what it is",
                    "context": "brief context where it appears"
                }}
            ]
        }}

        Focus on:
        - Theoretical frameworks and models
        - Key concepts and constructs
        - Research methodologies
        - Important variables
        - Theoretical perspectives

        Only return valid JSON, no additional text. If no entities are found, return {{"entities": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            entities = []
            for e in data.get("entities", []):
                entities.append(ResearchEntity(
                    name=e["name"],
                    entity_type=e["entity_type"],
                    description=e["description"],
                    context=e["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return entities
        except json.JSONDecodeError:
            logger.warning("Failed to parse entities JSON")
            return []
    
    def extract_relationships(self, text: str, section: str, paper_id: str) -> List[Relationship]:
        """Extract relationships between entities using LLM"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify relationships between theories, concepts, and entities.

        Text: {text}

        Extract relationships in this JSON format:
        {{
            "relationships": [
                {{
                    "source_entity": "name of the source entity",
                    "target_entity": "name of the target entity",
                    "relationship_type": "uses|extends|contradicts|supports|builds_on|influences|relates_to",
                    "strength": "strong|moderate|weak",
                    "context": "brief context of the relationship"
                }}
            ]
        }}

        Look for relationships like:
        - Theory A extends Theory B
        - Concept X uses Methodology Y
        - Finding Z supports Theory W
        - Framework A builds on Framework B

        Only return valid JSON, no additional text. If no relationships are found, return {{"relationships": []}}.
        """
        
        response = self.llm_client.extract_with_retry(prompt)
        
        try:
            data = json.loads(response)
            relationships = []
            for r in data.get("relationships", []):
                relationships.append(Relationship(
                    source_entity=r["source_entity"],
                    target_entity=r["target_entity"],
                    relationship_type=r["relationship_type"],
                    strength=r["strength"],
                    context=r["context"],
                    section=section,
                    paper_id=paper_id
                ))
            return relationships
        except json.JSONDecodeError:
            logger.warning("Failed to parse relationships JSON")
            return []


class KnowledgeGraphBuilder:
    """Builds and manages the knowledge graph"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def create_constraints(self):
        """Create database constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
                "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                "CREATE CONSTRAINT research_question_unique IF NOT EXISTS FOR (rq:ResearchQuestion) REQUIRE rq.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint creation failed (may already exist): {e}")
    
    def add_paper(self, metadata: PaperMetadata):
        """Add paper node to the graph"""
        with self.driver.session() as session:
            query = """
            MERGE (p:Paper {paper_id: $paper_id})
            SET p.year = $year,
                p.volume = $volume,
                p.issue = $issue,
                p.title = $title,
                p.authors = $authors,
                p.abstract = $abstract,
                p.keywords = $keywords,
                p.doi = $doi
            """
            session.run(query, 
                       paper_id=metadata.paper_id,
                       year=metadata.year,
                       volume=metadata.volume,
                       issue=metadata.issue,
                       title=metadata.title,
                       authors=metadata.authors,
                       abstract=metadata.abstract,
                       keywords=metadata.keywords,
                       doi=metadata.doi)
    
    def add_research_question(self, question: ResearchQuestion):
        """Add research question node and link to paper"""
        with self.driver.session() as session:
            # Create research question node
            query = """
            MERGE (rq:ResearchQuestion {id: $id})
            SET rq.question = $question,
                rq.question_type = $question_type,
                rq.context = $context,
                rq.section = $section
            """
            question_id = f"{question.paper_id}_{hashlib.md5(question.question.encode()).hexdigest()[:8]}"
            session.run(query,
                       id=question_id,
                       question=question.question,
                       question_type=question.question_type,
                       context=question.context,
                       section=question.section)
            
            # Link to paper
            link_query = """
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (rq:ResearchQuestion {id: $question_id})
            MERGE (p)-[:HAS_RESEARCH_QUESTION]->(rq)
            """
            session.run(link_query, paper_id=question.paper_id, question_id=question_id)
    
    def add_methodology(self, methodology: Methodology):
        """Add methodology node and link to paper"""
        with self.driver.session() as session:
            query = """
            MERGE (m:Methodology {id: $id})
            SET m.method_type = $method_type,
                m.data_source = $data_source,
                m.sample_size = $sample_size,
                m.analysis_technique = $analysis_technique,
                m.context = $context,
                m.section = $section
            """
            method_id = f"{methodology.paper_id}_{hashlib.md5(methodology.context.encode()).hexdigest()[:8]}"
            session.run(query,
                       id=method_id,
                       method_type=methodology.method_type,
                       data_source=methodology.data_source,
                       sample_size=methodology.sample_size,
                       analysis_technique=methodology.analysis_technique,
                       context=methodology.context,
                       section=methodology.section)
            
            # Link to paper
            link_query = """
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (m:Methodology {id: $method_id})
            MERGE (p)-[:USES_METHODOLOGY]->(m)
            """
            session.run(link_query, paper_id=methodology.paper_id, method_id=method_id)
    
    def add_finding(self, finding: Finding):
        """Add finding node and link to paper"""
        with self.driver.session() as session:
            query = """
            MERGE (f:Finding {id: $id})
            SET f.finding = $finding,
                f.finding_type = $finding_type,
                f.significance = $significance,
                f.context = $context,
                f.section = $section
            """
            finding_id = f"{finding.paper_id}_{hashlib.md5(finding.finding.encode()).hexdigest()[:8]}"
            session.run(query,
                       id=finding_id,
                       finding=finding.finding,
                       finding_type=finding.finding_type,
                       significance=finding.significance,
                       context=finding.context,
                       section=finding.section)
            
            # Link to paper
            link_query = """
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (f:Finding {id: $finding_id})
            MERGE (p)-[:REPORTS_FINDING]->(f)
            """
            session.run(link_query, paper_id=finding.paper_id, finding_id=finding_id)
    
    def add_contribution(self, contribution: Contribution):
        """Add contribution node and link to paper"""
        with self.driver.session() as session:
            query = """
            MERGE (c:Contribution {id: $id})
            SET c.contribution = $contribution,
                c.contribution_type = $contribution_type,
                c.context = $context,
                c.section = $section
            """
            contrib_id = f"{contribution.paper_id}_{hashlib.md5(contribution.contribution.encode()).hexdigest()[:8]}"
            session.run(query,
                       id=contrib_id,
                       contribution=contribution.contribution,
                       contribution_type=contribution.contribution_type,
                       context=contribution.context,
                       section=contribution.section)
            
            # Link to paper
            link_query = """
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (c:Contribution {id: $contrib_id})
            MERGE (p)-[:MAKES_CONTRIBUTION]->(c)
            """
            session.run(link_query, paper_id=contribution.paper_id, contrib_id=contrib_id)
    
    def add_entity(self, entity: ResearchEntity):
        """Add entity node and link to paper"""
        with self.driver.session() as session:
            # Create entity node
            query = """
            MERGE (e:Entity {name: $name})
            SET e.entity_type = $entity_type,
                e.description = $description
            """
            session.run(query,
                       name=entity.name,
                       entity_type=entity.entity_type,
                       description=entity.description)
            
            # Link to paper
            link_query = """
            MATCH (p:Paper {paper_id: $paper_id})
            MATCH (e:Entity {name: $entity_name})
            MERGE (p)-[:MENTIONS_ENTITY {context: $context, section: $section}]->(e)
            """
            session.run(link_query,
                       paper_id=entity.paper_id,
                       entity_name=entity.name,
                       context=entity.context,
                       section=entity.section)
    
    def add_relationship(self, relationship: Relationship):
        """Add relationship between entities"""
        with self.driver.session() as session:
            # Ensure both entities exist
            entity_query = """
            MERGE (e1:Entity {name: $source_entity})
            MERGE (e2:Entity {name: $target_entity})
            """
            session.run(entity_query,
                       source_entity=relationship.source_entity,
                       target_entity=relationship.target_entity)
            
            # Create relationship
            rel_query = """
            MATCH (e1:Entity {name: $source_entity})
            MATCH (e2:Entity {name: $target_entity})
            MERGE (e1)-[r:RELATES_TO {
                relationship_type: $relationship_type,
                strength: $strength,
                context: $context,
                section: $section,
                paper_id: $paper_id
            }]->(e2)
            """
            session.run(rel_query,
                       source_entity=relationship.source_entity,
                       target_entity=relationship.target_entity,
                       relationship_type=relationship.relationship_type,
                       strength=relationship.strength,
                       context=relationship.context,
                       section=relationship.section,
                       paper_id=relationship.paper_id)


class LiteratureAgent:
    """Main literature agent that orchestrates the entire process"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j", neo4j_password: str = "password",
                 openai_api_key: Optional[str] = None, model: str = "gpt-4"):
        self.llm_client = LLMClient(openai_api_key, model)
        self.pdf_processor = PDFProcessor(self.llm_client)
        self.entity_extractor = LLMExtractor(self.llm_client)
        self.knowledge_graph = KnowledgeGraphBuilder(neo4j_uri, neo4j_user, neo4j_password)
        
    def process_single_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF paper and extract all information using LLM"""
        logger.info(f"Processing paper: {pdf_path.name}")
        
        # Extract text and sections
        text = self.pdf_processor.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return {}
        
        sections = self.pdf_processor.identify_sections_llm(text)
        
        # Extract metadata
        year, volume, issue = self.pdf_processor.extract_metadata_from_filename(pdf_path.name)
        paper_id = pdf_path.stem
        
        # Create paper metadata
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
        
        # Extract entities and relationships using LLM
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
    
    def process_bucket(self, bucket_path: Path) -> Dict[str, Any]:
        """Process all papers in a 5-year bucket"""
        logger.info(f"Processing bucket: {bucket_path.name}")
        
        pdf_files = list(bucket_path.glob("*.pdf"))
        bucket_results = {
            'bucket_name': bucket_path.name,
            'total_papers': len(pdf_files),
            'processed_papers': 0,
            'papers': []
        }
        
        for pdf_file in pdf_files:
            try:
                paper_data = self.process_single_paper(pdf_file)
                if paper_data:
                    bucket_results['papers'].append(paper_data)
                    bucket_results['processed_papers'] += 1
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
        
        return bucket_results
    
    def build_knowledge_graph(self, bucket_results: Dict[str, Any]):
        """Build knowledge graph from bucket results"""
        logger.info(f"Building knowledge graph for bucket: {bucket_results['bucket_name']}")
        
        for paper_data in bucket_results['papers']:
            # Add paper metadata
            self.knowledge_graph.add_paper(paper_data['metadata'])
            
            # Add research questions
            for question in paper_data['questions']:
                self.knowledge_graph.add_research_question(question)
            
            # Add methodologies
            for methodology in paper_data['methodologies']:
                self.knowledge_graph.add_methodology(methodology)
            
            # Add findings
            for finding in paper_data['findings']:
                self.knowledge_graph.add_finding(finding)
            
            # Add contributions
            for contribution in paper_data['contributions']:
                self.knowledge_graph.add_contribution(contribution)
            
            # Add entities
            for entity in paper_data['entities']:
                self.knowledge_graph.add_entity(entity)
            
            # Add relationships
            for relationship in paper_data['relationships']:
                self.knowledge_graph.add_relationship(relationship)
    
    def process_all_buckets(self, base_dir: Path):
        """Process all 5-year buckets in the directory"""
        logger.info("Starting processing of all buckets")
        
        # Connect to Neo4j
        self.knowledge_graph.connect()
        self.knowledge_graph.create_constraints()
        
        # Find all bucket directories
        bucket_dirs = [d for d in base_dir.iterdir() if d.is_dir() and re.match(r'\d{4}-\d{4}', d.name)]
        bucket_dirs.sort()
        
        total_processed = 0
        for bucket_dir in bucket_dirs:
            try:
                bucket_results = self.process_bucket(bucket_dir)
                self.build_knowledge_graph(bucket_results)
                total_processed += bucket_results['processed_papers']
                logger.info(f"Completed bucket {bucket_dir.name}: {bucket_results['processed_papers']} papers")
            except Exception as e:
                logger.error(f"Error processing bucket {bucket_dir.name}: {e}")
        
        logger.info(f"Total papers processed: {total_processed}")
        
        # Close Neo4j connection
        self.knowledge_graph.close()
    
    def query_knowledge_graph(self, query: str) -> List[Dict[str, Any]]:
        """Query the knowledge graph with a natural language question"""
        # Connect to Neo4j
        self.knowledge_graph.connect()
        
        # Simple query mapping (could be enhanced with NLP)
        query_lower = query.lower()
        
        if 'research question' in query_lower:
            cypher_query = """
            MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
            RETURN p.title as paper_title, p.year as year, rq.question as question, rq.question_type as type
            ORDER BY p.year DESC
            LIMIT 20
            """
        elif 'methodology' in query_lower or 'method' in query_lower:
            cypher_query = """
            MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
            RETURN p.title as paper_title, p.year as year, m.method_type as method_type, 
                   m.analysis_technique as technique, m.sample_size as sample_size
            ORDER BY p.year DESC
            LIMIT 20
            """
        elif 'finding' in query_lower or 'result' in query_lower:
            cypher_query = """
            MATCH (p:Paper)-[:REPORTS_FINDING]->(f:Finding)
            RETURN p.title as paper_title, p.year as year, f.finding as finding, f.finding_type as type
            ORDER BY p.year DESC
            LIMIT 20
            """
        elif 'contribution' in query_lower:
            cypher_query = """
            MATCH (p:Paper)-[:MAKES_CONTRIBUTION]->(c:Contribution)
            RETURN p.title as paper_title, p.year as year, c.contribution as contribution, 
                   c.contribution_type as type
            ORDER BY p.year DESC
            LIMIT 20
            """
        elif 'theory' in query_lower or 'concept' in query_lower:
            cypher_query = """
            MATCH (p:Paper)-[:MENTIONS_ENTITY]->(e:Entity)
            WHERE e.entity_type = 'theory' OR e.entity_type = 'concept'
            RETURN p.title as paper_title, p.year as year, e.name as entity_name, e.entity_type as type
            ORDER BY p.year DESC
            LIMIT 20
            """
        else:
            # Default query - show recent papers
            cypher_query = """
            MATCH (p:Paper)
            RETURN p.title as paper_title, p.year as year, p.abstract as abstract
            ORDER BY p.year DESC
            LIMIT 10
            """
        
        with self.knowledge_graph.driver.session() as session:
            result = session.run(cypher_query)
            return [dict(record) for record in result]
        
        self.knowledge_graph.close()


def main():
    """Main function to run the literature agent"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in the .env file or environment.")
        return
    
    # Initialize the agent
    agent = LiteratureAgent(openai_api_key=api_key)
    
    # Set the base directory (current directory)
    base_dir = Path(__file__).parent
    
    # Process all buckets
    agent.process_all_buckets(base_dir)
    
    # Example queries
    print("\n=== Example Queries ===")
    
    queries = [
        "What are the main research questions in recent papers?",
        "What methodologies are commonly used?",
        "What are the key findings?",
        "What theories are mentioned?",
        "What are the main contributions?",
        "What relationships exist between theories?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = agent.query_knowledge_graph(query)
        for result in results[:3]:  # Show first 3 results
            print(f"  - {result}")


if __name__ == "__main__":
    main()
