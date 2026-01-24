#!/usr/bin/env python3
"""
Redesigned Methodology Extraction Framework
Multi-stage, focused, graph-optimized extraction system
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

# Import new modules
from prompt_template import get_prompt_template, ExtractionType
from llm_cache import get_cache
from conflict_resolver import get_resolver, ConflictResolutionStrategy

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedesignedOllamaExtractor:
    """Redesigned LLM extractor with focused, multi-stage extraction"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self.max_retries = 5  # Increased retries for robustness
        self.retry_delay = 5  # Increased initial delay
        self.timeout = 300  # 5 minutes for complex extractions
        
        # Initialize prompt template and cache
        self.prompt_template = get_prompt_template()
        self.cache = get_cache()
        self.prompt_version = "2.0"
        
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
        except Exception as e:
            logger.error(f"✗ Failed to connect to OLLAMA: {e}")
            raise
    
    def _call_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make API call to OLLAMA"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": max_tokens,
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
            raise Exception(f"OLLAMA API error: {response.status_code}")
    
    def extract_with_retry(self, prompt: str, max_tokens: int = 2000, timeout: int = None, 
                          max_retries: int = None, prompt_type: str = "generic", 
                          input_text: str = "") -> str:
        """Extract using OLLAMA with robust retry logic and caching"""
        import time
        
        # Check cache first (if input_text provided)
        if input_text and prompt_type != "generic":
            cached_response = self.cache.get(input_text, prompt_type, self.prompt_version)
            if cached_response:
                # Parse cached response if it's a dict, otherwise return as string
                if isinstance(cached_response, dict):
                    return json.dumps(cached_response)
                return str(cached_response)
        
        last_exception = None
        
        # Use provided timeout or default
        call_timeout = timeout if timeout is not None else self.timeout
        retries = max_retries if max_retries is not None else self.max_retries
        
        response_text = None
        for attempt in range(retries):
            try:
                # Temporarily override timeout for this call
                original_timeout = self.timeout
                self.timeout = call_timeout
                try:
                    response_text = self._call_ollama(prompt, max_tokens)
                    
                    # Cache the response (if input_text provided)
                    if input_text and prompt_type != "generic" and response_text:
                        try:
                            # Try to parse as JSON for caching
                            parsed = self._parse_json_response(response_text)
                            if parsed:
                                self.cache.set(input_text, prompt_type, parsed, self.prompt_version)
                        except:
                            # If not JSON, cache as string
                            self.cache.set(input_text, prompt_type, {"response": response_text}, self.prompt_version)
                    
                    return response_text
                finally:
                    self.timeout = original_timeout
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if it's a timeout
                is_timeout = "timeout" in error_str or "timed out" in error_str or "read timed out" in error_str
                
                if attempt < retries - 1:
                    # Exponential backoff with longer waits for timeouts
                    if is_timeout:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential: 5, 10, 20, 40, 80
                        logger.warning(f"OLLAMA timeout (attempt {attempt + 1}/{retries}), waiting {wait_time}s before retry...")
                    else:
                        wait_time = self.retry_delay * (attempt + 1)  # Linear: 5, 10, 15, 20, 25
                        logger.warning(f"OLLAMA error (attempt {attempt + 1}/{retries}): {str(e)[:100]}, retrying in {wait_time}s...")
                    
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {retries} OLLAMA attempts failed. Last error: {str(e)[:200]}")
                    raise
    
    def identify_methodology_section(self, text: str) -> Dict[str, Any]:
        """
        Stage 1: LLM-based section identification (OPTIMIZED)
        Returns: {section_text, start_pos, end_pos, confidence}
        """
        # Use first 10k chars for section detection (reduced from 30k)
        sample_text = text[:10000]
        
        prompt = f"""Find the METHODOLOGY section in this paper. Be FAST and CONCISE.

Paper text (first 10k chars):
{sample_text}

Look for sections: Methods, Methodology, Research Design, Data and Methods, Empirical Strategy.

Return JSON:
{{
  "section_found": true/false,
  "section_start": "first 50 chars of section",
  "confidence": 0.0-1.0
}}

If not found:
{{
  "section_found": false,
  "section_start": "",
  "confidence": 0.0
}}

Return ONLY valid JSON. Be FAST."""
        
        try:
            response = self.extract_with_retry(prompt, max_tokens=800, timeout=120, max_retries=3)
            result = self._parse_json_response(response)
        except Exception as e:
            logger.warning(f"LLM section detection failed: {str(e)[:100]}, using fallback...")
            # Fallback: simple keyword-based search
            result = self._fallback_section_detection(text)
        
        # If LLM found section, extract it from full text
        if result.get("section_found") and result.get("section_start"):
            section_start_text = result["section_start"]
            # Find this text in full document
            start_idx = text.lower().find(section_start_text.lower()[:30])
            if start_idx > 0:
                # Extract section (up to 10k chars or until next major section)
                section_text = self._extract_section_from_position(text, start_idx)
                result["section_text"] = section_text
                result["section_start_pos"] = start_idx
                result["section_end_pos"] = start_idx + len(section_text)
        
        return result
    
    def _fallback_section_detection(self, text: str) -> Dict[str, Any]:
        """Fallback: simple keyword-based section detection"""
        methodology_keywords = [
            "methodology", "methods", "research design", "data and methods",
            "empirical strategy", "method", "approach", "analytical approach"
        ]
        
        text_lower = text.lower()
        for keyword in methodology_keywords:
            # Look for section headers (usually on their own line or followed by colon)
            pattern = rf'\n\s*{re.escape(keyword)}\s*[:]?\s*\n'
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                start_pos = match.start()
                section_text = self._extract_section_from_position(text, start_pos)
                if len(section_text) > 500:  # Valid section found
                    return {
                        "section_found": True,
                        "section_text": section_text,
                        "section_start": section_text[:50],
                        "section_start_pos": start_pos,
                        "section_end_pos": start_pos + len(section_text),
                        "confidence": 0.6
                    }
        
        # No section found
        return {
            "section_found": False,
            "section_text": "",
            "section_start": "",
            "confidence": 0.0
        }
    
    def _extract_section_from_position(self, text: str, start_pos: int) -> str:
        """Extract methodology section from identified position"""
        section_end_keywords = ["results", "findings", "conclusion", "discussion", "references", "appendix"]
        
        section_text = text[start_pos:start_pos + 10000]  # Max 10k chars
        
        # Find end of section
        lines = section_text.split('\n')
        extracted_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            # Stop if we hit another major section
            if any(keyword in line_lower for keyword in section_end_keywords):
                if len(line.strip()) < 100:  # Likely a header
                    break
            extracted_lines.append(line)
        
        return '\n'.join(extracted_lines).strip()
    
    def extract_primary_methods(self, methodology_text: str, paper_id: str) -> Dict[str, Any]:
        """
        Stage 2: Extract primary methods only (focused, short prompt)
        Returns: {method_type, primary_methods: [3-5 methods max], confidence}
        """
        if len(methodology_text) > 8000:
            methodology_text = methodology_text[:8000]
        
        prompt = f"""Extract PRIMARY methods from this methodology section. Be FAST and CONCISE.

Methodology text:
{methodology_text[:6000]}

Extract ONLY methods EXPLICITLY mentioned. Return JSON:
{{
  "method_type": "quantitative" or "qualitative" or "mixed",
  "primary_methods": ["method1", "method2"],
  "confidence": 0.0-1.0
}}

Return ONLY valid JSON. Be FAST."""
        
        try:
            response = self.extract_with_retry(prompt, max_tokens=600, timeout=120, max_retries=3)
            return self._parse_json_response(response)
        except Exception as e:
            logger.warning(f"Primary methods extraction failed: {str(e)[:100]}, using fallback...")
            return {
                "method_type": "unknown",
                "primary_methods": [],
                "confidence": 0.0
            }
    
    def extract_method_details(self, method_name: str, methodology_text: str, method_type: str) -> Dict[str, Any]:
        """
        Stage 3: Extract detailed information for a specific method
        Returns: {method_name, software, sample_size, data_sources, etc.}
        """
        if len(methodology_text) > 6000:
            methodology_text = methodology_text[:6000]
        
        prompt = f"""Extract details for method: "{method_name}". Be FAST and CONCISE.

Methodology text:
{methodology_text[:4000]}

Extract ONLY explicitly stated info. Return JSON:
{{
  "method_name": "{method_name}",
  "software": ["software if mentioned"],
  "sample_size": "size if mentioned",
  "data_sources": ["source if mentioned"],
  "variables": {{
    "dependent": ["DV if mentioned"],
    "independent": ["IV if mentioned"],
    "control": ["CV if mentioned"]
  }},
  "time_period": "period if mentioned",
  "confidence": 0.0-1.0
}}

Return ONLY valid JSON. Be FAST."""
        
        try:
            response = self.extract_with_retry(prompt, max_tokens=800, timeout=120, max_retries=3)
            return self._parse_json_response(response)
        except Exception as e:
            logger.warning(f"Method details extraction failed for {method_name}: {str(e)[:100]}, using fallback...")
            return {
                "method_name": method_name,
                "software": [],
                "sample_size": None,
                "data_sources": [],
                "variables": {"dependent": [], "independent": [], "control": []},
                "time_period": None,
                "confidence": 0.0
            }
    
    def extract_paper_metadata(self, text: str, paper_id: str) -> Dict[str, Any]:
        """
        Extract comprehensive paper metadata and author information
        OPTIMIZED: Uses only first 5k chars for faster processing
        """
        # OPTIMIZED: Use only first 5k chars (title, authors, abstract are usually in first 3-4k)
        # This is much faster for LLM and reduces timeout risk
        metadata_text = text[:5000]
        
        # OPTIMIZED: Simplified prompt - focus on essential fields only
        prompt = f"""Extract basic metadata from this paper. Be FAST and CONCISE.

Paper text (first 5,000 chars):
{metadata_text}

Extract ONLY:
1. TITLE: Main title (copy exactly)
2. ABSTRACT: Abstract text (if labeled "Abstract" or "Research Summary")
3. AUTHORS: Author names (first 3-5 names, format: "Name1, Name2, Name3")
4. DOI: If present (format: 10.1002/smj.XXXX)
5. KEYWORDS: If present (array of keywords)

Return JSON (MINIMAL - only what you find):
{{
  "paper_metadata": {{
    "title": "title or null",
    "abstract": "abstract or null",
    "doi": "doi or null",
    "keywords": ["kw1", "kw2"] or []
  }},
  "authors": ["Author1", "Author2"] or []
}}

Return ONLY valid JSON. Be FAST."""
        
        # OPTIMIZED: Reduced max_tokens, shorter timeout, fewer retries for faster failure
        response = self.extract_with_retry(prompt, max_tokens=1500, timeout=120, max_retries=3)
        result = self._parse_json_response(response)
        
        # Normalize the result structure - handle cases where LLM returns fields at wrong level
        if "paper_metadata" not in result:
            result["paper_metadata"] = {}
        
        # Move top-level fields into paper_metadata if they exist
        for field in ["title", "abstract", "doi", "journal", "publication_year", "year", "volume", "issue", "pages", "keywords"]:
            if field in result and field not in result["paper_metadata"]:
                result["paper_metadata"][field] = result.pop(field)
        
        # Ensure paper_id and year are set
        result["paper_metadata"]["paper_id"] = paper_id
        
        # Handle year field (could be "year" or "publication_year")
        year = result["paper_metadata"].get("publication_year") or result["paper_metadata"].get("year")
        if not year or year == 0:
            if '_' in paper_id:
                try:
                    year = int(paper_id.split('_')[0])
                except:
                    year = 0
        result["paper_metadata"]["publication_year"] = year
        if "year" in result["paper_metadata"] and result["paper_metadata"]["year"] != year:
            result["paper_metadata"]["year"] = year
        
        # Ensure journal is set
        if not result["paper_metadata"].get("journal"):
            result["paper_metadata"]["journal"] = "Strategic Management Journal"
        
        # Convert simple author list to structured format if needed
        if "authors" not in result:
            result["authors"] = []
        elif result["authors"] and isinstance(result["authors"][0], str):
            # Convert ["Name1", "Name2"] to structured format
            structured_authors = []
            for i, author_name in enumerate(result["authors"][:5], 1):  # Limit to first 5
                name_parts = author_name.strip().split()
                structured_authors.append({
                    "full_name": author_name,
                    "given_name": name_parts[0] if name_parts else "",
                    "family_name": name_parts[-1] if len(name_parts) > 1 else name_parts[0] if name_parts else "",
                    "middle_initial": None,
                    "position": i,
                    "corresponding_author": False,
                    "affiliations": []
                })
            result["authors"] = structured_authors
        
        # Ensure other sections exist
        if "acknowledgments" not in result:
            result["acknowledgments"] = {}
        if "editorial_information" not in result:
            result["editorial_information"] = {}
        if "extraction_metadata" not in result:
            result["extraction_metadata"] = {}
        
        return result
    
    def extract_theories(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract theories and theoretical frameworks from paper
        Uses standardized prompt template with few-shot examples
        """
        # Use first 20k chars (covers introduction + literature review)
        theory_text = text[:20000]
        
        # Build standardized prompt with examples
        rules = [
            "Extract EXACT theory names as they appear - do NOT summarize or rewrite",
            "PRIMARY theories: Only if explicitly stated as MAIN framework AND used in analysis",
            "SUPPORTING theories: Only if EXPLICITLY USED to support arguments (not just mentioned)",
            "DO NOT extract theories only mentioned in literature review without being used",
            "Use canonical names (e.g., 'Resource-Based View' not 'RBV' if both appear)",
            "Be EXTREMELY conservative - fewer accurate theories is better than many generic ones"
        ]
        
        json_schema = {
            "theories": [{
                "theory_name": "exact theory name as written",
                "theory_type": "framework or concept or model or perspective",
                "domain": "strategic_management or organizational_behavior or other",
                "role": "primary or supporting or challenging or extending",
                "section": "introduction or literature_review or discussion",
                "usage_context": "brief description of how theory is used",
                "description": "brief description of theory if provided in paper"
            }]
        }
        
        prompt = self.prompt_template.build_prompt(
            extraction_type=ExtractionType.THEORY,
            input_text=theory_text,
            task_description="Extract theories and theoretical frameworks from this Strategic Management Journal paper. Focus on Introduction and Literature Review sections.",
            json_schema=json_schema,
            rules=rules,
            paper_id=paper_id
        )
        
        # Optimized: faster timeout, fewer tokens, fewer retries
        # Use caching with input text
        response = self.extract_with_retry(
            prompt, 
            max_tokens=1500, 
            timeout=90, 
            max_retries=2,
            prompt_type="theory",
            input_text=theory_text
        )
        
        # Try to parse cached response if it's already a dict
        if isinstance(response, str):
            result = self._parse_json_response(response)
        else:
            result = response if isinstance(response, dict) else {}
        
        # Normalize structure
        theories = result.get("theories", [])
        if not theories and "theory_name" in result:
            # Handle case where LLM returns single theory at top level
            theories = [result]
        
        # Validate and clean theories
        validated_theories = []
        for theory in theories:
            theory_name = theory.get("theory_name", "").strip()
            if theory_name:
                # Ensure required fields
                theory["theory_name"] = theory_name
                theory["role"] = theory.get("role", "supporting")
                theory["section"] = theory.get("section", "literature_review")
                validated_theories.append(theory)
        
        return validated_theories
    
    def extract_phenomena(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract phenomena from paper
        Phenomena are observable events, patterns, behaviors, or trends studied in the research
        Uses standardized prompt template with few-shot examples
        """
        # Use first 25k chars (covers introduction, literature review, and methodology)
        # Phenomena are often described in these sections
        phenomenon_text = text[:25000]
        
        # Build standardized prompt with examples
        rules = [
            "Extract EXACT phenomenon names as they appear - do NOT summarize or rewrite",
            "Phenomena are observable events, patterns, behaviors, or trends that are being studied",
            "Extract ONLY phenomena that are explicitly stated as the focus of the research",
            "DO NOT extract generic concepts or theories - only concrete phenomena",
            "Be conservative - extract only clearly identified phenomena",
            "Include context about how the phenomenon is studied"
        ]
        
        json_schema = {
            "phenomena": [{
                "phenomenon_name": "exact phenomenon name as written",
                "phenomenon_type": "behavior or pattern or event or trend or process",
                "domain": "strategic_management or organizational_behavior or other",
                "description": "brief description of the phenomenon",
                "section": "introduction or literature_review or methodology",
                "context": "how the phenomenon is studied or examined"
            }]
        }
        
        prompt = self.prompt_template.build_prompt(
            extraction_type=ExtractionType.PHENOMENON,
            input_text=phenomenon_text,
            task_description="Extract phenomena (observable events, patterns, behaviors, or trends) that are the focus of this Strategic Management Journal paper. Focus on Introduction, Literature Review, and Methodology sections.",
            json_schema=json_schema,
            rules=rules,
            paper_id=paper_id
        )
        
        # Optimized: faster timeout, fewer tokens, fewer retries
        response = self.extract_with_retry(
            prompt, 
            max_tokens=1500, 
            timeout=90, 
            max_retries=2,
            prompt_type="phenomenon",
            input_text=phenomenon_text
        )
        
        # Try to parse cached response if it's already a dict
        if isinstance(response, str):
            result = self._parse_json_response(response)
        else:
            result = response if isinstance(response, dict) else {}
        
        # Normalize structure
        phenomena = result.get("phenomena", [])
        if not phenomena and "phenomenon_name" in result:
            # Handle case where LLM returns single phenomenon at top level
            phenomena = [result]
        
        # Validate and clean phenomena
        validated_phenomena = []
        for phenomenon in phenomena:
            phenomenon_name = phenomenon.get("phenomenon_name", "").strip()
            if phenomenon_name:
                # Ensure required fields
                phenomenon["phenomenon_name"] = phenomenon_name
                phenomenon["phenomenon_type"] = phenomenon.get("phenomenon_type", "behavior")
                phenomenon["section"] = phenomenon.get("section", "introduction")
                validated_phenomena.append(phenomenon)
        
        return validated_phenomena
    
    def extract_research_questions(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract research questions from paper
        Focuses on Introduction and Abstract sections
        """
        # Use first 15k chars (covers abstract + introduction)
        rq_text = text[:15000]
        
        prompt = f"""Extract research questions from this Strategic Management Journal paper.

RULES: Extract EXACT question text as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (first 15,000 chars - Abstract + Introduction):
{rq_text}

TASK: Extract all research questions explicitly stated in this paper.

Look for:
1. **Question Text**: Exact question as written (e.g., "How do firms achieve competitive advantage?")
2. **Question Type**: 
   - "descriptive": What is/are...?
   - "explanatory": Why/How does...?
   - "predictive": What will...?
   - "prescriptive": How should...?
3. **Section**: Where question appears ("abstract", "introduction", "literature_review")
4. **Domain**: Research domain (e.g., "strategic_management", "organizational_behavior")

Common question patterns:
- "How do...?"
- "What factors influence...?"
- "Why do...?"
- "To what extent...?"
- "Under what conditions...?"
- "What is the relationship between...?"

Return JSON:
{{
  "research_questions": [
    {{
      "question": "exact question text as written",
      "question_type": "descriptive" or "explanatory" or "predictive" or "prescriptive",
      "section": "abstract" or "introduction" or "literature_review",
      "domain": "strategic_management" or other
    }}
  ]
}}

IMPORTANT:
- Extract ONLY explicitly stated questions (look for question marks "?")
- Use exact question text - do not paraphrase
- If question is split across sentences, combine them
- Do NOT make up questions - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=2000)
        result = self._parse_json_response(response)
        
        # Normalize structure
        questions = result.get("research_questions", [])
        if not questions and "question" in result:
            # Handle case where LLM returns single question at top level
            questions = [result]
        
        # Validate and clean questions
        validated_questions = []
        for q in questions:
            question_text = q.get("question", "").strip()
            if question_text and "?" in question_text:
                # Ensure required fields
                q["question"] = question_text
                q["question_type"] = q.get("question_type", "explanatory")
                q["section"] = q.get("section", "introduction")
                validated_questions.append(q)
        
        return validated_questions
    
    def extract_variables(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract variables (dependent, independent, control, moderator, mediator) from paper
        Focuses on Methodology and Results sections
        """
        # Use methodology section + first 10k chars (covers methodology + results)
        # Try to find methodology section first
        methodology_section = ""
        methodology_keywords = ["methodology", "methods", "research design", "data and methods", 
                              "empirical strategy", "analysis", "method", "approach"]
        
        text_lower = text.lower()
        for keyword in methodology_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract 5000 chars from methodology section
                methodology_section = text[idx:idx+5000]
                break
        
        # Combine methodology section with first 10k chars for context
        variable_text = (methodology_section + "\n\n" + text[:10000])[:20000]
        
        prompt = f"""Extract variables from this Strategic Management Journal paper.

RULES: Extract EXACT variable names as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (Methodology + Results sections, first 20,000 chars):
{variable_text}

TASK: Extract all variables mentioned in this paper, including dependent, independent, control, moderator, and mediator variables.

Look for:
1. **Variable Name**: Exact name as written (e.g., "Firm Performance", "CEO Tenure", "ROA")
2. **Variable Type**: 
   - "dependent": Outcome variable (DV, Y variable)
   - "independent": Predictor variable (IV, X variable)
   - "control": Control variable
   - "moderator": Moderating variable
   - "mediator": Mediating variable
3. **Measurement**: How variable is measured (e.g., "ROA", "Tobin's Q", "5-point Likert scale")
4. **Operationalization**: How variable is operationalized (e.g., "measured as return on assets")
5. **Domain**: Variable domain (e.g., "organizational", "financial", "strategic", "behavioral")

Common variable patterns:
- "Our dependent variable is..."
- "We measure X as..."
- "Y is operationalized as..."
- "We control for..."
- "X moderates the relationship..."
- "M mediates the effect of..."

Return JSON:
{{
  "variables": [
    {{
      "variable_name": "exact variable name as written",
      "variable_type": "dependent" or "independent" or "control" or "moderator" or "mediator",
      "measurement": "how variable is measured",
      "operationalization": "how variable is operationalized",
      "domain": "organizational" or "financial" or "strategic" or "behavioral" or other
    }}
  ]
}}

IMPORTANT:
- Extract ONLY variables explicitly mentioned in the text
- Use exact variable names - do not paraphrase
- Identify variable type from context (e.g., "dependent variable" = dependent)
- Do NOT make up variables - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=3000)
        result = self._parse_json_response(response)
        
        # Normalize structure
        variables = result.get("variables", [])
        if not variables and "variable_name" in result:
            # Handle case where LLM returns single variable at top level
            variables = [result]
        
        # Validate and clean variables
        validated_variables = []
        for var in variables:
            var_name = var.get("variable_name", "").strip()
            if var_name:
                # Ensure required fields
                var["variable_name"] = var_name
                var["variable_type"] = var.get("variable_type", "control")
                var["domain"] = var.get("domain", "organizational")
                validated_variables.append(var)
        
        return validated_variables
    
    def extract_findings(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract research findings/results from paper
        Focuses on Results and Discussion sections
        """
        # Try to find Results/Discussion sections
        results_section = ""
        results_keywords = ["results", "findings", "empirical results", "main findings", 
                           "discussion", "implications", "conclusion"]
        
        text_lower = text.lower()
        for keyword in results_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract 10000 chars from results section
                results_section = text[idx:idx+10000]
                break
        
        # Combine with first 15k chars for context
        findings_text = (results_section + "\n\n" + text[:15000])[:25000]
        
        prompt = f"""Extract research findings from this Strategic Management Journal paper.

RULES: Extract EXACT finding text as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (Results + Discussion sections, first 25,000 chars):
{findings_text}

TASK: Extract all research findings and results explicitly stated in this paper.

Look for:
1. **Finding Text**: Summary of finding as written
2. **Finding Type**: 
   - "positive": Positive/supportive finding
   - "negative": Negative/contradictory finding
   - "null": Null/non-significant finding
   - "mixed": Mixed or conditional finding
3. **Significance**: Statistical significance if mentioned (e.g., "p < 0.05", "significant")
4. **Effect Size**: Effect size if mentioned (e.g., "Cohen's d = 0.5", "R² = 0.3")
5. **Section**: Where finding appears ("results", "discussion", "conclusion")

Common finding patterns:
- "We find that..."
- "Our results show..."
- "The analysis reveals..."
- "We observe..."
- "The data indicate..."

Return JSON:
{{
  "findings": [
    {{
      "finding_text": "exact finding text as written",
      "finding_type": "positive" or "negative" or "null" or "mixed",
      "significance": "statistical significance if mentioned" or null,
      "effect_size": "effect size if mentioned" or null,
      "section": "results" or "discussion" or "conclusion"
    }}
  ]
}}

IMPORTANT:
- Extract ONLY findings explicitly stated in the text
- Use exact finding text - do not paraphrase
- Do NOT make up findings - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=3000)
        result = self._parse_json_response(response)
        
        # Normalize structure
        findings = result.get("findings", [])
        if not findings and "finding_text" in result:
            findings = [result]
        
        # Validate and clean findings
        validated_findings = []
        for finding in findings:
            finding_text = finding.get("finding_text", "").strip()
            if finding_text:
                finding["finding_text"] = finding_text
                finding["finding_type"] = finding.get("finding_type", "positive")
                finding["section"] = finding.get("section", "results")
                validated_findings.append(finding)
        
        return validated_findings
    
    def extract_contributions(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract research contributions from paper
        Focuses on Discussion, Conclusion, and Abstract sections
        """
        # Try to find Contribution/Discussion/Conclusion sections
        contribution_section = ""
        contribution_keywords = ["contribution", "contributions", "we contribute", "this paper contributes",
                               "discussion", "conclusion", "implications", "theoretical contribution",
                               "practical contribution", "managerial implications"]
        
        text_lower = text.lower()
        for keyword in contribution_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract 8000 chars from contribution section
                contribution_section = text[idx:idx+8000]
                break
        
        # Combine with abstract and first 10k chars
        contribution_text = (contribution_section + "\n\n" + text[:10000])[:20000]
        
        prompt = f"""Extract research contributions from this Strategic Management Journal paper.

RULES: Extract EXACT contribution text as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (Contribution + Discussion + Abstract sections, first 20,000 chars):
{contribution_text}

TASK: Extract all research contributions explicitly stated in this paper.

Look for:
1. **Contribution Text**: Description of contribution as written
2. **Contribution Type**: 
   - "theoretical": Theoretical contribution
   - "empirical": Empirical contribution
   - "methodological": Methodological contribution
   - "practical": Practical/managerial contribution
3. **Section**: Where contribution appears ("abstract", "discussion", "conclusion")

Common contribution patterns:
- "We contribute to..."
- "This paper contributes..."
- "Our contribution is..."
- "The main contribution..."
- "We extend..."

Return JSON:
{{
  "contributions": [
    {{
      "contribution_text": "exact contribution text as written",
      "contribution_type": "theoretical" or "empirical" or "methodological" or "practical",
      "section": "abstract" or "discussion" or "conclusion"
    }}
  ]
}}

IMPORTANT:
- Extract ONLY contributions explicitly stated in the text
- Use exact contribution text - do not paraphrase
- Do NOT make up contributions - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=2500)
        result = self._parse_json_response(response)
        
        # Normalize structure
        contributions = result.get("contributions", [])
        if not contributions and "contribution_text" in result:
            contributions = [result]
        
        # Validate and clean contributions
        validated_contributions = []
        for contrib in contributions:
            contrib_text = contrib.get("contribution_text", "").strip()
            if contrib_text:
                contrib["contribution_text"] = contrib_text
                contrib["contribution_type"] = contrib.get("contribution_type", "theoretical")
                contrib["section"] = contrib.get("section", "discussion")
                validated_contributions.append(contrib)
        
        return validated_contributions
    
    def extract_software(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract software/tools used in paper
        Focuses on Methodology section
        """
        # Try to find Methodology section
        methodology_section = ""
        methodology_keywords = ["methodology", "methods", "research design", "data and methods", 
                              "empirical strategy", "analysis", "software", "statistical software"]
        
        text_lower = text.lower()
        for keyword in methodology_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract 5000 chars from methodology section
                methodology_section = text[idx:idx+5000]
                break
        
        # Combine with first 10k chars for context
        software_text = (methodology_section + "\n\n" + text[:10000])[:15000]
        
        prompt = f"""Extract software and analysis tools from this Strategic Management Journal paper.

RULES: Extract EXACT software names as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (Methodology section, first 15,000 chars):
{software_text}

TASK: Extract all software, tools, and analysis platforms mentioned in this paper.

Look for:
1. **Software Name**: Exact name as written (e.g., "Stata", "R", "Python", "SPSS", "MATLAB")
2. **Version**: Version number if mentioned (e.g., "Stata 17", "R 4.2")
3. **Usage**: How software is used (e.g., "for data analysis", "for statistical analysis")
4. **Software Type**: 
   - "statistical": Statistical software (Stata, R, SPSS, SAS)
   - "programming": Programming languages (Python, MATLAB, Julia)
   - "qualitative": Qualitative analysis tools (NVivo, Atlas.ti)
   - "other": Other tools

Common software patterns:
- "We use [Software]..."
- "Analysis was conducted using [Software]..."
- "Data were analyzed with [Software]..."
- "[Software] version [X]..."

Return JSON:
{{
  "software": [
    {{
      "software_name": "exact software name as written",
      "version": "version number if mentioned" or null,
      "usage": "how software is used",
      "software_type": "statistical" or "programming" or "qualitative" or "other"
    }}
  ]
}}

IMPORTANT:
- Extract ONLY software explicitly mentioned in the text
- Use exact software names - do not paraphrase
- Do NOT make up software - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=1500)
        result = self._parse_json_response(response)
        
        # Normalize structure
        software_list = result.get("software", [])
        if not software_list and "software_name" in result:
            software_list = [result]
        
        # Validate and clean software
        validated_software = []
        for sw in software_list:
            if not isinstance(sw, dict):
                continue
            sw_name = sw.get("software_name")
            if sw_name and isinstance(sw_name, str):
                sw_name = sw_name.strip()
                if sw_name:
                    sw["software_name"] = sw_name
                    sw["software_type"] = sw.get("software_type", "other")
                    validated_software.append(sw)
        
        return validated_software
    
    def extract_datasets(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract datasets and data sources from paper
        Focuses on Methodology and Data sections
        """
        # Try to find Data/Methodology sections
        data_section = ""
        data_keywords = ["data", "dataset", "data source", "data collection", "sample", 
                        "methodology", "methods", "empirical setting"]
        
        text_lower = text.lower()
        for keyword in data_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract 8000 chars from data section
                data_section = text[idx:idx+8000]
                break
        
        # Combine with first 10k chars for context
        dataset_text = (data_section + "\n\n" + text[:10000])[:18000]
        
        prompt = f"""Extract datasets and data sources from this Strategic Management Journal paper.

RULES: Extract EXACT dataset names as written. Do NOT summarize or rewrite. If not found, use null or [].

Paper text (Data + Methodology sections, first 18,000 chars):
{dataset_text}

TASK: Extract all datasets, data sources, and databases mentioned in this paper.

Look for:
1. **Dataset Name**: Exact name as written (e.g., "Compustat", "CRSP", "SDC Platinum", "World Bank")
2. **Dataset Type**: 
   - "archival": Archival/secondary data
   - "survey": Survey data
   - "experimental": Experimental data
   - "interview": Interview data
   - "public": Publicly available data
   - "proprietary": Proprietary data
3. **Time Period**: Time period covered (e.g., "1990-2020", "2005-2015")
4. **Sample Size**: Sample size if mentioned
5. **Access**: How data was accessed (e.g., "via subscription", "publicly available")

Common dataset patterns:
- "We use data from [Dataset]..."
- "Data were obtained from [Dataset]..."
- "Our sample comes from [Dataset]..."
- "We analyze [Dataset] data..."

Return JSON:
{{
  "datasets": [
    {{
      "dataset_name": "exact dataset name as written",
      "dataset_type": "archival" or "survey" or "experimental" or "interview" or "public" or "proprietary",
      "time_period": "time period covered" or null,
      "sample_size": "sample size if mentioned" or null,
      "access": "how data was accessed" or null
    }}
  ]
}}

IMPORTANT:
- Extract ONLY datasets explicitly mentioned in the text
- Use exact dataset names - do not paraphrase
- Do NOT make up datasets - only extract what is actually stated
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=2000)
        result = self._parse_json_response(response)
        
        # Normalize structure
        datasets = result.get("datasets", [])
        if not datasets and "dataset_name" in result:
            datasets = [result]
        
        # Validate and clean datasets
        validated_datasets = []
        for ds in datasets:
            if not isinstance(ds, dict):
                continue
            ds_name = ds.get("dataset_name")
            if ds_name and isinstance(ds_name, str):
                ds_name = ds_name.strip()
                if ds_name:
                    ds["dataset_name"] = ds_name
                    ds["dataset_type"] = ds.get("dataset_type", "archival")
                    validated_datasets.append(ds)
        
        return validated_datasets
    
    def extract_citations(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
        """
        Extract citations from references section
        Returns list of cited papers with metadata
        """
        # Find references section (usually at end of paper)
        ref_section = self._find_references_section(text)
        if not ref_section:
            logger.warning(f"No references section found for {paper_id}")
            return []
        
        # Use first 15k chars of references section
        ref_text = ref_section[:15000]
        
        prompt = f"""Extract citations and references from this research paper's references section.

References section text (first 15,000 chars):
{ref_text}

TASK: Extract all cited papers with their metadata.

Look for:
1. **Author Names**: First author and co-authors
2. **Title**: Paper title (in quotes or italics)
3. **Year**: Publication year
4. **Journal/Conference**: Publication venue
5. **DOI**: If available
6. **Citation Context**: How it's cited in the paper (if mentioned)

Common citation formats:
- "Author, A. (Year). Title. Journal, Volume(Issue), Pages."
- "Author, A., & Author, B. (Year). Title. Conference Name."
- "Author et al. (Year). Title. Journal."

Return JSON:
{{
  "citations": [
    {{
      "cited_title": "exact title as written",
      "cited_authors": ["Author1", "Author2"],
      "cited_year": year or null,
      "cited_journal": "journal name" or null,
      "cited_doi": "doi" or null,
      "citation_type": "theoretical" or "methodological" or "empirical" or "general",
      "section": "introduction" or "literature_review" or "discussion" or "methodology"
    }}
  ]
}}

IMPORTANT:
- Extract ONLY citations explicitly listed in references
- Use exact titles as written (do not paraphrase)
- If year/journal/DOI not found, use null
- Return ONLY valid JSON."""

        response = self.extract_with_retry(prompt, max_tokens=2000, timeout=90, max_retries=2)
        result = self._parse_json_response(response)
        
        citations = result.get("citations", [])
        if not citations and "cited_title" in result:
            citations = [result]
        
        # Validate citations
        validated_citations = []
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            title = citation.get("cited_title", "").strip()
            if title and len(title) > 5:  # Minimum title length
                citation["cited_title"] = title
                citation["cited_authors"] = citation.get("cited_authors", [])
                citation["cited_year"] = citation.get("cited_year")
                citation["cited_journal"] = citation.get("cited_journal")
                citation["cited_doi"] = citation.get("cited_doi")
                citation["citation_type"] = citation.get("citation_type", "general")
                citation["section"] = citation.get("section", "literature_review")
                validated_citations.append(citation)
        
        return validated_citations
    
    def _find_references_section(self, text: str) -> Optional[str]:
        """Find references section in paper text"""
        # Look for references section markers
        ref_markers = [
            "references",
            "reference list",
            "bibliography",
            "works cited",
            "literature cited"
        ]
        
        text_lower = text.lower()
        for marker in ref_markers:
            idx = text_lower.find(marker)
            if idx != -1:
                # Extract from marker to end (or next major section)
                ref_section = text[idx:]
                # Stop at appendices or acknowledgments
                stop_markers = ["appendix", "acknowledgment", "acknowledgement"]
                for stop in stop_markers:
                    stop_idx = ref_section.lower().find(stop)
                    if stop_idx != -1 and stop_idx < len(ref_section) * 0.9:
                        ref_section = ref_section[:stop_idx]
                return ref_section
        
        return None
    
    def validate_entity_against_source(self, entity: Dict[str, Any], source_text: str, 
                                      entity_type: str) -> Tuple[bool, float, str]:
        """
        Validate extracted entity exists in source text
        Returns: (is_valid, confidence, validation_status)
        """
        if not source_text or not entity:
            return (False, 0.0, "no_source_text")
        
        source_lower = source_text.lower()
        
        # Get entity name based on type
        entity_name = None
        if entity_type == "theory":
            entity_name = entity.get("theory_name", "")
        elif entity_type == "method":
            entity_name = entity.get("method_name", "")
        elif entity_type == "variable":
            entity_name = entity.get("variable_name", "")
        elif entity_type == "research_question":
            entity_name = entity.get("question", "")
        elif entity_type == "citation":
            entity_name = entity.get("cited_title", "")
        
        if not entity_name:
            return (False, 0.0, "no_entity_name")
        
        entity_lower = entity_name.lower()
        
        # Check exact match
        if entity_lower in source_lower:
            return (True, 1.0, "exact_match")
        
        # Check for key words (for multi-word entities)
        # Only check if entity has at least 2 words (avoid matching single generic words)
        entity_words = [w for w in entity_lower.split() if len(w) > 3]
        if len(entity_words) >= 2:  # Require at least 2 significant words
            matches = sum(1 for word in entity_words if word in source_lower)
            match_ratio = matches / len(entity_words) if entity_words else 0
            
            if match_ratio >= 0.7:  # 70% of words match
                return (True, 0.8, "partial_match")
            elif match_ratio >= 0.5:  # 50% of words match
                return (True, 0.6, "weak_match")
        
        # Check for abbreviations or variations
        if entity_type == "theory":
            # Check for common abbreviations (e.g., "RBV" for "Resource-Based View")
            if "rbv" in entity_lower and ("resource" in source_lower and "based" in source_lower):
                return (True, 0.7, "abbreviation_match")
        
        return (False, 0.0, "not_found")
    
    def validate_method_in_text(self, method_name: str, text: str) -> Tuple[bool, float]:
        """
        Stage 4: Validate that method is actually mentioned in text
        Returns: (is_valid, confidence)
        """
        text_lower = text.lower()
        method_lower = method_name.lower()
        
        # Check for exact match or key words
        if method_lower in text_lower:
            return (True, 1.0)
        
        # Check for key words from method name
        method_words = [w for w in method_lower.split() if len(w) > 3]
        matches = sum(1 for word in method_words if word in text_lower)
        
        if matches >= len(method_words) * 0.7:  # 70% of words match
            return (True, 0.8)
        
        return (False, 0.0)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response with robust error handling"""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:].strip()
            elif response.startswith("```"):
                response = response[3:].strip()
            if response.endswith("```"):
                response = response[:-3].strip()
            
            start_idx = response.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found")
            
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
            
            if end_idx == -1:
                raise ValueError("Invalid JSON structure")
            
            json_str = response[start_idx:end_idx + 1]
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return {}


class RedesignedPDFProcessor:
    """PDF text extraction"""
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
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


class RedesignedNeo4jIngester:
    """Graph-optimized Neo4j ingester - Methods as nodes
    
    CRITICAL FIXES IMPLEMENTED:
    - Entity normalization (prevents duplicates)
    - Data validation (ensures quality)
    - Transaction management (ensures atomicity)
    - Batch writes (optimized performance)
    """
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, extractor=None):
        # Store connection parameters for reconnection
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Initialize normalizer and validator
        from entity_normalizer import get_normalizer
        from data_validator import DataValidator
        self.normalizer = get_normalizer()
        self.validator = DataValidator()
        self.extractor = extractor  # Store extractor for validation
        self.conflict_resolver = get_resolver()  # Conflict resolution
        
        # Configure Neo4j driver with connection pooling and retry
        self.driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password),
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
            connection_timeout=30
        )
    
    def close(self):
        self.driver.close()
    
    def ingest_paper_with_methods(self, paper_data: Dict[str, Any], methods_data: List[Dict[str, Any]], 
                                   authors: List[Dict[str, Any]] = None, full_metadata: Dict[str, Any] = None,
                                   theories_data: List[Dict[str, Any]] = None,
                                   research_questions_data: List[Dict[str, Any]] = None,
                                   variables_data: List[Dict[str, Any]] = None,
                                   findings_data: List[Dict[str, Any]] = None,
                                   contributions_data: List[Dict[str, Any]] = None,
                                   software_data: List[Dict[str, Any]] = None,
                                   datasets_data: List[Dict[str, Any]] = None,
                                   phenomena_data: List[Dict[str, Any]] = None,
                                   citations_data: List[Dict[str, Any]] = None,
                                   research_questions_extracted: List[Dict[str, Any]] = None):
        """Ingest paper with methods as separate nodes, including comprehensive metadata and authors"""
        paper_id = paper_data.get("paper_id", "")
        if authors is None:
            authors = []
        if full_metadata is None:
            full_metadata = {}
        if phenomena_data is None:
            phenomena_data = []
        if citations_data is None:
            citations_data = []
        if research_questions_extracted is None:
            research_questions_extracted = []
        # Merge research_questions_data and research_questions_extracted
        if research_questions_data and research_questions_extracted:
            research_questions_data = research_questions_data + research_questions_extracted
        elif research_questions_extracted:
            research_questions_data = research_questions_extracted
        
        # Retry logic for Neo4j operations
        max_neo4j_retries = 3
        neo4j_retry_delay = 5
        
        for neo4j_attempt in range(max_neo4j_retries):
            try:
                # Test connection first
                with self.driver.session() as test_session:
                    test_session.run("RETURN 1").single()
                break  # Connection good, proceed
            except Exception as e:
                if neo4j_attempt < max_neo4j_retries - 1:
                    error_str = str(e).lower()
                    if "routing" in error_str or "connection" in error_str or "defunct" in error_str:
                        logger.warning(f"Neo4j connection issue (attempt {neo4j_attempt + 1}/{max_neo4j_retries}), reconnecting...")
                        import time
                        time.sleep(neo4j_retry_delay)
                        # Recreate driver connection
                        try:
                            self.driver.close()
                        except:
                            pass
                        self.driver = GraphDatabase.driver(
                            self.neo4j_uri,
                            auth=(self.neo4j_user, self.neo4j_password),
                            max_connection_lifetime=30 * 60,
                            max_connection_pool_size=50,
                            connection_acquisition_timeout=60,
                            connection_timeout=30
                        )
                        continue
                raise
        
        # Ensure paper_id is always set (required for validation)
        if not paper_id:
            logger.error("Paper ID is missing, cannot ingest")
            return
        
        # Ensure paper_data has paper_id
        if "paper_id" not in paper_data:
            paper_data["paper_id"] = paper_id
        
        # Validate paper metadata before ingestion (with fallback for missing fields)
        try:
            validated_metadata = self.validator.validate_paper_metadata(paper_data)
            if not validated_metadata:
                logger.warning(f"Paper metadata validation failed for {paper_id}, using minimal metadata")
                # Use minimal valid metadata
                paper_data = {
                    "paper_id": paper_id,
                    "title": paper_data.get("title", f"Paper {paper_id}"),
                    "abstract": paper_data.get("abstract", ""),
                    "publication_year": paper_data.get("publication_year") or paper_data.get("year"),
                    "journal": paper_data.get("journal", "Strategic Management Journal"),
                    "paper_type": paper_data.get("paper_type", "empirical_quantitative")
                }
                validated_metadata = self.validator.validate_paper_metadata(paper_data)
                if not validated_metadata:
                    logger.error(f"Even minimal metadata validation failed for {paper_id}, skipping ingestion")
                    return
        except Exception as e:
            logger.error(f"Metadata validation error for {paper_id}: {str(e)[:200]}, using minimal metadata")
            # Use minimal valid metadata
            paper_data = {
                "paper_id": paper_id,
                "title": paper_data.get("title", f"Paper {paper_id}"),
                "abstract": paper_data.get("abstract", ""),
                "publication_year": paper_data.get("publication_year") or paper_data.get("year"),
                "journal": paper_data.get("journal", "Strategic Management Journal"),
                "paper_type": paper_data.get("paper_type", "empirical_quantitative")
            }
        
        # Use explicit transaction for atomicity
        with self.driver.session() as session:
            tx = session.begin_transaction()
            try:
                # Create/update paper node with comprehensive metadata
                tx.run("""
                    MERGE (p:Paper {paper_id: $paper_id})
                    SET p.title = $title,
                        p.abstract = $abstract,
                        p.year = $year,
                        p.journal = $journal,
                        p.doi = $doi,
                        p.keywords = $keywords,
                        p.volume = $volume,
                        p.issue = $issue,
                        p.pages = $pages,
                        p.paper_type = $paper_type,
                        p.publication_date = $publication_date,
                        p.online_publication_date = $online_publication_date,
                        p.acceptance_date = $acceptance_date,
                        p.open_access = $open_access,
                        p.updated_at = datetime()
                """,
                paper_id=paper_id,
                title=validated_metadata.title or "",
                abstract=validated_metadata.abstract or "",
                year=validated_metadata.publication_year or 0,
                journal=validated_metadata.journal or "",
                doi=validated_metadata.doi,
                keywords=validated_metadata.keywords or [],
                volume=validated_metadata.volume,
                issue=validated_metadata.issue,
                pages=validated_metadata.pages,
                paper_type=validated_metadata.paper_type,
                publication_date=paper_data.get("publication_date"),  # Not in validated model yet
                online_publication_date=paper_data.get("online_publication_date"),
                acceptance_date=paper_data.get("acceptance_date"),
                open_access=paper_data.get("open_access"))
                
                # Create author nodes and relationships (with validation)
                for idx, author in enumerate(authors, start=1):
                    full_name = author.get("full_name", "")
                    if not full_name:
                        continue
                    
                    # Generate author_id if not provided by LLM
                    # IMPORTANT: Must add author_id to dict BEFORE validation
                    author_id = author.get("author_id", "")
                    if not author_id:
                        # Generate from name: "John Smith" -> "smith_john"
                        family_name = author.get("family_name", "").lower().replace(" ", "_")
                        given_name = author.get("given_name", "").lower().replace(" ", "_")
                        if family_name and given_name:
                            author_id = f"{family_name}_{given_name}"
                        else:
                            # Fallback: use full name
                            author_id = full_name.lower().replace(" ", "_").replace(".", "").replace(",", "")[:50]
                    
                    # Add author_id and position to author dict BEFORE validation
                    author_with_id = author.copy()
                    author_with_id["author_id"] = author_id
                    # Set position from list index if missing or invalid
                    if author_with_id.get("position") is None or not isinstance(author_with_id.get("position"), int):
                        author_with_id["position"] = idx
                    
                    # Validate author data
                    validated_author = self.validator.validate_author(author_with_id)
                    if not validated_author:
                        logger.warning(f"Skipping invalid author data: {author}")
                        continue
                    
                    # Create author node
                    tx.run("""
                        MERGE (a:Author {author_id: $author_id})
                        SET a.full_name = $full_name,
                            a.given_name = $given_name,
                            a.family_name = $family_name,
                            a.middle_initial = $middle_initial,
                            a.email = $email,
                            a.orcid = $orcid,
                            a.position = $position,
                            a.corresponding_author = $corresponding_author
                    """,
                    author_id=validated_author.author_id,
                    full_name=validated_author.full_name,
                    given_name=validated_author.given_name or "",
                    family_name=validated_author.family_name or "",
                    middle_initial=validated_author.middle_initial,
                    email=validated_author.email,
                    orcid=validated_author.orcid,
                    position=validated_author.position,
                    corresponding_author=validated_author.corresponding_author)
                    
                    # Create AUTHORED relationship
                    tx.run("""
                        MATCH (a:Author {author_id: $author_id})
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (a)-[r:AUTHORED {position: $position}]->(p)
                    """,
                    author_id=validated_author.author_id,
                    paper_id=paper_id,
                    position=validated_author.position)
                    
                    # Create affiliation nodes and relationships
                    for affiliation in author.get("affiliations", []):
                        # Handle both string and object formats
                        if isinstance(affiliation, str):
                            # Convert string to object format
                            institution_name = affiliation.strip()
                            affiliation_obj = {"institution_name": institution_name}
                        elif isinstance(affiliation, dict):
                            affiliation_obj = affiliation
                            institution_name = affiliation_obj.get("institution_name", "")
                        else:
                            continue
                        
                        if not institution_name:
                            continue
                        
                        institution_id = affiliation_obj.get("institution_id", institution_name.lower().replace(" ", "_").replace(".", "").replace(",", ""))
                        
                        # Create institution node
                        tx.run("""
                            MERGE (i:Institution {institution_id: $institution_id})
                            SET i.institution_name = $institution_name,
                                i.school_college = $school_college,
                                i.department = $department,
                                i.city = $city,
                                i.state_province = $state_province,
                                i.country = $country
                        """,
                        institution_id=institution_id,
                        institution_name=institution_name,
                        school_college=affiliation_obj.get("school_college"),
                        department=affiliation_obj.get("department"),
                        city=affiliation_obj.get("city"),
                        state_province=affiliation_obj.get("state_province"),
                        country=affiliation_obj.get("country", ""))
                        
                        # Create AFFILIATED_WITH relationship
                        position_title = affiliation_obj.get("position_title")
                        affiliation_type = affiliation_obj.get("affiliation_type", "primary")
                        
                        # Only set position_title if it's not null
                        if position_title:
                            tx.run("""
                                MATCH (a:Author {author_id: $author_id})
                                MATCH (i:Institution {institution_id: $institution_id})
                                MERGE (a)-[r:AFFILIATED_WITH {
                                    affiliation_type: $affiliation_type,
                                    position_title: $position_title
                                }]->(i)
                            """,
                            author_id=validated_author.author_id,
                            institution_id=institution_id,
                            affiliation_type=affiliation_type,
                            position_title=position_title)
                        else:
                            tx.run("""
                                MATCH (a:Author {author_id: $author_id})
                                MATCH (i:Institution {institution_id: $institution_id})
                                MERGE (a)-[r:AFFILIATED_WITH {
                                    affiliation_type: $affiliation_type
                                }]->(i)
                            """,
                            author_id=validated_author.author_id,
                            institution_id=institution_id,
                            affiliation_type=affiliation_type)
            
                # OPTIMIZED: Delete all existing relationships in a single batched query
                tx.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[r]->()
                    WHERE type(r) IN ['USES_METHOD', 'USES_THEORY', 'ADDRESSES', 'USES_VARIABLE', 
                                      'REPORTS', 'MAKES', 'USES_SOFTWARE', 'USES_DATASET', 
                                      'STUDIES_PHENOMENON', 'EXPLAINS_PHENOMENON']
                    DELETE r
                """, paper_id=paper_id)
            
                # Create theory nodes and relationships (with normalization, validation, and source validation)
                if theories_data:
                    # Get source text for validation (from full_metadata if available)
                    source_text = full_metadata.get('full_text', '') if full_metadata else ''
                    
                    for theory in theories_data:
                        # Normalize theory data before validation
                        from normalize_before_validation import normalize_theory_data
                        normalized_theory = normalize_theory_data(theory)
                        if not normalized_theory:
                            logger.warning(f"Could not normalize theory data: {theory}")
                            continue
                        
                        # Validate theory data
                        validated_theory = self.validator.validate_theory(normalized_theory)
                        if not validated_theory:
                            # Try to create with minimal data if validation fails
                            logger.warning(f"Theory validation failed, creating with minimal data: {normalized_theory.get('theory_name', 'unknown')}")
                            # Use normalized data directly with defaults
                            theory_name = normalized_theory.get('theory_name', normalized_theory.get('name', 'Unknown Theory'))
                            role = normalized_theory.get('role', 'supporting')
                            # Create theory node anyway
                            normalized_name = self.normalizer.normalize_theory(theory_name)
                            if normalized_name:
                                tx.run("""
                                    MERGE (t:Theory {name: $theory_name})
                                    SET t.domain = COALESCE($domain, 'strategic_management'),
                                        t.theory_type = COALESCE($theory_type, 'framework'),
                                        t.description = COALESCE($description, ''),
                                        t.updated_at = datetime()
                                """,
                                theory_name=normalized_name,
                                domain=normalized_theory.get('domain'),
                                theory_type=normalized_theory.get('theory_type'),
                                description=normalized_theory.get('description', ''))
                                
                                # Create relationship
                                tx.run("""
                                    MATCH (p:Paper {paper_id: $paper_id})
                                    MATCH (t:Theory {name: $theory_name})
                                    MERGE (p)-[r:USES_THEORY]->(t)
                                    SET r.role = $role,
                                        r.section = COALESCE($section, 'literature_review'),
                                        r.updated_at = datetime()
                                """,
                                paper_id=paper_id,
                                theory_name=normalized_name,
                                role=role,
                                section=normalized_theory.get('section'))
                                
                                # Create Author-Theory relationships
                                tx.run("""
                                    MATCH (p:Paper {paper_id: $paper_id})<-[:AUTHORED]-(a:Author)
                                    MATCH (t:Theory {name: $theory_name})
                                    MERGE (a)-[r:USES_THEORY {
                                        paper_id: $paper_id,
                                        role: $role,
                                        section: $section
                                    }]->(t)
                                    ON CREATE SET r.first_used_year = $publication_year,
                                                  r.paper_count = 1
                                    ON MATCH SET r.paper_count = r.paper_count + 1
                                """,
                                paper_id=paper_id,
                                theory_name=normalized_name,
                                role=role,
                                section=normalized_theory.get('section', 'literature_review'),
                                publication_year=paper_data.get("publication_year") or paper_data.get("year"))
                            continue
                        
                        # Validate against source text (if extractor available)
                        if source_text and self.extractor:
                            is_valid, confidence, status = self.extractor.validate_entity_against_source(
                                theory, source_text, "theory"
                            )
                            if not is_valid:
                                logger.warning(f"Theory '{theory.get('theory_name')}' not found in source text (status: {status})")
                                # Still create but with lower confidence
                                theory['validation_status'] = status
                                theory['confidence'] = confidence
                            else:
                                theory['validation_status'] = status
                                theory['confidence'] = confidence
                        else:
                            theory['validation_status'] = 'not_validated'
                            theory['confidence'] = 1.0
                        
                        # Normalize theory name
                        original_name = validated_theory.theory_name
                        normalized_name = self.normalizer.normalize_theory(original_name)
                        
                        if not normalized_name:
                            continue
                        
                        # Check for existing theory and resolve conflicts
                        existing_theory_result = tx.run("""
                            MATCH (t:Theory {name: $theory_name})
                            RETURN t.name as name, t.domain as domain, 
                                   t.theory_type as theory_type, t.description as description,
                                   t.original_name as original_name
                            LIMIT 1
                        """, theory_name=normalized_name)
                        
                        existing_theory_record = existing_theory_result.single()
                        
                        if existing_theory_record:
                            # Conflict resolution: check if we should update
                            existing_theory = {
                                "theory_name": existing_theory_record["name"],
                                "domain": existing_theory_record.get("domain"),
                                "theory_type": existing_theory_record.get("theory_type"),
                                "description": existing_theory_record.get("description"),
                                "original_name": existing_theory_record.get("original_name")
                            }
                            
                            new_theory = {
                                "theory_name": normalized_name,
                                "domain": validated_theory.domain or "strategic_management",
                                "theory_type": validated_theory.theory_type or "framework",
                                "description": validated_theory.description,
                                "original_name": original_name,
                                "confidence": theory.get('confidence', 1.0),
                                "extracted_at": datetime.now().isoformat()
                            }
                            
                            # Resolve conflict
                            resolved_theory, resolution_reason = self.conflict_resolver.resolve_conflict(
                                existing_theory, new_theory, "theory",
                                ConflictResolutionStrategy.HIGHEST_CONFIDENCE
                            )
                            
                            if resolution_reason.startswith("new_entity"):
                                # Update with new entity
                                tx.run("""
                                    MATCH (t:Theory {name: $theory_name})
                                    SET t.domain = $domain,
                                        t.theory_type = $theory_type,
                                        t.description = $description,
                                        t.original_name = $original_name,
                                        t.updated_at = datetime()
                                """,
                                theory_name=normalized_name,
                                domain=resolved_theory.get("domain"),
                                theory_type=resolved_theory.get("theory_type"),
                                description=resolved_theory.get("description"),
                                original_name=resolved_theory.get("original_name"))
                                logger.debug(f"Updated theory {normalized_name}: {resolution_reason}")
                            elif resolution_reason == "merged":
                                # Update with merged entity
                                tx.run("""
                                    MATCH (t:Theory {name: $theory_name})
                                    SET t.domain = COALESCE($domain, t.domain),
                                        t.theory_type = COALESCE($theory_type, t.theory_type),
                                        t.description = COALESCE($description, t.description),
                                        t.updated_at = datetime()
                                """,
                                theory_name=normalized_name,
                                domain=resolved_theory.get("domain"),
                                theory_type=resolved_theory.get("theory_type"),
                                description=resolved_theory.get("description"))
                                logger.debug(f"Merged theory {normalized_name}: {resolution_reason}")
                            # else: keep existing (no update needed)
                        else:
                            # New theory - create node
                            tx.run("""
                                MERGE (t:Theory {name: $theory_name})
                                SET t.domain = $domain,
                                    t.theory_type = $theory_type,
                                    t.description = $description,
                                    t.original_name = $original_name,
                                    t.created_at = datetime()
                            """,
                            theory_name=normalized_name,
                            domain=validated_theory.domain or "strategic_management",
                            theory_type=validated_theory.theory_type or "framework",
                            description=validated_theory.description,
                            original_name=original_name)
                        
                        # Create or update USES_THEORY relationship (using normalized name, with confidence)
                        confidence_score = theory.get('confidence', 1.0)
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            MATCH (t:Theory {name: $theory_name})
                            MERGE (p)-[r:USES_THEORY]->(t)
                            SET r.role = $role,
                                r.section = $section,
                                r.usage_context = $usage_context,
                                r.confidence = $confidence,
                                r.validation_status = $validation_status,
                                r.updated_at = datetime()
                        """,
                        paper_id=paper_id,
                        theory_name=normalized_name,
                        role=validated_theory.role,
                        section=validated_theory.section or "literature_review",
                        usage_context=validated_theory.usage_context,
                        confidence=confidence_score,
                        validation_status=theory.get('validation_status', 'not_validated'))
                        
                        # Create Author-Theory relationships
                        # Link all authors of this paper to the theory they use
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})<-[:AUTHORED]-(a:Author)
                            MATCH (t:Theory {name: $theory_name})
                            MERGE (a)-[r:USES_THEORY {
                                paper_id: $paper_id,
                                role: $role,
                                section: $section
                            }]->(t)
                            ON CREATE SET r.first_used_year = $publication_year,
                                          r.paper_count = 1
                            ON MATCH SET r.paper_count = r.paper_count + 1
                        """,
                        paper_id=paper_id,
                        theory_name=normalized_name,
                        role=validated_theory.role,
                        section=validated_theory.section or "literature_review",
                        publication_year=paper_data.get("publication_year") or paper_data.get("year"))
            
                # OPTIMIZED: Batch create research question nodes and relationships
                if research_questions_data:
                    validated_rqs = []
                    for rq in research_questions_data:
                        validated_rq = self.validator.validate_research_question(rq)
                        if not validated_rq:
                            logger.warning(f"Skipping invalid research question data: {rq}")
                            continue
                        
                        question_text = validated_rq.question
                        question_id = f"{paper_id}_rq_{hash(question_text) % 10000}"
                        validated_rqs.append({
                            "question_id": question_id,
                            "question": question_text,
                            "question_type": validated_rq.question_type or "explanatory",
                            "domain": validated_rq.domain or "strategic_management",
                            "section": validated_rq.section or "introduction"
                        })
                    
                    # Batch create in single query
                    if validated_rqs:
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            UNWIND $research_questions AS rq
                            MERGE (rq_node:ResearchQuestion {question_id: rq.question_id})
                            SET rq_node.question = rq.question,
                                rq_node.question_type = rq.question_type,
                                rq_node.domain = rq.domain,
                                rq_node.section = rq.section
                            MERGE (p)-[:ADDRESSES]->(rq_node)
                        """, paper_id=paper_id, research_questions=validated_rqs)
            
                # OPTIMIZED: Batch create variable nodes and relationships
                if variables_data:
                    validated_vars = []
                    for var in variables_data:
                        # Normalize before validation
                        try:
                            from normalize_before_validation import normalize_variable_data
                            normalized_var = normalize_variable_data(var)
                            if not normalized_var:
                                logger.warning(f"Skipping invalid variable data: {var}")
                                continue
                            var = normalized_var
                        except Exception as e:
                            logger.warning(f"Error normalizing variable: {e}")
                        
                        validated_var = self.validator.validate_variable(var)
                        if not validated_var:
                            logger.warning(f"Skipping invalid variable data: {var}")
                            continue
                        
                        var_name = validated_var.variable_name
                        var_id = f"{paper_id}_var_{hash(var_name) % 10000}"
                        validated_vars.append({
                            "var_id": var_id,
                            "var_name": var_name,
                            "variable_type": validated_var.variable_type,
                            "measurement": validated_var.measurement or "",
                            "operationalization": validated_var.operationalization or "",
                            "domain": validated_var.domain or "organizational"
                        })
                    
                    # Batch create in single query
                    if validated_vars:
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            UNWIND $variables AS var
                            MERGE (v:Variable {variable_id: var.var_id})
                            SET v.variable_name = var.var_name,
                                v.variable_type = var.variable_type,
                                v.measurement = var.measurement,
                                v.operationalization = var.operationalization,
                                v.domain = var.domain
                            MERGE (p)-[r:USES_VARIABLE {variable_type: var.variable_type}]->(v)
                        """, paper_id=paper_id, variables=validated_vars)
            
                # OPTIMIZED: Batch create finding nodes and relationships
                if findings_data:
                    validated_findings = []
                    for finding in findings_data:
                        # Normalize before validation
                        try:
                            from normalize_before_validation import normalize_finding_data
                            normalized_finding = normalize_finding_data(finding)
                            if not normalized_finding:
                                logger.warning(f"Skipping invalid finding data: {finding}")
                                continue
                            finding = normalized_finding
                        except Exception as e:
                            logger.warning(f"Error normalizing finding: {e}")
                        
                        validated_finding = self.validator.validate_finding(finding)
                        if not validated_finding:
                            logger.warning(f"Skipping invalid finding data: {finding}")
                            continue
                        
                        finding_text = validated_finding.finding_text
                        finding_id = f"{paper_id}_finding_{hash(finding_text) % 10000}"
                        validated_findings.append({
                            "finding_id": finding_id,
                            "finding_text": finding_text,
                            "finding_type": validated_finding.finding_type or "positive",
                            "significance": validated_finding.significance or "",
                            "effect_size": validated_finding.effect_size or "",
                            "section": validated_finding.section or "results"
                        })
                    
                    # Batch create in single query
                    if validated_findings:
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            UNWIND $findings AS finding
                            MERGE (f:Finding {finding_id: finding.finding_id})
                            SET f.finding_text = finding.finding_text,
                                f.finding_type = finding.finding_type,
                                f.significance = finding.significance,
                                f.effect_size = finding.effect_size,
                                f.section = finding.section
                            MERGE (p)-[:REPORTS]->(f)
                        """, paper_id=paper_id, findings=validated_findings)
            
                # OPTIMIZED: Batch create contribution nodes and relationships
                if contributions_data:
                    validated_contribs = []
                    for contrib in contributions_data:
                        # Normalize before validation
                        try:
                            from normalize_before_validation import normalize_contribution_data
                            normalized_contrib = normalize_contribution_data(contrib)
                            if not normalized_contrib:
                                logger.warning(f"Skipping invalid contribution data: {contrib}")
                                continue
                            contrib = normalized_contrib
                        except Exception as e:
                            logger.warning(f"Error normalizing contribution: {e}")
                        
                        validated_contrib = self.validator.validate_contribution(contrib)
                        if not validated_contrib:
                            logger.warning(f"Skipping invalid contribution data: {contrib}")
                            continue
                        
                        contrib_text = validated_contrib.contribution_text
                        contrib_id = f"{paper_id}_contrib_{hash(contrib_text) % 10000}"
                        validated_contribs.append({
                            "contrib_id": contrib_id,
                            "contrib_text": contrib_text,
                            "contribution_type": validated_contrib.contribution_type or "theoretical",
                            "section": validated_contrib.section or "discussion"
                        })
                    
                    # Batch create in single query
                    if validated_contribs:
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            UNWIND $contributions AS contrib
                            MERGE (c:Contribution {contribution_id: contrib.contrib_id})
                            SET c.contribution_text = contrib.contrib_text,
                                c.contribution_type = contrib.contribution_type,
                                c.section = contrib.section
                            MERGE (p)-[:MAKES]->(c)
                        """, paper_id=paper_id, contributions=validated_contribs)
            
                # Create software nodes and relationships (with normalization and validation)
                if software_data:
                    for sw in software_data:
                        # Validate software data
                        validated_software = self.validator.validate_software(sw)
                        if not validated_software:
                            logger.warning(f"Skipping invalid software data: {sw}")
                            continue
                        
                        # Normalize software name
                        original_name = validated_software.software_name
                        normalized_name = self.normalizer.normalize_software(original_name)
                        
                        if not normalized_name:
                            continue
                        
                        # Create software node with normalized name
                        tx.run("""
                            MERGE (s:Software {software_name: $software_name})
                            SET s.version = $version,
                                s.software_type = $software_type,
                                s.usage = $usage,
                                s.original_name = $original_name
                        """,
                        software_name=normalized_name,
                        version=validated_software.version,
                        software_type=validated_software.software_type or "other",
                        usage=validated_software.usage,
                        original_name=original_name)
                        
                        # Create USES_SOFTWARE relationship
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            MATCH (s:Software {software_name: $software_name})
                            MERGE (p)-[r:USES_SOFTWARE]->(s)
                        """,
                        paper_id=paper_id,
                        software_name=normalized_name)
            
                # Create dataset nodes and relationships (with validation)
                if datasets_data:
                    for ds in datasets_data:
                        # Validate dataset data
                        validated_dataset = self.validator.validate_dataset(ds)
                        if not validated_dataset:
                            logger.warning(f"Skipping invalid dataset data: {ds}")
                            continue
                        
                        ds_name = validated_dataset.dataset_name
                        
                        # Create dataset node
                        tx.run("""
                            MERGE (d:Dataset {dataset_name: $dataset_name})
                            SET d.dataset_type = $dataset_type,
                                d.time_period = $time_period,
                                d.sample_size = $sample_size,
                                d.access = $access
                        """,
                        dataset_name=ds_name,
                        dataset_type=validated_dataset.dataset_type or "archival",
                        time_period=validated_dataset.time_period,
                        sample_size=validated_dataset.sample_size,
                        access=validated_dataset.access)
                        
                        # Create USES_DATASET relationship
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            MATCH (d:Dataset {dataset_name: $dataset_name})
                            MERGE (p)-[r:USES_DATASET]->(d)
                        """,
                        paper_id=paper_id,
                        dataset_name=ds_name)
                
                # Delete existing phenomenon relationships
                tx.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[r:STUDIES_PHENOMENON]->()
                    DELETE r
                """, paper_id=paper_id)
            
                # Create phenomenon nodes and relationships (with validation)
                if phenomena_data:
                    for phenomenon in phenomena_data:
                        # Validate phenomenon data
                        validated_phenomenon = self.validator.validate_phenomenon(phenomenon)
                        if not validated_phenomenon:
                            logger.warning(f"Skipping invalid phenomenon data: {phenomenon}")
                            continue
                        
                        phenomenon_name = validated_phenomenon.phenomenon_name
                        # Normalize phenomenon name using EntityNormalizer
                        normalized_phenomenon_name = self.normalizer.normalize_phenomenon(phenomenon_name)
                        if not normalized_phenomenon_name:
                            logger.warning(f"Skipping phenomenon with empty normalized name: {phenomenon_name}")
                            continue
                        
                        # Create phenomenon node
                        tx.run("""
                            MERGE (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                            SET ph.phenomenon_type = $phenomenon_type,
                                ph.domain = $domain,
                                ph.description = $description,
                                ph.context = $context
                        """,
                        phenomenon_name=normalized_phenomenon_name,
                        phenomenon_type=validated_phenomenon.phenomenon_type or "behavior",
                        domain=validated_phenomenon.domain or "strategic_management",
                        description=validated_phenomenon.description,
                        context=validated_phenomenon.context)
                        
                        # Create STUDIES_PHENOMENON relationship
                        # Note: Neo4j doesn't allow null values in relationship properties, so use empty string
                        context_value = validated_phenomenon.context or ""
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})
                            MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                            MERGE (p)-[r:STUDIES_PHENOMENON {
                                section: $section,
                                context: $context
                            }]->(ph)
                        """,
                        paper_id=paper_id,
                        phenomenon_name=normalized_phenomenon_name,
                        section=validated_phenomenon.section or "introduction",
                        context=context_value)
                        
                        # Create Author-Phenomenon relationships
                        # Link all authors of this paper to the phenomenon they study
                        # Note: Neo4j doesn't allow null values in relationship properties, so use empty string
                        context_value = validated_phenomenon.context or ""
                        tx.run("""
                            MATCH (p:Paper {paper_id: $paper_id})<-[:AUTHORED]-(a:Author)
                            MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                            MERGE (a)-[r:STUDIES_PHENOMENON {
                                paper_id: $paper_id,
                                section: $section,
                                context: $context
                            }]->(ph)
                            ON CREATE SET r.first_studied_year = $publication_year,
                                          r.paper_count = 1
                            ON MATCH SET r.paper_count = r.paper_count + 1
                        """,
                        paper_id=paper_id,
                        phenomenon_name=normalized_phenomenon_name,
                        section=validated_phenomenon.section or "introduction",
                        context=context_value,
                        publication_year=paper_data.get("publication_year") or paper_data.get("year"))
                        
                        # Create Theory-Phenomenon relationships
                        # If theories exist, check if any theory is used to explain this phenomenon
                        if theories_data:
                            # Import connection strength calculator
                            try:
                                from connection_strength_calculator import get_strength_calculator
                                # Enable embeddings if available (Phase 2 Fix #2)
                                try:
                                    from sentence_transformers import SentenceTransformer
                                    use_embeddings = True
                                    logger.debug("Embeddings available, enabling semantic similarity")
                                except ImportError:
                                    use_embeddings = False
                                    logger.debug("Embeddings not available, using keyword-based similarity")
                                
                                strength_calculator = get_strength_calculator(use_embeddings=use_embeddings)
                            except ImportError:
                                logger.warning("Connection strength calculator not available, using simple logic")
                                strength_calculator = None
                            
                            for theory in theories_data:
                                theory_name = theory.get("theory_name", "").strip()
                                if not theory_name:
                                    continue
                                
                                # Normalize theory name
                                normalized_theory_name = self.normalizer.normalize_theory(theory_name)
                                if not normalized_theory_name:
                                    continue
                                
                                # Calculate connection strength using mathematical model
                                if strength_calculator:
                                    connection_strength, factor_scores = strength_calculator.calculate_strength(
                                        theory=theory,
                                        phenomenon={
                                            "phenomenon_name": normalized_phenomenon_name,
                                            "section": validated_phenomenon.section,
                                            "context": validated_phenomenon.context,
                                            "description": validated_phenomenon.description
                                        },
                                        paper_data=paper_data
                                    )
                                    
                                    # Only create connection if strength meets threshold
                                    if strength_calculator.should_create_connection(connection_strength, threshold=0.3):
                                        # Create or update EXPLAINS_PHENOMENON relationship
                                        # Use MERGE on relationship pattern (paper_id is unique identifier)
                                        # Then SET all properties to ensure they're updated
                                        tx.run("""
                                            MATCH (t:Theory {name: $theory_name})
                                            MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                                            MERGE (t)-[r:EXPLAINS_PHENOMENON {
                                                paper_id: $paper_id
                                            }]->(ph)
                                            SET r.theory_role = $theory_role,
                                                r.section = $section,
                                                r.connection_strength = $connection_strength,
                                                r.role_weight = $role_weight,
                                                r.section_score = $section_score,
                                                r.keyword_score = $keyword_score,
                                                r.semantic_score = $semantic_score,
                                                r.explicit_bonus = $explicit_bonus
                                        """,
                                        theory_name=normalized_theory_name,
                                        phenomenon_name=normalized_phenomenon_name,
                                        paper_id=paper_id,
                                        theory_role=theory.get("role", "supporting"),
                                        section=theory.get("section", "literature_review"),
                                        connection_strength=round(connection_strength, 3),
                                        role_weight=round(factor_scores.get("role_weight", 0), 3),
                                        section_score=round(factor_scores.get("section_score", 0), 3),
                                        keyword_score=round(factor_scores.get("keyword_score", 0), 3),
                                        semantic_score=round(factor_scores.get("semantic_score", 0), 3),
                                        explicit_bonus=round(factor_scores.get("explicit_bonus", 0), 3))
                                        logger.debug(f"Connected theory {normalized_theory_name} to phenomenon {normalized_phenomenon_name} "
                                                    f"(strength: {connection_strength:.3f}, factors: {factor_scores})")
                                else:
                                    # Fallback to simple logic if calculator not available
                                    phenomenon_context = (validated_phenomenon.context or "").lower()
                                    theory_usage = (theory.get("usage_context", "") or "").lower()
                                    
                                    should_connect = False
                                    connection_strength = 0.5
                                    
                                    # Check if theory is primary and phenomenon is mentioned in same section
                                    if theory.get("role") == "primary" and validated_phenomenon.section == theory.get("section"):
                                        should_connect = True
                                        connection_strength = 0.7
                                    
                                    # Check if theory usage context mentions phenomenon keywords
                                    if not should_connect and phenomenon_context and theory_usage:
                                        phenomenon_words = set(phenomenon_context.split())
                                        theory_words = set(theory_usage.split())
                                        if len(phenomenon_words.intersection(theory_words)) >= 2:
                                            should_connect = True
                                            connection_strength = 0.5
                                    
                                    if should_connect:
                                        # Create or update EXPLAINS_PHENOMENON relationship (fallback path)
                                        tx.run("""
                                            MATCH (t:Theory {name: $theory_name})
                                            MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
                                            MERGE (t)-[r:EXPLAINS_PHENOMENON {
                                                paper_id: $paper_id
                                            }]->(ph)
                                            SET r.theory_role = $theory_role,
                                                r.section = $section,
                                                r.connection_strength = $connection_strength
                                        """,
                                        theory_name=normalized_theory_name,
                                        phenomenon_name=normalized_phenomenon_name,
                                        paper_id=paper_id,
                                        theory_role=theory.get("role", "supporting"),
                                        section=theory.get("section", "literature_review"),
                                        connection_strength=connection_strength)
                                        logger.debug(f"Connected theory {normalized_theory_name} to phenomenon {normalized_phenomenon_name} "
                                                    f"(simple logic, strength: {connection_strength})")
            
                # Create citation relationships (CITES)
                if citations_data:
                    # Delete existing citation relationships
                    tx.run("""
                        MATCH (p:Paper {paper_id: $paper_id})-[r:CITES]->()
                        DELETE r
                    """, paper_id=paper_id)
                    
                    for citation in citations_data:
                        cited_title = citation.get("cited_title", "").strip()
                        if not cited_title:
                            continue
                        
                        # Try to find cited paper by title similarity
                        # First try exact match
                        cited_paper_result = tx.run("""
                            MATCH (cited:Paper)
                            WHERE toLower(cited.title) = toLower($title)
                            RETURN cited.paper_id as paper_id
                            LIMIT 1
                        """, title=cited_title)
                        
                        cited_paper_record = cited_paper_result.single()
                        
                        if cited_paper_record:
                            # Found exact match - create CITES relationship
                            cited_paper_id = cited_paper_record['paper_id']
                            tx.run("""
                                MATCH (citing:Paper {paper_id: $citing_paper_id})
                                MATCH (cited:Paper {paper_id: $cited_paper_id})
                                MERGE (citing)-[r:CITES {
                                    citation_type: $citation_type,
                                    section: $section,
                                    confidence: $confidence
                                }]->(cited)
                            """,
                            citing_paper_id=paper_id,
                            cited_paper_id=cited_paper_id,
                            citation_type=citation.get("citation_type", "general"),
                            section=citation.get("section", "literature_review"),
                            confidence=0.9)  # High confidence for exact match
                        else:
                            # No exact match - try fuzzy match by title similarity
                            # This is a simplified version - could be enhanced with embeddings
                            cited_paper_result = tx.run("""
                                MATCH (cited:Paper)
                                WHERE toLower(cited.title) CONTAINS toLower($title_keyword)
                                   OR toLower($title_keyword) CONTAINS toLower(cited.title)
                                RETURN cited.paper_id as paper_id, cited.title as title
                                LIMIT 5
                            """, title_keyword=cited_title[:50])  # Use first 50 chars for matching
                            
                            for record in cited_paper_result:
                                # Simple similarity check
                                existing_title = record['title'].lower()
                                if cited_title.lower()[:30] in existing_title or existing_title[:30] in cited_title.lower():
                                    cited_paper_id = record['paper_id']
                                    tx.run("""
                                        MATCH (citing:Paper {paper_id: $citing_paper_id})
                                        MATCH (cited:Paper {paper_id: $cited_paper_id})
                                        MERGE (citing)-[r:CITES {
                                            citation_type: $citation_type,
                                            section: $section,
                                            confidence: $confidence
                                        }]->(cited)
                                    """,
                                    citing_paper_id=paper_id,
                                    cited_paper_id=cited_paper_id,
                                    citation_type=citation.get("citation_type", "general"),
                                    section=citation.get("section", "literature_review"),
                                    confidence=0.7)  # Lower confidence for fuzzy match
                                    break
            
                # Delete existing method relationships
                tx.run("""
                    MATCH (p:Paper {paper_id: $paper_id})-[r:USES_METHOD]->()
                    DELETE r
                """, paper_id=paper_id)
                
                # Create method nodes and relationships (with normalization and validation)
                logger.info(f"Processing {len(methods_data) if methods_data else 0} methods for paper {paper_id}")
                for method_data in methods_data:
                    # Normalize method data before validation
                    from normalize_before_validation import normalize_method_data
                    normalized_method = normalize_method_data(method_data)
                    if not normalized_method:
                        logger.warning(f"Could not normalize method data: {method_data}")
                        continue
                    
                    # Validate method data
                    validated_method = self.validator.validate_method(normalized_method)
                    if not validated_method:
                        # Try to create with minimal data if validation fails
                        logger.warning(f"Method validation failed, creating with minimal data: {normalized_method.get('method_name', 'unknown')}")
                        method_name = normalized_method.get('method_name', normalized_method.get('name', 'Unknown Method'))
                        method_type = normalized_method.get('method_type', 'quantitative')
                        normalized_name = self.normalizer.normalize_method(method_name)
                        if normalized_name:
                            tx.run("""
                                MERGE (m:Method {name: $method_name, type: $method_type})
                                SET m.confidence = COALESCE($confidence, 0.7),
                                    m.software = COALESCE($software, []),
                                    m.sample_size = $sample_size,
                                    m.data_sources = COALESCE($data_sources, []),
                                    m.time_period = $time_period,
                                    m.updated_at = datetime()
                                WITH m
                                MATCH (p:Paper {paper_id: $paper_id})
                                MERGE (p)-[r:USES_METHOD]->(m)
                                SET r.confidence = COALESCE($confidence, 0.7)
                            """,
                            method_name=normalized_name,
                            method_type=method_type,
                            confidence=normalized_method.get('confidence', 0.7),
                            software=normalized_method.get('software', []),
                            sample_size=normalized_method.get('sample_size'),
                            data_sources=normalized_method.get('data_sources', []),
                            time_period=normalized_method.get('time_period'),
                            paper_id=paper_id)
                        continue
                    
                    # Normalize method name
                    original_name = validated_method.method_name
                    normalized_name = self.normalizer.normalize_method(original_name)
                    
                    if not normalized_name:
                        continue
                    
                    # Ensure confidence is in valid range
                    confidence = max(0.5, validated_method.confidence)  # Minimum 0.5 for validated methods
                    
                    # Create method node with normalized name
                    tx.run("""
                        MERGE (m:Method {name: $method_name, type: $method_type})
                        SET m.confidence = $confidence,
                            m.software = $software,
                            m.sample_size = $sample_size,
                            m.data_sources = $data_sources,
                            m.time_period = $time_period,
                            m.original_name = $original_name,
                            m.updated_at = datetime()
                        WITH m
                        MATCH (p:Paper {paper_id: $paper_id})
                        MERGE (p)-[r:USES_METHOD {confidence: $confidence}]->(m)
                    """,
                    method_name=normalized_name,
                    method_type=validated_method.method_type,
                    confidence=confidence,
                    software=validated_method.software or [],
                    sample_size=validated_method.sample_size,
                    data_sources=validated_method.data_sources or [],
                    time_period=validated_method.time_period,
                    original_name=original_name,
                    paper_id=paper_id)
                    
                    # Create software nodes (normalized)
                    for software in validated_method.software or []:
                        normalized_sw = self.normalizer.normalize_software(software)
                        if normalized_sw:
                            tx.run("""
                                MERGE (s:Software {software_name: $software_name})
                                WITH s
                                MATCH (p:Paper {paper_id: $paper_id})
                                MERGE (p)-[:USES_SOFTWARE]->(s)
                            """,
                            software_name=normalized_sw,
                            paper_id=paper_id)
                
                # Commit transaction if all operations succeed
                tx.commit()
                logger.info(f"✓ Successfully ingested paper {paper_id} with all entities")
                
            except Exception as e:
                # Rollback transaction on any error
                tx.rollback()
                logger.error(f"✗ Transaction failed for paper {paper_id}: {e}")
                raise
    
    def _create_method_similarity_relationships(self, session, paper_id: str, methods_data: List[Dict[str, Any]]):
        """Create similarity relationships between methods using LLM"""
        # This would use LLM to find similar methods across papers
        # Implementation similar to previous but optimized for method nodes
        pass


