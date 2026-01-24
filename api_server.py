#!/usr/bin/env python3
"""
FastAPI server for SMJ Research Chatbot
Connects React frontend with Neo4j knowledge graph
"""

import os
import json
import logging
import requests
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from neo4j import GraphDatabase
from dotenv import load_dotenv

# Graph RAG import (optional - only if embeddings exist)
try:
    from graphrag_query_system import GraphRAGQuerySystem
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    logger.warning("GraphRAG not available - install dependencies if needed")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    persona: Optional[str] = None  # Optional persona: historian, reviewer2, advisor, strategist

class QueryResponse(BaseModel):
    answer: str
    graphData: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    neo4j_connected: bool
    timestamp: str

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    data: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    data: Dict[str, Any] = {}

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Theory Comparison Models (Phase 1.3)
class TheoryComparisonRequest(BaseModel):
    theories: List[str]  # List of theory names to compare
    query: Optional[str] = None  # Optional user question for context

class CompatibilityScore(BaseModel):
    score: float  # 0.0 to 1.0
    factors: List[str]  # List of factors contributing to compatibility

class Tension(BaseModel):
    type: str  # e.g., "assumption_conflict", "competing_explanation", "level_mismatch"
    description: str
    evidence: str

class IntegrationSuggestion(BaseModel):
    feasibility: str  # "high", "medium", "low"
    suggestions: List[str]
    rationale: str

class TheoryComparisonResponse(BaseModel):
    theories: List[str]
    compatibility: CompatibilityScore
    tensions: List[Tension]
    integration: IntegrationSuggestion
    shared_phenomena: List[Dict[str, Any]]
    unique_phenomena: Dict[str, List[Dict[str, Any]]]  # theory_name -> list of phenomena
    methods_overlap: List[str]
    co_usage_frequency: int
    narrative: str

# Theory Context Models (Phase 2.1)
class TheoryAssumption(BaseModel):
    assumption: str
    evidence: str
    frequency: int  # Number of papers supporting this assumption

class TheoryConstruct(BaseModel):
    construct_name: str
    frequency: int
    related_phenomena: List[str]

class TemporalUsage(BaseModel):
    year: int
    paper_count: int
    methods: List[str]

class CoUsageTheory(BaseModel):
    theory_name: str
    co_usage_count: int
    shared_phenomena: List[str]

class TheoryContextResponse(BaseModel):
    theory: Dict[str, Any]  # Theory name, domain, etc.
    phenomena: List[Dict[str, Any]]
    methods: List[Dict[str, Any]]
    papers: List[Dict[str, Any]]
    temporal_usage: List[TemporalUsage]
    co_usage_theories: List[CoUsageTheory]
    assumptions: List[TheoryAssumption]
    constructs: List[TheoryConstruct]
    levels_of_analysis: Dict[str, int]  # level -> count
    assumptions_narrative: str
    constructs_narrative: str

# Contribution Opportunities Models (Phase 2.2)
class OpportunityEvidence(BaseModel):
    connection_strength: Optional[float] = None
    similar_theories: List[str] = []
    similar_phenomena: List[str] = []
    similar_methods: List[str] = []
    paper_count: int = 0
    research_density: str = "low"  # "low", "medium", "high"

class ContributionOpportunity(BaseModel):
    type: str  # "theory-phenomenon", "theory-method", "construct", "sparsity"
    theory: Optional[str] = None
    phenomenon: Optional[str] = None
    method: Optional[str] = None
    construct_name: Optional[str] = None
    opportunity_score: float  # 0.0 to 1.0
    evidence: OpportunityEvidence
    contribution_statement: str
    research_questions: List[str]
    rationale: str

class ContributionOpportunitiesResponse(BaseModel):
    opportunities: List[ContributionOpportunity]
    total: int
    summary: str

# Trend Analysis Models (Phase 3.1)
class PeriodUsage(BaseModel):
    period: str
    start_year: int
    end_year: int
    paper_count: int
    usage_frequency: Optional[float] = None

class EvolutionStep(BaseModel):
    from_period: str
    to_period: str
    change: int
    change_percentage: float
    evolution_type: str  # "increasing", "decreasing", "stable"

class TrendForecast(BaseModel):
    next_period: str
    predicted_paper_count: int
    confidence: float  # 0.0 to 1.0
    trend_direction: str  # "increasing", "decreasing", "stable"
    rationale: str

class TrendAnalysisResponse(BaseModel):
    entity_type: str  # "theory", "method", "phenomenon"
    entity_name: str
    usage_by_period: List[PeriodUsage]
    evolution_steps: List[EvolutionStep]
    forecast: Optional[TrendForecast] = None
    narrative: str
    summary: str

# Neo4j connection class
class Neo4jService:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "").strip()
        self.user = os.getenv("NEO4J_USER", "").strip()
        self.password = os.getenv("NEO4J_PASSWORD", "").strip()
        self.driver = None
        
        # Validate environment variables
        if not self.uri:
            logger.error("✗ NEO4J_URI environment variable is not set or is empty")
        if not self.user:
            logger.error("✗ NEO4J_USER environment variable is not set or is empty")
        if not self.password:
            logger.error("✗ NEO4J_PASSWORD environment variable is not set or is empty")
        
        if self.uri and self.user and self.password:
            self.connect()
        else:
            logger.error("✗ Cannot connect to Neo4j: Missing required environment variables")

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Connected to Neo4j")
        except Exception as e:
            logger.error(f"✗ Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def is_connected(self) -> bool:
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            return False

    def get_all_research_data(self) -> Dict[str, Any]:
        """Get all research data for LLM processing - Updated to use latest schema"""
        if not self.is_connected():
            return {"questions": [], "methods": [], "findings": [], "theories": [], "phenomena": []}

        try:
            with self.driver.session() as session:
                # Get research questions - using ADDRESSES relationship
                questions_result = session.run("""
                    MATCH (p:Paper)-[:ADDRESSES]->(q:ResearchQuestion)
                    RETURN q.question as question, 
                           q.question_id as question_id,
                           p.paper_id as paper_id, 
                           COALESCE(p.year, 0) as year,
                           q.question_type as question_type,
                           q.domain as domain
                    LIMIT 500
                """)
                questions = [dict(record) for record in questions_result]

                # Get methods - using USES_METHOD relationship (new schema)
                methods_result = session.run("""
                    MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                    RETURN m.name as method_name,
                           m.type as method_type,
                           p.paper_id as paper_id, 
                           COALESCE(p.year, 0) as year,
                           m.software as software
                    LIMIT 500
                """)
                methods = [dict(record) for record in methods_result]

                # Get findings - using USES_FINDING or similar relationship
                findings_result = session.run("""
                    MATCH (p:Paper)-[:HAS_FINDING]->(f:Finding)
                    RETURN f.finding_text as finding,
                           f.finding_id as finding_id,
                           p.paper_id as paper_id, 
                           COALESCE(p.year, 0) as year,
                           f.finding_type as finding_type
                    LIMIT 500
                """)
                findings = [dict(record) for record in findings_result]

                # Get theories - using USES_THEORY relationship
                theories_result = session.run("""
                    MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                    RETURN t.name as theory_name,
                           t.domain as domain,
                           r.role as role,
                           p.paper_id as paper_id, 
                           COALESCE(p.year, 0) as year
                    LIMIT 500
                """)
                theories = [dict(record) for record in theories_result]

                # Get phenomena - using STUDIES_PHENOMENON relationship
                phenomena_result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    RETURN ph.phenomenon_name as phenomenon_name,
                           ph.phenomenon_type as phenomenon_type,
                           ph.domain as domain,
                           p.paper_id as paper_id, 
                           COALESCE(p.year, 0) as year
                    LIMIT 500
                """)
                phenomena = [dict(record) for record in phenomena_result]

                logger.info(f"Retrieved: {len(questions)} questions, {len(methods)} methods, {len(findings)} findings, {len(theories)} theories, {len(phenomena)} phenomena")
                return {
                    "questions": questions,
                    "methods": methods,
                    "findings": findings,
                    "theories": theories,
                    "phenomena": phenomena
                }
        except Exception as e:
            logger.error(f"Error getting research data: {e}")
            return {"questions": [], "methods": [], "findings": [], "theories": [], "phenomena": []}

    def get_graph_data_for_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Get relevant graph data for a specific query"""
        if not self.is_connected():
            return None

        try:
            with self.driver.session() as session:
                # Get papers and their relationships
                result = session.run("""
                    MATCH (p:Paper)
                    OPTIONAL MATCH (p)-[:HAS_QUESTION]->(q:ResearchQuestion)
                    OPTIONAL MATCH (p)-[:HAS_METHODOLOGY]->(m:Methodology)
                    OPTIONAL MATCH (p)-[:HAS_FINDING]->(f:Finding)
                    OPTIONAL MATCH (p)-[:HAS_ENTITY]->(e:Entity)
                    OPTIONAL MATCH (p1:Paper)-[r:RELATES_TO]->(p2:Paper)
                    RETURN p, q, m, f, e, r, p1, p2
                    LIMIT 50
                """)

                nodes = []
                edges = []
                node_ids = set()

                for record in result:
                    # Add paper nodes
                    paper = record.get('p')
                    if paper and paper['paper_id'] not in node_ids:
                        nodes.append({
                            "data": {
                                "id": paper['paper_id'],
                                "label": f"{paper['paper_id']} ({paper.get('year', 'N/A')})",
                                "type": "paper",
                                "year": paper.get('year'),
                                "centrality": 0.5
                            }
                        })
                        node_ids.add(paper['paper_id'])

                    # Add question nodes
                    question = record.get('q')
                    if question and f"q_{question['id']}" not in node_ids:
                        nodes.append({
                            "data": {
                                "id": f"q_{question['id']}",
                                "label": question['question'][:50] + "..." if len(question['question']) > 50 else question['question'],
                                "type": "question",
                                "paper_id": question.get('paper_id')
                            }
                        })
                        node_ids.add(f"q_{question['id']}")

                    # Add methodology nodes
                    methodology = record.get('m')
                    if methodology and f"m_{methodology['id']}" not in node_ids:
                        nodes.append({
                            "data": {
                                "id": f"m_{methodology['id']}",
                                "label": methodology['methodology'][:30] + "..." if len(methodology['methodology']) > 30 else methodology['methodology'],
                                "type": "methodology",
                                "paper_id": methodology.get('paper_id')
                            }
                        })
                        node_ids.add(f"m_{methodology['id']}")

                    # Add finding nodes
                    finding = record.get('f')
                    if finding and f"f_{finding['id']}" not in node_ids:
                        nodes.append({
                            "data": {
                                "id": f"f_{finding['id']}",
                                "label": finding['finding'][:40] + "..." if len(finding['finding']) > 40 else finding['finding'],
                                "type": "finding",
                                "paper_id": finding.get('paper_id')
                            }
                        })
                        node_ids.add(f"f_{finding['id']}")

                    # Add entity nodes
                    entity = record.get('e')
                    if entity and f"e_{entity['id']}" not in node_ids:
                        nodes.append({
                            "data": {
                                "id": f"e_{entity['id']}",
                                "label": entity['name'][:20] + "..." if len(entity['name']) > 20 else entity['name'],
                                "type": "entity",
                                "paper_id": entity.get('paper_id')
                            }
                        })
                        node_ids.add(f"e_{entity['id']}")

                    # Add relationships
                    rel = record.get('r')
                    p1 = record.get('p1')
                    p2 = record.get('p2')
                    if rel and p1 and p2:
                        edge_id = f"{p1['paper_id']}_{p2['paper_id']}"
                        if edge_id not in [e['data']['id'] for e in edges]:
                            edges.append({
                                "data": {
                                    "id": edge_id,
                                    "source": p1['paper_id'],
                                    "target": p2['paper_id'],
                                    "label": rel.get('relationship_type', 'RELATES_TO'),
                                    "strength": rel.get('strength', 0.5)
                                }
                            })

                return {
                    "nodes": nodes,
                    "edges": edges
                }

        except Exception as e:
            logger.error(f"Error getting graph data: {e}")
            return None

# Initialize FastAPI app
app = FastAPI(
    title="SMJ Research Chatbot API",
    description="API for Strategic Management Journal Research Chatbot with Knowledge Graph",
    version="1.0.0"
)

# Add CORS middleware - MUST be added before routes
# Configure for Railway deployment with explicit frontend URL
frontend_url = os.getenv("FRONTEND_URL", "https://web-production-ff38d.up.railway.app")

# Build list of allowed origins
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://web-production-ff38d.up.railway.app",  # Explicitly add Railway frontend
]

# Add frontend URL from environment if different
if frontend_url and frontend_url not in cors_origins:
    cors_origins.append(frontend_url)

# Railway regex pattern for dynamic Railway domains
railway_regex = r"https://.*\.(railway\.app|up\.railway\.app)"

# Configure CORS middleware
# Using allow_origins=["*"] for maximum compatibility
# Note: allow_credentials must be False when using ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - simplest solution for Railway
    allow_credentials=False,  # Required when using allow_origins=["*"]
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight for 1 hour
)

# Additional middleware to ensure CORS headers are always present
# This handles OPTIONS preflight requests BEFORE they reach route handlers
# IMPORTANT: This middleware runs FIRST (outermost) because middleware runs in reverse order
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS preflight requests directly
        if request.method == "OPTIONS":
            logger.info(f"🔵 Handling OPTIONS preflight for: {request.url.path}")
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "3600",
                }
            )
        
        # For all other requests, add CORS headers to response
        response = await call_next(request)
        # Explicitly set CORS headers on ALL responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response

# Add CORS middleware FIRST so it runs last (outermost layer)
# This ensures OPTIONS requests are caught before CORSMiddleware
app.add_middleware(CORSHeaderMiddleware)

