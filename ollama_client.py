#!/usr/bin/env python3
"""
OLLAMA Client for SMJ Research Extraction
Uses local OLLAMA models for cost-effective entity extraction
"""

import json
import logging
import requests
import time
from typing import Optional, Dict, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for OLLAMA local models with retry logic and error handling"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2
        self.timeout = 120  # 2 minutes timeout for complex extractions
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test OLLAMA connection and model availability"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model in model_names:
                    logger.info(f"✓ OLLAMA connected, model '{self.model}' available")
                else:
                    logger.warning(f"⚠️ Model '{self.model}' not found. Available models: {model_names}")
                    # Try to use the first available model
                    if model_names:
                        self.model = model_names[0]
                        logger.info(f"Using available model: {self.model}")
                    else:
                        raise Exception("No models available in OLLAMA")
            else:
                raise Exception(f"OLLAMA API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to OLLAMA: {e}")
            logger.error("Please ensure OLLAMA is running: ollama serve")
            raise
    
    def extract_with_retry(self, prompt: str, max_tokens: int = 2000) -> str:
        """Extract information using OLLAMA with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self._call_ollama(prompt, max_tokens)
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise
    
    def _call_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make API call to OLLAMA"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent extraction
                "top_p": 0.9,
                "max_tokens": max_tokens,
                "stop": ["```", "---", "END"]
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
    
    def extract_research_questions(self, text: str, section: str, paper_id: str) -> list:
        """Extract research questions using OLLAMA"""
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
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "questions")
    
    def extract_methodology(self, text: str, section: str, paper_id: str) -> list:
        """Extract methodology information using OLLAMA"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify methodology information.

        Text: {text}

        Extract methodology in this JSON format:
        {{
            "methodologies": [
                {{
                    "methodology": "description of the methodology",
                    "method_type": "quantitative|qualitative|mixed|theoretical|case_study|survey|experiment",
                    "context": "brief context about the methodology"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no methodology found, return {{"methodologies": []}}.
        """
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "methodologies")
    
    def extract_findings(self, text: str, section: str, paper_id: str) -> list:
        """Extract research findings using OLLAMA"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify key findings.

        Text: {text}

        Extract findings in this JSON format:
        {{
            "findings": [
                {{
                    "finding": "description of the finding",
                    "finding_type": "empirical|theoretical|practical|statistical",
                    "context": "brief context about the finding"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no findings found, return {{"findings": []}}.
        """
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "findings")
    
    def extract_contributions(self, text: str, section: str, paper_id: str) -> list:
        """Extract research contributions using OLLAMA"""
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
                    "contribution_type": "theoretical|empirical|methodological|practical",
                    "context": "brief context about the contribution"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no contributions found, return {{"contributions": []}}.
        """
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "contributions")
    
    def extract_entities(self, text: str, section: str, paper_id: str) -> list:
        """Extract research entities using OLLAMA"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify key research entities.

        Text: {text}

        Extract entities in this JSON format:
        {{
            "entities": [
                {{
                    "name": "entity name",
                    "type": "concept|theory|framework|method|construct|variable|phenomenon",
                    "context": "brief context about the entity"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no entities found, return {{"entities": []}}.
        """
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "entities")
    
    def extract_relationships(self, text: str, section: str, paper_id: str) -> list:
        """Extract relationships between entities using OLLAMA"""
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        prompt = f"""
        Analyze this text from the {section} section of a research paper and identify relationships between entities.

        Text: {text}

        Extract relationships in this JSON format:
        {{
            "relationships": [
                {{
                    "source": "source entity name",
                    "target": "target entity name",
                    "relationship_type": "influences|affects|relates_to|causes|predicts|moderates|mediates",
                    "context": "brief context about the relationship"
                }}
            ]
        }}

        Only return valid JSON, no additional text. If no relationships found, return {{"relationships": []}}.
        """
        
        response = self.extract_with_retry(prompt)
        return self._parse_json_response(response, "relationships")
    
    def identify_sections(self, text: str) -> Dict[str, str]:
        """Identify paper sections using OLLAMA"""
        if len(text) > 15000:
            text = text[:15000] + "..."
        
        prompt = f"""
        Analyze this academic paper and extract sections. Return ONLY a valid JSON object with these exact keys:

        Text: {text[:5000]}

        Return this JSON format:
        {{
            "abstract": "content or null",
            "introduction": "content or null", 
            "literature_review": "content or null",
            "methodology": "content or null",
            "results": "content or null",
            "discussion": "content or null",
            "conclusion": "content or null"
        }}

        JSON only, no other text.
        """
        
        response = self.extract_with_retry(prompt, max_tokens=3000)
        result = self._parse_json_response(response, None)
        
        # Ensure we have a dict with the expected keys
        if not isinstance(result, dict):
            result = {}
        
        # Filter out null values and ensure all keys exist
        expected_keys = ["abstract", "introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
        clean_result = {}
        for key in expected_keys:
            value = result.get(key)
            if value and value != "null" and value.strip():
                clean_result[key] = value.strip()
        
        return clean_result
    
    def _parse_json_response(self, response: str, key: str = None) -> Any:
        """Parse JSON response from OLLAMA with robust error handling"""
        try:
            # Clean the response
            response = response.strip()
            
            # Remove any markdown formatting
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Try to find JSON object boundaries
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx + 1]
            
            # Parse JSON
            data = json.loads(response)
            
            if key:
                return data.get(key, [])
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.warning(f"Response was: {response[:300]}...")
            
            # Try to extract data using regex as fallback
            try:
                import re
                if key:
                    # Look for the specific key pattern
                    pattern = f'"{key}":\\s*\\[([^\\]]*)\\]'
                    match = re.search(pattern, response, re.DOTALL)
                    if match:
                        # This is a simplified fallback - in practice you'd need more sophisticated parsing
                        return []
                return {} if key is None else []
            except:
                return [] if key else {}
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return [] if key else {}

def test_ollama_connection():
    """Test OLLAMA connection and model"""
    try:
        client = OllamaClient()
        print("✓ OLLAMA connection successful")
        
        # Test with a simple prompt
        response = client.extract_with_retry("What is strategic management? Answer in one sentence.")
        print(f"✓ Model response: {response[:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ OLLAMA connection failed: {e}")
        print("\nTo fix this:")
        print("1. Install OLLAMA: https://ollama.ai/")
        print("2. Pull a model: ollama pull llama3.1:8b")
        print("3. Start OLLAMA: ollama serve")
        return False

if __name__ == "__main__":
    test_ollama_connection()
