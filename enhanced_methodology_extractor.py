#!/usr/bin/env python3
"""
Enhanced Methodology Extraction System with Paper Metadata and Method Relationships
Extracts comprehensive paper metadata and detailed methodology information
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import fitz  # PyMuPDF
from neo4j import GraphDatabase
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedOllamaExtractor:
    """Enhanced OLLAMA-based extractor for paper metadata and detailed methodology"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:7b"):
        self.base_url = base_url
        self.model = model
        self.max_retries = 3
        self.retry_delay = 3
        self.timeout = 180
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test OLLAMA connection"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model in model_names:
                    logger.info(f"✓ OLLAMA connected, model '{self.model}' available")
                else:
                    logger.warning(f"⚠️ Model '{self.model}' not found. Available: {model_names}")
                    if model_names:
                        self.model = model_names[0]
                        logger.info(f"Using available model: {self.model}")
            else:
                raise Exception(f"OLLAMA API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to OLLAMA: {e}")
            raise
    
    def extract_with_retry(self, prompt: str, max_tokens: int = 6000) -> str:
        """Extract using OLLAMA with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self._call_ollama(prompt, max_tokens)
                return response
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Timeout detected, waiting {wait_time} seconds before retry...")
                    import time
                    time.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise
    
    def _call_ollama(self, prompt: str, max_tokens: int = 6000) -> str:
        """Make API call to OLLAMA"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": max_tokens,
                "stop": ["```", "---", "END", "USER:"]
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            raise Exception(f"OLLAMA API error: {response.status_code} - {response.text}")
    
    def extract_paper_metadata(self, text: str, paper_id: str) -> Dict[str, Any]:
        """Extract comprehensive paper metadata"""
        # Increased text limit from 20,000 to 50,000 characters
        if len(text) > 50000:
            text = text[:50000] + "..."
        
        prompt = f"""Extract paper metadata from this academic paper. Return ONLY valid JSON.

Paper text: {text[:20000]}

Extract the following information:
- Title: The main title of the paper
- Abstract: The abstract section (first 500 characters)
- Authors: List of author names
- Year: Publication year
- Email: Corresponding author email if found
- Journal: Journal name
- DOI: DOI if available
- Keywords: List of keywords

Return JSON format:
{{
  "paper_id": "{paper_id}",
  "title": "Paper Title",
  "abstract": "Abstract text...",
  "authors": ["Author 1", "Author 2"],
  "year": 2023,
  "email": "author@university.edu",
  "journal": "Journal Name",
  "doi": "10.1000/182",
  "keywords": ["keyword1", "keyword2"]
}}"""
        
        response = self.extract_with_retry(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    def extract_detailed_methodology(self, text: str, paper_id: str) -> Dict[str, Any]:
        """Extract detailed methodology with specific method types - Enhanced version"""
        # Increased text limit from 20,000 to 50,000 characters
        if len(text) > 50000:
            text = text[:50000] + "..."
        
        # First, try to find the methodology section specifically
        methodology_section = self._extract_methodology_section(text)
        
        # Increased methodology section limit from 2,000 to 5,000 characters
        methodology_text = methodology_section[:5000] if methodology_section else ""
        full_text_sample = text[:15000]  # Increased from 8,000 to 15,000 characters
        
        # If methodology section exists but is not in the first 15k chars, include it explicitly
        if methodology_text and methodology_text not in full_text_sample:
            # Find methodology section in full text and include more context
            methodology_start = text.find(methodology_section[:200]) if methodology_section else -1
            if methodology_start > 0:
                # Include text around methodology section
                start = max(0, methodology_start - 2000)
                end = min(len(text), methodology_start + len(methodology_section) + 2000)
                context_around_methodology = text[start:end]
                full_text_sample = context_around_methodology[:15000]
        
        prompt = f"""You are an expert research methodology analyst. Extract detailed methodology information from this academic paper.

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. Extract ONLY what is EXPLICITLY STATED in the paper text below
2. DO NOT list all possible methods - only extract methods that are ACTUALLY MENTIONED in this specific paper
3. If a method is NOT mentioned in the paper, DO NOT include it - use empty array []
4. Each paper is DIFFERENT - extract what is unique to THIS paper
5. For software, extract ONLY the exact software names and versions mentioned in THIS paper
6. DO NOT return generic lists - be paper-specific

Paper ID: {paper_id}

{"=" * 60}
METHODOLOGY SECTION FROM THIS PAPER:
{methodology_text if methodology_text else "No specific methodology section identified - analyze the full text below"}
{"=" * 60}

RELEVANT PAPER TEXT:
{full_text_sample}
{"=" * 60}

IMPORTANT: The examples below show TYPES of methods that might exist. Only extract methods that are ACTUALLY MENTIONED in the paper text above.

QUANTITATIVE METHODS: Only extract if explicitly mentioned:
- Regression: OLS, Logistic Regression, Probit, Tobit, Poisson, Negative Binomial
- Advanced: IV/2SLS, 3SLS, GMM, Difference-in-Differences, RDD, Event Study
- Survival: Cox PH, Weibull, Accelerated Failure Time
- Time series: ARIMA, VAR, GARCH, Cointegration
- Panel: Fixed Effects, Random Effects, First Differences, System GMM
- ML: Random Forest, SVM, Neural Network, XGBoost
- Structural: SEM, CFA, Path Analysis
- Other: Meta-Analysis, Monte Carlo, Bootstrap

QUALITATIVE METHODS: Only extract if explicitly mentioned:
- Case Study, Multiple Case Study, Comparative Case Study
- Grounded Theory, Thematic Analysis, Content Analysis
- Ethnography, Participant Observation, Field Study
- QCA, Fuzzy-Set QCA, Crisp-Set QCA
- Discourse Analysis, Narrative Analysis, Phenomenology
- Action Research, Participatory Research

SOFTWARE: Extract exact software names and versions:
- Statistical: "Stata", "R", "SAS", "SPSS", "MATLAB", "Python", "Julia"
- Qualitative: "NVivo", "Atlas.ti", "MAXQDA", "Dedoose"
- Specialized: "Mplus", "Amos", "Lisrel", "EViews", "Gretl"
- Always include version numbers if mentioned (e.g., "Stata 17", "R 4.2.1")

RESEARCH DESIGN: Extract design types:
- "Experimental", "Quasi-Experimental", "RCT", "Natural Experiment"
- "Cross-Sectional", "Longitudinal", "Panel Study", "Time Series"
- "Case Study", "Multiple Case Study", "Comparative Case Study"
- "Survey", "Interview Study", "Field Study", "Archival Study"
- "Meta-Analysis", "Systematic Review", "SLR"

SAMPLE SIZE: Extract specific numbers or descriptions (e.g., "1,234 firms", "348 observations", "15 interviews", "N=500")

DATA SOURCES: Extract specific databases or sources (e.g., "Compustat", "CRSP", "Thomson Reuters", "SEC filings", "Interviews", "Survey data", "Archival data")

VARIABLES/CONSTRUCTS: Extract key variables or constructs measured:
- Dependent variables (e.g., "Firm Performance", "Innovation", "CEO Turnover")
- Independent variables (e.g., "Board Independence", "R&D Investment", "Market Competition")
- Control variables (e.g., "Firm Size", "Industry", "Year")
- Moderators/Mediators if mentioned

STATISTICAL TESTS: Extract specific tests used:
- "t-test", "F-test", "Chi-square", "Mann-Whitney U", "Kruskal-Wallis"
- "Hausman test", "Breusch-Pagan test", "Shapiro-Wilk test"
- "Granger Causality", "Unit Root Test", "Cointegration Test"
- "Robustness checks", "Sensitivity analysis", "Placebo tests"

VALIDITY/RELIABILITY: Extract measures mentioned:
- "Cronbach's Alpha", "Inter-rater reliability", "Test-retest reliability"
- "Construct validity", "Convergent validity", "Discriminant validity"
- "Internal validity", "External validity", "Face validity"

ASSUMPTIONS: Extract statistical assumptions checked:
- "Normality", "Homoscedasticity", "Multicollinearity", "Independence"
- "Linearity", "Stationarity", "No autocorrelation"

LIMITATIONS: Extract methodology limitations mentioned by authors

HYPOTHESES: Extract number of hypotheses or key hypotheses tested (if mentioned)

DATA COLLECTION: Extract data collection methods:
- "Survey", "Interviews", "Focus groups", "Observation", "Archival research"
- "Secondary data", "Primary data", "Longitudinal data collection"

TIME PERIOD: Extract time period of study (e.g., "2000-2020", "2015-2019")

CRITICAL WARNINGS:
1. The JSON schema below shows the STRUCTURE only - do NOT copy example values
2. If a method is NOT mentioned in THIS paper, use empty array [] - DO NOT list all possible methods
3. Each paper is UNIQUE - extract only what THIS specific paper states
4. DO NOT return generic lists like ["OLS", "Logistic Regression", "Probit", "Tobit", "Poisson", "Negative Binomial"] unless ALL are mentioned
5. If only "OLS" is mentioned, return ["OLS"] - NOT the entire list
6. The examples above are REFERENCE ONLY - extract what is ACTUALLY in the paper text

Return comprehensive JSON format with confidence score (0.0-1.0):
{{
  "paper_id": "{paper_id}",
  "methodology": {{
    "type": "quantitative/qualitative/mixed/other",
    "design": [],
    "quant_methods": [],
    "qual_methods": [],
    "software": [],
    "sample_size": "",
    "data_sources": [],
    "analysis_techniques": [],
    "statistical_tests": [],
    "variables": {{
      "dependent": [],
      "independent": [],
      "control": [],
      "moderators": [],
      "mediators": []
    }},
    "validity_reliability": {{
      "reliability_measures": [],
      "validity_measures": []
    }},
    "assumptions_checked": [],
    "limitations": [],
    "hypotheses_count": 0,
    "data_collection": [],
    "time_period": "",
    "confidence": 0.0,
    "extraction_notes": ""
  }}
}}

Calculate confidence as:
- 0.9-1.0: Very clear methodology section with specific methods, software, and sample details
- 0.7-0.89: Clear methodology with most details present
- 0.5-0.69: Some methodology details found but incomplete
- 0.3-0.49: Vague or minimal methodology information
- 0.0-0.29: No clear methodology found or very unclear

CRITICAL: Return ONLY valid JSON. No explanations, no markdown, no additional text. Start with {{ and end with }}."""
        
        response = self.extract_with_retry(prompt, max_tokens=8000)  # Increased to 8000 for comprehensive extraction
        result = self._parse_json_response(response)
        
        # Post-process to validate and filter extracted methods
        if result and "methodology" in result:
            methodology = result["methodology"]
            
            # Validate extracted methods against actual text
            methodology = self._validate_extracted_methods(methodology, text, methodology_section)
            
            # Recalculate confidence if not properly set
            confidence = methodology.get("confidence", 0.0)
            if confidence == 0.0 or confidence < 0.1:
                confidence = self._calculate_confidence(methodology)
                methodology["confidence"] = confidence
            
            result["methodology"] = methodology
        
        return result
    
    def _validate_extracted_methods(self, methodology: Dict[str, Any], full_text: str, methodology_section: str) -> Dict[str, Any]:
        """Validate that extracted methods are actually mentioned in the paper text"""
        # Combine text sources for validation
        validation_text = (methodology_section + " " + full_text[:20000]).lower()
        
        # Common generic lists that should be filtered
        generic_quant_list = ["ols", "logistic regression", "probit", "tobit", "poisson", "negative binomial"]
        generic_qual_list = ["case study", "multiple case study", "comparative case study"]
        generic_software_list = ["stata", "r", "sas", "spss", "matlab", "python", "julia"]
        
        # Validate quantitative methods
        quant_methods = methodology.get("quant_methods", [])
        if quant_methods:
            # Check if this looks like a generic list (all items from generic list)
            if len(quant_methods) >= 4 and all(m.lower() in generic_quant_list for m in quant_methods):
                # Validate each method is actually mentioned
                validated_quant = []
                for method in quant_methods:
                    method_lower = method.lower()
                    # Check if method is mentioned in text
                    if method_lower in validation_text or any(word in validation_text for word in method_lower.split() if len(word) > 3):
                        validated_quant.append(method)
                methodology["quant_methods"] = validated_quant
                if len(validated_quant) < len(quant_methods):
                    logger.info(f"Filtered {len(quant_methods) - len(validated_quant)} unvalidated quant methods")
        
        # Validate qualitative methods
        qual_methods = methodology.get("qual_methods", [])
        if qual_methods:
            # Check if this looks like a generic list
            if len(qual_methods) >= 3 and all(m.lower() in generic_qual_list for m in qual_methods):
                validated_qual = []
                for method in qual_methods:
                    method_lower = method.lower()
                    if method_lower in validation_text or any(word in validation_text for word in method_lower.split() if len(word) > 3):
                        validated_qual.append(method)
                methodology["qual_methods"] = validated_qual
                if len(validated_qual) < len(qual_methods):
                    logger.info(f"Filtered {len(qual_methods) - len(validated_qual)} unvalidated qual methods")
        
        # Validate software
        software = methodology.get("software", [])
        if software:
            # Check if this looks like a generic list
            if len(software) >= 5 and all(s.lower().split()[0] in generic_software_list if s else False for s in software):
                validated_software = []
                for sw in software:
                    sw_lower = sw.lower()
                    if sw_lower in validation_text or any(word in validation_text for word in sw_lower.split() if len(word) > 2):
                        validated_software.append(sw)
                methodology["software"] = validated_software
                if len(validated_software) < len(software):
                    logger.info(f"Filtered {len(software) - len(validated_software)} unvalidated software")
        
        return methodology
    
    def _calculate_confidence(self, methodology: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality"""
        confidence = 0.0
        
        # Base confidence from methodology type
        m_type = methodology.get("type", "").lower()
        if m_type and m_type != "other":
            confidence += 0.2
        
        # Confidence from specific methods
        quant_methods = methodology.get("quant_methods", [])
        qual_methods = methodology.get("qual_methods", [])
        if quant_methods or qual_methods:
            # Check if methods are specific (not generic)
            specific_methods = []
            generic_terms = ["statistical", "analysis", "method", "approach", "data", "study"]
            
            for method in quant_methods + qual_methods:
                method_lower = method.lower()
                # Check if it's a specific method (not just generic words)
                # A method is specific if it doesn't contain only generic terms OR has more than 2 words
                is_generic = any(term in method_lower for term in generic_terms) and len(method.split()) <= 2
                if not is_generic:
                    specific_methods.append(method)
            
            if specific_methods:
                confidence += 0.3
            elif quant_methods or qual_methods:
                confidence += 0.1
        
        # Confidence from software
        software = methodology.get("software", [])
        if software:
            confidence += 0.2
        
        # Confidence from sample size
        sample_size = methodology.get("sample_size", "")
        if sample_size and sample_size.strip():
            confidence += 0.1
        
        # Confidence from data sources
        data_sources = methodology.get("data_sources", [])
        if data_sources:
            confidence += 0.1
        
        # Confidence from design
        design = methodology.get("design", [])
        if design:
            confidence += 0.1
        
        # Confidence from variables (comprehensive extraction)
        variables = methodology.get("variables", {})
        if isinstance(variables, dict):
            dep_vars = variables.get("dependent", [])
            ind_vars = variables.get("independent", [])
            if dep_vars or ind_vars:
                confidence += 0.05
        
        # Confidence from validity/reliability measures
        validity_reliability = methodology.get("validity_reliability", {})
        if isinstance(validity_reliability, dict):
            rel_measures = validity_reliability.get("reliability_measures", [])
            val_measures = validity_reliability.get("validity_measures", [])
            if rel_measures or val_measures:
                confidence += 0.05
        
        # Confidence from assumptions checked
        assumptions = methodology.get("assumptions_checked", [])
        if assumptions:
            confidence += 0.05
        
        # Confidence from data collection methods
        data_collection = methodology.get("data_collection", [])
        if data_collection:
            confidence += 0.05
        
        # Confidence from time period
        time_period = methodology.get("time_period", "")
        if time_period and time_period.strip():
            confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_methodology_section(self, text: str) -> str:
        """Extract the methodology section from the paper text"""
        # Look for methodology section headers
        methodology_keywords = [
            "methodology", "methods", "research design", "data and methods",
            "empirical strategy", "analysis", "method", "approach"
        ]
        
        lines = text.split('\n')
        methodology_section = ""
        in_methodology = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line contains methodology keywords
            if any(keyword in line_lower for keyword in methodology_keywords):
                if len(line.strip()) < 100:  # Likely a header
                    in_methodology = True
                    methodology_section += line + "\n"
                    continue
            
            if in_methodology:
                methodology_section += line + "\n"
                
                # Stop if we hit another major section
                if any(section in line_lower for section in ["results", "findings", "conclusion", "discussion", "references"]):
                    break
                
                # Increased limit from 3000 to 8000 characters for longer methodology sections
                if len(methodology_section) > 8000:
                    break
        
        return methodology_section.strip()
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from OLLAMA with robust error handling"""
        try:
            # Clean the response
            response = response.strip()
            
            # Remove any markdown formatting
            if response.startswith("```json"):
                response = response[7:].strip()
            elif response.startswith("```"):
                response = response[3:].strip()
            if response.endswith("```"):
                response = response[:-3].strip()
            
            # Try to find JSON object boundaries (handle nested objects)
            start_idx = response.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            # Find matching closing brace
            brace_count = 0
            end_idx = -1
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if end_idx == -1 or end_idx <= start_idx:
                raise ValueError("Invalid JSON structure")
            
            json_str = response[start_idx:end_idx + 1]
            
            # Parse JSON
            data = json.loads(json_str)
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.warning(f"Response was: {response[:500]}...")
            
            # Return empty structure as fallback
            return {
                "paper_id": "",
                "title": "",
                "abstract": "",
                "authors": [],
                "year": 0,
                "email": "",
                "journal": "",
                "doi": "",
                "keywords": [],
                "methodology": {
                    "type": "other",
                    "design": [],
                    "quant_methods": [],
                    "qual_methods": [],
                    "software": [],
                    "sample_size": "",
                    "data_sources": [],
                    "analysis_techniques": [],
                    "statistical_tests": [],
                    "variables": {
                        "dependent": [],
                        "independent": [],
                        "control": [],
                        "moderators": [],
                        "mediators": []
                    },
                    "validity_reliability": {
                        "reliability_measures": [],
                        "validity_measures": []
                    },
                    "assumptions_checked": [],
                    "limitations": [],
                    "hypotheses_count": 0,
                    "data_collection": [],
                    "time_period": "",
                    "confidence": 0.0,
                    "extraction_notes": f"JSON parsing failed: {str(e)}"
                }
            }
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}

class PDFProcessor:
    """Handles PDF text extraction"""
    
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

class EnhancedNeo4jIngester:
    """Enhanced Neo4j ingester with method relationships"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, extractor: EnhancedOllamaExtractor = None):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.extractor = extractor  # LLM extractor for method normalization
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def ingest_paper_with_metadata(self, paper_data: Dict[str, Any]):
        """Ingest paper with comprehensive metadata"""
        paper_id = paper_data.get("paper_id", "")
        
        if not paper_id:
            logger.warning("Invalid paper data, skipping ingestion")
            return
        
        with self.driver.session() as session:
            # Create paper node with metadata
            session.run("""
                MERGE (p:Paper {paper_id: $paper_id})
                SET p.title = $title,
                    p.abstract = $abstract,
                    p.authors = $authors,
                    p.year = $year,
                    p.email = $email,
                    p.journal = $journal,
                    p.doi = $doi,
                    p.keywords = $keywords,
                    p.created_at = datetime()
            """, 
            paper_id=paper_id,
            title=paper_data.get("title", ""),
            abstract=paper_data.get("abstract", ""),
            authors=paper_data.get("authors", []),
            year=paper_data.get("year", 0),
            email=paper_data.get("email", ""),
            journal=paper_data.get("journal", ""),
            doi=paper_data.get("doi", ""),
            keywords=paper_data.get("keywords", []))
    
    def ingest_detailed_methodology(self, methodology_data: Dict[str, Any]):
        """Ingest detailed methodology with method relationships"""
        paper_id = methodology_data.get("paper_id", "")
        methodology = methodology_data.get("methodology", {})
        
        if not paper_id or not methodology:
            logger.warning("Invalid methodology data, skipping ingestion")
            return
        
        with self.driver.session() as session:
            # Remove any existing methodology nodes for this paper
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                OPTIONAL MATCH (p)-[r:HAS_METHODOLOGY]->(old_m:Methodology)
                DELETE r, old_m
            """, paper_id=paper_id)
            
            # Extract nested structures and flatten them for Neo4j
            variables = methodology.get("variables", {})
            validity_reliability = methodology.get("validity_reliability", {})
            
            # Flatten variables
            dependent_vars = variables.get("dependent", []) if isinstance(variables, dict) else []
            independent_vars = variables.get("independent", []) if isinstance(variables, dict) else []
            control_vars = variables.get("control", []) if isinstance(variables, dict) else []
            moderators = variables.get("moderators", []) if isinstance(variables, dict) else []
            mediators = variables.get("mediators", []) if isinstance(variables, dict) else []
            
            # Flatten validity/reliability
            reliability_measures = validity_reliability.get("reliability_measures", []) if isinstance(validity_reliability, dict) else []
            validity_measures = validity_reliability.get("validity_measures", []) if isinstance(validity_reliability, dict) else []
            
            # Create detailed methodology node with comprehensive fields
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                CREATE (m:Methodology {paper_id: $paper_id})
                SET m.type = $type,
                    m.design = $design,
                    m.quant_methods = $quant_methods,
                    m.qual_methods = $qual_methods,
                    m.software = $software,
                    m.sample_size = $sample_size,
                    m.data_sources = $data_sources,
                    m.analysis_techniques = $analysis_techniques,
                    m.statistical_tests = $statistical_tests,
                    m.dependent_variables = $dependent_vars,
                    m.independent_variables = $independent_vars,
                    m.control_variables = $control_vars,
                    m.moderators = $moderators,
                    m.mediators = $mediators,
                    m.reliability_measures = $reliability_measures,
                    m.validity_measures = $validity_measures,
                    m.assumptions_checked = $assumptions_checked,
                    m.limitations = $limitations,
                    m.hypotheses_count = $hypotheses_count,
                    m.data_collection = $data_collection,
                    m.time_period = $time_period,
                    m.confidence = $confidence,
                    m.extraction_notes = $extraction_notes,
                    m.created_at = datetime()
                CREATE (p)-[:HAS_METHODOLOGY]->(m)
            """, 
            paper_id=paper_id,
            type=methodology.get("type", ""),
            design=methodology.get("design", []),
            quant_methods=methodology.get("quant_methods", []),
            qual_methods=methodology.get("qual_methods", []),
            software=methodology.get("software", []),
            sample_size=methodology.get("sample_size", ""),
            data_sources=methodology.get("data_sources", []),
            analysis_techniques=methodology.get("analysis_techniques", []),
            statistical_tests=methodology.get("statistical_tests", []),
            dependent_vars=dependent_vars,
            independent_vars=independent_vars,
            control_vars=control_vars,
            moderators=moderators,
            mediators=mediators,
            reliability_measures=reliability_measures,
            validity_measures=validity_measures,
            assumptions_checked=methodology.get("assumptions_checked", []),
            limitations=methodology.get("limitations", []),
            hypotheses_count=methodology.get("hypotheses_count", 0),
            data_collection=methodology.get("data_collection", []),
            time_period=methodology.get("time_period", ""),
            confidence=methodology.get("confidence", 0.0),
            extraction_notes=methodology.get("extraction_notes", ""))
            
            # Create method relationships
            self._create_method_relationships(session, paper_id, methodology)
    
    def _normalize_method_name(self, method_description: str) -> str:
        """Use LLM to extract standardized method name from description"""
        if not method_description or not method_description.strip():
            return ""
        
        if not self.extractor:
            # Fallback: simple normalization without LLM
            return method_description.strip()
        
        prompt = f"""Extract the standardized, canonical name of the research method from this description.

