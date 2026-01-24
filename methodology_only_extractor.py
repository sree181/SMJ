#!/usr/bin/env python3
"""
Focused Methodology-Only Extraction System using OLLAMA
Extracts ONLY methodology information using your specific prompt
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
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

class OllamaMethodologyOnlyExtractor:
    """OLLAMA-based methodology-only extractor with your specific prompt"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:7b"):
        self.base_url = base_url
        self.model = model
        self.max_retries = 2  # Reduced retries
        self.retry_delay = 3  # Reduced delay
        self.timeout = 120  # 2 minutes timeout
        
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
    
    def extract_with_retry(self, prompt: str, max_tokens: int = 4000) -> str:
        """Extract methodology using OLLAMA with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self._call_ollama(prompt, max_tokens)
                return response
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                
                # If it's a timeout, wait longer before retry
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Timeout detected, waiting {wait_time} seconds before retry...")
                    import time
                    time.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
                    raise
    
    def _call_ollama(self, prompt: str, max_tokens: int = 4000) -> str:
        """Make API call to OLLAMA"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent extraction
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
    
    def extract_methodology_section(self, text: str) -> str:
        """Extract ONLY the methodology section from full paper text"""
        if len(text) > 15000:
            text = text[:15000] + "..."
        
        prompt = f"""
        Extract ONLY the METHOD/METHODOLOGY section from this academic paper.
        Return the raw text of the methodology section, nothing else.

        Paper text: {text}

        Look for sections titled: Methods, Methodology, Research Design, Data and Methods, 
        Empirical Strategy, Analysis, or similar.

        Return only the methodology section text, no other content.
        """
        
        response = self.extract_with_retry(prompt, max_tokens=2000)
        return response.strip()
    
    def extract_structured_methodology(self, method_text: str, paper_id: str) -> Dict[str, Any]:
        """Extract structured methodology using simplified prompt"""
        if len(method_text) > 4000:  # Reduced text length
            method_text = method_text[:4000] + "..."
        
        prompt = f"""Extract methodology information from this text. Return ONLY valid JSON.

Text: {method_text}

JSON format:
{{
  "paper_id": "{paper_id}",
  "methodology": {{
    "type": "quantitative",
    "design": ["case study"],
    "quant_methods": ["regression", "correlation"],
    "qual_methods": ["interviews", "surveys"],
    "software": ["SPSS", "R"],
    "confidence": 0.8,
    "extraction_notes": "Brief description"
  }}
}}"""
        
        response = self.extract_with_retry(prompt, max_tokens=4000)
        return self._parse_json_response(response)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
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
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.warning(f"Response was: {response[:500]}...")
            
            # Return empty structure as fallback
            return {
                "paper_id": "",
                "methodology": {
                    "type": "other",
                    "design": [],
                    "unit_of_analysis": [],
                    "context": {"domain": "", "setting": "", "geography": ""},
                    "timeframe": {"start": "", "end": "", "granularity": "", "notes": ""},
                    "sampling": {"frame": "", "technique": "", "inclusion_criteria": [], "exclusion_criteria": [], "sample_sizes": {"overall": None, "groups": {}}, "power_analysis": ""},
                    "data": {"sources": [], "acquisition": {"mode": "", "details": ""}, "preprocessing": {"cleaning": [], "imputation": "", "transformations": []}, "features_operationalization": [], "missing_data": {"strategy": "", "assumed_mechanism": ""}},
                    "measurement_quality": {"reliability": {"cronbach_alpha": None, "icc": None, "kappa": None, "other": ""}, "validity": {"construct": "", "convergent": "", "discriminant": "", "criterion": ""}},
                    "analysis": {"quant_methods": [], "qual_methods": [], "mixed_integration": "", "assumption_checks": [], "controls_fixed_effects": [], "evaluation_metrics": [], "baselines": [], "robustness_checks": []},
                    "implementation": {"software": [], "packages": [], "hardware": {"cpu": "", "gpu": "", "ram_gb": None}, "hyperparameters": {"learning_rate": None, "max_depth": None, "seed": None, "other": {}}, "data_splitting": {"strategy": "", "train_val_test": [None, None, None], "cv_folds": None}, "runtime": {"training": "", "inference": ""}, "reproducibility": {"code_url": "", "data_url": "", "preregistration_id": ""}},
                    "domain_specific": {"network": {"graph_type": "", "node_def": "", "edge_def": "", "temporal_window": "", "weights": ""}, "nlp": {"tokenization": "", "embeddings": "", "models": [], "prompt_templates": []}, "patent": {"cpc_rules": "", "orange_book_linkage": "", "piv_flags": ""}, "healthcare": {"trial_phase": "", "randomization": "", "blinding": ""}},
                    "advantages": [],
                    "limitations": [],
                    "threats_to_validity": [],
                    "ethics_irb": {"irb_id": "", "consent": "", "compensation": ""},
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

class Neo4jMethodologyOnlyIngester:
    """Ingests ONLY methodology data into Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def ingest_methodology_only(self, methodology_data: Dict[str, Any]):
        """Ingest ONLY methodology data into Neo4j with simplified schema"""
        paper_id = methodology_data.get("paper_id", "")
        methodology = methodology_data.get("methodology", {})
        
        if not paper_id or not methodology:
            logger.warning("Invalid methodology data, skipping ingestion")
            return
        
        with self.driver.session() as session:
            # Create paper node if it doesn't exist
            session.run("""
                MERGE (p:Paper {paper_id: $paper_id})
                SET p.year = $year
            """, paper_id=paper_id, year=self._extract_year_from_paper_id(paper_id))
            
            # Create methodology node with simplified properties (prevent duplicates)
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                // Remove any existing methodology nodes for this paper
                OPTIONAL MATCH (p)-[r:HAS_METHODOLOGY]->(old_m:Methodology)
                DELETE r, old_m
                // Create new methodology node
                CREATE (m:Methodology {paper_id: $paper_id})
                SET m.type = $type,
                    m.design = $design,
                    m.quant_methods = $quant_methods,
                    m.qual_methods = $qual_methods,
                    m.software = $software,
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
            confidence=methodology.get("confidence", 0.0),
            extraction_notes=methodology.get("extraction_notes", ""))
    
    def _extract_year_from_paper_id(self, paper_id: str) -> int:
        """Extract year from paper ID like '1988_305'"""
        try:
            return int(paper_id.split('_')[0])
        except:
            return 0

class MethodologyOnlyProcessor:
    """Main processor for methodology-only extraction and ingestion"""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None, 
                 ollama_model: str = "llama3.1:8b"):
        
        # Use environment variables if not provided
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        if neo4j_user is None:
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        if neo4j_password is None:
            neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize components
        self.extractor = OllamaMethodologyOnlyExtractor(model=ollama_model)
        self.pdf_processor = PDFProcessor()
        self.ingester = Neo4jMethodologyOnlyIngester(neo4j_uri, neo4j_user, neo4j_password)
    
    def process_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single paper for methodology-only extraction"""
        paper_id = pdf_path.stem
        logger.info(f"Processing methodology ONLY for: {paper_id}")
        
        try:
            # Extract text from PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            if not text:
                raise Exception(f"Failed to extract text from {pdf_path}")
            
            # Extract methodology section ONLY
            method_text = self.extractor.extract_methodology_section(text)
            if not method_text:
                raise Exception("No methodology section found")
            
            logger.info(f"Extracted methodology section ({len(method_text)} chars)")
            
            # Extract structured methodology using your exact prompt
            methodology_data = self.extractor.extract_structured_methodology(method_text, paper_id)
            
            # Ingest ONLY methodology into Neo4j
            self.ingester.ingest_methodology_only(methodology_data)
            
            logger.info(f"✓ Successfully processed methodology ONLY for {paper_id}")
            return methodology_data
            
        except Exception as e:
            logger.error(f"✗ Failed to process {paper_id}: {e}")
            raise

def main():
    """Test the methodology-only extraction system"""
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    processor = MethodologyOnlyProcessor(ollama_model='llama3.1:8b')
    
    # Test with a sample paper
    test_paper = Path('./1985-1989/1988_305.pdf')
    if test_paper.exists():
        print(f"🧪 Testing methodology-ONLY extraction with: {test_paper.name}")
        
        try:
            result = processor.process_paper(test_paper)
            print(f"✅ Successfully extracted methodology ONLY")
            print(f"📊 Methodology type: {result['methodology']['type']}")
            print(f"🔬 Design: {result['methodology']['design']}")
            print(f"📈 Quant methods: {result['methodology']['analysis']['quant_methods']}")
            print(f"📝 Qual methods: {result['methodology']['analysis']['qual_methods']}")
            print(f"🎯 Confidence: {result['methodology']['confidence']}")
            print(f"📝 Notes: {result['methodology']['extraction_notes'][:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Test paper not found")

if __name__ == "__main__":
    main()