# Explicit OPTIONS handler for all routes (backup - middleware should catch it first)
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle OPTIONS preflight requests explicitly (backup handler)"""
    logger.info(f"🟢 OPTIONS handler called for: {full_path}")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )

# Log CORS configuration for debugging
logger.info(f"✅ CORS configured: allow_origins=['*'], allow_credentials=False")
logger.info(f"✅ CORSHeaderMiddleware added to handle OPTIONS requests")
logger.info(f"✅ Explicit OPTIONS route handler registered")

# Include Advanced Analytics Router (Graph RAG-based)
try:
    from advanced_analytics_endpoints import router as advanced_analytics_router
    app.include_router(advanced_analytics_router)
    logger.info("✓ Advanced analytics endpoints loaded")
except ImportError as e:
    logger.warning(f"Advanced analytics endpoints not available: {e}")
except Exception as e:
    logger.error(f"Error loading advanced analytics endpoints: {e}")

# Include Research Analytics Router
try:
    from research_analytics_endpoints import router as research_router
    app.include_router(research_router)
    logger.info("✓ Research Analytics endpoints loaded")
except ImportError as e:
    logger.warning(f"Research Analytics endpoints not available: {e}")
except Exception as e:
    logger.error(f"Error loading research analytics endpoints: {e}")

# Initialize Neo4j service
neo4j_service = Neo4jService()

# LLM client for generating answers
class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if self.api_key:
            logger.info("Using OpenAI for LLM (OpenAI API key found)")
        else:
            logger.warning("OpenAI API key not found. LLM features will be limited to fallback responses.")

    def generate_answer(self, query: str, research_data: Dict[str, Any], persona: Optional[str] = None) -> str:
        """Generate answer using OpenAI based on research data with optional persona"""
        if self.api_key:
            try:
                return self._generate_answer_with_openai(query, research_data, persona)
            except Exception as e:
                logger.error(f"Error generating LLM answer with OpenAI: {e}")
                return self._generate_fallback_answer(query, research_data, persona)
        
        return self._generate_fallback_answer(query, research_data, persona)
    
    def _generate_answer_with_openai(self, query: str, research_data: Dict[str, Any], persona: Optional[str] = None) -> str:
        """Generate answer using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Prepare context from research data
        context = self._prepare_context(research_data)
        
        # Get persona-specific system prompt
        system_prompt = self._get_persona_prompt(persona)
        
        # Debug: Log the context being sent to LLM
        logger.info(f"Using OpenAI - Context length: {len(context)} characters")
        logger.info(f"Persona: {persona or 'default'}")

        prompt = f"""
        {system_prompt}

        User Question: {query}

        Available Research Data:
        {context}

        Please provide a comprehensive, well-structured answer based on the available data.
        If the data doesn't contain enough information to answer the question, 
        say so and suggest what additional information might be helpful.
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    
    def _prepare_context(self, research_data: Dict[str, Any]) -> str:
        """Prepare context string from research data - Updated for latest schema"""
        context_parts = []

        # Research Questions
        if research_data.get('questions'):
            context_parts.append("Research Questions:")
            for q in research_data['questions'][:10]:  # Increased limit
                paper_info = f" (Paper: {q.get('paper_id', 'Unknown')}, Year: {q.get('year', 0)})"
                question_type = f" [{q.get('question_type', '')}]" if q.get('question_type') else ""
                context_parts.append(f"- {q.get('question', '')}{question_type}{paper_info}")

        # Methods (new schema)
        if research_data.get('methods'):
            context_parts.append("\nResearch Methods:")
            for m in research_data['methods'][:10]:
                paper_info = f" (Paper: {m.get('paper_id', 'Unknown')}, Year: {m.get('year', 0)})"
                method_type = f" [{m.get('method_type', '')}]" if m.get('method_type') else ""
                context_parts.append(f"- {m.get('method_name', '')}{method_type}{paper_info}")

        # Findings
        if research_data.get('findings'):
            context_parts.append("\nKey Findings:")
            for f in research_data['findings'][:10]:
                paper_info = f" (Paper: {f.get('paper_id', 'Unknown')}, Year: {f.get('year', 0)})"
                finding_type = f" [{f.get('finding_type', '')}]" if f.get('finding_type') else ""
                context_parts.append(f"- {f.get('finding', '')}{finding_type}{paper_info}")

        # Theories (new)
        if research_data.get('theories'):
            context_parts.append("\nTheories Used:")
            theory_summary = {}
            for t in research_data['theories']:
                theory_name = t.get('theory_name', '')
                if theory_name:
                    if theory_name not in theory_summary:
                        theory_summary[theory_name] = {'count': 0, 'years': set()}
                    theory_summary[theory_name]['count'] += 1
                    if t.get('year'):
                        theory_summary[theory_name]['years'].add(t.get('year'))
            
            for theory_name, info in sorted(theory_summary.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
                years_str = f" (Years: {sorted(list(info['years']))[:5]})" if info['years'] else ""
                context_parts.append(f"- {theory_name}: {info['count']} uses{years_str}")

        # Phenomena (new)
        if research_data.get('phenomena'):
            context_parts.append("\nPhenomena Studied:")
            phenom_summary = {}
            for ph in research_data['phenomena']:
                phenom_name = ph.get('phenomenon_name', '')
                if phenom_name:
                    if phenom_name not in phenom_summary:
                        phenom_summary[phenom_name] = {'count': 0, 'type': ph.get('phenomenon_type', '')}
                    phenom_summary[phenom_name]['count'] += 1
            
            for phenom_name, info in sorted(phenom_summary.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
                type_str = f" [{info['type']}]" if info['type'] else ""
                context_parts.append(f"- {phenom_name}{type_str}: {info['count']} papers")

        return "\n".join(context_parts)

    def _get_persona_prompt(self, persona: Optional[str] = None) -> str:
        """Get persona-specific system prompt"""
        if not persona:
            return """You are a research assistant for Strategic Management Journal. 
            Answer the user's question based on the research data provided.
            
            Format your response in a clear, academic style with:
            1. Direct answer to the question
            2. Supporting evidence from the research
            3. Key insights and patterns
            4. Suggestions for further research if applicable"""
        
        persona_lower = persona.lower()
        
        if persona_lower == "historian":
            return """You are a research historian specializing in strategic management theory. 
            Your role is to trace theoretical genealogy, historical debates, and the evolution 
            of ideas in the field.
            
            When answering questions:
            1. Provide historical context and theoretical lineage
            2. Trace how ideas have evolved over time
            3. Identify key debates and turning points
            4. Connect current research to historical foundations
            5. Use a narrative, storytelling style that shows the progression of ideas
            
            Format your response as a historical narrative that helps the user understand 
            where ideas came from and how they developed."""
        
        elif persona_lower == "reviewer2" or persona_lower == "reviewer_2":
            return """You are "Reviewer #2" - a critical, skeptical, and rigorous peer reviewer 
            known for identifying gaps, weaknesses, and areas needing improvement.
            
            When answering questions:
            1. Be critical and identify limitations in the research
            2. Point out gaps, contradictions, or underdeveloped areas
            3. Question assumptions and methodological choices
            4. Suggest what's missing or what could be improved
            5. Be constructive but direct about weaknesses
            
            Format your response with:
            1. Critical assessment of the evidence
            2. Identification of gaps and limitations
            3. Questions that need to be addressed
            4. Suggestions for strengthening the research"""
        
        elif persona_lower == "advisor" or persona_lower == "mentor":
            return """You are a research advisor and mentor helping researchers develop their work. 
            Your role is to provide constructive guidance, suggest next steps, and help researchers 
            think strategically about their research.
            
            When answering questions:
            1. Provide constructive, actionable advice
            2. Suggest logical next steps and research directions
            3. Help identify opportunities and connections
            4. Offer encouragement while being realistic
            5. Think about long-term research trajectories
            
            Format your response with:
            1. Constructive insights and suggestions
            2. Recommended next steps
            3. Opportunities for contribution
            4. Strategic advice for moving forward"""
        
        elif persona_lower == "strategist" or persona_lower == "industry_strategist":
            return """You are an industry strategist who translates academic research into 
            practical business insights. Your role is to bridge theory and practice.
            
            When answering questions:
            1. Translate theoretical concepts into practical implications
            2. Connect research findings to business strategy
            3. Identify actionable insights for practitioners
            4. Consider real-world applications and constraints
            5. Think about how research can inform decision-making
            
            Format your response with:
            1. Practical implications of the research
            2. Business strategy connections
            3. Actionable insights for practitioners
            4. Real-world applications and examples"""
        
        else:
            # Default persona
            return """You are a research assistant for Strategic Management Journal. 
            Answer the user's question based on the research data provided.
            
            Format your response in a clear, academic style with:
            1. Direct answer to the question
            2. Supporting evidence from the research
            3. Key insights and patterns
            4. Suggestions for further research if applicable"""

    def generate_theory_comparison_narrative(self, theories: List[str], context_data: Dict[str, Any], 
                                            user_query: Optional[str] = None) -> str:
        """Generate LLM narrative for theory comparison"""
        if self.api_key:
            try:
                return self._generate_theory_comparison_with_openai(theories, context_data, user_query)
            except Exception as e:
                logger.error(f"Error generating theory comparison with OpenAI: {e}")
        
        # Fallback narrative
        return self._generate_fallback_theory_comparison(theories, context_data)
    
    def _generate_theory_comparison_with_openai(self, theories: List[str], context_data: Dict[str, Any],
                                               user_query: Optional[str] = None) -> str:
        """Generate theory comparison narrative using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        theories_str = ", ".join(theories)
        shared_count = len(context_data.get("shared_phenomena", []))
        compatibility = context_data.get("compatibility_score", 0.0)
        
        prompt = f"""
        You are a strategic management research expert. Compare the following theories:
        
        Theories: {theories_str}
        
        Context:
        - Shared Phenomena: {shared_count}
        - Compatibility: {compatibility:.2f}
        - Factors: {', '.join(context_data.get('compatibility_factors', []))}
        - Co-usage: {context_data.get('co_usage', 0)} papers
        - Tensions: {len(context_data.get('tensions', []))}
        
        User Question: {user_query if user_query else 'General comparison'}
        
        Provide a comprehensive comparison covering compatibility, tensions, and integration opportunities.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_theory_comparison(self, theories: List[str], context_data: Dict[str, Any]) -> str:
        """Generate fallback theory comparison narrative"""
        theories_str = " and ".join(theories)
        shared_count = len(context_data.get("shared_phenomena", []))
        compatibility = context_data.get("compatibility_score", 0.0)
        
        narrative = f"""
        Comparison of {theories_str}:
        
        Compatibility Score: {compatibility:.2f} (on a scale of 0.0 to 1.0)
        
        The theories share {shared_count} phenomena, indicating {'strong' if compatibility > 0.6 else 'moderate' if compatibility > 0.4 else 'limited'} overlap.
        
        Compatibility Factors: {', '.join(context_data.get('compatibility_factors', []))}
        
        {'The theories are used together in ' + str(context_data.get('co_usage', 0)) + ' papers, suggesting they can be complementary.' if context_data.get('co_usage', 0) > 0 else 'Limited co-usage suggests the theories may serve different purposes.'}
        
        For a detailed analysis, please ensure LLM services are available.
        """
        
        return narrative.strip()
    
    def generate_theory_assumptions_narrative(self, theory_name: str, assumptions_data: Dict[str, Any],
                                             phenomena: List[Dict], methods: List[Dict]) -> str:
        """Generate LLM narrative for theory assumptions"""
        if self.api_key:
            try:
                return self._generate_assumptions_narrative_with_openai(theory_name, assumptions_data, phenomena, methods)
            except Exception as e:
                logger.error(f"Error generating assumptions with OpenAI: {e}")
        
        return self._generate_fallback_assumptions_narrative(theory_name, assumptions_data)
    
    def _generate_assumptions_narrative_with_openai(self, theory_name: str, assumptions_data: Dict[str, Any],
                                                   phenomena: List[Dict], methods: List[Dict]) -> str:
        """Generate assumptions narrative using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"""
        Analyze the assumptions underlying {theory_name} based on its usage patterns:
        - Phenomena: {len(phenomena)}
        - Methods: {len(methods)}
        - Papers: {assumptions_data.get('papers_count', 0)}
        
        Identify core assumptions about firm behavior, resources, boundary conditions, and methodology.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_assumptions_narrative(self, theory_name: str, assumptions_data: Dict[str, Any]) -> str:
        """Generate fallback assumptions narrative"""
        return f"""
        Assumptions Analysis for {theory_name}:
        
        Based on usage patterns:
        - Explains {assumptions_data.get('phenomena_count', 0)} phenomena
        - Used with {assumptions_data.get('methods_count', 0)} methods
        - Appears in {assumptions_data.get('papers_count', 0)} papers
        
        For detailed assumptions analysis, please ensure LLM services are available.
        """
    
    def generate_theory_constructs_narrative(self, theory_name: str, constructs: List[TheoryConstruct],
                                            phenomena: List[Dict]) -> str:
        """Generate LLM narrative for theory constructs"""
        if self.api_key:
            try:
                return self._generate_constructs_narrative_with_openai(theory_name, constructs, phenomena)
            except Exception as e:
                logger.error(f"Error generating constructs with OpenAI: {e}")
        
        return self._generate_fallback_constructs_narrative(theory_name, constructs)
    
    def _generate_constructs_narrative_with_openai(self, theory_name: str, constructs: List[TheoryConstruct],
                                                  phenomena: List[Dict]) -> str:
        """Generate constructs narrative using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"""
        Analyze the key constructs of {theory_name}:
        - Constructs: {len(constructs)}
        - Phenomena: {len(phenomena)}
        
        Explain core constructs, their relationships, and theoretical structure.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_constructs_narrative(self, theory_name: str, constructs: List[TheoryConstruct]) -> str:
        """Generate fallback constructs narrative"""
        constructs_list = [f"{c.construct_name} ({c.frequency} phenomena)" for c in constructs[:5]]
        return f"""
        Constructs Analysis for {theory_name}:
        
        Key Constructs:
        {chr(10).join('- ' + c for c in constructs_list)}
        
        For detailed constructs analysis, please ensure LLM services are available.
        """
    
    def generate_contribution_statement(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> str:
        """Generate LLM contribution statement for an opportunity"""
        if self.api_key:
            try:
                return self._generate_contribution_statement_with_openai(opportunity_type, contribution_data)
            except Exception as e:
                logger.error(f"Error generating contribution statement with OpenAI: {e}")
        
        return self._generate_fallback_contribution_statement(opportunity_type, contribution_data)
    
            
            Context:
            - Current connection strength: {contribution_data.get('current_strength', 0.0):.2f}
            - Papers using this combination: {contribution_data.get('paper_count', 0)}
            - Similar theories: {', '.join(contribution_data.get('similar_theories', [])[:3])}
            - Opportunity score: {contribution_data.get('opportunity_score', 0.0):.2f}
            
            Write a 2-3 sentence contribution statement that:
            1. Identifies the research gap
            2. Explains why this combination is promising
            3. Suggests the potential contribution
            
            Be specific and academic in tone.
            """
        elif opportunity_type == "theory-method":
            prompt = f"""
            Generate a research contribution statement for using {contribution_data.get('method')} to study {contribution_data.get('theory')}.
            
    def _generate_contribution_statement_with_openai(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> str:
        """Generate contribution statement using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"Generate a research contribution statement for {opportunity_type} opportunity: {contribution_data}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_contribution_statement(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> str:
        """Generate fallback contribution statement"""
        if opportunity_type == "theory-phenomenon":
            return f"Exploring how {contribution_data.get('theory')} could explain {contribution_data.get('phenomenon')} represents an underexplored research opportunity (current strength: {contribution_data.get('current_strength', 0.0):.2f}, papers: {contribution_data.get('paper_count', 0)})."
        elif opportunity_type == "theory-method":
            return f"Using {contribution_data.get('method')} to study {contribution_data.get('theory')} is a novel methodological approach (current usage: {contribution_data.get('usage_count', 0)} papers)."
        else:
            return f"Studying {contribution_data.get('phenomenon')} represents an underexplored research area ({contribution_data.get('paper_count', 0)} papers)."
    
    def generate_research_questions(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> List[str]:
        """Generate research questions for an opportunity"""
        if self.api_key:
            try:
                return self._generate_research_questions_with_openai(opportunity_type, contribution_data)
            except Exception as e:
                logger.error(f"Error generating research questions with OpenAI: {e}")
        
        return self._generate_fallback_research_questions(opportunity_type, contribution_data)
    
            
            Context:
            - Current connection strength: {contribution_data.get('current_strength', 0.0):.2f}
            - Similar theories: {', '.join(contribution_data.get('similar_theories', [])[:2])}
            
            Generate research questions that are:
            1. Specific and actionable
            2. Grounded in the theory
            3. Focused on the phenomenon
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('response', '').strip()
            # Parse numbered list into array
            questions = []
            for line in text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets
                    question = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if question:
                        questions.append(question)
            return questions[:3] if questions else ["How can this opportunity be explored?"]
        else:
    
    def _generate_research_questions_with_openai(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> List[str]:
        """Generate research questions using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"Generate 2-3 research questions for {opportunity_type} opportunity: {contribution_data}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        text = response.choices[0].message.content.strip()
        questions = []
        for line in text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                question = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if question:
                    questions.append(question)
        return questions[:3] if questions else ["How can this opportunity be explored?"]
    
    def _generate_fallback_research_questions(self, opportunity_type: str, contribution_data: Dict[str, Any]) -> List[str]:
        """Generate fallback research questions"""
        if opportunity_type == "theory-phenomenon":
            return [
                f"How does {contribution_data.get('theory')} explain {contribution_data.get('phenomenon')}?",
                f"What are the mechanisms through which {contribution_data.get('theory')} relates to {contribution_data.get('phenomenon')}?"
            ]
        elif opportunity_type == "theory-method":
            return [
                f"How can {contribution_data.get('method')} be used to test {contribution_data.get('theory')}?",
                f"What insights does {contribution_data.get('method')} provide for {contribution_data.get('theory')}?"
            ]
        else:
            return [
                f"What theories can explain {contribution_data.get('phenomenon')}?",
                f"How is {contribution_data.get('phenomenon')} studied in the literature?"
            ]
    
    def generate_opportunities_summary(self, opportunities: List[ContributionOpportunity], query: Optional[str] = None) -> str:
        """Generate LLM summary of opportunities"""
        if not opportunities:
            return "No contribution opportunities found matching the criteria."
        
        if self.api_key:
            try:
                return self._generate_opportunities_summary_with_openai(opportunities, query)
            except Exception as e:
                logger.error(f"Error generating summary with OpenAI: {e}")
        
        return self._generate_fallback_opportunities_summary(opportunities)
    
    def _generate_opportunities_summary_with_openai(self, opportunities: List[ContributionOpportunity], query: Optional[str] = None) -> str:
        """Generate summary using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"Summarize these research opportunities: {opportunities[:5]}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_opportunities_summary(self, opportunities: List[ContributionOpportunity]) -> str:
        """Generate fallback summary"""
        theory_phenomenon_count = sum(1 for opp in opportunities if opp.type == "theory-phenomenon")
        theory_method_count = sum(1 for opp in opportunities if opp.type == "theory-method")
        construct_count = sum(1 for opp in opportunities if opp.type == "construct")
        
        return f"""
        Found {len(opportunities)} contribution opportunities:
        - {theory_phenomenon_count} theory-phenomenon gaps
        - {theory_method_count} theory-method gaps
        - {construct_count} rare constructs
        
        Top opportunities have scores ranging from {max([opp.opportunity_score for opp in opportunities[:3]]) if opportunities else 0:.2f} to {min([opp.opportunity_score for opp in opportunities[:3]]) if opportunities else 0:.2f}.
        """
    
    def generate_trend_narrative(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage], 
                                 evolution_steps: List[EvolutionStep], forecast: Optional[TrendForecast]) -> str:
        """Generate LLM narrative for trend analysis"""
        if self.api_key:
            try:
                return self._generate_trend_narrative_with_openai(entity_type, entity_name, usage_by_period, evolution_steps, forecast)
            except Exception as e:
                logger.error(f"Error generating trend narrative with OpenAI: {e}")
        
        return self._generate_fallback_trend_narrative(entity_type, entity_name, usage_by_period, evolution_steps, forecast)
    
        
        forecast_text = ""
        if forecast:
            forecast_text = f"\n\nForecast for {forecast.next_period}: {forecast.predicted_paper_count} papers ({forecast.trend_direction})"
        
        prompt = f"""
        Analyze the temporal evolution of {entity_type} "{entity_name}":
        
        Usage by Period:
        {usage_summary}
        
        Evolution Steps:
        {evolution_summary}
        {forecast_text}
        
        Write a 3-4 paragraph narrative that:
        1. Describes where the field has been (historical usage)
        2. Identifies key turning points and trends
        3. Explains where the field is going (based on recent trends)
        4. Discusses implications for future research
        
        Write in an academic but accessible style.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_trend_narrative_with_openai(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage],
                                             evolution_steps: List[EvolutionStep], forecast: Optional[TrendForecast]) -> str:
        """Generate trend narrative using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"Analyze temporal evolution of {entity_type} {entity_name}: {usage_by_period}, {evolution_steps}, {forecast}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_trend_narrative(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage],
                                          evolution_steps: List[EvolutionStep], forecast: Optional[TrendForecast]) -> str:
        """Generate fallback trend narrative"""
        narrative = f"The {entity_type} '{entity_name}' has been used across {len(usage_by_period)} time periods. "
        
        if usage_by_period:
            narrative += f"Usage ranged from {min(p.paper_count for p in usage_by_period)} to {max(p.paper_count for p in usage_by_period)} papers per period. "
        
        if evolution_steps:
            increasing = sum(1 for e in evolution_steps if e.evolution_type == "increasing")
            decreasing = sum(1 for e in evolution_steps if e.evolution_type == "decreasing")
            if increasing > decreasing:
                narrative += "Overall trend shows increasing usage over time. "
            elif decreasing > increasing:
                narrative += "Overall trend shows decreasing usage over time. "
            else:
                narrative += "Usage has remained relatively stable over time. "
        
        if forecast:
            narrative += f"Forecast for {forecast.next_period}: {forecast.predicted_paper_count} papers ({forecast.trend_direction})."
        
        return narrative
    
    def generate_trend_summary(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage],
                               evolution_steps: List[EvolutionStep]) -> str:
        """Generate LLM summary for trend analysis"""
        if self.api_key:
            try:
                return self._generate_trend_summary_with_openai(entity_type, entity_name, usage_by_period, evolution_steps)
            except Exception as e:
                logger.error(f"Error generating trend summary with OpenAI: {e}")
        
        return self._generate_fallback_trend_summary(entity_type, entity_name, usage_by_period, evolution_steps)
    
    def _generate_trend_summary_with_openai(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage],
                                           evolution_steps: List[EvolutionStep]) -> str:
        """Generate trend summary using OpenAI"""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        prompt = f"Summarize temporal evolution of {entity_type} {entity_name}: {usage_by_period}, {evolution_steps}"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_trend_summary(self, entity_type: str, entity_name: str, usage_by_period: List[PeriodUsage],
                                       evolution_steps: List[EvolutionStep]) -> str:
        """Generate fallback trend summary"""
        if not usage_by_period:
            return f"No temporal data available for {entity_type} '{entity_name}'."
        
        total_papers = sum(p.paper_count for p in usage_by_period)
        avg_papers = total_papers / len(usage_by_period) if usage_by_period else 0
        
        return f"{entity_type.title()} '{entity_name}' has been used in {total_papers} papers across {len(usage_by_period)} periods (average: {avg_papers:.1f} papers per period)."
    
    def _generate_fallback_answer(self, query: str, research_data: Dict[str, Any], persona: Optional[str] = None) -> str:
        """Generate a fallback answer without LLM - Updated for latest schema"""
        total_questions = len(research_data.get('questions', []))
        total_methods = len(research_data.get('methods', []))
        total_findings = len(research_data.get('findings', []))
        total_theories = len(research_data.get('theories', []))
        total_phenomena = len(research_data.get('phenomena', []))

        persona_note = f" (Persona: {persona})" if persona else ""
        
        return f"""
        I found {total_questions} research questions, {total_methods} methods, 
        {total_findings} findings, {total_theories} theory uses, and {total_phenomena} phenomena 
        in the knowledge graph.{persona_note}

        Query: {query}

        To provide a more detailed answer, I would need access to an LLM service. 
        The current data shows research activity across multiple papers, but I cannot 
        synthesize a comprehensive response without additional processing capabilities.

        Available data includes research questions, methods, findings, theories, and phenomena 
        from various Strategic Management Journal papers.
        """