Method description: {method_description}

Return ONLY the standardized method name (e.g., "Linear Regression", "Logistic Regression", "Hazard Model", "QCA", "Case Study", "Meta-Analysis", "SEM", "IV/2SLS", etc.).

If the description is too vague or generic, return "unknown".

Return only the method name, no explanation, no quotes, no JSON."""
        
        try:
            response = self.extractor.extract_with_retry(prompt, max_tokens=100)
            normalized = response.strip().strip('"').strip("'")
            # Remove common prefixes/suffixes
            normalized = normalized.replace("method:", "").replace("Method:", "").strip()
            return normalized if normalized and normalized.lower() != "unknown" else ""
        except Exception as e:
            logger.warning(f"Failed to normalize method name '{method_description}': {e}")
            return ""
    
    def _find_similar_methods_llm(self, current_method: str, other_methods: List[str]) -> List[str]:
        """Use LLM to find semantically similar methods"""
        if not current_method or not other_methods or not self.extractor:
            return []
        
        # Normalize current method
        normalized_current = self._normalize_method_name(current_method)
        if not normalized_current:
            return []
        
        # Limit methods list to avoid token limits
        methods_to_compare = other_methods[:20]  # Limit to 20 methods for efficiency
        methods_list = "\n".join([f"- {m}" for m in methods_to_compare])
        
        prompt = f"""You are comparing research methods to find which ones are the same or very similar.