class RedesignedMethodologyProcessor:
    """Main processor using redesigned multi-stage extraction"""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None,
                 ollama_model: str = "llama3.1:8b"):
        
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        if neo4j_user is None:
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        if neo4j_password is None:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.extractor = RedesignedOllamaExtractor(model=ollama_model)
        self.pdf_processor = RedesignedPDFProcessor()
        self.ingester = RedesignedNeo4jIngester(neo4j_uri, neo4j_user, neo4j_password)
    
    def _extract_fallback_metadata(self, text: str, paper_id: str, pdf_path: Path) -> Dict[str, Any]:
        """Extract basic metadata from filename and first page when LLM extraction fails"""
        import re
        
        # Extract year from filename (e.g., "2020_1103.pdf" -> 2020)
        year_match = re.match(r'(\d{4})_', paper_id)
        year = int(year_match.group(1)) if year_match else None
        
        # Extract title from first few lines (usually first 200 chars)
        first_lines = text[:500].strip().split('\n')
        title = ""
        for line in first_lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 20 and len(line) < 200:  # Reasonable title length
                # Skip common headers
                if not any(skip in line.lower() for skip in ['abstract', 'keywords', 'introduction', 'doi:', 'vol.', 'pp.']):
                    title = line
                    break
        
        # Extract abstract (look for "Abstract" or "Research Summary")
        abstract = ""
        abstract_patterns = [
            r'(?i)abstract[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:)',
            r'(?i)research summary[:\s]+(.*?)(?=\n\n|\n[A-Z][a-z]+:)',
        ]
        for pattern in abstract_patterns:
            match = re.search(pattern, text[:5000], re.DOTALL)
            if match:
                abstract = match.group(1).strip()[:1000]  # Limit to 1000 chars
                break
        
        return {
            "paper_id": paper_id,
            "title": title or f"Paper {paper_id}",
            "abstract": abstract or "",
            "publication_year": year,
            "journal": "Strategic Management Journal",
            "paper_type": "empirical_quantitative",  # Default assumption
            "extraction_method": "fallback"
        }
    
    def process_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process paper using redesigned multi-stage pipeline"""
        paper_id = pdf_path.stem
        logger.info(f"Processing: {paper_id}")
        
        try:
            # Extract text
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            if not text:
                raise Exception(f"Failed to extract text from {pdf_path}")
            
            # Stage 1: Identify methodology section
            logger.info("Stage 1: Identifying methodology section...")
            section_info = self.extractor.identify_methodology_section(text)
            methodology_text = section_info.get("section_text", "")
            
            if not methodology_text:
                logger.warning(f"No methodology section found for {paper_id}")
                methodology_text = text[:10000]  # Fallback to first 10k chars
            
            # Stage 2: Extract primary methods
            logger.info("Stage 2: Extracting primary methods...")
            primary_methods = self.extractor.extract_primary_methods(methodology_text, paper_id)
            
            method_type = primary_methods.get("method_type", "unknown")
            primary_method_list = primary_methods.get("primary_methods", [])
            
            # Stage 3: Extract details for each method
            logger.info(f"Stage 3: Extracting details for {len(primary_method_list)} methods...")
            methods_data = []
            for method_name in primary_method_list:
                # Stage 4: Validate method is in text
                is_valid, validation_confidence = self.extractor.validate_method_in_text(method_name, methodology_text)
                
                if is_valid:
                    # Extract details
                    method_details = self.extractor.extract_method_details(method_name, methodology_text, method_type)
                    method_details["method_name"] = method_name
                    method_details["method_type"] = method_type
                    # Calculate confidence: validation confidence * extraction confidence (default to 0.8 if not provided)
                    # Handle all possible None cases robustly
                    extraction_confidence = method_details.get("confidence")
                    if extraction_confidence is None:
                        extraction_confidence = 0.8  # Default if missing or None
                    try:
                        extraction_confidence = float(extraction_confidence)
                        if extraction_confidence == 0.0 or extraction_confidence < 0:
                            extraction_confidence = 0.8  # Default if 0 or negative
                    except (ValueError, TypeError):
                        extraction_confidence = 0.8  # Default if not a number
                    
                    # Ensure validation_confidence is not None
                    if validation_confidence is None:
                        validation_confidence = 0.5  # Default if validation failed
                    try:
                        validation_confidence = float(validation_confidence)
                        if validation_confidence < 0:
                            validation_confidence = 0.5  # Default if negative
                    except (ValueError, TypeError):
                        validation_confidence = 0.5  # Default if not a number
                    
                    method_details["confidence"] = validation_confidence * extraction_confidence
                    methods_data.append(method_details)
                else:
                    logger.warning(f"Method '{method_name}' not validated in text, skipping")
            
            # Extract paper metadata using LLM (with error handling and fallback)
            logger.info("Extracting paper metadata...")
            try:
                metadata_result = self.extractor.extract_paper_metadata(text, paper_id)
                paper_metadata = metadata_result.get("paper_metadata", {})
                authors = metadata_result.get("authors", [])
                logger.info(f"✓ Metadata extracted: title={bool(paper_metadata.get('title'))}, authors={len(authors)}, abstract={bool(paper_metadata.get('abstract'))}")
            except Exception as e:
                logger.error(f"✗ Metadata extraction failed: {str(e)[:200]}")
                # Fallback: Extract basic metadata from filename and first page
                logger.info("   Using fallback metadata extraction...")
                paper_metadata = self._extract_fallback_metadata(text, paper_id, pdf_path)
                authors = []
                metadata_result = {"paper_metadata": paper_metadata, "authors": authors}
                logger.info(f"✓ Fallback metadata: paper_id={paper_id}, year={paper_metadata.get('publication_year', 'N/A')}")
            
            # Extract theories (with error handling)
            logger.info("Extracting theories...")
            try:
                theories_data = self.extractor.extract_theories(text, paper_id)
                logger.info(f"✓ Theories extracted: {len(theories_data)} theories")
            except Exception as e:
                logger.warning(f"⚠️  Theories extraction failed: {str(e)[:200]}, continuing...")
                theories_data = []
            
            # Extract phenomena (with error handling)
            logger.info("Extracting phenomena...")
            try:
                phenomena_data = self.extractor.extract_phenomena(text, paper_id)
                logger.info(f"✓ Phenomena extracted: {len(phenomena_data)} phenomena")
            except Exception as e:
                logger.warning(f"⚠️  Phenomena extraction failed: {str(e)[:200]}, continuing...")
                phenomena_data = []
            
            # Extract research questions (with error handling)
            logger.info("Extracting research questions...")
            try:
                research_questions_data = self.extractor.extract_research_questions(text, paper_id)
                logger.info(f"✓ Research questions extracted: {len(research_questions_data)} questions")
            except Exception as e:
                logger.warning(f"⚠️  Research questions extraction failed: {str(e)[:200]}, continuing...")
                research_questions_data = []
            
            # Extract variables (with error handling)
            logger.info("Extracting variables...")
            try:
                variables_data = self.extractor.extract_variables(text, paper_id)
                logger.info(f"✓ Variables extracted: {len(variables_data)} variables")
            except Exception as e:
                logger.warning(f"⚠️  Variables extraction failed: {str(e)[:200]}, continuing...")
                variables_data = []
            
            # Extract findings (with error handling)
            logger.info("Extracting findings...")
            try:
                findings_data = self.extractor.extract_findings(text, paper_id)
                logger.info(f"✓ Findings extracted: {len(findings_data)} findings")
            except Exception as e:
                logger.warning(f"⚠️  Findings extraction failed: {str(e)[:200]}, continuing...")
                findings_data = []
            
            # Extract contributions (with error handling)
            logger.info("Extracting contributions...")
            try:
                contributions_data = self.extractor.extract_contributions(text, paper_id)
                logger.info(f"✓ Contributions extracted: {len(contributions_data)} contributions")
            except Exception as e:
                logger.warning(f"⚠️  Contributions extraction failed: {str(e)[:200]}, continuing...")
                contributions_data = []
            
            # Extract software (with error handling)
            logger.info("Extracting software...")
            try:
                software_data = self.extractor.extract_software(text, paper_id)
                logger.info(f"✓ Software extracted: {len(software_data)} software")
            except Exception as e:
                logger.warning(f"⚠️  Software extraction failed: {str(e)[:200]}, continuing...")
                software_data = []
            
            # Extract datasets (with error handling)
            logger.info("Extracting datasets...")
            try:
                datasets_data = self.extractor.extract_datasets(text, paper_id)
                logger.info(f"✓ Datasets extracted: {len(datasets_data)} datasets")
            except Exception as e:
                logger.warning(f"⚠️  Datasets extraction failed: {str(e)[:200]}, continuing...")
                datasets_data = []
            
            # Extract citations (with error handling)
            citations_data = []
            try:
                citations_data = self.extractor.extract_citations(text, paper_id)
                logger.info(f"✓ Citations extracted: {len(citations_data)} citations")
            except Exception as e:
                logger.warning(f"⚠️  Citations extraction failed: {str(e)[:200]}, continuing...")
                citations_data = []
            
            # Ingest to Neo4j (with error handling and retry)
            try:
                self.ingester.ingest_paper_with_methods(paper_metadata, methods_data, authors, metadata_result, 
                                                       theories_data, research_questions_data, variables_data,
                                                       findings_data, contributions_data, software_data, datasets_data,
                                                       phenomena_data, citations_data)
            except Exception as e:
                error_str = str(e).lower()
                if "routing" in error_str or "connection" in error_str or "defunct" in error_str:
                    # Retry ingestion once after reconnection
                    logger.warning(f"⚠️  Neo4j ingestion failed (connection issue), retrying...")
                    import time
                    time.sleep(5)
                    try:
                        # Recreate ingester connection
                        self.ingester.driver.close()
                        self.ingester.driver = GraphDatabase.driver(
                            self.ingester.neo4j_uri,
                            auth=(self.ingester.neo4j_user, self.ingester.neo4j_password),
                            max_connection_lifetime=30 * 60,
                            max_connection_pool_size=50,
                            connection_acquisition_timeout=60,
                            connection_timeout=30
                        )
                        self.ingester.ingest_paper_with_methods(paper_metadata, methods_data, authors, metadata_result, 
                                                               theories_data, research_questions_data, variables_data,
                                                               findings_data, contributions_data, software_data, datasets_data,
                                                               phenomena_data, citations_data)
                        logger.info("✓ Retry ingestion successful")
                    except Exception as retry_e:
                        logger.error(f"✗ Retry ingestion also failed: {str(retry_e)[:200]}")
                        raise  # Re-raise if retry also fails
                else:
                    raise  # Re-raise non-connection errors
            
            logger.info(f"✓ Successfully processed {paper_id} with {len(methods_data)} methods")
            
            return {
                "paper_metadata": paper_metadata,
                "authors": authors,
                "methods": methods_data,
                "theories": theories_data,
                "research_questions": research_questions_data,
                "variables": variables_data,
                "findings": findings_data,
                "contributions": contributions_data,
                "software": software_data,
                "datasets": datasets_data,
                "phenomena": phenomena_data,
                "methods_data": methods_data,
                "section_info": section_info
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to process {paper_id}: {e}")
            raise