# Initialize LLM client
llm_client = LLMClient()

# Initialize Graph RAG system (lazy - only if embeddings exist)
graphrag_system = None

def get_graphrag_system():
    """Lazy initialization of Graph RAG system"""
    global graphrag_system
    if graphrag_system is None and GRAPHRAG_AVAILABLE:
        try:
            # Check if embeddings exist before initializing
            with neo4j_service.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.embedding IS NOT NULL
                    RETURN count(p) as count
                    LIMIT 1
                """)
                count = result.single()['count'] if result.peek() else 0
                
                if count > 0:
                    logger.info("Initializing Graph RAG system (embeddings found)")
                    graphrag_system = GraphRAGQuerySystem()
                    return graphrag_system
                else:
                    logger.info("Graph RAG not initialized (no embeddings found)")
                    return None
        except Exception as e:
            logger.warning(f"Failed to initialize Graph RAG: {e}")
            return None
    return graphrag_system

# API Routes
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if neo4j_service.is_connected() else "unhealthy",
        neo4j_connected=neo4j_service.is_connected(),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query and return answer with graph data"""
    try:
        # Try Graph RAG first if available
        graphrag = get_graphrag_system()
        use_graphrag = graphrag is not None
        
        if use_graphrag:
            logger.info(f"Using Graph RAG for query: '{request.query[:50]}...'")
            try:
                # Use Graph RAG for hybrid search
                graphrag_result = graphrag.query(
                    request.query,
                    top_k=10,
                    similarity_threshold=0.3
                )
                
                # Check if result is valid
                if not graphrag_result:
                    raise ValueError("Graph RAG query returned None or empty result")
                
                # Generate answer using Graph RAG context
                persona = request.persona if hasattr(request, 'persona') else None
                answer = graphrag.generate_answer(graphrag_result, use_llm=True)
                
                # Check if answer is valid
                if not answer:
                    raise ValueError("Graph RAG generate_answer returned None or empty")
                
                # Prepare sources from Graph RAG results
                sources = []
                all_papers = (graphrag_result.get('papers', []) + 
                             graphrag_result.get('connected_papers', []))
                
                # Get full paper details from Neo4j
                paper_ids = [p.get('paper_id') for p in all_papers if p.get('paper_id')]
                if paper_ids:
                    with neo4j_service.driver.session() as session:
                        result = session.run("""
                            MATCH (p:Paper)
                            WHERE p.paper_id IN $paper_ids
                            OPTIONAL MATCH (p)<-[:AUTHORED_BY]-(a:Author)
                            OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                            OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                            WITH p,
                                 collect(DISTINCT a) as authors,
                                 collect(DISTINCT t.name) as theories,
                                 collect(DISTINCT m.name) as methods
                            RETURN p.paper_id as paper_id,
                                   p.title as title,
                                   p.abstract as abstract,
                                   p.year as year,
                                   p.journal as journal,
                                   p.doi as doi,
                                   p.keywords as keywords,
                                   authors,
                                   theories,
                                   methods
                            LIMIT 20
                        """, paper_ids=paper_ids)
                        
                        for record in result:
                            authors_list = []
                            for author in record.get('authors', []):
                                if author:
                                    authors_list.append({
                                        'full_name': author.get('full_name') or author.get('name', ''),
                                        'given_name': author.get('given_name', ''),
                                        'family_name': author.get('family_name', ''),
                                    })
                            
                            sources.append({
                                'paper_id': record.get('paper_id'),
                                'id': record.get('paper_id'),
                                'title': record.get('title'),
                                'abstract': record.get('abstract'),
                                'publication_year': record.get('year'),
                                'journal': record.get('journal'),
                                'doi': record.get('doi'),
                                'keywords': record.get('keywords') or [],
                                'authors': authors_list,
                                'theories': [{'name': t} for t in (record.get('theories') or [])],
                                'methods': [{'name': m} for m in (record.get('methods') or [])]
                            })
                
                # Get graph data
                graph_data = neo4j_service.get_graph_data_for_query(request.query)
                
                return QueryResponse(
                    answer=answer,
                    graphData=graph_data,
                    sources=sources,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.warning(f"Graph RAG failed, falling back to standard method: {e}")
                use_graphrag = False
        
        # Fallback to standard method
        if not use_graphrag:
            logger.info(f"Using standard query method for: '{request.query[:50]}...'")
            # Get research data
            research_data = neo4j_service.get_all_research_data()
            
            # Generate answer using LLM with persona (if provided)
            persona = request.persona if hasattr(request, 'persona') else None
            answer = llm_client.generate_answer(request.query, research_data, persona=persona)
            
            # Get graph data
            graph_data = neo4j_service.get_graph_data_for_query(request.query)
            
            # Prepare sources - get actual papers related to the query
            sources = []
            try:
                # Extract key terms from query for paper search
                query_lower = request.query.lower()
                # Try to find papers related to the query
                with neo4j_service.driver.session() as session:
                    # Search for papers using theories/methods mentioned in query
                    paper_result = session.run("""
                        MATCH (p:Paper)
                        OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                        OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                        WHERE toLower(COALESCE(p.title, '')) CONTAINS $query
                           OR toLower(COALESCE(p.abstract, '')) CONTAINS $query
                           OR toLower(t.name) CONTAINS $query
                           OR toLower(m.name) CONTAINS $query
                        WITH DISTINCT p
                        OPTIONAL MATCH (p)<-[:AUTHORED_BY]-(a:Author)
                        OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                        OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                        WITH p, 
                             collect(DISTINCT a) as authors,
                             collect(DISTINCT t.name) as theories,
                             collect(DISTINCT m.name) as methods
                        RETURN p.paper_id as paper_id,
                               p.title as title,
                               p.abstract as abstract,
                               p.year as year,
                               p.journal as journal,
                               p.doi as doi,
                               p.keywords as keywords,
                               authors,
                               theories,
                               methods
                        LIMIT 10
                    """, parameters={'query': query_lower})
                    
                    for record in paper_result:
                        # Format authors
                        authors_list = []
                        for author in record.get('authors', []):
                            if author:
                                authors_list.append({
                                    'full_name': author.get('full_name') or author.get('name', ''),
                                    'given_name': author.get('given_name', ''),
                                    'family_name': author.get('family_name', ''),
                                })
                        
                        sources.append({
                            'paper_id': record.get('paper_id'),
                            'id': record.get('paper_id'),
                            'title': record.get('title'),
                            'abstract': record.get('abstract'),
                            'publication_year': record.get('year'),
                            'journal': record.get('journal'),
                            'doi': record.get('doi'),
                            'keywords': record.get('keywords') or [],
                            'authors': authors_list,
                            'theories': [{'name': t} for t in (record.get('theories') or [])],
                            'methods': [{'name': m} for m in (record.get('methods') or [])]
                        })
            except Exception as e:
                logger.warning(f"Error getting paper sources: {e}")

            return QueryResponse(
                answer=answer,
                graphData=graph_data,
                sources=sources,
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph")
async def get_graph_data():
    """Get full knowledge graph data"""
    try:
        graph_data = neo4j_service.get_graph_data_for_query("")
        return {"graphData": graph_data}
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get knowledge graph statistics"""
    try:
        if not neo4j_service.is_connected():
            return {"error": "Neo4j not connected"}

        with neo4j_service.driver.session() as session:
            # Get counts - updated to match actual graph structure
            paper_count = session.run("MATCH (p:Paper) RETURN count(p) as count").single()['count']
            
            # Try to get theories count
            theory_count_result = session.run("MATCH (t:Theory) RETURN count(t) as count")
            theory_count = theory_count_result.single()['count'] if theory_count_result.peek() else 0
            
            # Try to get methods count
            method_count_result = session.run("MATCH (m:Method) RETURN count(m) as count")
            method_count = method_count_result.single()['count'] if method_count_result.peek() else 0
            
            # Try to get authors count
            author_count_result = session.run("MATCH (a:Author) RETURN count(DISTINCT a) as count")
            author_count = author_count_result.single()['count'] if author_count_result.peek() else 0
            
            # Fallback to old structure if needed
            question_count = session.run("MATCH (q:ResearchQuestion) RETURN count(q) as count").single()['count']
            methodology_count = session.run("MATCH (m:Methodology) RETURN count(m) as count").single()['count']
            finding_count = session.run("MATCH (f:Finding) RETURN count(f) as count").single()['count']
            entity_count = session.run("MATCH (e:Entity) RETURN count(e) as count").single()['count']
            relationship_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

            return {
                "papers": paper_count,
                "theories": theory_count if theory_count > 0 else entity_count,
                "methods": method_count if method_count > 0 else methodology_count,
                "authors": author_count,
                "questions": question_count,
                "findings": finding_count,
                "relationships": relationship_count
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_papers(request: QueryRequest):
    """Search for papers by query - searches across papers, theories, and methods"""
    try:
        if not neo4j_service.is_connected():
            return {"error": "Neo4j not connected", "papers": []}

        search_term = request.query.lower().strip()
        # Split into words for flexible matching
        search_words = [w.strip() for w in search_term.split() if w.strip()]
        
        with neo4j_service.driver.session() as session:
            # Comprehensive search - find papers matching search term in multiple ways
            # Use flexible matching: match if ALL words appear (for multi-word queries)
            # or exact substring match
            
            if len(search_words) > 1:
                # Multi-word query: match if theory/method contains all words
                paper_ids_result = session.run("""
                    // Find papers by theory (all words must match)
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE all(word in $words WHERE toLower(t.name) CONTAINS word)
                    RETURN DISTINCT p.paper_id as paper_id
                    
                    UNION
                    
                    // Find papers by method (all words must match)
                    MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                    WHERE all(word in $words WHERE toLower(m.name) CONTAINS word)
                    RETURN DISTINCT p.paper_id as paper_id
                    
                    UNION
                    
                    // Find papers by title/abstract/keywords (exact phrase or all words)
                    MATCH (p:Paper)
                    WHERE toLower(COALESCE(p.title, '')) CONTAINS $search_term 
                       OR toLower(COALESCE(p.abstract, '')) CONTAINS $search_term
                       OR all(word in $words WHERE toLower(COALESCE(p.title, '')) CONTAINS word)
                       OR all(word in $words WHERE toLower(COALESCE(p.abstract, '')) CONTAINS word)
                       OR any(kw in COALESCE(p.keywords, []) WHERE toLower(kw) CONTAINS $search_term)
                    RETURN DISTINCT p.paper_id as paper_id
                """, search_term=search_term, words=search_words)
            else:
                # Single word query: simple substring match
                paper_ids_result = session.run("""
                    // Find papers by theory
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE toLower(t.name) CONTAINS $search_term
                    RETURN DISTINCT p.paper_id as paper_id
                    
                    UNION
                    
                    // Find papers by method
                    MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                    WHERE toLower(m.name) CONTAINS $search_term
                    RETURN DISTINCT p.paper_id as paper_id
                    
                    UNION
                    
                    // Find papers by title/abstract/keywords
                    MATCH (p:Paper)
                    WHERE toLower(COALESCE(p.title, '')) CONTAINS $search_term 
                       OR toLower(COALESCE(p.abstract, '')) CONTAINS $search_term
                       OR any(kw in COALESCE(p.keywords, []) WHERE toLower(kw) CONTAINS $search_term)
                    RETURN DISTINCT p.paper_id as paper_id
                """, search_term=search_term)
            
            paper_ids = [record['paper_id'] for record in paper_ids_result if record.get('paper_id')]
            
            if not paper_ids:
                return {"papers": [], "count": 0}
            
            # Now get full details for matched papers
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.paper_id IN $paper_ids
                OPTIONAL MATCH (p)-[:AUTHORED]-(a:Author)
                OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                
                WITH p, 
                     collect(DISTINCT a) as authors, 
                     collect(DISTINCT {
                         name: t.name,
                         theory_name: t.name,
                         role: head([(p)-[r:USES_THEORY]->(t) | r.role]),
                         section: head([(p)-[r:USES_THEORY]->(t) | r.section])
                     }) as theories,
                     collect(DISTINCT {
                         name: m.name,
                         method_name: m.name,
                         category: m.category
                     }) as methods
                
                RETURN p.paper_id as paper_id,
                       p.title as title,
                       p.abstract as abstract,
                       p.publication_year as publication_year,
                       p.journal as journal,
                       p.doi as doi,
                       p.keywords as keywords,
                       authors,
                       theories,
                       methods
                ORDER BY p.publication_year DESC
                LIMIT 50
            """, paper_ids=paper_ids)
            
            papers = []
            for record in result:
                # Format authors
                authors_list = []
                for author in record.get('authors', []):
                    if author:
                        authors_list.append({
                            'full_name': author.get('full_name') or author.get('name', ''),
                            'given_name': author.get('given_name', ''),
                            'family_name': author.get('family_name', ''),
                            'email': author.get('email'),
                            'orcid': author.get('orcid')
                        })
                
                # Format theories - handle both object and string formats
                theories_list = []
                for t in (record.get('theories') or []):
                    if isinstance(t, dict):
                        # Filter out None values and ensure name exists
                        theory_obj = {k: v for k, v in t.items() if v is not None}
                        if theory_obj.get('name') or theory_obj.get('theory_name'):
                            theories_list.append(theory_obj)
                    elif t:
                        # String, wrap it
                        theories_list.append({'name': str(t), 'theory_name': str(t)})
                
                # Format methods - handle both object and string formats
                methods_list = []
                for m in (record.get('methods') or []):
                    if isinstance(m, dict):
                        # Filter out None values and ensure name exists
                        method_obj = {k: v for k, v in m.items() if v is not None}
                        if method_obj.get('name') or method_obj.get('method_name'):
                            methods_list.append(method_obj)
                    elif m:
                        # String, wrap it
                        methods_list.append({'name': str(m), 'method_name': str(m)})
                
                papers.append({
                    'paper_id': record.get('paper_id'),
                    'id': record.get('paper_id'),
                    'title': record.get('title'),
                    'abstract': record.get('abstract'),
                    'publication_year': record.get('publication_year'),
                    'journal': record.get('journal'),
                    'doi': record.get('doi'),
                    'keywords': record.get('keywords') or [],
                    'authors': authors_list,
                    'theories': theories_list,
                    'methods': methods_list
                })
            
            return {"papers": papers, "count": len(papers)}
            
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers/{paper_id}")
async def get_paper(paper_id: str):
    """Get detailed information about a specific paper"""
    try:
        if not neo4j_service.is_connected():
            return {"error": "Neo4j not connected"}

        with neo4j_service.driver.session() as session:
            # Get paper with all relationships
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                OPTIONAL MATCH (p)-[:AUTHORED]-(a:Author)
                OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                OPTIONAL MATCH (p)-[:ADDRESSES]->(rq:ResearchQuestion)
                OPTIONAL MATCH (p)-[:USES_VARIABLE]->(v:Variable)
                OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
                WITH p, 
                     collect(DISTINCT a) as authors,
                     collect(DISTINCT {
                         name: t.name,
                         theory_name: t.name,
                         role: head([(p)-[r:USES_THEORY]->(t) | r.role]),
                         section: head([(p)-[r:USES_THEORY]->(t) | r.section]),
                         description: t.description,
                         domain: t.domain
                     }) as theories,
                     collect(DISTINCT {
                         name: m.name,
                         method_name: m.name,
                         description: m.description,
                         category: m.category
                     }) as methods,
                     collect(DISTINCT {
                         question: rq.question,
                         question_id: rq.question_id,
                         type: rq.type
                     }) as research_questions,
                     collect(DISTINCT {
                         name: v.name,
                         variable_name: v.name,
                         type: v.type,
                         description: v.description
                     }) as variables,
                     collect(DISTINCT cited.paper_id) as citations
                RETURN p,
                       authors,
                       theories,
                       methods,
                       research_questions,
                       variables,
                       citations
            """, paper_id=paper_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Paper not found")
            
            paper = record.get('p')
            
            # Format authors
            authors_list = []
            for author in record.get('authors', []):
                if author:
                    authors_list.append({
                        'full_name': author.get('full_name') or author.get('name', ''),
                        'given_name': author.get('given_name', ''),
                        'family_name': author.get('family_name', ''),
                        'email': author.get('email'),
                        'orcid': author.get('orcid'),
                        'position': author.get('position')
                    })
            
            return {
                'paper_id': paper.get('paper_id'),
                'id': paper.get('paper_id'),
                'title': paper.get('title'),
                'abstract': paper.get('abstract'),
                'publication_year': paper.get('publication_year'),
                'journal': paper.get('journal') or 'Strategic Management Journal',
                'doi': paper.get('doi'),
                'keywords': paper.get('keywords') or [],
                'authors': authors_list,
                'theories': record.get('theories') or [],
                'methods': record.get('methods') or [],
                'research_questions': record.get('research_questions') or [],
                'variables': record.get('variables') or [],
                'citations': record.get('citations') or []
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONNECTION STRENGTH ENDPOINTS (Phase 2 - New)
# ============================================================================

@app.get("/api/connections/theory-phenomenon")
async def get_theory_phenomenon_connections(
    theory_name: Optional[str] = Query(None, description="Filter by theory name"),
    phenomenon_name: Optional[str] = Query(None, description="Filter by phenomenon name"),
    min_strength: float = Query(0.3, ge=0.0, le=1.0, description="Minimum connection strength"),
    max_strength: float = Query(1.0, ge=0.0, le=1.0, description="Maximum connection strength"),
    paper_id: Optional[str] = Query(None, description="Filter by paper ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get Theory-Phenomenon connections with strength
    
    Returns all connections matching the filters, with pagination support.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # Build query with filters
            where_clauses = []
            params = {
                "min_strength": min_strength,
                "max_strength": max_strength,
                "limit": limit,
                "offset": offset
            }
            
            if theory_name:
                where_clauses.append("t.name = $theory_name")
                params["theory_name"] = theory_name
            
            if phenomenon_name:
                where_clauses.append("ph.phenomenon_name = $phenomenon_name")
                params["phenomenon_name"] = phenomenon_name
            
            if paper_id:
                where_clauses.append("r.paper_id = $paper_id")
                params["paper_id"] = paper_id
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = f"""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WHERE {where_clause}
                  AND r.connection_strength >= $min_strength
                  AND r.connection_strength <= $max_strength
                RETURN count(r) as total
            """
            total_result = session.run(count_query, **params).single()
            total = total_result["total"] if total_result else 0
            
            # Get connections
            query = f"""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WHERE {where_clause}
                  AND r.connection_strength >= $min_strength
                  AND r.connection_strength <= $max_strength
                RETURN t.name as theory_name,
                       t.domain as theory_domain,
                       ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain as phenomenon_domain,
                       ph.description as phenomenon_description,
                       r.connection_strength,
                       r.role_weight,
                       r.section_score,
                       r.keyword_score,
                       r.semantic_score,
                       r.explicit_bonus,
                       r.paper_id,
                       r.theory_role,
                       r.section
                ORDER BY r.connection_strength DESC
                SKIP $offset
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            connections = []
            
            for record in result:
                connections.append({
                    "theory": {
                        "name": record.get("theory_name"),
                        "domain": record.get("theory_domain")
                    },
                    "phenomenon": {
                        "phenomenon_name": record.get("phenomenon_name"),
                        "phenomenon_type": record.get("phenomenon_type"),
                        "domain": record.get("phenomenon_domain"),
                        "description": record.get("phenomenon_description")
                    },
                    "connection_strength": round(record.get("connection_strength", 0.0), 3),
                    "factor_scores": {
                        "role_weight": round(record.get("role_weight", 0.0), 3),
                        "section_score": round(record.get("section_score", 0.0), 3),
                        "keyword_score": round(record.get("keyword_score", 0.0), 3),
                        "semantic_score": round(record.get("semantic_score", 0.0), 3),
                        "explicit_bonus": round(record.get("explicit_bonus", 0.0), 3)
                    },
                    "paper_id": record.get("paper_id"),
                    "theory_role": record.get("theory_role"),
                    "section": record.get("section")
                })
            
            return {
                "connections": connections,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theory-phenomenon connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/connections/aggregated")
async def get_aggregated_connections(
    theory_name: Optional[str] = Query(None),
    phenomenon_name: Optional[str] = Query(None),
    min_paper_count: int = Query(2, ge=1),
    sort_by: str = Query("avg_strength", regex="^(avg_strength|paper_count|max_strength)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get aggregated connection strength statistics across papers
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # Check if aggregated relationships exist
            check_result = session.run("""
                MATCH ()-[r:EXPLAINS_PHENOMENON_AGGREGATED]->()
                RETURN count(r) as count
            """).single()
            
            if check_result and check_result["count"] == 0:
                # No aggregated data yet - return message
                return {
                    "aggregated_connections": [],
                    "total": 0,
                    "message": "No aggregated data found. Run compute_connection_strength_aggregation.py first."
                }
            
            # Build query
            where_clauses = ["agg.paper_count >= $min_paper_count"]
            params = {
                "min_paper_count": min_paper_count,
                "limit": limit
            }
            
            if theory_name:
                where_clauses.append("t.name = $theory_name")
                params["theory_name"] = theory_name
            
            if phenomenon_name:
                where_clauses.append("ph.phenomenon_name = $phenomenon_name")
                params["phenomenon_name"] = phenomenon_name
            
            where_clause = " AND ".join(where_clauses)
            
            # Get total count
            count_query = f"""
                MATCH (t:Theory)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                WHERE {where_clause}
                RETURN count(agg) as total
            """
            total_result = session.run(count_query, **params).single()
            total = total_result["total"] if total_result else 0
            
            # Get aggregated connections
            order_clause = f"agg.{sort_by} {order.upper()}"
            query = f"""
                MATCH (t:Theory)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                WHERE {where_clause}
                RETURN t.name as theory_name,
                       t.domain as theory_domain,
                       ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain as phenomenon_domain,
                       agg.avg_strength,
                       agg.paper_count,
                       agg.max_strength,
                       agg.min_strength,
                       agg.std_strength,
                       agg.avg_role_weight,
                       agg.avg_section_score,
                       agg.avg_keyword_score,
                       agg.avg_semantic_score,
                       agg.avg_explicit_bonus,
                       agg.paper_ids
                ORDER BY {order_clause}
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            aggregated_connections = []
            
            for record in result:
                aggregated_connections.append({
                    "theory": {
                        "name": record.get("theory_name"),
                        "domain": record.get("theory_domain")
                    },
                    "phenomenon": {
                        "phenomenon_name": record.get("phenomenon_name"),
                        "phenomenon_type": record.get("phenomenon_type"),
                        "domain": record.get("phenomenon_domain")
                    },
                    "avg_strength": round(record.get("avg_strength", 0.0), 3),
                    "paper_count": record.get("paper_count", 0),
                    "max_strength": round(record.get("max_strength", 0.0), 3),
                    "min_strength": round(record.get("min_strength", 0.0), 3),
                    "std_strength": round(record.get("std_strength", 0.0), 3) if record.get("std_strength") else None,
                    "avg_factor_scores": {
                        "role_weight": round(record.get("avg_role_weight", 0.0), 3),
                        "section_score": round(record.get("avg_section_score", 0.0), 3),
                        "keyword_score": round(record.get("avg_keyword_score", 0.0), 3),
                        "semantic_score": round(record.get("avg_semantic_score", 0.0), 3),
                        "explicit_bonus": round(record.get("avg_explicit_bonus", 0.0), 3)
                    },
                    "paper_ids": record.get("paper_ids", [])
                })
            
            return {
                "aggregated_connections": aggregated_connections,
                "total": total
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting aggregated connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/phenomena")
async def list_phenomena(
    domain: Optional[str] = Query(None),
    phenomenon_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List all phenomena with optional filters
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # Build query
            where_clauses = []
            params = {"limit": limit, "offset": offset}
            
            if domain:
                where_clauses.append("ph.domain = $domain")
                params["domain"] = domain
            
            if phenomenon_type:
                where_clauses.append("ph.phenomenon_type = $phenomenon_type")
                params["phenomenon_type"] = phenomenon_type
            
            if search:
                where_clauses.append("toLower(ph.phenomenon_name) CONTAINS toLower($search)")
                params["search"] = search
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # Get total count
            count_query = f"""
                MATCH (ph:Phenomenon)
                WHERE {where_clause}
                RETURN count(ph) as total
            """
            total_result = session.run(count_query, **params).single()
            total = total_result["total"] if total_result else 0
            
            # Get phenomena with statistics
            query = f"""
                MATCH (ph:Phenomenon)
                WHERE {where_clause}
                OPTIONAL MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph)
                OPTIONAL MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph)
                WITH ph,
                     count(DISTINCT t) as theory_count,
                     count(DISTINCT p) as paper_count
                RETURN ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain,
                       ph.description,
                       theory_count,
                       paper_count
                ORDER BY ph.phenomenon_name
                SKIP $offset
                LIMIT $limit
            """
            
            result = session.run(query, **params)
            phenomena = []
            
            for record in result:
                phenomena.append({
                    "phenomenon_name": record.get("phenomenon_name"),
                    "phenomenon_type": record.get("phenomenon_type"),
                    "domain": record.get("domain"),
                    "description": record.get("description"),
                    "theory_count": record.get("theory_count", 0),
                    "paper_count": record.get("paper_count", 0)
                })
            
            return {
                "phenomena": phenomena,
                "total": total
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing phenomena: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/top-connections")
async def get_top_connections(
    n: int = Query(10, ge=1, le=100),
    type: str = Query("all", regex="^(all|aggregated|individual)$"),
    min_paper_count: Optional[int] = Query(None, ge=1)
):
    """
    Get top N connections by strength
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            top_connections = []
            
            if type in ["all", "aggregated"]:
                # Get top aggregated connections
                where_clause = ""
                params = {"n": n}
                
                if min_paper_count:
                    where_clause = "WHERE agg.paper_count >= $min_paper_count"
                    params["min_paper_count"] = min_paper_count
                
                query = f"""
                    MATCH (t:Theory)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                    {where_clause}
                    RETURN t.name as theory_name,
                           ph.phenomenon_name,
                           agg.avg_strength as strength,
                           agg.paper_count,
                           'aggregated' as type
                    ORDER BY agg.avg_strength DESC
                    LIMIT $n
                """
                
                result = session.run(query, **params)
                for record in result:
                    top_connections.append({
                        "theory": record.get("theory_name"),
                        "phenomenon": record.get("phenomenon_name"),
                        "strength": round(record.get("strength", 0.0), 3),
                        "paper_count": record.get("paper_count", 0),
                        "type": "aggregated"
                    })
            
            if type in ["all", "individual"]:
                # Get top individual connections
                query = """
                    MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    RETURN t.name as theory_name,
                           ph.phenomenon_name,
                           r.connection_strength as strength,
                           1 as paper_count,
                           'individual' as type
                    ORDER BY r.connection_strength DESC
                    LIMIT $n
                """
                
                result = session.run(query, {"n": n})
                for record in result:
                    top_connections.append({
                        "theory": record.get("theory_name"),
                        "phenomenon": record.get("phenomenon_name"),
                        "strength": round(record.get("strength", 0.0), 3),
                        "paper_count": 1,
                        "type": "individual"
                    })
            
            # Sort by strength and take top N
            top_connections.sort(key=lambda x: x["strength"], reverse=True)
            top_connections = top_connections[:n]
            
            return {"top_connections": top_connections}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# REMAINING CONNECTION STRENGTH ENDPOINTS (Phase 2 - Pending)
# ============================================================================

@app.get("/api/connections/theory-phenomenon/{theory_name}")
async def get_phenomena_for_theory(
    theory_name: str,
    min_strength: float = Query(0.3, ge=0.0, le=1.0, description="Minimum connection strength")
):
    """
    Get all phenomena explained by a specific theory
    
    Returns all phenomena that this theory explains, with connection strengths
    across all papers.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # First check if theory exists
            theory_check = session.run("""
                MATCH (t:Theory {name: $theory_name})
                RETURN t.name as name, t.domain as domain
            """, theory_name=theory_name).single()
            
            if not theory_check:
                raise HTTPException(status_code=404, detail=f"Theory '{theory_name}' not found")
            
            # Get all phenomena explained by this theory
            # Use aggregated if available, otherwise use individual connections
            result = session.run("""
                MATCH (t:Theory {name: $theory_name})
                OPTIONAL MATCH (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                WHERE agg.avg_strength >= $min_strength
                WITH t, ph, agg.avg_strength as strength, agg.paper_count as paper_count, 
                     agg.paper_ids as paper_ids, 'aggregated' as source
                
                // Fallback to individual if no aggregated
                OPTIONAL MATCH (t)-[r:EXPLAINS_PHENOMENON]->(ph2:Phenomenon)
                WHERE r.connection_strength >= $min_strength
                  AND NOT EXISTS((t)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(ph2))
                WITH t, 
                     collect(DISTINCT {
                         phenomenon: ph,
                         strength: strength,
                         paper_count: paper_count,
                         paper_ids: paper_ids,
                         source: source
                     }) + collect(DISTINCT {
                         phenomenon: ph2,
                         strength: r.connection_strength,
                         paper_count: 1,
                         paper_ids: [r.paper_id],
                         source: 'individual'
                     }) as all_phenomena
                
                UNWIND all_phenomena as phen
                WITH t, phen.phenomenon as ph, phen.strength as strength,
                     phen.paper_count as paper_count, phen.paper_ids as paper_ids
                WHERE ph IS NOT NULL
                
                WITH t, ph,
                     max(strength) as max_strength,
                     sum(paper_count) as total_paper_count,
                     collect(DISTINCT paper_ids) as all_paper_ids
                
                UNWIND all_paper_ids as paper_id_list
                UNWIND paper_id_list as paper_id
                WITH t, ph, max_strength, total_paper_count, 
                     collect(DISTINCT paper_id) as unique_paper_ids
                
                RETURN ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain as phenomenon_domain,
                       ph.description as phenomenon_description,
                       max_strength as connection_strength,
                       total_paper_count as paper_count,
                       unique_paper_ids as paper_ids
                ORDER BY max_strength DESC
            """, theory_name=theory_name, min_strength=min_strength)
            
            phenomena = []
            for record in result:
                phenomena.append({
                    "phenomenon_name": record.get("phenomenon_name"),
                    "phenomenon_type": record.get("phenomenon_type"),
                    "domain": record.get("phenomenon_domain"),
                    "description": record.get("phenomenon_description"),
                    "connection_strength": round(record.get("connection_strength", 0.0), 3),
                    "paper_count": record.get("paper_count", 0),
                    "paper_ids": record.get("paper_ids", [])
                })
            
            return {
                "theory": {
                    "name": theory_check["name"],
                    "domain": theory_check.get("domain")
                },
                "phenomena": phenomena,
                "total_phenomena": len(phenomena)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting phenomena for theory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/connections/phenomenon-theory/{phenomenon_name}")
async def get_theories_for_phenomenon(
    phenomenon_name: str,
    min_strength: float = Query(0.3, ge=0.0, le=1.0, description="Minimum connection strength")
):
    """
    Get all theories explaining a specific phenomenon
    
    Returns all theories that explain this phenomenon, with connection strengths
    across all papers.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # First check if phenomenon exists
            phenomenon_check = session.run("""
                MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                RETURN ph.phenomenon_name, ph.phenomenon_type, ph.domain, ph.description
            """, phenomenon_name=phenomenon_name).single()
            
            if not phenomenon_check:
                raise HTTPException(status_code=404, detail=f"Phenomenon '{phenomenon_name}' not found")
            
            # Get all theories explaining this phenomenon
            # Use aggregated if available, otherwise use individual connections
            result = session.run("""
                MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                OPTIONAL MATCH (t:Theory)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph)
                WHERE agg.avg_strength >= $min_strength
                WITH ph, t, agg.avg_strength as strength, agg.paper_count as paper_count,
                     agg.paper_ids as paper_ids, 'aggregated' as source
                
                // Fallback to individual if no aggregated
                OPTIONAL MATCH (t2:Theory)-[r:EXPLAINS_PHENOMENON]->(ph)
                WHERE r.connection_strength >= $min_strength
                  AND NOT EXISTS((t2)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(ph))
                WITH ph,
                     collect(DISTINCT {
                         theory: t,
                         strength: strength,
                         paper_count: paper_count,
                         paper_ids: paper_ids,
                         source: source
                     }) + collect(DISTINCT {
                         theory: t2,
                         strength: r.connection_strength,
                         paper_count: 1,
                         paper_ids: [r.paper_id],
                         source: 'individual',
                         role: r.theory_role
                     }) as all_theories
                
                UNWIND all_theories as th
                WITH ph, th.theory as t, th.strength as strength,
                     th.paper_count as paper_count, th.paper_ids as paper_ids,
                     th.role as role
                WHERE t IS NOT NULL
                
                WITH ph, t,
                     max(strength) as max_strength,
                     sum(paper_count) as total_paper_count,
                     collect(DISTINCT paper_ids) as all_paper_ids,
                     collect(DISTINCT role) as roles_used
                
                UNWIND all_paper_ids as paper_id_list
                UNWIND paper_id_list as paper_id
                WITH ph, t, max_strength, total_paper_count,
                     collect(DISTINCT paper_id) as unique_paper_ids,
                     roles_used
                
                RETURN t.name as theory_name,
                       t.domain as theory_domain,
                       max_strength as connection_strength,
                       total_paper_count as paper_count,
                       unique_paper_ids as paper_ids,
                       roles_used
                ORDER BY max_strength DESC
            """, phenomenon_name=phenomenon_name, min_strength=min_strength)
            
            theories = []
            for record in result:
                theories.append({
                    "theory_name": record.get("theory_name"),
                    "domain": record.get("theory_domain"),
                    "connection_strength": round(record.get("connection_strength", 0.0), 3),
                    "paper_count": record.get("paper_count", 0),
                    "paper_ids": record.get("paper_ids", []),
                    "theory_role": record.get("roles_used", [])[0] if record.get("roles_used") else None
                })
            
            return {
                "phenomenon": {
                    "phenomenon_name": phenomenon_check["phenomenon_name"],
                    "phenomenon_type": phenomenon_check.get("phenomenon_type"),
                    "domain": phenomenon_check.get("domain"),
                    "description": phenomenon_check.get("description")
                },
                "theories": theories,
                "total_theories": len(theories)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theories for phenomenon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/phenomena/{phenomenon_name}")
async def get_phenomenon_detail(phenomenon_name: str):
    """
    Get detailed information about a phenomenon
    
    Returns full phenomenon details, all theories explaining it, all papers studying it,
    and statistics.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # Get phenomenon details
            phenomenon_result = session.run("""
                MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                RETURN ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain,
                       ph.description,
                       ph.context
            """, phenomenon_name=phenomenon_name).single()
            
            if not phenomenon_result:
                raise HTTPException(status_code=404, detail=f"Phenomenon '{phenomenon_name}' not found")
            
            # Get all theories explaining this phenomenon
            theories_result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                WITH t, r, ph
                OPTIONAL MATCH (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph)
                WITH t, r, ph,
                     COALESCE(agg.avg_strength, r.connection_strength) as strength,
                     COALESCE(agg.paper_count, 1) as paper_count
                RETURN DISTINCT t.name as theory_name,
                       t.domain as theory_domain,
                       strength,
                       paper_count,
                       r.theory_role as role
                ORDER BY strength DESC
            """, phenomenon_name=phenomenon_name).data()
            
            theories = []
            for record in theories_result:
                theories.append({
                    "theory_name": record.get("theory_name"),
                    "domain": record.get("theory_domain"),
                    "connection_strength": round(record.get("strength", 0.0), 3),
                    "paper_count": record.get("paper_count", 0),
                    "theory_role": record.get("role")
                })
            
            # Get all papers studying this phenomenon
            papers_result = session.run("""
                MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                RETURN p.paper_id,
                       p.title,
                       p.publication_year,
                       p.journal
                ORDER BY p.publication_year DESC
            """, phenomenon_name=phenomenon_name).data()
            
            papers = []
            for record in papers_result:
                papers.append({
                    "paper_id": record.get("paper_id"),
                    "title": record.get("title"),
                    "publication_year": record.get("publication_year"),
                    "journal": record.get("journal")
                })
            
            # Calculate statistics
            stats_result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                WITH r.connection_strength as strength
                RETURN count(strength) as total_theories,
                       avg(strength) as avg_connection_strength,
                       max(strength) as max_connection_strength,
                       min(strength) as min_connection_strength
            """, phenomenon_name=phenomenon_name).single()
            
            # Count papers
            paper_count_result = session.run("""
                MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                RETURN count(DISTINCT p) as total_papers
            """, phenomenon_name=phenomenon_name).single()
            
            return {
                "phenomenon": {
                    "phenomenon_name": phenomenon_result["phenomenon_name"],
                    "phenomenon_type": phenomenon_result.get("phenomenon_type"),
                    "domain": phenomenon_result.get("domain"),
                    "description": phenomenon_result.get("description"),
                    "context": phenomenon_result.get("context")
                },
                "theories": theories,
                "papers": papers,
                "statistics": {
                    "total_theories": stats_result.get("total_theories", 0) if stats_result else 0,
                    "total_papers": paper_count_result.get("total_papers", 0) if paper_count_result else 0,
                    "avg_connection_strength": round(stats_result.get("avg_connection_strength", 0.0), 3) if stats_result else 0.0,
                    "max_connection_strength": round(stats_result.get("max_connection_strength", 0.0), 3) if stats_result else 0.0,
                    "min_connection_strength": round(stats_result.get("min_connection_strength", 0.0), 3) if stats_result else 0.0
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting phenomenon detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/connection-strength-distribution")
async def get_connection_strength_distribution():
    """
    Get distribution of connection strengths
    
    Returns distribution statistics showing how many connections fall into
    each strength category (very_strong, strong, moderate, weak).
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            # Get distribution from individual connections
            result = session.run("""
                MATCH ()-[r:EXPLAINS_PHENOMENON]->()
                WITH r.connection_strength as strength
                RETURN count(strength) as total_connections,
                       avg(strength) as avg_strength,
                       percentileCont(strength, 0.5) as median_strength,
                       stDev(strength) as std_strength,
                       max(strength) as max_strength,
                       min(strength) as min_strength
            """).single()
            
            if not result or result.get("total_connections", 0) == 0:
                return {
                    "distribution": {
                        "very_strong": {"count": 0, "percentage": 0.0},
                        "strong": {"count": 0, "percentage": 0.0},
                        "moderate": {"count": 0, "percentage": 0.0},
                        "weak": {"count": 0, "percentage": 0.0}
                    },
                    "statistics": {
                        "total_connections": 0,
                        "avg_strength": 0.0,
                        "median_strength": 0.0,
                        "std_strength": 0.0
                    }
                }
            
            total = result.get("total_connections", 0)
            
            # Get counts for each category
            distribution_result = session.run("""
                MATCH ()-[r:EXPLAINS_PHENOMENON]->()
                WITH r.connection_strength as strength
                RETURN 
                    sum(CASE WHEN strength >= 0.8 THEN 1 ELSE 0 END) as very_strong,
                    sum(CASE WHEN strength >= 0.6 AND strength < 0.8 THEN 1 ELSE 0 END) as strong,
                    sum(CASE WHEN strength >= 0.4 AND strength < 0.6 THEN 1 ELSE 0 END) as moderate,
                    sum(CASE WHEN strength >= 0.3 AND strength < 0.4 THEN 1 ELSE 0 END) as weak
            """).single()
            
            very_strong = distribution_result.get("very_strong", 0) if distribution_result else 0
            strong = distribution_result.get("strong", 0) if distribution_result else 0
            moderate = distribution_result.get("moderate", 0) if distribution_result else 0
            weak = distribution_result.get("weak", 0) if distribution_result else 0
            
            return {
                "distribution": {
                    "very_strong": {
                        "count": very_strong,
                        "percentage": round((very_strong / total * 100) if total > 0 else 0, 1)
                    },
                    "strong": {
                        "count": strong,
                        "percentage": round((strong / total * 100) if total > 0 else 0, 1)
                    },
                    "moderate": {
                        "count": moderate,
                        "percentage": round((moderate / total * 100) if total > 0 else 0, 1)
                    },
                    "weak": {
                        "count": weak,
                        "percentage": round((weak / total * 100) if total > 0 else 0, 1)
                    }
                },
                "statistics": {
                    "total_connections": total,
                    "avg_strength": round(result.get("avg_strength", 0.0), 3),
                    "median_strength": round(result.get("median_strength", 0.0), 3),
                    "std_strength": round(result.get("std_strength", 0.0), 3),
                    "max_strength": round(result.get("max_strength", 0.0), 3),
                    "min_strength": round(result.get("min_strength", 0.0), 3)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection strength distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/connections/{connection_id}/factors")
async def get_connection_factors(connection_id: str):
    """
    Get detailed factor breakdown for a connection
    
    Connection ID format: "{theory_name}::{phenomenon_name}::{paper_id}"
    Or simplified: "{theory_name}::{phenomenon_name}" (uses aggregated if available)
    
    Returns detailed breakdown of all 5 factors with explanations.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        # Parse connection_id
        # Format: "theory_name::phenomenon_name::paper_id" or "theory_name::phenomenon_name"
        parts = connection_id.split("::")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid connection_id format. Use: 'theory_name::phenomenon_name::paper_id' or 'theory_name::phenomenon_name'")
        
        theory_name = parts[0]
        phenomenon_name = parts[1]
        paper_id = parts[2] if len(parts) > 2 else None
        
        with neo4j_service.driver.session() as session:
            # Try to get connection with paper_id first, then aggregated, then any
            if paper_id:
                result = session.run("""
                    MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON {
                        paper_id: $paper_id
                    }]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                    RETURN r.connection_strength,
                           r.role_weight,
                           r.section_score,
                           r.keyword_score,
                           r.semantic_score,
                           r.explicit_bonus,
                           r.theory_role,
                           r.section
                """, theory_name=theory_name, phenomenon_name=phenomenon_name, paper_id=paper_id).single()
            else:
                # Try aggregated first
                result = session.run("""
                    MATCH (t:Theory {name: $theory_name})-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                    RETURN agg.avg_strength as connection_strength,
                           agg.avg_role_weight as role_weight,
                           agg.avg_section_score as section_score,
                           agg.avg_keyword_score as keyword_score,
                           agg.avg_semantic_score as semantic_score,
                           agg.avg_explicit_bonus as explicit_bonus,
                           null as theory_role,
                           null as section
                """, theory_name=theory_name, phenomenon_name=phenomenon_name).single()
                
                # Fallback to any individual connection
                if not result:
                    result = session.run("""
                        MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                        RETURN r.connection_strength,
                               r.role_weight,
                               r.section_score,
                               r.keyword_score,
                               r.semantic_score,
                               r.explicit_bonus,
                               r.theory_role,
                               r.section
                        LIMIT 1
                    """, theory_name=theory_name, phenomenon_name=phenomenon_name).single()
            
            if not result:
                raise HTTPException(status_code=404, detail="Connection not found")
            
            connection_strength = round(result.get("connection_strength", 0.0), 3)
            role_weight = round(result.get("role_weight", 0.0), 3)
            section_score = round(result.get("section_score", 0.0), 3)
            keyword_score = round(result.get("keyword_score", 0.0), 3)
            semantic_score = round(result.get("semantic_score", 0.0), 3)
            explicit_bonus = round(result.get("explicit_bonus", 0.0), 3)
            
            # Calculate percentages
            total = connection_strength if connection_strength > 0 else 1.0
            
            # Generate explanations
            def get_role_explanation(role_weight):
                if role_weight >= 0.35:
                    return "Primary theory (40% base weight)"
                elif role_weight >= 0.15:
                    return "Supporting theory (20% base weight)"
                elif role_weight >= 0.1:
                    return "Extending or challenging theory (10-15% base weight)"
                else:
                    return "Theory role not specified"
            
            def get_section_explanation(section_score):
                if section_score >= 0.15:
                    return "Same section (20% boost)"
                elif section_score >= 0.08:
                    return "Adjacent sections (10% boost)"
                else:
                    return "Distant sections (5% boost)"
            
            def get_keyword_explanation(keyword_score):
                if keyword_score >= 0.15:
                    return "Strong keyword overlap (Jaccard similarity ≥ 0.5)"
                elif keyword_score >= 0.08:
                    return "Moderate keyword overlap (Jaccard similarity 0.2-0.5)"
                else:
                    return "Weak keyword overlap (Jaccard similarity < 0.2)"
            
            def get_semantic_explanation(semantic_score):
                if semantic_score >= 0.15:
                    return "Very similar meaning (cosine similarity ≥ 0.7)"
                elif semantic_score >= 0.1:
                    return "Similar meaning (cosine similarity 0.5-0.7)"
                else:
                    return "Somewhat similar meaning (cosine similarity 0.3-0.5)"
            
            def get_explicit_explanation(explicit_bonus):
                if explicit_bonus >= 0.08:
                    return "Exact phenomenon mention (10% bonus)"
                elif explicit_bonus >= 0.05:
                    return "Strong key words match (5-8% bonus)"
                else:
                    return "No explicit mention"
            
            factors = {
                "role_weight": {
                    "value": role_weight,
                    "percentage": round((role_weight / total * 100) if total > 0 else 0, 1),
                    "explanation": get_role_explanation(role_weight)
                },
                "section_score": {
                    "value": section_score,
                    "percentage": round((section_score / total * 100) if total > 0 else 0, 1),
                    "explanation": get_section_explanation(section_score)
                },
                "keyword_score": {
                    "value": keyword_score,
                    "percentage": round((keyword_score / total * 100) if total > 0 else 0, 1),
                    "explanation": get_keyword_explanation(keyword_score)
                },
                "semantic_score": {
                    "value": semantic_score,
                    "percentage": round((semantic_score / total * 100) if total > 0 else 0, 1),
                    "explanation": get_semantic_explanation(semantic_score)
                },
                "explicit_bonus": {
                    "value": explicit_bonus,
                    "percentage": round((explicit_bonus / total * 100) if total > 0 else 0, 1),
                    "explanation": get_explicit_explanation(explicit_bonus)
                }
            }
            
            return {
                "connection": {
                    "theory": theory_name,
                    "phenomenon": phenomenon_name,
                    "connection_strength": connection_strength,
                    "paper_id": paper_id,
                    "theory_role": result.get("theory_role"),
                    "section": result.get("section")
                },
                "factors": factors
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 1.1: KNOWLEDGE REPUTATION & STRENGTH METRICS
# ============================================================================

@app.get("/api/metrics/{entity_type}/{entity_name}")
async def get_knowledge_metrics(
    entity_type: str,
    entity_name: str
):
    """
    Get knowledge reputation and strength metrics for a theory, method, or phenomenon
    
    Computes:
    - Momentum: Usage over time (for theories/methods)
    - Obsolescence: Decline rate (for methods)
    - Hotness: Recent study volume and diversity (for phenomena)
    - Evidence Strength: Average connection strength, paper count, diversity
    
    Returns both computed metrics and LLM-generated narrative summary.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        # Validate entity type
        valid_types = ["theory", "method", "phenomenon"]
        if entity_type.lower() not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid entity_type. Must be one of: {valid_types}"
            )
        
        entity_type_lower = entity_type.lower()
        
        # Normalize entity name using EntityNormalizer
        from entity_normalizer import get_normalizer
        normalizer = get_normalizer()
        
        # URL decode the entity name (handles spaces, special chars)
        import urllib.parse
        entity_name_decoded = urllib.parse.unquote(entity_name)
        
        # Normalize to canonical form
        if entity_type_lower == "theory":
            normalized_name = normalizer.normalize_theory(entity_name_decoded)
        elif entity_type_lower == "method":
            normalized_name = normalizer.normalize_method(entity_name_decoded)
        elif entity_type_lower == "phenomenon":
            normalized_name = normalizer.normalize_phenomenon(entity_name_decoded)
        else:
            normalized_name = entity_name_decoded
        
        # If normalization didn't change the name, try to find similar entity in graph
        if normalized_name == entity_name_decoded:
            # Try fuzzy search in Neo4j to find closest match
            with neo4j_service.driver.session() as session:
                if entity_type_lower == "theory":
                    fuzzy_match = session.run("""
                        MATCH (t:Theory)
                        WHERE toLower(t.name) CONTAINS toLower($search_name)
                           OR toLower($search_name) CONTAINS toLower(t.name)
                        RETURN t.name as name
                        ORDER BY size(t.name) ASC
                        LIMIT 1
                    """, search_name=entity_name_decoded).single()
                elif entity_type_lower == "method":
                    fuzzy_match = session.run("""
                        MATCH (m:Method)
                        WHERE toLower(m.name) CONTAINS toLower($search_name)
                           OR toLower($search_name) CONTAINS toLower(m.name)
                        RETURN m.name as name
                        ORDER BY size(m.name) ASC
                        LIMIT 1
                    """, search_name=entity_name_decoded).single()
                elif entity_type_lower == "phenomenon":
                    fuzzy_match = session.run("""
                        MATCH (ph:Phenomenon)
                        WHERE toLower(ph.phenomenon_name) CONTAINS toLower($search_name)
                           OR toLower($search_name) CONTAINS toLower(ph.phenomenon_name)
                        RETURN ph.phenomenon_name as name
                        ORDER BY size(ph.phenomenon_name) ASC
                        LIMIT 1
                    """, search_name=entity_name_decoded).single()
                else:
                    fuzzy_match = None
                
                if fuzzy_match:
                    normalized_name = fuzzy_match.get("name", normalized_name)
        
        with neo4j_service.driver.session() as session:
            metrics = {}
            supporting_data = {}
            
            if entity_type_lower == "theory":
                metrics, supporting_data = await _compute_theory_metrics(
                    session, normalized_name
                )
            elif entity_type_lower == "method":
                metrics, supporting_data = await _compute_method_metrics(
                    session, normalized_name
                )
            elif entity_type_lower == "phenomenon":
                metrics, supporting_data = await _compute_phenomenon_metrics(
                    session, normalized_name
                )
            
            # If no metrics found, check if entity exists at all
            if not metrics and not supporting_data:
                # Check if entity exists
                exists = False
                if entity_type_lower == "theory":
                    exists = session.run("""
                        MATCH (t:Theory {name: $name})
                        RETURN count(t) as count
                    """, name=normalized_name).single().get("count", 0) > 0
                elif entity_type_lower == "method":
                    exists = session.run("""
                        MATCH (m:Method {name: $name})
                        RETURN count(m) as count
                    """, name=normalized_name).single().get("count", 0) > 0
                elif entity_type_lower == "phenomenon":
                    exists = session.run("""
                        MATCH (ph:Phenomenon {phenomenon_name: $name})
                        RETURN count(ph) as count
                    """, name=normalized_name).single().get("count", 0) > 0
                
                if not exists:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{entity_type.capitalize()} '{entity_name_decoded}' not found. "
                               f"Tried normalized name: '{normalized_name}'. "
                               f"Use /api/{entity_type_lower}s/search?q=... to find available entities."
                    )
            
            # Generate LLM narrative summary
            llm_client = LLMClient()
            narrative = await _generate_metrics_narrative(
                llm_client, entity_type_lower, entity_name, metrics, supporting_data
            )
            
            return {
                "entity": {
                    "type": entity_type_lower,
                    "name": normalized_name,
                    "originalName": entity_name_decoded,
                    "normalized": normalized_name != entity_name_decoded
                },
                "metrics": metrics,
                "supportingData": supporting_data,
                "narrative": narrative,
                "timestamp": datetime.now().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _compute_theory_metrics(session, theory_name: str) -> Tuple[Dict, Dict]:
    """Compute metrics for a theory"""
    metrics = {}
    supporting_data = {}
    
    # 1. Momentum: Usage over time (papers per year)
    momentum_result = session.run("""
        MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: $theory_name})
        WHERE p.publication_year IS NOT NULL
        WITH p.publication_year as year, count(p) as paper_count
        ORDER BY year
        RETURN collect({year: year, count: paper_count}) as usage_over_time,
               min(year) as first_year,
               max(year) as last_year,
               sum(paper_count) as total_papers
    """, theory_name=theory_name).single()
    
    if momentum_result:
        usage_over_time = momentum_result.get("usage_over_time", [])
        first_year = momentum_result.get("first_year", 0)
        last_year = momentum_result.get("last_year", 0)
        total_papers = momentum_result.get("total_papers", 0)
        
        # Calculate momentum (recent usage vs historical)
        if len(usage_over_time) >= 2:
            recent_years = [u for u in usage_over_time if u["year"] >= last_year - 3]
            historical_years = [u for u in usage_over_time if u["year"] < last_year - 3]
            
            recent_avg = sum(u["count"] for u in recent_years) / len(recent_years) if recent_years else 0
            historical_avg = sum(u["count"] for u in historical_years) / len(historical_years) if historical_years else 0
            
            if historical_avg > 0:
                momentum = (recent_avg - historical_avg) / historical_avg
            else:
                momentum = 1.0 if recent_avg > 0 else 0.0
        else:
            momentum = 0.0
        
        metrics["momentum"] = round(momentum, 3)
        supporting_data["usage_over_time"] = usage_over_time
        supporting_data["first_year"] = first_year
        supporting_data["last_year"] = last_year
        supporting_data["total_papers"] = total_papers
    
    # 2. Evidence Strength: Connection strength to phenomena
    strength_result = session.run("""
        MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
        WITH r.connection_strength as strength
        WHERE strength IS NOT NULL
        RETURN avg(strength) as avg_strength,
               max(strength) as max_strength,
               min(strength) as min_strength,
               count(strength) as connection_count
    """, theory_name=theory_name).single()
    
    if strength_result:
        avg_strength = strength_result.get("avg_strength", 0.0) or 0.0
        max_strength = strength_result.get("max_strength", 0.0) or 0.0
        min_strength = strength_result.get("min_strength", 0.0) or 0.0
        connection_count = strength_result.get("connection_count", 0)
        
        metrics["evidenceStrength"] = {
            "avgConnectionStrength": round(avg_strength, 3),
            "maxConnectionStrength": round(max_strength, 3),
            "minConnectionStrength": round(min_strength, 3),
            "phenomenonCount": connection_count
        }
        supporting_data["connection_strengths"] = {
            "avg": avg_strength,
            "max": max_strength,
            "min": min_strength,
            "count": connection_count
        }
    
    # 3. Diversity: Number of distinct phenomena explained
    diversity_result = session.run("""
        MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
        RETURN count(DISTINCT ph) as phenomenon_diversity
    """, theory_name=theory_name).single()
    
    if diversity_result:
        diversity = diversity_result.get("phenomenon_diversity", 0)
        metrics["diversity"] = diversity
        supporting_data["phenomenon_diversity"] = diversity
    
    return metrics, supporting_data

async def _compute_method_metrics(session, method_name: str) -> Tuple[Dict, Dict]:
    """Compute metrics for a method"""
    metrics = {}
    supporting_data = {}
    
    # 1. Momentum: Usage over time
    momentum_result = session.run("""
        MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: $method_name})
        WHERE p.publication_year IS NOT NULL
        WITH p.publication_year as year, count(p) as paper_count
        ORDER BY year
        RETURN collect({year: year, count: paper_count}) as usage_over_time,
               min(year) as first_year,
               max(year) as last_year,
               sum(paper_count) as total_papers
    """, method_name=method_name).single()
    
    if momentum_result:
        usage_over_time = momentum_result.get("usage_over_time", [])
        first_year = momentum_result.get("first_year", 0)
        last_year = momentum_result.get("last_year", 0)
        total_papers = momentum_result.get("total_papers", 0)
        
        # Calculate momentum
        if len(usage_over_time) >= 2:
            recent_years = [u for u in usage_over_time if u["year"] >= last_year - 3]
            historical_years = [u for u in usage_over_time if u["year"] < last_year - 3]
            
            recent_avg = sum(u["count"] for u in recent_years) / len(recent_years) if recent_years else 0
            historical_avg = sum(u["count"] for u in historical_years) / len(historical_years) if historical_years else 0
            
            if historical_avg > 0:
                momentum = (recent_avg - historical_avg) / historical_avg
            else:
                momentum = 1.0 if recent_avg > 0 else 0.0
        else:
            momentum = 0.0
        
        metrics["momentum"] = round(momentum, 3)
        supporting_data["usage_over_time"] = usage_over_time
        supporting_data["first_year"] = first_year
        supporting_data["last_year"] = last_year
        supporting_data["total_papers"] = total_papers
    
    # 2. Obsolescence: Decline rate (negative momentum)
    if metrics.get("momentum", 0) < 0:
        metrics["obsolescence"] = abs(round(metrics["momentum"], 3))
    else:
        metrics["obsolescence"] = 0.0
    
    # 3. Adoption Rate: Rate of new papers using this method
    if momentum_result and total_papers > 0:
        years_span = last_year - first_year + 1 if last_year > first_year else 1
        adoption_rate = total_papers / years_span if years_span > 0 else 0
        metrics["adoptionRate"] = round(adoption_rate, 2)
        supporting_data["adoption_rate"] = adoption_rate
    
    return metrics, supporting_data

async def _compute_phenomenon_metrics(session, phenomenon_name: str) -> Tuple[Dict, Dict]:
    """Compute metrics for a phenomenon"""
    metrics = {}
    supporting_data = {}
    
    # 1. Hotness: Recent study volume and diversity
    hotness_result = session.run("""
        MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
        WHERE p.publication_year IS NOT NULL
        WITH p.publication_year as year, count(p) as paper_count
        ORDER BY year DESC
        RETURN collect({year: year, count: paper_count}) as usage_over_time,
               max(year) as most_recent_year,
               sum(paper_count) as total_papers
    """, phenomenon_name=phenomenon_name).single()
    
    if hotness_result:
        usage_over_time = hotness_result.get("usage_over_time", [])
        most_recent_year = hotness_result.get("most_recent_year", 0)
        total_papers = hotness_result.get("total_papers", 0)
        
        # Calculate hotness (recent papers in last 3 years)
        recent_papers = sum(
            u["count"] for u in usage_over_time 
            if u["year"] >= most_recent_year - 2
        )
        
        # Diversity: Number of distinct theories explaining this phenomenon
        diversity_result = session.run("""
            MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
            RETURN count(DISTINCT t) as theory_diversity
        """, phenomenon_name=phenomenon_name).single()
        
        theory_diversity = diversity_result.get("theory_diversity", 0) if diversity_result else 0
        
        # Hotness score: combination of recent papers and diversity
        hotness_score = (recent_papers * 0.6) + (theory_diversity * 0.4)
        
        metrics["hotness"] = round(hotness_score, 2)
        metrics["recentPapers"] = recent_papers
        metrics["theoryDiversity"] = theory_diversity
        supporting_data["usage_over_time"] = usage_over_time
        supporting_data["most_recent_year"] = most_recent_year
        supporting_data["total_papers"] = total_papers
    
    # 2. Evidence Strength: Average connection strength from theories
    strength_result = session.run("""
        MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
        WITH r.connection_strength as strength
        WHERE strength IS NOT NULL
        RETURN avg(strength) as avg_strength,
               max(strength) as max_strength,
               min(strength) as min_strength,
               count(strength) as theory_count
    """, phenomenon_name=phenomenon_name).single()
    
    if strength_result:
        avg_strength = strength_result.get("avg_strength", 0.0) or 0.0
        max_strength = strength_result.get("max_strength", 0.0) or 0.0
        min_strength = strength_result.get("min_strength", 0.0) or 0.0
        theory_count = strength_result.get("theory_count", 0)
        
        metrics["evidenceStrength"] = {
            "avgConnectionStrength": round(avg_strength, 3),
            "maxConnectionStrength": round(max_strength, 3),
            "minConnectionStrength": round(min_strength, 3),
            "theoryCount": theory_count
        }
        supporting_data["connection_strengths"] = {
            "avg": avg_strength,
            "max": max_strength,
            "min": min_strength,
            "count": theory_count
        }
    
    return metrics, supporting_data

async def _generate_metrics_narrative(
    llm_client: LLMClient,
    entity_type: str,
    entity_name: str,
    metrics: Dict[str, Any],
    supporting_data: Dict[str, Any]
) -> str:
    """Generate LLM narrative summary of metrics"""
    try:
        # Prepare context for LLM
        context = f"""
        Knowledge Metrics for {entity_type.upper()}: {entity_name}
        
        Metrics:
        {json.dumps(metrics, indent=2)}
        
        Supporting Data:
        - Total papers: {supporting_data.get('total_papers', 0)}
        - First year: {supporting_data.get('first_year', 'N/A')}
        - Last year: {supporting_data.get('last_year', supporting_data.get('most_recent_year', 'N/A'))}
        """
        
        if entity_type == "theory":
            prompt = f"""
            You are a research intelligence analyst. Based on the following metrics for the theory "{entity_name}",
            provide a concise narrative summary (2-3 paragraphs) that explains:
            
            1. The theory's momentum (is it growing, stable, or declining in usage?)
            2. Its evidence strength (how well-supported is it by connections to phenomena?)
            3. Its diversity (how many different phenomena does it explain?)
            4. Overall assessment of the theory's reputation and standing in the field
            
            Metrics Data:
            {context}
            
            Write in a clear, academic style suitable for researchers.
            """
        elif entity_type == "method":
            prompt = f"""
            You are a research intelligence analyst. Based on the following metrics for the method "{entity_name}",
            provide a concise narrative summary (2-3 paragraphs) that explains:
            
            1. The method's momentum and adoption rate
            2. Whether it's becoming obsolete or gaining traction
            3. Its usage patterns over time
            4. Overall assessment of the method's current standing in the field
            
            Metrics Data:
            {context}
            
            Write in a clear, academic style suitable for researchers.
            """
        else:  # phenomenon
            prompt = f"""
            You are a research intelligence analyst. Based on the following metrics for the phenomenon "{entity_name}",
            provide a concise narrative summary (2-3 paragraphs) that explains:
            
            1. The phenomenon's "hotness" (how actively is it being studied recently?)
            2. Its evidence strength (how well-explained is it by theories?)
            3. The diversity of theories explaining it
            4. Overall assessment of the phenomenon's importance and research activity
            
            Metrics Data:
            {context}
            
            Write in a clear, academic style suitable for researchers.
            """
        
        # Use LLM to generate narrative
        research_data = {"metrics": metrics, "supporting_data": supporting_data}
        narrative = llm_client.generate_answer(
            f"Summarize the knowledge metrics for this {entity_type}",
            research_data
        )
        
        # If LLM fails, generate fallback
        if not narrative or len(narrative) < 50:
            narrative = _generate_fallback_narrative(entity_type, entity_name, metrics, supporting_data)
        
        return narrative
        
    except Exception as e:
        logger.error(f"Error generating metrics narrative: {e}")
        return _generate_fallback_narrative(entity_type, entity_name, metrics, supporting_data)

def _generate_fallback_narrative(
    entity_type: str,
    entity_name: str,
    metrics: Dict[str, Any],
    supporting_data: Dict[str, Any]
) -> str:
    """Generate fallback narrative without LLM"""
    total_papers = supporting_data.get("total_papers", 0)
    
    if entity_type == "theory":
        momentum = metrics.get("momentum", 0)
        momentum_desc = "growing" if momentum > 0.1 else "stable" if momentum > -0.1 else "declining"
        evidence = metrics.get("evidenceStrength", {})
        avg_strength = evidence.get("avgConnectionStrength", 0)
        
        return f"""
        The theory "{entity_name}" has been used in {total_papers} papers. 
        Its usage shows a {momentum_desc} trend (momentum: {momentum:.2f}).
        The theory explains {evidence.get('phenomenonCount', 0)} distinct phenomena with an average 
        connection strength of {avg_strength:.2f}, indicating {'strong' if avg_strength > 0.7 else 'moderate' if avg_strength > 0.5 else 'weak'} 
        empirical support.
        """
    elif entity_type == "method":
        momentum = metrics.get("momentum", 0)
        obsolescence = metrics.get("obsolescence", 0)
        adoption = metrics.get("adoptionRate", 0)
        
        return f"""
        The method "{entity_name}" has been used in {total_papers} papers.
        It shows a {'growing' if momentum > 0.1 else 'stable' if momentum > -0.1 else 'declining'} 
        trend with an adoption rate of {adoption:.1f} papers per year.
        {'The method appears to be becoming less common.' if obsolescence > 0.2 else 'The method maintains steady usage.'}
        """
    else:  # phenomenon
        hotness = metrics.get("hotness", 0)
        recent = metrics.get("recentPapers", 0)
        diversity = metrics.get("theoryDiversity", 0)
        
        return f"""
        The phenomenon "{entity_name}" has been studied in {total_papers} papers, with {recent} papers 
        in the last 3 years. It is explained by {diversity} distinct theories, indicating 
        {'high' if diversity > 3 else 'moderate' if diversity > 1 else 'limited'} theoretical diversity.
        The phenomenon shows {'high' if hotness > 5 else 'moderate' if hotness > 2 else 'low'} 
        current research activity.
        """

# ============================================================================
# DISCOVERY ENDPOINTS: Search and list entities
# ============================================================================

@app.get("/api/theories/search")
async def search_theories(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search for theories by name
    Returns list of matching theories with basic info
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)
                WHERE toLower(t.name) CONTAINS toLower($query)
                OPTIONAL MATCH (p:Paper)-[:USES_THEORY]->(t)
                WITH t, count(DISTINCT p) as paper_count
                OPTIONAL MATCH (t)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, paper_count, count(DISTINCT ph) as phenomenon_count
                RETURN t.name as name,
                       t.domain as domain,
                       paper_count,
                       phenomenon_count
                ORDER BY paper_count DESC, phenomenon_count DESC
                LIMIT $limit
            """, query=q, limit=limit).data()
            
            theories = [
                {
                    "name": record.get("name"),
                    "domain": record.get("domain"),
                    "paperCount": record.get("paper_count", 0),
                    "phenomenonCount": record.get("phenomenon_count", 0)
                }
                for record in result
            ]
            
            return {
                "query": q,
                "theories": theories,
                "total": len(theories)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching theories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/methods/search")
async def search_methods(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search for methods by name
    Returns list of matching methods with basic info
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            result = session.run("""
                MATCH (m:Method)
                WHERE toLower(m.name) CONTAINS toLower($query)
                OPTIONAL MATCH (p:Paper)-[:USES_METHOD]->(m)
                WITH m, count(DISTINCT p) as paper_count
                RETURN m.name as name,
                       m.type as type,
                       m.category as category,
                       paper_count
                ORDER BY paper_count DESC
                LIMIT $limit
            """, query=q, limit=limit).data()
            
            methods = [
                {
                    "name": record.get("name"),
                    "type": record.get("type"),
                    "category": record.get("category"),
                    "paperCount": record.get("paper_count", 0)
                }
                for record in result
            ]
            
            return {
                "query": q,
                "methods": methods,
                "total": len(methods)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/phenomena/search")
async def search_phenomena(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Search for phenomena by name
    Returns list of matching phenomena with basic info
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        with neo4j_service.driver.session() as session:
            result = session.run("""
                MATCH (ph:Phenomenon)
                WHERE toLower(ph.phenomenon_name) CONTAINS toLower($query)
                OPTIONAL MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph)
                WITH ph, count(DISTINCT p) as paper_count
                OPTIONAL MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph)
                WITH ph, paper_count, count(DISTINCT t) as theory_count
                RETURN ph.phenomenon_name as name,
                       ph.phenomenon_type as type,
                       ph.domain as domain,
                       paper_count,
                       theory_count
                ORDER BY paper_count DESC, theory_count DESC
                LIMIT $limit
            """, query=q, limit=limit).data()
            
            phenomena = [
                {
                    "phenomenon_name": record.get("name"),
                    "phenomenon_type": record.get("type"),
                    "domain": record.get("domain"),
                    "paperCount": record.get("paper_count", 0),
                    "theoryCount": record.get("theory_count", 0)
                }
                for record in result
            ]
            
            return {
                "query": q,
                "phenomena": phenomena,
                "total": len(phenomena)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching phenomena: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/theories")
async def list_theories(
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("paper_count", description="Sort by: paper_count, name, phenomenon_count")
):
    """
    List all theories with pagination
    Useful for browsing available theories
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        valid_sorts = ["paper_count", "name", "phenomenon_count"]
        if sort_by not in valid_sorts:
            sort_by = "paper_count"
        
        with neo4j_service.driver.session() as session:
            # Get total count
            total_result = session.run("""
                MATCH (t:Theory)
                RETURN count(t) as total
            """).single()
            total = total_result.get("total", 0) if total_result else 0
            
            # Get theories with pagination
            order_clause = f"paper_count DESC" if sort_by == "paper_count" else \
                          f"phenomenon_count DESC" if sort_by == "phenomenon_count" else \
                          f"t.name ASC"
            
            result = session.run(f"""
                MATCH (t:Theory)
                OPTIONAL MATCH (p:Paper)-[:USES_THEORY]->(t)
                WITH t, count(DISTINCT p) as paper_count
                OPTIONAL MATCH (t)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, paper_count, count(DISTINCT ph) as phenomenon_count
                RETURN t.name as name,
                       t.domain as domain,
                       paper_count,
                       phenomenon_count
                ORDER BY {order_clause}
                SKIP $offset
                LIMIT $limit
            """, offset=offset, limit=limit).data()
            
            theories = [
                {
                    "name": record.get("name"),
                    "domain": record.get("domain"),
                    "paperCount": record.get("paper_count", 0),
                    "phenomenonCount": record.get("phenomenon_count", 0)
                }
                for record in result
            ]
            
            return {
                "theories": theories,
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < total
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing theories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# THEORY COMPARISON ENDPOINT (Phase 1.3)
# ============================================================================

@app.post("/api/theories/compare", response_model=TheoryComparisonResponse)
async def compare_theories(request: TheoryComparisonRequest):
    """
    Compare multiple theories to analyze compatibility, tensions, and integration opportunities.
    
    Analyzes:
    - Shared phenomena (theories explaining same phenomena)
    - Connection strengths
    - Co-usage patterns (theories used together in papers)
    - Method overlap
    - Compatibility score
    - Tensions (conflicting assumptions, competing explanations)
    - Integration suggestions
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if len(request.theories) < 2:
            raise HTTPException(status_code=400, detail="At least 2 theories required for comparison")
        
        if len(request.theories) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 theories can be compared at once")
        
        # Normalize theory names
        from entity_normalizer import get_normalizer
        normalizer = get_normalizer()
        normalized_theories = [normalizer.normalize_theory(t) for t in request.theories]
        
        with neo4j_service.driver.session() as session:
            # Verify all theories exist
            for theory_name in normalized_theories:
                theory_check = session.run("""
                    MATCH (t:Theory {name: $theory_name})
                    RETURN t.name as name
                """, theory_name=theory_name).single()
                
                if not theory_check:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Theory '{theory_name}' not found. Try searching for available theories."
                    )
            
            # Get phenomena for each theory
            theory_phenomena = {}
            theory_methods = {}
            theory_papers = {}
            
            for theory_name in normalized_theories:
                # Get phenomena
                phenomena_result = session.run("""
                    MATCH (t:Theory {name: $theory_name})
                    OPTIONAL MATCH (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                    WITH t, ph, agg.avg_strength as strength, agg.paper_count as paper_count
                    WHERE ph IS NOT NULL
                    
                    OPTIONAL MATCH (t)-[r:EXPLAINS_PHENOMENON]->(ph2:Phenomenon)
                    WHERE NOT EXISTS((t)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(ph2))
                    WITH t, 
                         collect(DISTINCT {
                             phenomenon: ph,
                             strength: strength,
                             paper_count: paper_count
                         }) + collect(DISTINCT {
                             phenomenon: ph2,
                             strength: r.connection_strength,
                             paper_count: 1
                         }) as all_phenomena
                    
                    UNWIND all_phenomena as phen
                    WITH t, phen.phenomenon as ph, phen.strength as strength,
                         phen.paper_count as paper_count
                    WHERE ph IS NOT NULL
                    
                    WITH ph,
                         max(strength) as max_strength,
                         sum(paper_count) as total_paper_count
                    
                    RETURN ph.phenomenon_name,
                           ph.phenomenon_type,
                           max_strength as connection_strength,
                           total_paper_count as paper_count
                    ORDER BY max_strength DESC
                """, theory_name=theory_name)
                
                phenomena = []
                for record in phenomena_result:
                    phenomena.append({
                        "phenomenon_name": record.get("phenomenon_name"),
                        "phenomenon_type": record.get("phenomenon_type"),
                        "connection_strength": round(record.get("connection_strength", 0.0), 3),
                        "paper_count": record.get("paper_count", 0)
                    })
                theory_phenomena[theory_name] = phenomena
                
                # Get methods used with this theory
                methods_result = session.run("""
                    MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)-[:USES_METHOD]->(m:Method)
                    WITH m, count(DISTINCT p) as paper_count
                    RETURN m.name as method_name, paper_count
                    ORDER BY paper_count DESC
                    LIMIT 10
                """, theory_name=theory_name)
                
                methods = [record.get("method_name") for record in methods_result]
                theory_methods[theory_name] = methods
                
                # Get papers using this theory
                papers_result = session.run("""
                    MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)
                    RETURN collect(DISTINCT p.paper_id) as paper_ids
                """, theory_name=theory_name).single()
                
                theory_papers[theory_name] = set(papers_result.get("paper_ids", []) if papers_result else [])
            
            # Find shared phenomena
            all_phenomena_sets = [set(p["phenomenon_name"] for p in phenomena) for phenomena in theory_phenomena.values()]
            shared_phenomena_names = set.intersection(*all_phenomena_sets) if all_phenomena_sets else set()
            
            shared_phenomena = []
            for phen_name in shared_phenomena_names:
                # Get details from first theory that has it
                for theory_name, phenomena in theory_phenomena.items():
                    phen_data = next((p for p in phenomena if p["phenomenon_name"] == phen_name), None)
                    if phen_data:
                        shared_phenomena.append({
                            "phenomenon_name": phen_name,
                            "phenomenon_type": phen_data.get("phenomenon_type"),
                            "theories": normalized_theories,
                            "avg_connection_strength": sum(
                                next((p["connection_strength"] for p in theory_phenomena[t] 
                                     if p["phenomenon_name"] == phen_name), 0.0)
                                for t in normalized_theories
                            ) / len(normalized_theories)
                        })
                        break
            
            # Find unique phenomena per theory
            unique_phenomena = {}
            for theory_name in normalized_theories:
                unique = [
                    p for p in theory_phenomena[theory_name]
                    if p["phenomenon_name"] not in shared_phenomena_names
                ]
                unique_phenomena[theory_name] = unique
            
            # Calculate co-usage frequency (papers using multiple theories)
            if len(normalized_theories) == 2:
                co_usage = len(theory_papers[normalized_theories[0]] & theory_papers[normalized_theories[1]])
            else:
                # For 3+ theories, count papers using all of them
                co_usage = len(set.intersection(*[theory_papers[t] for t in normalized_theories]))
            
            # Find method overlap
            all_methods_sets = [set(methods) for methods in theory_methods.values()]
            methods_overlap = list(set.intersection(*all_methods_sets)) if all_methods_sets else []
            
            # Calculate compatibility score
            compatibility_factors = []
            compatibility_score = 0.0
            
            # Factor 1: Shared phenomena (40% weight)
            if shared_phenomena:
                shared_phenomena_score = min(len(shared_phenomena) / 10.0, 1.0)  # Cap at 1.0
                compatibility_score += shared_phenomena_score * 0.4
                compatibility_factors.append(f"Share {len(shared_phenomena)} phenomena")
            
            # Factor 2: Co-usage frequency (30% weight)
            total_papers = len(set.union(*[theory_papers[t] for t in normalized_theories]))
            if total_papers > 0:
                co_usage_ratio = co_usage / total_papers
                compatibility_score += co_usage_ratio * 0.3
                if co_usage > 0:
                    compatibility_factors.append(f"Co-used in {co_usage} papers")
            
            # Factor 3: Method overlap (20% weight)
            if methods_overlap:
                method_overlap_score = min(len(methods_overlap) / 5.0, 1.0)
                compatibility_score += method_overlap_score * 0.2
                compatibility_factors.append(f"Share {len(methods_overlap)} methods")
            
            # Factor 4: Average connection strength for shared phenomena (10% weight)
            if shared_phenomena:
                avg_strength = sum(p["avg_connection_strength"] for p in shared_phenomena) / len(shared_phenomena)
                compatibility_score += avg_strength * 0.1
                if avg_strength > 0.7:
                    compatibility_factors.append("Strong connections to shared phenomena")
            
            compatibility_score = min(compatibility_score, 1.0)  # Cap at 1.0
            
            if not compatibility_factors:
                compatibility_factors.append("Limited overlap found")
            
            # Detect tensions
            tensions = []
            
            # Tension 1: Competing explanations (theories explain same phenomena with different roles)
            for phen in shared_phenomena:
                phen_name = phen["phenomenon_name"]
                # Check if theories have different roles for this phenomenon
                roles = []
                for theory_name in normalized_theories:
                    # Query for roles (primary, supporting, etc.)
                    role_result = session.run("""
                        MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phen_name})
                        RETURN collect(DISTINCT r.theory_role) as roles
                        LIMIT 1
                    """, theory_name=theory_name, phen_name=phen_name).single()
                    
                    if role_result:
                        roles.extend(role_result.get("roles", []))
                
                if len(set(roles)) > 1 and "primary" in roles:
                    tensions.append(Tension(
                        type="competing_explanation",
                        description=f"Both theories explain '{phen_name}' but with different emphasis",
                        evidence=f"Theories use different roles (primary vs supporting) for this phenomenon"
                    ))
            
            # Tension 2: High unique phenomena count (theories focus on different domains)
            total_unique = sum(len(unique_phenomena[t]) for t in normalized_theories)
            if total_unique > len(shared_phenomena) * 2:
                tensions.append(Tension(
                    type="domain_divergence",
                    description="Theories focus on largely different phenomena",
                    evidence=f"Only {len(shared_phenomena)} shared phenomena vs {total_unique} unique phenomena"
                ))
            
            # Generate integration suggestions
            integration_feasibility = "medium"
            integration_suggestions = []
            integration_rationale = ""
            
            if compatibility_score >= 0.7:
                integration_feasibility = "high"
                integration_suggestions.append(
                    "Combine theories as complementary frameworks - one for resource analysis, one for dynamic processes"
                )
                integration_suggestions.append(
                    "Use one theory as primary lens, the other for boundary conditions or moderators"
                )
                integration_rationale = "High compatibility suggests theories can be integrated effectively"
            elif compatibility_score >= 0.4:
                integration_feasibility = "medium"
                integration_suggestions.append(
                    "Explore integration at specific phenomena where both theories apply"
                )
                integration_suggestions.append(
                    "Consider sequential application - one theory for initial analysis, the other for deeper investigation"
                )
                integration_rationale = "Moderate compatibility - integration possible but requires careful consideration"
            else:
                integration_feasibility = "low"
                integration_suggestions.append(
                    "Theories may be better used independently for different research questions"
                )
                integration_suggestions.append(
                    "Consider using each theory for its unique strengths rather than forcing integration"
                )
                integration_rationale = "Low compatibility - theories serve different purposes"
            
            # Generate LLM narrative
            context_data = {
                "theories": normalized_theories,
                "shared_phenomena": shared_phenomena,
                "unique_phenomena": {k: len(v) for k, v in unique_phenomena.items()},
                "compatibility_score": compatibility_score,
                "compatibility_factors": compatibility_factors,
                "co_usage": co_usage,
                "methods_overlap": methods_overlap,
                "tensions": [{"type": t.type, "description": t.description} for t in tensions]
            }
            
            narrative = llm_client.generate_theory_comparison_narrative(
                normalized_theories,
                context_data,
                request.query
            )
            
            return TheoryComparisonResponse(
                theories=normalized_theories,
                compatibility=CompatibilityScore(
                    score=round(compatibility_score, 3),
                    factors=compatibility_factors
                ),
                tensions=tensions,
                integration=IntegrationSuggestion(
                    feasibility=integration_feasibility,
                    suggestions=integration_suggestions,
                    rationale=integration_rationale
                ),
                shared_phenomena=shared_phenomena,
                unique_phenomena={k: v[:10] for k, v in unique_phenomena.items()},  # Limit to top 10
                methods_overlap=methods_overlap[:10],  # Limit to top 10
                co_usage_frequency=co_usage,
                narrative=narrative
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing theories: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# THEORY CONTEXT ENDPOINT (Phase 2.1)
# ============================================================================

@app.get("/api/theories/{theory_name}/context", response_model=TheoryContextResponse)
async def get_theory_context(theory_name: str):
    """
    Get full context for a theory including phenomena, methods, papers, temporal usage,
    assumptions, constructs, and levels of analysis.
    
    Provides comprehensive understanding of how a theory is used in research.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        # Normalize theory name
        from entity_normalizer import get_normalizer
        normalizer = get_normalizer()
        normalized_name = normalizer.normalize_theory(theory_name)
        
        with neo4j_service.driver.session() as session:
            # Verify theory exists
            theory_check = session.run("""
                MATCH (t:Theory {name: $theory_name})
                RETURN t.name as name, t.domain as domain
            """, theory_name=normalized_name).single()
            
            if not theory_check:
                raise HTTPException(
                    status_code=404,
                    detail=f"Theory '{normalized_name}' not found. Try searching for available theories."
                )
            
            # Get phenomena
            phenomena_result = session.run("""
                MATCH (t:Theory {name: $theory_name})
                OPTIONAL MATCH (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon)
                WITH t, ph, agg.avg_strength as strength, agg.paper_count as paper_count
                WHERE ph IS NOT NULL
                
                OPTIONAL MATCH (t)-[r:EXPLAINS_PHENOMENON]->(ph2:Phenomenon)
                WHERE NOT EXISTS((t)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(ph2))
                WITH t,
                     collect(DISTINCT {
                         phenomenon: ph,
                         strength: strength,
                         paper_count: paper_count
                     }) + collect(DISTINCT {
                         phenomenon: ph2,
                         strength: r.connection_strength,
                         paper_count: 1
                     }) as all_phenomena
                
                UNWIND all_phenomena as phen
                WITH t, phen.phenomenon as ph, phen.strength as strength,
                     phen.paper_count as paper_count
                WHERE ph IS NOT NULL
                
                WITH ph,
                     max(strength) as max_strength,
                     sum(paper_count) as total_paper_count
                
                RETURN ph.phenomenon_name,
                       ph.phenomenon_type,
                       ph.domain as phenomenon_domain,
                       max_strength as connection_strength,
                       total_paper_count as paper_count
                ORDER BY max_strength DESC
            """, theory_name=normalized_name)
            
            phenomena = []
            for record in phenomena_result:
                phenomena.append({
                    "phenomenon_name": record.get("phenomenon_name"),
                    "phenomenon_type": record.get("phenomenon_type"),
                    "domain": record.get("phenomenon_domain"),
                    "connection_strength": round(record.get("connection_strength", 0.0), 3),
                    "paper_count": record.get("paper_count", 0)
                })
            
            # Get methods
            methods_result = session.run("""
                MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)-[:USES_METHOD]->(m:Method)
                WITH m, count(DISTINCT p) as paper_count,
                     collect(DISTINCT p.publication_year) as years
                RETURN m.name as method_name,
                       m.category as method_category,
                       paper_count,
                       years
                ORDER BY paper_count DESC
                LIMIT 20
            """, theory_name=normalized_name)
            
            methods = []
            for record in methods_result:
                methods.append({
                    "name": record.get("method_name"),
                    "category": record.get("method_category"),
                    "paper_count": record.get("paper_count", 0),
                    "years": sorted([y for y in record.get("years", []) if y and y > 0])
                })
            
            # Get papers with years
            papers_result = session.run("""
                MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)
                OPTIONAL MATCH (p)-[:AUTHORED]-(a:Author)
                WITH p, collect(DISTINCT a.full_name) as authors
                RETURN p.paper_id as paper_id,
                       p.title as title,
                       p.publication_year as publication_year,
                       p.journal as journal,
                       authors
                ORDER BY p.publication_year DESC
                LIMIT 50
            """, theory_name=normalized_name)
            
            papers = []
            for record in papers_result:
                papers.append({
                    "paper_id": record.get("paper_id"),
                    "title": record.get("title"),
                    "publication_year": record.get("publication_year"),
                    "journal": record.get("journal"),
                    "authors": record.get("authors", [])
                })
            
            # Get temporal usage patterns
            temporal_result = session.run("""
                MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)
                WHERE p.publication_year IS NOT NULL AND p.publication_year > 0
                WITH p.publication_year as year, count(DISTINCT p) as paper_count
                ORDER BY year
                RETURN year, paper_count
            """, theory_name=normalized_name)
            
            temporal_usage = []
            for record in temporal_result:
                year = record.get("year")
                # Get methods used in this year
                methods_in_year = session.run("""
                    MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)-[:USES_METHOD]->(m:Method)
                    WHERE p.publication_year = $year
                    RETURN collect(DISTINCT m.name) as methods
                """, theory_name=normalized_name, year=year).single()
                
                temporal_usage.append(TemporalUsage(
                    year=year,
                    paper_count=record.get("paper_count", 0),
                    methods=methods_in_year.get("methods", [])[:5] if methods_in_year else []
                ))
            
            # Get co-usage with other theories
            co_usage_result = session.run("""
                MATCH (t1:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)-[:USES_THEORY]->(t2:Theory)
                WHERE t1 <> t2
                WITH t2, count(DISTINCT p) as co_usage_count
                ORDER BY co_usage_count DESC
                LIMIT 10
                
                // Get shared phenomena
                MATCH (t1:Theory {name: $theory_name})-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)<-[:EXPLAINS_PHENOMENON]-(t2)
                WITH t2, co_usage_count, collect(DISTINCT ph.phenomenon_name) as shared_phenomena
                RETURN t2.name as theory_name, co_usage_count, shared_phenomena
            """, theory_name=normalized_name)
            
            co_usage_theories = []
            for record in co_usage_result:
                co_usage_theories.append(CoUsageTheory(
                    theory_name=record.get("theory_name"),
                    co_usage_count=record.get("co_usage_count", 0),
                    shared_phenomena=record.get("shared_phenomena", [])[:5]
                ))
            
            # Extract assumptions (simplified - based on theory usage patterns)
            assumptions = []
            assumptions_data = {
                "phenomena_count": len(phenomena),
                "methods_count": len(methods),
                "papers_count": len(papers),
                "co_usage_count": len(co_usage_theories)
            }
            
            # Generate assumptions narrative using LLM
            assumptions_narrative = llm_client.generate_theory_assumptions_narrative(
                normalized_name,
                assumptions_data,
                phenomena,
                methods
            )
            
            # Extract constructs (simplified - based on phenomena and methods)
            constructs = []
            # Group phenomena by type as proxy for constructs
            construct_map = {}
            for phen in phenomena:
                phen_type = phen.get("phenomenon_type", "general")
                if phen_type not in construct_map:
                    construct_map[phen_type] = []
                construct_map[phen_type].append(phen["phenomenon_name"])
            
            for construct_type, related_phenomena in construct_map.items():
                constructs.append(TheoryConstruct(
                    construct_name=construct_type,
                    frequency=len(related_phenomena),
                    related_phenomena=related_phenomena[:5]
                ))
            
            # Generate constructs narrative
            constructs_narrative = llm_client.generate_theory_constructs_narrative(
                normalized_name,
                constructs,
                phenomena
            )
            
            # Levels of analysis (simplified - based on phenomena domains)
            levels_of_analysis = {}
            for phen in phenomena:
                domain = phen.get("domain", "general")
                levels_of_analysis[domain] = levels_of_analysis.get(domain, 0) + 1
            
            return TheoryContextResponse(
                theory={
                    "name": theory_check["name"],
                    "domain": theory_check.get("domain")
                },
                phenomena=phenomena,
                methods=methods,
                papers=papers,
                temporal_usage=temporal_usage,
                co_usage_theories=co_usage_theories,
                assumptions=assumptions,
                constructs=constructs,
                levels_of_analysis=levels_of_analysis,
                assumptions_narrative=assumptions_narrative,
                constructs_narrative=constructs_narrative
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theory context: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONTRIBUTION OPPORTUNITIES ENDPOINT (Phase 2.2)
# ============================================================================

@app.get("/api/contributions/opportunities", response_model=ContributionOpportunitiesResponse)
async def get_contribution_opportunities(
    query: Optional[str] = Query(None, description="Optional query to filter opportunities"),
    type: Optional[str] = Query(None, regex="^(theory-phenomenon|theory-method|construct|sparsity|all)$", description="Filter by opportunity type"),
    min_potential: float = Query(0.5, ge=0.0, le=1.0, description="Minimum opportunity score"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Identify contribution opportunities and research gaps.
    
    Detects:
    - Underexplored Theory-Phenomenon combinations (low/missing connections)
    - Underexplored Theory-Method combinations
    - Rare/emerging constructs
    - Sparsity gaps in knowledge graph
    
    Returns opportunities with evidence, contribution statements, and research questions.
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        opportunities = []
        
        with neo4j_service.driver.session() as session:
            # 1. Detect Theory-Phenomenon Gaps
            if not type or type in ["theory-phenomenon", "all"]:
                theory_phenomenon_opportunities = await _detect_theory_phenomenon_gaps(
                    session, query, min_potential, limit
                )
                opportunities.extend(theory_phenomenon_opportunities)
            
            # 2. Detect Theory-Method Gaps
            if not type or type in ["theory-method", "all"]:
                theory_method_opportunities = await _detect_theory_method_gaps(
                    session, query, min_potential, limit
                )
                opportunities.extend(theory_method_opportunities)
            
            # 3. Detect Rare Constructs
            if not type or type in ["construct", "all"]:
                construct_opportunities = await _detect_rare_constructs(
                    session, query, min_potential, limit
                )
                opportunities.extend(construct_opportunities)
            
            # Sort by opportunity score (descending)
            opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
            
            # Limit results
            opportunities = opportunities[:limit]
            
            # Generate summary using LLM
            summary = llm_client.generate_opportunities_summary(opportunities, query)
            
            return ContributionOpportunitiesResponse(
                opportunities=opportunities,
                total=len(opportunities),
                summary=summary
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contribution opportunities: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def _detect_theory_phenomenon_gaps(session, query: Optional[str], min_potential: float, limit: int) -> List[ContributionOpportunity]:
    """Detect underexplored theory-phenomenon combinations"""
    opportunities = []
    
    # Get all theories and phenomena
    theories_result = session.run("""
        MATCH (t:Theory)
        RETURN t.name as theory_name
        LIMIT 50
    """)
    
    theories = [record.get("theory_name") for record in theories_result]
    
    phenomena_result = session.run("""
        MATCH (ph:Phenomenon)
        RETURN ph.phenomenon_name as phenomenon_name
        LIMIT 100
    """)
    
    phenomena = [record.get("phenomenon_name") for record in phenomena_result]
    
    # For each theory-phenomenon pair, check connection strength
    for theory_name in theories[:20]:  # Limit to avoid too many combinations
        for phen_name in phenomena[:30]:
            # Check if connection exists and its strength
            connection_result = session.run("""
                MATCH (t:Theory {name: $theory_name})
                OPTIONAL MATCH (t)-[agg:EXPLAINS_PHENOMENON_AGGREGATED]->(ph:Phenomenon {phenomenon_name: $phen_name})
                OPTIONAL MATCH (t)-[r:EXPLAINS_PHENOMENON]->(ph)
                WHERE NOT EXISTS((t)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(ph))
                
                WITH COALESCE(agg.avg_strength, r.connection_strength, 0.0) as strength,
                     COALESCE(agg.paper_count, 1, 0) as paper_count
                
                RETURN strength, paper_count
            """, theory_name=theory_name, phen_name=phen_name).single()
            
            if connection_result:
                strength = connection_result.get("strength", 0.0) or 0.0
                paper_count = connection_result.get("paper_count", 0) or 0
                
                # Calculate opportunity score
                # Low strength (< 0.5) or missing connection = high opportunity
                connection_gap = 1.0 - strength if strength > 0 else 1.0
                
                # Find similar theories that explain this phenomenon
                similar_theories_result = session.run("""
                    MATCH (ph:Phenomenon {phenomenon_name: $phen_name})<-[:EXPLAINS_PHENOMENON]-(t:Theory)
                    WHERE t.name <> $theory_name
                    WITH t, count(*) as count
                    ORDER BY count DESC
                    LIMIT 3
                    RETURN collect(t.name) as similar_theories
                """, theory_name=theory_name, phen_name=phen_name).single()
                
                similar_theories = similar_theories_result.get("similar_theories", []) if similar_theories_result else []
                
                # Find similar phenomena explained by this theory
                similar_phenomena_result = session.run("""
                    MATCH (t:Theory {name: $theory_name})-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    WHERE ph.phenomenon_name <> $phen_name
                    WITH ph, count(*) as count
                    ORDER BY count DESC
                    LIMIT 3
                    RETURN collect(ph.phenomenon_name) as similar_phenomena
                """, theory_name=theory_name, phen_name=phen_name).single()
                
                similar_phenomena = similar_phenomena_result.get("similar_phenomena", []) if similar_phenomena_result else []
                
                # Calculate opportunity score
                opportunity_score = 0.0
                
                # Factor 1: Connection gap (40%)
                opportunity_score += connection_gap * 0.4
                
                # Factor 2: Similarity evidence (30%)
                if similar_theories or similar_phenomena:
                    similarity_score = min((len(similar_theories) + len(similar_phenomena)) / 6.0, 1.0)
                    opportunity_score += similarity_score * 0.3
                
                # Factor 3: Research density (20%) - fewer papers = higher opportunity
                if paper_count == 0:
                    density_score = 1.0
                elif paper_count <= 2:
                    density_score = 0.8
                elif paper_count <= 5:
                    density_score = 0.5
                else:
                    density_score = 0.2
                opportunity_score += density_score * 0.2
                
                # Factor 4: Semantic fit (10%) - simplified, assume good fit if similar theories/phenomena exist
                semantic_score = 0.5 if (similar_theories or similar_phenomena) else 0.2
                opportunity_score += semantic_score * 0.1
                
                opportunity_score = min(opportunity_score, 1.0)
                
                # Only include if meets minimum potential
                if opportunity_score >= min_potential:
                    # Generate contribution statement and research questions
                    contribution_data = {
                        "theory": theory_name,
                        "phenomenon": phen_name,
                        "current_strength": strength,
                        "paper_count": paper_count,
                        "similar_theories": similar_theories,
                        "similar_phenomena": similar_phenomena,
                        "opportunity_score": opportunity_score
                    }
                    
                    contribution_statement = llm_client.generate_contribution_statement(
                        "theory-phenomenon",
                        contribution_data
                    )
                    
                    research_questions = llm_client.generate_research_questions(
                        "theory-phenomenon",
                        contribution_data
                    )
                    
                    rationale = f"Current connection strength: {strength:.2f}, Paper count: {paper_count}. "
                    if similar_theories:
                        rationale += f"Similar theories ({', '.join(similar_theories[:2])}) explain this phenomenon. "
                    if similar_phenomena:
                        rationale += f"Theory explains similar phenomena ({', '.join(similar_phenomena[:2])})."
                    
                    opportunities.append(ContributionOpportunity(
                        type="theory-phenomenon",
                        theory=theory_name,
                        phenomenon=phen_name,
                        opportunity_score=round(opportunity_score, 3),
                        evidence=OpportunityEvidence(
                            connection_strength=strength if strength > 0 else None,
                            similar_theories=similar_theories,
                            similar_phenomena=similar_phenomena,
                            paper_count=paper_count,
                            research_density="low" if paper_count <= 2 else "medium" if paper_count <= 5 else "high"
                        ),
                        contribution_statement=contribution_statement,
                        research_questions=research_questions,
                        rationale=rationale
                    ))
    
    return opportunities

async def _detect_theory_method_gaps(session, query: Optional[str], min_potential: float, limit: int) -> List[ContributionOpportunity]:
    """Detect underexplored theory-method combinations"""
    opportunities = []
    
    # Get theories and their method usage
    theory_methods_result = session.run("""
        MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)-[:USES_METHOD]->(m:Method)
        WITH t, m, count(DISTINCT p) as usage_count
        WHERE usage_count <= 3  // Rarely used together
        RETURN t.name as theory_name, m.name as method_name, usage_count
        ORDER BY usage_count ASC
        LIMIT 30
    """)
    
    for record in theory_methods_result:
        theory_name = record.get("theory_name")
        method_name = record.get("method_name")
        usage_count = record.get("usage_count", 0)
        
        # Get methods commonly used with this theory
        common_methods_result = session.run("""
            MATCH (t:Theory {name: $theory_name})<-[:USES_THEORY]-(p:Paper)-[:USES_METHOD]->(m:Method)
            WHERE m.name <> $method_name
            WITH m, count(DISTINCT p) as count
            ORDER BY count DESC
            LIMIT 5
            RETURN collect(m.name) as common_methods
        """, theory_name=theory_name, method_name=method_name).single()
        
        common_methods = common_methods_result.get("common_methods", []) if common_methods_result else []
        
        # Calculate opportunity score
        opportunity_score = 0.0
        
        # Factor 1: Usage rarity (50%)
        rarity_score = 1.0 if usage_count == 0 else max(0.0, 1.0 - (usage_count / 10.0))
        opportunity_score += rarity_score * 0.5
        
        # Factor 2: Method diversity (30%) - theory uses diverse methods = good fit
        diversity_score = min(len(common_methods) / 5.0, 1.0)
        opportunity_score += diversity_score * 0.3
        
        # Factor 3: Novelty (20%) - method not commonly used with theory
        novelty_score = 0.8 if usage_count <= 1 else 0.5
        opportunity_score += novelty_score * 0.2
        
        opportunity_score = min(opportunity_score, 1.0)
        
        if opportunity_score >= min_potential:
            contribution_data = {
                "theory": theory_name,
                "method": method_name,
                "usage_count": usage_count,
                "common_methods": common_methods,
                "opportunity_score": opportunity_score
            }
            
            contribution_statement = llm_client.generate_contribution_statement(
                "theory-method",
                contribution_data
            )
            
            research_questions = llm_client.generate_research_questions(
                "theory-method",
                contribution_data
            )
            
            rationale = f"Rarely used together ({usage_count} papers). "
            if common_methods:
                rationale += f"Theory commonly uses methods like {', '.join(common_methods[:2])}, suggesting this method could provide novel insights."
            
            opportunities.append(ContributionOpportunity(
                type="theory-method",
                theory=theory_name,
                method=method_name,
                opportunity_score=round(opportunity_score, 3),
                evidence=OpportunityEvidence(
                    similar_methods=common_methods,
                    paper_count=usage_count,
                    research_density="low" if usage_count <= 1 else "medium"
                ),
                contribution_statement=contribution_statement,
                research_questions=research_questions,
                rationale=rationale
            ))
    
    return opportunities

async def _detect_rare_constructs(session, query: Optional[str], min_potential: float, limit: int) -> List[ContributionOpportunity]:
    """Detect rare/emerging constructs"""
    opportunities = []
    
    # Find phenomena with low paper count (rare constructs)
    rare_phenomena_result = session.run("""
        MATCH (ph:Phenomenon)
        OPTIONAL MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph)
        WITH ph, count(DISTINCT p) as paper_count
        WHERE paper_count <= 3  // Rarely studied
        RETURN ph.phenomenon_name as phenomenon_name,
               ph.phenomenon_type as phenomenon_type,
               paper_count
        ORDER BY paper_count ASC
        LIMIT 20
    """)
    
    for record in rare_phenomena_result:
        phen_name = record.get("phenomenon_name")
        phen_type = record.get("phenomenon_type")
        paper_count = record.get("paper_count", 0)
        
        # Get theories that could explain this phenomenon
        potential_theories_result = session.run("""
            MATCH (ph:Phenomenon {phenomenon_name: $phen_name})
            OPTIONAL MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph)
            WITH ph, collect(t.name) as existing_theories
            
            // Find theories that explain similar phenomena
            MATCH (ph2:Phenomenon {phenomenon_type: $phen_type})
            WHERE ph2.phenomenon_name <> $phen_name
            MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph2)
            WHERE NOT t.name IN existing_theories
            WITH t, count(DISTINCT ph2) as similar_count
            ORDER BY similar_count DESC
            LIMIT 3
            RETURN collect(t.name) as potential_theories
        """, phen_name=phen_name, phen_type=phen_type or "general").single()
        
        potential_theories = potential_theories_result.get("potential_theories", []) if potential_theories_result else []
        
        # Calculate opportunity score
        opportunity_score = 0.0
        
        # Factor 1: Rarity (50%)
        rarity_score = 1.0 if paper_count == 0 else max(0.0, 1.0 - (paper_count / 5.0))
        opportunity_score += rarity_score * 0.5
        
        # Factor 2: Potential theories (30%)
        potential_score = min(len(potential_theories) / 3.0, 1.0)
        opportunity_score += potential_score * 0.3
        
        # Factor 3: Emerging pattern (20%)
        emergence_score = 0.8 if paper_count <= 1 else 0.5
        opportunity_score += emergence_score * 0.2
        
        opportunity_score = min(opportunity_score, 1.0)
        
        if opportunity_score >= min_potential:
            contribution_data = {
                "phenomenon": phen_name,
                "phenomenon_type": phen_type,
                "paper_count": paper_count,
                "potential_theories": potential_theories,
                "opportunity_score": opportunity_score
            }
            
            contribution_statement = llm_client.generate_contribution_statement(
                "construct",
                contribution_data
            )
            
            research_questions = llm_client.generate_research_questions(
                "construct",
                contribution_data
            )
            
            rationale = f"Rarely studied ({paper_count} papers). "
            if potential_theories:
                rationale += f"Potential theories: {', '.join(potential_theories)} could explain this phenomenon."
            
            opportunities.append(ContributionOpportunity(
                type="construct",
                phenomenon=phen_name,
                construct_name=phen_type,
                opportunity_score=round(opportunity_score, 3),
                evidence=OpportunityEvidence(
                    similar_theories=potential_theories,
                    paper_count=paper_count,
                    research_density="low"
                ),
                contribution_statement=contribution_statement,
                research_questions=research_questions,
                rationale=rationale
            ))
    
    return opportunities

# ============================================================================
# TREND ANALYSIS ENDPOINT (Phase 3.1)
# ============================================================================

@app.get("/api/trends/{entity_type}/{entity_name}", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    entity_type: str,
    entity_name: str,
    period: Optional[str] = Query(None, description="Specific period to analyze (e.g., '2020-2024')")
):
    """
    Analyze temporal trends for a theory, method, or phenomenon.
    
    Returns:
    - Usage patterns across time periods
    - Evolution steps between periods
    - Trend forecast for next period
    - LLM-generated narrative
    """
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        # Normalize entity name
        from entity_normalizer import get_normalizer
        normalizer = get_normalizer()
        
        if entity_type == "theory":
            normalized_name = normalizer.normalize_theory(entity_name)
        elif entity_type == "method":
            normalized_name = normalizer.normalize_method(entity_name)
        elif entity_type == "phenomenon":
            normalized_name = normalizer.normalize_phenomenon(entity_name)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid entity_type: {entity_type}. Must be 'theory', 'method', or 'phenomenon'")
        
        with neo4j_service.driver.session() as session:
            # Get usage by period
            usage_by_period = await _get_usage_by_period(session, entity_type, normalized_name)
            
            # Get evolution steps
            evolution_steps = await _get_evolution_steps(session, entity_type, normalized_name)
            
            # Generate forecast
            forecast = await _generate_forecast(usage_by_period, evolution_steps)
            
            # Generate narrative
            narrative = llm_client.generate_trend_narrative(
                entity_type, normalized_name, usage_by_period, evolution_steps, forecast
            )
            
            # Generate summary
            summary = llm_client.generate_trend_summary(
                entity_type, normalized_name, usage_by_period, evolution_steps
            )
            
            return TrendAnalysisResponse(
                entity_type=entity_type,
                entity_name=normalized_name,
                usage_by_period=usage_by_period,
                evolution_steps=evolution_steps,
                forecast=forecast,
                narrative=narrative,
                summary=summary
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def _get_usage_by_period(session, entity_type: str, entity_name: str) -> List[PeriodUsage]:
    """Get usage statistics by time period"""
    usage = []
    
    if entity_type == "theory":
        query = """
            MATCH (tp:TimePeriod)-[r:HAS_THEORY_USAGE]->(t:Theory {name: $entity_name})
            RETURN tp.period_name as period,
                   tp.start_year as start_year,
                   tp.end_year as end_year,
                   r.paper_count as paper_count,
                   r.usage_frequency as usage_frequency
            ORDER BY tp.start_year ASC
        """
    elif entity_type == "method":
        query = """
            MATCH (tp:TimePeriod)-[r:HAS_METHOD_USAGE]->(m:Method {name: $entity_name})
            RETURN tp.period_name as period,
                   tp.start_year as start_year,
                   tp.end_year as end_year,
                   r.paper_count as paper_count,
                   r.usage_frequency as usage_frequency
            ORDER BY tp.start_year ASC
        """
    else:  # phenomenon - may not have temporal relationships, use paper relationships
        query = """
            MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $entity_name})
            WHERE p.publication_year IS NOT NULL
            WITH CASE
                WHEN p.publication_year >= 2020 AND p.publication_year <= 2024 THEN '2020-2024'
                WHEN p.publication_year >= 2015 AND p.publication_year <= 2019 THEN '2015-2019'
                WHEN p.publication_year >= 2010 AND p.publication_year <= 2014 THEN '2010-2014'
                WHEN p.publication_year >= 2005 AND p.publication_year <= 2009 THEN '2005-2009'
                WHEN p.publication_year >= 2000 AND p.publication_year <= 2004 THEN '2000-2004'
                ELSE 'other'
            END as period,
            CASE
                WHEN p.publication_year >= 2020 AND p.publication_year <= 2024 THEN 2020
                WHEN p.publication_year >= 2015 AND p.publication_year <= 2019 THEN 2015
                WHEN p.publication_year >= 2010 AND p.publication_year <= 2014 THEN 2010
                WHEN p.publication_year >= 2005 AND p.publication_year <= 2009 THEN 2005
                WHEN p.publication_year >= 2000 AND p.publication_year <= 2004 THEN 2000
                ELSE 1995
            END as start_year,
            CASE
                WHEN p.publication_year >= 2020 AND p.publication_year <= 2024 THEN 2024
                WHEN p.publication_year >= 2015 AND p.publication_year <= 2019 THEN 2019
                WHEN p.publication_year >= 2010 AND p.publication_year <= 2014 THEN 2014
                WHEN p.publication_year >= 2005 AND p.publication_year <= 2009 THEN 2009
                WHEN p.publication_year >= 2000 AND p.publication_year <= 2004 THEN 2004
                ELSE 1999
            END as end_year,
            count(DISTINCT p) as paper_count
            WHERE period <> 'other'
            RETURN period, start_year, end_year, paper_count, 
                   (paper_count * 1.0) as usage_frequency
            ORDER BY start_year ASC
        """
    
    result = session.run(query, entity_name=entity_name)
    
    for record in result:
        usage.append(PeriodUsage(
            period=record.get("period"),
            start_year=record.get("start_year"),
            end_year=record.get("end_year"),
            paper_count=record.get("paper_count", 0) or 0,
            usage_frequency=record.get("usage_frequency")
        ))
    
    return usage

async def _get_evolution_steps(session, entity_type: str, entity_name: str) -> List[EvolutionStep]:
    """Get evolution steps between periods"""
    evolution_steps = []
    
    # Get usage by period first
    usage_by_period = await _get_usage_by_period(session, entity_type, entity_name)
    
    # Calculate evolution between consecutive periods
    for i in range(len(usage_by_period) - 1):
        current = usage_by_period[i]
        next_period = usage_by_period[i + 1]
        
        change = next_period.paper_count - current.paper_count
        change_percentage = 0.0
        if current.paper_count > 0:
            change_percentage = (change / current.paper_count) * 100.0
        elif next_period.paper_count > 0:
            change_percentage = 100.0  # New usage
        
        # Determine evolution type
        if abs(change_percentage) < 10:
            evolution_type = "stable"
        elif change_percentage > 0:
            evolution_type = "increasing"
        else:
            evolution_type = "decreasing"
        
        evolution_steps.append(EvolutionStep(
            from_period=current.period,
            to_period=next_period.period,
            change=change,
            change_percentage=round(change_percentage, 1),
            evolution_type=evolution_type
        ))
    
    return evolution_steps

async def _generate_forecast(usage_by_period: List[PeriodUsage], evolution_steps: List[EvolutionStep]) -> Optional[TrendForecast]:
    """Generate forecast for next period"""
    if len(usage_by_period) < 2:
        return None
    
    # Simple linear trend forecast
    recent_periods = usage_by_period[-3:] if len(usage_by_period) >= 3 else usage_by_period
    
    # Calculate average change
    if len(evolution_steps) > 0:
        recent_changes = [step.change for step in evolution_steps[-2:]]
        avg_change = sum(recent_changes) / len(recent_changes) if recent_changes else 0
        
        # Get last period
        last_period = usage_by_period[-1]
        
        # Predict next period (5 years after last period)
        next_start_year = last_period.end_year + 1
        next_end_year = next_start_year + 4
        next_period = f"{next_start_year}-{next_end_year}"
        
        # Predict paper count
        predicted_count = max(0, int(last_period.paper_count + avg_change))
        
        # Determine trend direction
        if avg_change > 1:
            trend_direction = "increasing"
        elif avg_change < -1:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        # Confidence based on data quality
        confidence = min(0.9, 0.5 + (len(usage_by_period) * 0.1))
        
        rationale = f"Based on recent trend ({avg_change:+.1f} papers per period), "
        rationale += f"predicted usage in {next_period} is {predicted_count} papers."
        
        return TrendForecast(
            next_period=next_period,
            predicted_paper_count=predicted_count,
            confidence=round(confidence, 2),
            trend_direction=trend_direction,
            rationale=rationale
        )
    
    return None

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting SMJ Research Chatbot API Server")
    if neo4j_service.is_connected():
        logger.info("✓ Neo4j connection established")
    else:
        logger.warning("⚠️ Neo4j connection failed")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down SMJ Research Chatbot API Server")
    neo4j_service.close()

if __name__ == "__main__":
    # Use PORT from environment (Railway sets this) or default to 5000
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production (Railway)
        log_level="info"
    )