Current method: {current_method}
Normalized name: {normalized_current}

Other methods to compare:
{methods_list}

For each method in the list, determine if it represents the SAME or VERY SIMILAR method as "{normalized_current}".

Return a JSON array of method descriptions that are the same or very similar. If none are similar, return an empty array [].

Example: If current method is "parametric proportional hazards model regressions" and another method is "Cox proportional hazards regression", they are the same method.

Return ONLY valid JSON array, no other text:
["method1", "method2", ...]"""
        
        try:
            response = self.extractor.extract_with_retry(prompt, max_tokens=500)
            # Parse JSON array
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip().strip("[]")
            
            # Try to parse as JSON array
            import json
            try:
                similar_methods = json.loads(f"[{response}]")
                return [m for m in similar_methods if m in other_methods]
            except:
                # Fallback: extract quoted strings
                import re
                similar_methods = re.findall(r'"([^"]+)"', response)
                return [m for m in similar_methods if m in other_methods]
        except Exception as e:
            logger.warning(f"Failed to find similar methods for '{current_method}': {e}")
            return []
    
    def _create_method_relationships(self, session, paper_id: str, methodology: Dict[str, Any]):
        """Create 'same method' relationships between papers using LLM-based semantic matching"""
        quant_methods = methodology.get("quant_methods", [])
        qual_methods = methodology.get("qual_methods", [])
        
        # Get all existing methodologies from other papers
        all_methods_query = session.run("""
            MATCH (p:Paper)-[:HAS_METHODOLOGY]->(m:Methodology)
            WHERE p.paper_id <> $paper_id
            RETURN p.paper_id as other_paper_id,
                   m.quant_methods as quant_methods,
                   m.qual_methods as qual_methods
        """, paper_id=paper_id)
        
        other_papers_data = []
        for record in all_methods_query:
            other_papers_data.append({
                'paper_id': record['other_paper_id'],
                'quant_methods': record['quant_methods'] or [],
                'qual_methods': record['qual_methods'] or []
            })
        
        # Process quantitative methods
        for method in quant_methods:
            if not method or not method.strip():
                continue
            
            # Normalize current method
            normalized_method = self._normalize_method_name(method)
            if not normalized_method:
                continue
            
            # Collect all other quant methods
            all_other_quant_methods = []
            for paper_data in other_papers_data:
                all_other_quant_methods.extend(paper_data['quant_methods'])
            
            if not all_other_quant_methods:
                continue
            
            # Find similar methods using LLM
            similar_methods = self._find_similar_methods_llm(method, all_other_quant_methods)
            
            # Create relationships for papers with similar methods
            for similar_method in similar_methods:
                for paper_data in other_papers_data:
                    if similar_method in paper_data['quant_methods']:
                        other_paper_id = paper_data['paper_id']
                        # Create bidirectional relationship
                        session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})
                            MATCH (p2:Paper {paper_id: $paper2})
                            MERGE (p1)-[r:SAME_METHOD {
                                method: $normalized_method,
                                method_type: 'quantitative',
                                original_method: $original_method
                            }]->(p2)
                            MERGE (p2)-[r2:SAME_METHOD {
                                method: $normalized_method,
                                method_type: 'quantitative',
                                original_method: $original_method
                            }]->(p1)
                        """, paper1=paper_id, paper2=other_paper_id, 
                             normalized_method=normalized_method, 
                             original_method=method)
        
        # Process qualitative methods
        for method in qual_methods:
            if not method or not method.strip():
                continue
            
            # Normalize current method
            normalized_method = self._normalize_method_name(method)
            if not normalized_method:
                continue
            
            # Collect all other qual methods
            all_other_qual_methods = []
            for paper_data in other_papers_data:
                all_other_qual_methods.extend(paper_data['qual_methods'])
            
            if not all_other_qual_methods:
                continue
            
            # Find similar methods using LLM
            similar_methods = self._find_similar_methods_llm(method, all_other_qual_methods)
            
            # Create relationships for papers with similar methods
            for similar_method in similar_methods:
                for paper_data in other_papers_data:
                    if similar_method in paper_data['qual_methods']:
                        other_paper_id = paper_data['paper_id']
                        # Create bidirectional relationship
                        session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})
                            MATCH (p2:Paper {paper_id: $paper2})
                            MERGE (p1)-[r:SAME_METHOD {
                                method: $normalized_method,
                                method_type: 'qualitative',
                                original_method: $original_method
                            }]->(p2)
                            MERGE (p2)-[r2:SAME_METHOD {
                                method: $normalized_method,
                                method_type: 'qualitative',
                                original_method: $original_method
                            }]->(p1)
                        """, paper1=paper_id, paper2=other_paper_id,
                             normalized_method=normalized_method,
                             original_method=method)

class EnhancedMethodologyProcessor:
    """Main processor for enhanced methodology extraction and ingestion"""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None, 
                 ollama_model: str = "codellama:7b"):
        
        # Use environment variables if not provided
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        if neo4j_user is None:
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        if neo4j_password is None:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize components
        self.extractor = EnhancedOllamaExtractor(model=ollama_model)
        self.pdf_processor = PDFProcessor()
        self.ingester = EnhancedNeo4jIngester(neo4j_uri, neo4j_user, neo4j_password, extractor=self.extractor)
    
    def process_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single paper for enhanced extraction"""
        paper_id = pdf_path.stem
        logger.info(f"Processing enhanced extraction for: {paper_id}")
        
        try:
            # Extract text from PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            if not text:
                raise Exception(f"Failed to extract text from {pdf_path}")
            
            # Extract paper metadata
            logger.info("Extracting paper metadata...")
            paper_metadata = self.extractor.extract_paper_metadata(text, paper_id)
            
            # Extract detailed methodology
            logger.info("Extracting detailed methodology...")
            methodology_data = self.extractor.extract_detailed_methodology(text, paper_id)
            
            # Ingest paper metadata
            self.ingester.ingest_paper_with_metadata(paper_metadata)
            
            # Ingest detailed methodology with relationships
            self.ingester.ingest_detailed_methodology(methodology_data)
            
            logger.info(f"✓ Successfully processed enhanced extraction for {paper_id}")
            return {
                "paper_metadata": paper_metadata,
                "methodology_data": methodology_data
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to process {paper_id}: {e}")
            raise

def main():
    """Test the enhanced extraction system"""
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    processor = EnhancedMethodologyProcessor(ollama_model='codellama:7b')
    
    # Test with a sample paper
    test_paper = Path('./1985-1989/1988_305.pdf')
    if test_paper.exists():
        print(f"🧪 Testing enhanced extraction with: {test_paper.name}")
        
        try:
            result = processor.process_paper(test_paper)
            print(f"✅ Successfully extracted enhanced data")
            print(f"📄 Title: {result['paper_metadata']['title']}")
            print(f"👥 Authors: {result['paper_metadata']['authors']}")
            print(f"📊 Methodology: {result['methodology_data']['methodology']['type']}")
            print(f"🔬 Quant methods: {result['methodology_data']['methodology']['quant_methods']}")
            print(f"💻 Software: {result['methodology_data']['methodology']['software']}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Test paper not found")

if __name__ == "__main__":
    main()
