#!/usr/bin/env python3
"""
Enhanced GPT-4 Turbo Extractor with JSON Mode
High-quality extraction with structured outputs for SMJ literature analysis
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib

from dotenv import load_dotenv
import openai
from openai import AsyncOpenAI
import fitz  # PyMuPDF

from entity_normalizer import get_normalizer
from data_validator import DataValidator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Structured extraction result"""
    paper_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    theories: List[Dict[str, Any]] = field(default_factory=list)
    phenomena: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    variables: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    contributions: List[Dict[str, Any]] = field(default_factory=list)
    authors: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    research_questions: List[Dict[str, Any]] = field(default_factory=list)
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "metadata": self.metadata,
            "theories": self.theories,
            "phenomena": self.phenomena,
            "methods": self.methods,
            "variables": self.variables,
            "findings": self.findings,
            "contributions": self.contributions,
            "authors": self.authors,
            "citations": self.citations,
            "research_questions": self.research_questions,
            "extraction_metadata": self.extraction_metadata
        }


class EnhancedGPT4Extractor:
    """
    Production-grade extractor using GPT-4 Turbo with JSON mode
    Designed for Strategic Management Journal literature analysis
    """

    # Comprehensive JSON schemas for structured extraction
    SCHEMAS = {
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "abstract": {"type": "string"},
                "publication_year": {"type": "integer"},
                "doi": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "paper_type": {"type": "string", "enum": ["empirical_quantitative", "empirical_qualitative", "theoretical", "review", "meta_analysis", "research_note"]},
                "research_context": {"type": "string"}
            }
        },
        "theories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theory_name": {"type": "string"},
                    "role": {"type": "string", "enum": ["primary", "supporting", "challenging", "extending"]},
                    "domain": {"type": "string"},
                    "usage_context": {"type": "string"},
                    "section": {"type": "string"},
                    "key_constructs": {"type": "array", "items": {"type": "string"}},
                    "assumptions": {"type": "array", "items": {"type": "string"}},
                    "boundary_conditions": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["theory_name", "role", "usage_context"]
            }
        },
        "phenomena": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "phenomenon_name": {"type": "string"},
                    "phenomenon_type": {"type": "string", "enum": ["behavior", "pattern", "event", "trend", "process", "outcome"]},
                    "domain": {"type": "string"},
                    "description": {"type": "string"},
                    "context": {"type": "string"},
                    "level_of_analysis": {"type": "string", "enum": ["individual", "team", "organization", "industry", "economy", "multi_level"]},
                    "temporal_scope": {"type": "string"},
                    "geographic_scope": {"type": "string"},
                    "related_theories": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["phenomenon_name", "description"]
            }
        },
        "methods": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "method_name": {"type": "string"},
                    "method_type": {"type": "string", "enum": ["quantitative", "qualitative", "mixed", "computational", "experimental"]},
                    "method_category": {"type": "string"},
                    "software": {"type": "array", "items": {"type": "string"}},
                    "sample_size": {"type": "string"},
                    "sample_type": {"type": "string"},
                    "data_sources": {"type": "array", "items": {"type": "string"}},
                    "time_period": {"type": "string"},
                    "geographic_scope": {"type": "string"},
                    "industry_context": {"type": "string"},
                    "robustness_checks": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["method_name", "method_type"]
            }
        },
        "variables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "variable_name": {"type": "string"},
                    "variable_type": {"type": "string", "enum": ["dependent", "independent", "control", "moderator", "mediator", "instrumental"]},
                    "measurement": {"type": "string"},
                    "operationalization": {"type": "string"},
                    "data_source": {"type": "string"},
                    "theoretical_basis": {"type": "string"}
                },
                "required": ["variable_name", "variable_type"]
            }
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding_text": {"type": "string"},
                    "finding_type": {"type": "string", "enum": ["hypothesis_supported", "hypothesis_rejected", "unexpected", "exploratory"]},
                    "statistical_significance": {"type": "string"},
                    "effect_size": {"type": "string"},
                    "practical_significance": {"type": "string"},
                    "related_hypotheses": {"type": "array", "items": {"type": "string"}},
                    "boundary_conditions": {"type": "string"}
                },
                "required": ["finding_text"]
            }
        },
        "contributions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "contribution_text": {"type": "string"},
                    "contribution_type": {"type": "string", "enum": ["theoretical", "empirical", "methodological", "practical"]},
                    "novelty_claim": {"type": "string"},
                    "extends_prior_work": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["contribution_text", "contribution_type"]
            }
        },
        "authors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "given_name": {"type": "string"},
                    "family_name": {"type": "string"},
                    "position": {"type": "integer"},
                    "affiliations": {"type": "array", "items": {"type": "string"}},
                    "corresponding_author": {"type": "boolean"}
                },
                "required": ["full_name", "position"]
            }
        },
        "theory_phenomenon_links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theory_name": {"type": "string"},
                    "phenomenon_name": {"type": "string"},
                    "relationship_type": {"type": "string", "enum": ["explains", "predicts", "describes", "challenges", "extends"]},
                    "mechanism": {"type": "string"},
                    "evidence_strength": {"type": "string", "enum": ["strong", "moderate", "weak", "theoretical"]},
                    "context_conditions": {"type": "string"}
                },
                "required": ["theory_name", "phenomenon_name", "relationship_type"]
            }
        },
        "research_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_text": {"type": "string"},
                    "question_type": {"type": "string", "enum": ["descriptive", "explanatory", "predictive", "prescriptive", "exploratory"]},
                    "primary": {"type": "boolean"},
                    "section": {"type": "string"},
                    "related_theories": {"type": "array", "items": {"type": "string"}},
                    "related_phenomena": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question_text"]
            }
        },
        # Combined schemas for optimized extraction (3 calls instead of 10)
        "metadata_and_authors": {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "abstract": {"type": "string"},
                        "publication_year": {"type": "integer"},
                        "doi": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "paper_type": {"type": "string", "enum": ["empirical_quantitative", "empirical_qualitative", "theoretical", "review", "meta_analysis", "research_note"]},
                        "research_context": {"type": "string"}
                    }
                },
                "authors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "full_name": {"type": "string"},
                            "given_name": {"type": "string"},
                            "family_name": {"type": "string"},
                            "position": {"type": "integer"},
                            "affiliations": {"type": "array", "items": {"type": "string"}},
                            "corresponding_author": {"type": "boolean"}
                        },
                        "required": ["full_name", "position"]
                    }
                }
            },
            "required": ["metadata", "authors"]
        },
        "theories_phenomena_links": {
            "type": "object",
            "properties": {
                "theories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theory_name": {"type": "string"},
                            "role": {"type": "string", "enum": ["primary", "supporting", "challenging", "extending"]},
                            "domain": {"type": "string"},
                            "usage_context": {"type": "string"},
                            "section": {"type": "string"},
                            "key_constructs": {"type": "array", "items": {"type": "string"}},
                            "assumptions": {"type": "array", "items": {"type": "string"}},
                            "boundary_conditions": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["theory_name", "role", "usage_context"]
                    }
                },
                "phenomena": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "phenomenon_name": {"type": "string"},
                            "phenomenon_type": {"type": "string", "enum": ["behavior", "pattern", "event", "trend", "process", "outcome"]},
                            "domain": {"type": "string"},
                            "description": {"type": "string"},
                            "context": {"type": "string"},
                            "level_of_analysis": {"type": "string", "enum": ["individual", "team", "organization", "industry", "economy", "multi_level"]},
                            "temporal_scope": {"type": "string"},
                            "geographic_scope": {"type": "string"},
                            "related_theories": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["phenomenon_name", "description"]
                    }
                },
                "theory_phenomenon_links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theory_name": {"type": "string"},
                            "phenomenon_name": {"type": "string"},
                            "relationship_type": {"type": "string", "enum": ["explains", "predicts", "describes", "challenges", "extends"]},
                            "mechanism": {"type": "string"},
                            "evidence_strength": {"type": "string", "enum": ["strong", "moderate", "weak", "theoretical"]},
                            "context_conditions": {"type": "string"}
                        },
                        "required": ["theory_name", "phenomenon_name", "relationship_type"]
                    }
                }
            },
            "required": ["theories", "phenomena", "theory_phenomenon_links"]
        },
        "methods_variables_findings_contributions_questions": {
            "type": "object",
            "properties": {
                "methods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method_name": {"type": "string"},
                            "method_type": {"type": "string", "enum": ["quantitative", "qualitative", "mixed", "computational", "experimental"]},
                            "method_category": {"type": "string"},
                            "software": {"type": "array", "items": {"type": "string"}},
                            "sample_size": {"type": "string"},
                            "sample_type": {"type": "string"},
                            "data_sources": {"type": "array", "items": {"type": "string"}},
                            "time_period": {"type": "string"},
                            "geographic_scope": {"type": "string"},
                            "industry_context": {"type": "string"},
                            "robustness_checks": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["method_name", "method_type"]
                    }
                },
                "variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable_name": {"type": "string"},
                            "variable_type": {"type": "string", "enum": ["dependent", "independent", "control", "moderator", "mediator", "instrumental"]},
                            "measurement": {"type": "string"},
                            "operationalization": {"type": "string"},
                            "data_source": {"type": "string"},
                            "theoretical_basis": {"type": "string"}
                        },
                        "required": ["variable_name", "variable_type"]
                    }
                },
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "finding_text": {"type": "string"},
                            "finding_type": {"type": "string", "enum": ["hypothesis_supported", "hypothesis_rejected", "unexpected", "exploratory"]},
                            "statistical_significance": {"type": "string"},
                            "effect_size": {"type": "string"},
                            "practical_significance": {"type": "string"},
                            "related_hypotheses": {"type": "array", "items": {"type": "string"}},
                            "boundary_conditions": {"type": "string"}
                        },
                        "required": ["finding_text"]
                    }
                },
                "contributions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "contribution_text": {"type": "string"},
                            "contribution_type": {"type": "string", "enum": ["theoretical", "empirical", "methodological", "practical"]},
                            "novelty_claim": {"type": "string"},
                            "extends_prior_work": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["contribution_text", "contribution_type"]
                    }
                },
                "research_questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_text": {"type": "string"},
                            "question_type": {"type": "string", "enum": ["descriptive", "explanatory", "predictive", "prescriptive", "exploratory"]},
                            "primary": {"type": "boolean"},
                            "section": {"type": "string"},
                            "related_theories": {"type": "array", "items": {"type": "string"}},
                            "related_phenomena": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["question_text"]
                    }
                }
            },
            "required": ["methods", "variables", "findings", "contributions", "research_questions"]
        }
    }

    def __init__(self,
                 api_key: str = None,
                 model: str = "gpt-4-turbo-preview",
                 max_retries: int = 3,
                 temperature: float = 0.1):
        """
        Initialize the enhanced extractor

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model: Model to use (default: gpt-4-turbo-preview)
            max_retries: Maximum retry attempts
            temperature: LLM temperature for extraction
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")

        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature

        # Initialize clients
        self.client = openai.OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        # Initialize normalizer and validator
        self.normalizer = get_normalizer()
        self.validator = DataValidator()

        # Cache directory
        self.cache_dir = Path("extraction_cache")
        self.cache_dir.mkdir(exist_ok=True)

        logger.info(f"Initialized EnhancedGPT4Extractor with model: {model}")

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for SMJ analysis"""
        return """You are an expert research methodology analyst specializing in Strategic Management Journal (SMJ) literature analysis.

Your task is to extract structured information from academic papers to support research on:
1. Topical fragmentation vs convergence in strategic management
2. Theory-phenomenon relationships (multiple theories → single phenomenon, single theory → multiple phenomena)
3. Temporal evolution of theories and methodologies
4. Key author networks and contributions

EXTRACTION PRINCIPLES:
1. Extract ONLY what is EXPLICITLY stated - never infer or assume
2. Use EXACT terminology from the paper - do not paraphrase theory/phenomenon names
3. Distinguish between theories USED in the paper vs merely MENTIONED in literature review
4. Identify the LEVEL OF ANALYSIS for each phenomenon (individual, team, organization, industry, economy)
5. Capture TEMPORAL and GEOGRAPHIC scope when mentioned
6. Note BOUNDARY CONDITIONS for theories and findings
7. Identify MECHANISMS linking theories to phenomena

QUALITY STANDARDS:
- High confidence (0.8+): Explicitly stated, central to paper
- Medium confidence (0.5-0.8): Clearly mentioned, supporting role
- Low confidence (0.3-0.5): Implied or briefly mentioned
- Do not extract if confidence < 0.3

OUTPUT: Valid JSON only. No markdown, no comments, no extra text."""

    def _build_extraction_prompt(self, text: str, extraction_type: str, paper_id: str) -> str:
        """Build extraction prompt for specific entity type"""

        prompts = {
            "metadata": f"""Extract paper metadata from this Strategic Management Journal paper.

TEXT (first 6000 chars):
{text[:6000]}

Return JSON with:
- title: exact title
- abstract: full abstract text
- publication_year: integer year
- doi: if present
- keywords: array of keywords
- paper_type: empirical_quantitative, empirical_qualitative, theoretical, review, meta_analysis, or research_note
- research_context: brief description of research setting""",

            "theories": f"""Extract THEORIES and THEORETICAL FRAMEWORKS from this paper.

CRITICAL RULES:
1. Only extract theories ACTUALLY USED in the analysis, not just mentioned
2. PRIMARY = main theoretical framework driving the research
3. SUPPORTING = theories used to support arguments
4. CHALLENGING = theories the paper argues against
5. EXTENDING = theories the paper builds upon/extends
6. Include KEY CONSTRUCTS for each theory
7. Note ASSUMPTIONS and BOUNDARY CONDITIONS if stated

TEXT:
{text[:15000]}

Return JSON array of theories with: theory_name, role, domain, usage_context, section, key_constructs, assumptions, boundary_conditions, confidence""",

            "phenomena": f"""Extract PHENOMENA studied in this paper.

PHENOMENA = Observable behaviors, patterns, events, trends, processes, or outcomes being investigated.

CRITICAL RULES:
1. Identify the MAIN phenomenon being studied
2. Note related/secondary phenomena
3. Specify LEVEL OF ANALYSIS (individual, team, organization, industry, economy, multi_level)
4. Capture TEMPORAL SCOPE (cross-sectional, longitudinal, historical)
5. Note GEOGRAPHIC SCOPE if specified
6. Link to theories that explain this phenomenon

TEXT:
{text[:15000]}

Return JSON array of phenomena with: phenomenon_name, phenomenon_type, domain, description, context, level_of_analysis, temporal_scope, geographic_scope, related_theories, confidence""",

            "methods": f"""Extract RESEARCH METHODS and METHODOLOGY from this paper.

Focus on the METHODOLOGY section and capture:
1. Primary analytical method(s)
2. Software/tools used
3. Sample details (size, type, selection criteria)
4. Data sources
5. Time period covered
6. Robustness checks performed

TEXT:
{text[:12000]}

Return JSON array of methods with: method_name, method_type, method_category, software, sample_size, sample_type, data_sources, time_period, geographic_scope, industry_context, robustness_checks, confidence""",

            "variables": f"""Extract VARIABLES from this paper's methodology.

Identify:
1. Dependent variables (outcomes)
2. Independent variables (predictors)
3. Control variables
4. Moderators (boundary conditions)
5. Mediators (mechanisms)
6. Instrumental variables (if any)

For each, note measurement and operationalization.

TEXT:
{text[:12000]}

Return JSON array of variables with: variable_name, variable_type, measurement, operationalization, data_source, theoretical_basis""",

            "findings": f"""Extract KEY FINDINGS and RESULTS from this paper.

Focus on:
1. Hypothesis test results (supported/rejected)
2. Statistical significance and effect sizes
3. Unexpected findings
4. Boundary conditions discovered

TEXT:
{text[:12000]}

Return JSON array of findings with: finding_text, finding_type, statistical_significance, effect_size, practical_significance, related_hypotheses, boundary_conditions""",

            "contributions": f"""Extract CONTRIBUTIONS claimed by this paper.

Identify:
1. Theoretical contributions (new theory, extension, integration)
2. Empirical contributions (new evidence, new context)
3. Methodological contributions (new method, improved measurement)
4. Practical contributions (managerial implications)

TEXT:
{text[:10000]}

Return JSON array of contributions with: contribution_text, contribution_type, novelty_claim, extends_prior_work""",

            "authors": f"""Extract AUTHOR information from this paper.

TEXT (first 3000 chars):
{text[:3000]}

Return JSON array of authors with: full_name, given_name, family_name, position (1=first author), affiliations (as array of institution names), corresponding_author, email (if available), orcid (if available).

For affiliations, extract institution/university names. If available, also extract: city, country, department, school_college.""",

            "theory_phenomenon_links": f"""Analyze the RELATIONSHIPS between theories and phenomena in this paper.

For each theory-phenomenon pair:
1. How does the theory explain/predict the phenomenon?
2. What is the MECHANISM linking them?
3. What is the EVIDENCE STRENGTH (strong, moderate, weak, theoretical)?
4. What are the CONTEXT CONDITIONS?

TEXT:
{text[:15000]}

Return JSON array with: theory_name, phenomenon_name, relationship_type, mechanism, evidence_strength, context_conditions""",
            
            # Combined extraction prompts (optimized - 3 calls instead of 10)
            "metadata_and_authors": f"""Extract PAPER METADATA and AUTHOR INFORMATION from this paper.

METADATA: Extract title, abstract, publication year, DOI, keywords, paper type, research context.
AUTHORS: Extract all authors with full names, positions, affiliations (institution names as strings), corresponding author status, email, orcid.

TEXT (first 5000 chars for metadata + authors):
{text[:5000]}

Return JSON object with: metadata (object), authors (array)""",
            
            "theories_phenomena_links": f"""Extract THEORIES, PHENOMENA, and their RELATIONSHIPS from this paper.

THEORIES: Extract all theoretical frameworks used (primary, supporting, challenging, extending).
PHENOMENA: Extract all observable behaviors, patterns, events, trends, processes, or outcomes studied.
THEORY-PHENOMENON LINKS: Analyze how each theory explains/predicts each phenomenon.

Focus on Introduction and Literature Review sections.

TEXT:
{text[:15000]}

Return JSON object with: theories (array), phenomena (array), theory_phenomenon_links (array)""",
            
            "methods_variables_findings_contributions_questions": f"""Extract METHODOLOGY, VARIABLES, FINDINGS, CONTRIBUTIONS, and RESEARCH QUESTIONS from this paper.

METHODS: Extract research methods, software, sample details, data sources, time period.
VARIABLES: Extract dependent, independent, control, moderator, mediator variables.
FINDINGS: Extract key results, hypothesis tests, statistical significance, effect sizes.
CONTRIBUTIONS: Extract theoretical, empirical, methodological, practical contributions.
RESEARCH QUESTIONS: Extract all research questions addressed.

Focus on Methodology, Results, and Discussion sections.

TEXT:
{text[:15000]}

Return JSON object with: methods (array), variables (array), findings (array), contributions (array), research_questions (array)"""
        }

        return prompts.get(extraction_type, prompts["metadata"])

    async def _extract_with_json_mode(self,
                                       text: str,
                                       extraction_type: str,
                                       paper_id: str) -> Dict[str, Any]:
        """
        Extract using GPT-4 Turbo with JSON mode
        OPTIMIZED: Supports combined extraction types (3 calls instead of 10)

        Args:
            text: Paper text to extract from
            extraction_type: Type of extraction (can be combined type)
            paper_id: Paper identifier

        Returns:
            Extracted data as dictionary
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_extraction_prompt(text, extraction_type, paper_id)

        # Increase max_tokens for combined extractions (but stay within model limits)
        # GPT-4 Turbo supports max 4096 completion tokens, so we use 4000 to be safe
        is_combined = extraction_type in ["metadata_and_authors", "theories_phenomena_links", 
                                          "methods_variables_findings_contributions_questions"]
        max_tokens = 4000  # Model limit is 4096, using 4000 for safety

        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=self.temperature,
                    max_tokens=max_tokens
                )

                result = json.loads(response.choices[0].message.content)
                logger.debug(f"Successfully extracted {extraction_type} for {paper_id} ({len(str(result))} chars)")
                return result

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error for {extraction_type} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {}

            except Exception as e:
                logger.error(f"Extraction error for {extraction_type} (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {}

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()
            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"PDF extraction failed for {pdf_path}: {e}")
            return ""

    def _normalize_entities(self, result: ExtractionResult) -> ExtractionResult:
        """Normalize all extracted entities"""

        # Normalize theories
        for theory in result.theories:
            if "theory_name" in theory:
                theory["theory_name"] = self.normalizer.normalize_theory(theory["theory_name"])

        # Normalize methods
        for method in result.methods:
            if "method_name" in method:
                method["method_name"] = self.normalizer.normalize_method(method["method_name"])
            if "software" in method:
                method["software"] = [
                    self.normalizer.normalize_software(s) for s in method["software"]
                ]

        # Normalize phenomena
        for phenomenon in result.phenomena:
            if "phenomenon_name" in phenomenon:
                phenomenon["phenomenon_name"] = self.normalizer.normalize_phenomenon(phenomenon["phenomenon_name"])

        # Normalize variables
        for variable in result.variables:
            if "variable_name" in variable:
                variable["variable_name"] = self.normalizer.normalize_variable(variable["variable_name"])

        return result

    def _validate_entities(self, result: ExtractionResult) -> ExtractionResult:
        """Validate all extracted entities - with normalization before validation"""

        # Normalize and validate theories
        validated_theories = []
        for theory in result.theories:
            # Normalize before validation
            try:
                from normalize_before_validation import normalize_theory_data
                normalized_theory = normalize_theory_data(theory)
                if normalized_theory:
                    validated = self.validator.validate_theory(normalized_theory)
                    if validated:
                        validated_theories.append(normalized_theory)
                    else:
                        # Keep even if validation fails (will be handled in ingestion)
                        validated_theories.append(normalized_theory)
                else:
                    validated_theories.append(theory)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing theory {theory.get('theory_name', 'unknown')}: {e}")
                validated_theories.append(theory)  # Keep original on error
        result.theories = validated_theories

        # Normalize and validate methods
        validated_methods = []
        for method in result.methods:
            if "confidence" not in method:
                method["confidence"] = 0.8
            # Normalize before validation
            try:
                from normalize_before_validation import normalize_method_data
                normalized_method = normalize_method_data(method)
                if normalized_method:
                    validated = self.validator.validate_method(normalized_method)
                    if validated:
                        validated_methods.append(normalized_method)
                    else:
                        # Keep even if validation fails (will be handled in ingestion)
                        validated_methods.append(normalized_method)
                else:
                    validated_methods.append(method)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing method {method.get('method_name', 'unknown')}: {e}")
                validated_methods.append(method)  # Keep original on error
        result.methods = validated_methods

        # Normalize and validate phenomena
        validated_phenomena = []
        for phenomenon in result.phenomena:
            try:
                from normalize_before_validation import normalize_phenomenon_data
                normalized_phenomenon = normalize_phenomenon_data(phenomenon)
                if normalized_phenomenon:
                    validated = self.validator.validate_phenomenon(normalized_phenomenon)
                    if validated:
                        validated_phenomena.append(normalized_phenomenon)
                    else:
                        validated_phenomena.append(normalized_phenomenon)  # Keep even if validation fails
                else:
                    validated_phenomena.append(phenomenon)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing phenomenon {phenomenon.get('phenomenon_name', 'unknown')}: {e}")
                validated_phenomena.append(phenomenon)  # Keep original on error
        result.phenomena = validated_phenomena

        # Normalize and validate variables
        validated_variables = []
        for variable in result.variables:
            try:
                from normalize_before_validation import normalize_variable_data
                normalized_variable = normalize_variable_data(variable)
                if normalized_variable:
                    validated = self.validator.validate_variable(normalized_variable)
                    if validated:
                        validated_variables.append(normalized_variable)
                    else:
                        validated_variables.append(normalized_variable)  # Keep even if validation fails
                else:
                    validated_variables.append(variable)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing variable {variable.get('variable_name', 'unknown')}: {e}")
                validated_variables.append(variable)  # Keep original on error
        result.variables = validated_variables

        # Normalize and validate findings
        validated_findings = []
        for finding in result.findings:
            try:
                from normalize_before_validation import normalize_finding_data
                normalized_finding = normalize_finding_data(finding)
                if normalized_finding:
                    validated = self.validator.validate_finding(normalized_finding)
                    if validated:
                        validated_findings.append(normalized_finding)
                    else:
                        validated_findings.append(normalized_finding)  # Keep even if validation fails
                else:
                    validated_findings.append(finding)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing finding: {e}")
                validated_findings.append(finding)  # Keep original on error
        result.findings = validated_findings

        # Normalize and validate contributions
        validated_contributions = []
        for contribution in result.contributions:
            try:
                from normalize_before_validation import normalize_contribution_data
                normalized_contribution = normalize_contribution_data(contribution)
                if normalized_contribution:
                    validated = self.validator.validate_contribution(normalized_contribution)
                    if validated:
                        validated_contributions.append(normalized_contribution)
                    else:
                        validated_contributions.append(normalized_contribution)  # Keep even if validation fails
                else:
                    validated_contributions.append(contribution)  # Keep original if normalization fails
            except Exception as e:
                logger.warning(f"Error normalizing contribution: {e}")
                validated_contributions.append(contribution)  # Keep original on error
        result.contributions = validated_contributions

        return result

    async def extract_paper_async(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract all entities from a paper asynchronously
        OPTIMIZED: Uses 3 combined API calls instead of 10 separate calls (3-5x speedup)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Complete ExtractionResult
        """
        paper_id = pdf_path.stem
        start_time = datetime.now()

        logger.info(f"Starting optimized extraction for {paper_id} (3 combined API calls)")

        # Extract text from PDF
        text = self._extract_pdf_text(pdf_path)
        if not text:
            logger.error(f"No text extracted from {pdf_path}")
            return ExtractionResult(paper_id=paper_id)

        # OPTIMIZED: Run 3 combined extractions in parallel instead of 10 separate calls
        # This reduces API calls from 10 to 3, providing 3-5x speedup
        extraction_tasks = [
            self._extract_with_json_mode(text, "metadata_and_authors", paper_id),
            self._extract_with_json_mode(text, "theories_phenomena_links", paper_id),
            self._extract_with_json_mode(text, "methods_variables_findings_contributions_questions", paper_id)
        ]

        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        # Build result object
        result = ExtractionResult(paper_id=paper_id)

        # Process Call 1: metadata_and_authors (with bounds checking)
        if len(results) > 0 and isinstance(results[0], dict) and not isinstance(results[0], Exception):
            result.metadata = results[0].get("metadata", {})
            result.metadata["paper_id"] = paper_id
            result.authors = results[0].get("authors", []) or []
        else:
            error_msg = str(results[0]) if len(results) > 0 and isinstance(results[0], Exception) else "No result"
            logger.warning(f"Failed to extract metadata_and_authors for {paper_id}: {error_msg}")
            result.metadata = {}
            result.authors = []

        # Process Call 2: theories_phenomena_links (with bounds checking)
        if len(results) > 1 and isinstance(results[1], dict) and not isinstance(results[1], Exception):
            result.theories = results[1].get("theories", []) or []
            result.phenomena = results[1].get("phenomena", []) or []
            result.extraction_metadata["theory_phenomenon_links"] = results[1].get("theory_phenomenon_links", []) or []
        else:
            error_msg = str(results[1]) if len(results) > 1 and isinstance(results[1], Exception) else "No result"
            logger.warning(f"Failed to extract theories_phenomena_links for {paper_id}: {error_msg}")
            result.theories = []
            result.phenomena = []
            result.extraction_metadata["theory_phenomenon_links"] = []

        # Process Call 3: methods_variables_findings_contributions_questions (with bounds checking)
        if len(results) > 2 and isinstance(results[2], dict) and not isinstance(results[2], Exception):
            result.methods = results[2].get("methods", []) or []
            result.variables = results[2].get("variables", []) or []
            result.findings = results[2].get("findings", []) or []
            result.contributions = results[2].get("contributions", []) or []
            result.research_questions = results[2].get("research_questions", []) or []
        else:
            error_msg = str(results[2]) if len(results) > 2 and isinstance(results[2], Exception) else "No result"
            logger.warning(f"Failed to extract methods_variables_findings_contributions_questions for {paper_id}: {error_msg}")
            result.methods = []
            result.variables = []
            result.findings = []
            result.contributions = []
            result.research_questions = []

        # Ensure all fields are lists (defensive)
        result.theories = result.theories or []
        result.phenomena = result.phenomena or []
        result.methods = result.methods or []
        result.variables = result.variables or []
        result.findings = result.findings or []
        result.contributions = result.contributions or []
        result.authors = result.authors or []
        result.research_questions = result.research_questions or []
        result.metadata = result.metadata or {}
        result.extraction_metadata = result.extraction_metadata or {}

        # Add extraction metadata
        extraction_time = (datetime.now() - start_time).total_seconds()
        result.extraction_metadata["extraction_time"] = extraction_time
        result.extraction_metadata["model"] = self.model
        result.extraction_metadata["extracted_at"] = datetime.now().isoformat()
        result.extraction_metadata["text_length"] = len(text)
        result.extraction_metadata["api_calls"] = 3  # Track optimization

        # Normalize and validate
        result = self._normalize_entities(result)
        result = self._validate_entities(result)

        # Debug: Check if theories/methods are actually in results
        theories_count = len(result.theories) if result.theories else 0
        methods_count = len(result.methods) if result.methods else 0
        if theories_count == 0 and len(results) > 1 and isinstance(results[1], dict):
            theories_raw = results[1].get("theories", [])
            if theories_raw:
                logger.warning(f"⚠️ Theories found in raw results but not in result object: {len(theories_raw)} theories")
        if methods_count == 0 and len(results) > 2 and isinstance(results[2], dict):
            methods_raw = results[2].get("methods", [])
            if methods_raw:
                logger.warning(f"⚠️ Methods found in raw results but not in result object: {len(methods_raw)} methods")
        
        logger.info(f"Completed extraction for {paper_id}: {theories_count} theories, "
                   f"{len(result.phenomena)} phenomena, {methods_count} methods")

        return result

    def extract_paper(self, pdf_path: Path) -> ExtractionResult:
        """Synchronous wrapper for extract_paper_async"""
        return asyncio.run(self.extract_paper_async(pdf_path))

    async def extract_papers_batch(self,
                                    pdf_paths: List[Path],
                                    max_concurrent: int = 10) -> List[ExtractionResult]:
        """
        Extract multiple papers with controlled concurrency

        Args:
            pdf_paths: List of PDF file paths
            max_concurrent: Maximum concurrent extractions

        Returns:
            List of ExtractionResults
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_limit(path: Path) -> ExtractionResult:
            async with semaphore:
                try:
                    return await self.extract_paper_async(path)
                except Exception as e:
                    logger.error(f"Failed to extract {path}: {e}")
                    return ExtractionResult(paper_id=path.stem)

        tasks = [extract_with_limit(path) for path in pdf_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, ExtractionResult):
                valid_results.append(result)
            else:
                logger.error(f"Extraction failed for {pdf_paths[i]}: {result}")
                valid_results.append(ExtractionResult(paper_id=pdf_paths[i].stem))

        return valid_results


# Singleton instance
_extractor = None

def get_extractor(model: str = "gpt-4-turbo-preview") -> EnhancedGPT4Extractor:
    """Get singleton extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = EnhancedGPT4Extractor(model=model)
    return _extractor


if __name__ == "__main__":
    # Test extraction
    import sys

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        extractor = get_extractor()
        result = extractor.extract_paper(pdf_path)
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("Usage: python enhanced_gpt4_extractor.py <pdf_path>")
