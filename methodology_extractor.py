#!/usr/bin/env python3
"""
Focused Methodology Extraction System using OLLAMA
Extracts detailed methodology information using structured prompts
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
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

@dataclass
class MethodologyData:
    """Structured methodology data"""
    paper_id: str
    methodology_type: str
    design: List[str]
    unit_of_analysis: List[str]
    context: Dict[str, str]
    timeframe: Dict[str, str]
    sampling: Dict[str, Any]
    data: Dict[str, Any]
    measurement_quality: Dict[str, Any]
    analysis: Dict[str, Any]
    implementation: Dict[str, Any]
    domain_specific: Dict[str, Any]
    advantages: List[str]
    limitations: List[str]
    threats_to_validity: List[str]
    ethics_irb: Dict[str, str]
    confidence: float
    extraction_notes: str

class OllamaMethodologyExtractor:
    """OLLAMA-based methodology extractor with structured prompts"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self.max_retries = 3
        self.retry_delay = 2
        self.timeout = 180  # 3 minutes for complex extractions
        
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
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
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
        """Extract methodology section from full paper text"""
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
        """Extract structured methodology using the detailed prompt"""
        if len(method_text) > 8000:
            method_text = method_text[:8000] + "..."
        
        prompt = f"""SYSTEM:
You are a scholarly information extraction engine. 
Goal: Read ONLY the METHOD/METHODOLOGY section of an academic paper and return STRICT JSON for graph ingestion.
The JSON must follow the exact schema below, no comments, no trailing commas, no markdown fences, no extra text.

Definitions:
- methodology.type ∈ {{"quantitative","qualitative","mixed","other"}}.
- methodology.design: list canonical design terms (e.g., "experimental","cross-sectional","panel","case study","quasi-experimental","RCT","SLR","meta-analysis","simulation").
- quant_methods: specific statistical/ML/econometric methods actually used (e.g., "OLS","logit","DiD","FE regression","IV/2SLS","RDD","Cox PH","ARIMA","VAR","SVM","Random Forest","XGBoost","Neural Network","SEM/CFA").
- qual_methods: specific qualitative approaches (e.g., "grounded theory","thematic analysis","content analysis","ethnography","discourse analysis","QCA").
- mixed_integration: how qual+quant are combined (e.g., "sequential explanatory","sequential exploratory","concurrent triangulation").
- evaluation_metrics: e.g., "R²","MAE","RMSE","AUC","F1","Precision","Recall","OR","HR","p-value","CI","CFI","TLI","RMSEA".
- assumption_checks: e.g., "parallel trends","stationarity","normality","homoscedasticity","multicollinearity/VIF","common support/overlap".
- controls_fixed_effects: e.g., "entity FE","time FE","clustered SEs at firm level".
- timeframe: prefer ISO if available; else free text window.
- If a field is not explicitly present, return [] or "" as appropriate and set confidence lower.

Normalization rules:
- Extract only what is stated or unambiguously implied in the METHODS.
- Remove citation clutter (e.g., "[12]", "(Smith, 2020)") from values.
- Units of analysis: nouns like "individual","firm","patent","post","document","country","network node","edge","time-slice".
- Software: explicit tool names and versions when stated (e.g., "Stata 17","R 4.2","Python 3.10","PyTorch 2.1","TensorFlow 2.13").

Output schema (JSON object):
{{
  "paper_id": "{paper_id}",
  "methodology": {{
    "type": "",
    "design": [],
    "unit_of_analysis": [],
    "context": {{"domain": "", "setting": "", "geography": ""}},
    "timeframe": {{"start": "", "end": "", "granularity": "", "notes": ""}},
    "sampling": {{
      "frame": "", "technique": "", 
      "inclusion_criteria": [], "exclusion_criteria": [],
      "sample_sizes": {{"overall": null, "groups": {{}}}},
      "power_analysis": ""
    }},
    "data": {{
      "sources": [{{"name":"", "type":"", "url_or_doi":"", "license":""}}],
      "acquisition": {{"mode":"", "details":""}},
      "preprocessing": {{"cleaning":[], "imputation":"", "transformations":[]}},
      "features_operationalization": [{{"construct":"", "variables":[], "rules":""}}],
      "missing_data": {{"strategy":"", "assumed_mechanism":""}}
    }},
    "measurement_quality": {{
      "reliability": {{"cronbach_alpha": null, "icc": null, "kappa": null, "other":""}},
      "validity": {{"construct":"", "convergent":"", "discriminant":"", "criterion":""}}
    }},
    "analysis": {{
      "quant_methods": [], 
      "qual_methods": [], 
      "mixed_integration": "",
      "assumption_checks": [],
      "controls_fixed_effects": [],
      "evaluation_metrics": [],
      "baselines": [],
      "robustness_checks": []
    }},
    "implementation": {{
      "software": [{{"name":"", "version":""}}],
      "packages": [{{"name":"", "version":""}}],
      "hardware": {{"cpu":"", "gpu":"", "ram_gb": null}},
      "hyperparameters": {{"learning_rate": null, "max_depth": null, "seed": null, "other": {{}}}},
      "data_splitting": {{"strategy":"", "train_val_test":[null,null,null], "cv_folds": null}},
      "runtime": {{"training":"", "inference":""}},
      "reproducibility": {{"code_url":"", "data_url":"", "preregistration_id":""}}
    }},
    "domain_specific": {{
      "network": {{"graph_type":"","node_def":"","edge_def":"","temporal_window":"","weights":""}},
      "nlp": {{"tokenization":"","embeddings":"","models":[], "prompt_templates":[]}},
      "patent": {{"cpc_rules":"","orange_book_linkage":"","piv_flags":""}},
      "healthcare": {{"trial_phase":"","randomization":"","blinding":""}}
    }},
    "advantages": [],
    "limitations": [],
    "threats_to_validity": [],
    "ethics_irb": {{"irb_id":"", "consent":"", "compensation":""}},
    "confidence": 0.0,
    "extraction_notes": ""
  }}
}}

Return only a single JSON object (UTF-8, no BOM). If you must guess, mark in extraction_notes and lower confidence.

USER:
METHOD/METHODOLOGY SECTION (verbatim):
{method_text}
"""
        
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

class Neo4jMethodologyIngester:
    """Ingests methodology data into Neo4j"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def ingest_methodology(self, methodology_data: Dict[str, Any]):
        """Ingest structured methodology data into Neo4j"""
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
            
            # Flatten nested structures for Neo4j compatibility
            context = methodology.get("context", {})
            timeframe = methodology.get("timeframe", {})
            sampling = methodology.get("sampling", {})
            data = methodology.get("data", {})
            measurement_quality = methodology.get("measurement_quality", {})
            analysis = methodology.get("analysis", {})
            implementation = methodology.get("implementation", {})
            domain_specific = methodology.get("domain_specific", {})
            ethics_irb = methodology.get("ethics_irb", {})
            
            # Create methodology node with flattened properties
            session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                MERGE (m:Methodology {paper_id: $paper_id})
                SET m.type = $type,
                    m.design = $design,
                    m.unit_of_analysis = $unit_of_analysis,
                    m.domain = $domain,
                    m.setting = $setting,
                    m.geography = $geography,
                    m.timeframe_start = $timeframe_start,
                    m.timeframe_end = $timeframe_end,
                    m.timeframe_granularity = $timeframe_granularity,
                    m.timeframe_notes = $timeframe_notes,
                    m.sampling_frame = $sampling_frame,
                    m.sampling_technique = $sampling_technique,
                    m.inclusion_criteria = $inclusion_criteria,
                    m.exclusion_criteria = $exclusion_criteria,
                    m.sample_size_overall = $sample_size_overall,
                    m.power_analysis = $power_analysis,
                    m.data_sources = $data_sources,
                    m.acquisition_mode = $acquisition_mode,
                    m.acquisition_details = $acquisition_details,
                    m.preprocessing_cleaning = $preprocessing_cleaning,
                    m.preprocessing_imputation = $preprocessing_imputation,
                    m.preprocessing_transformations = $preprocessing_transformations,
                    m.missing_data_strategy = $missing_data_strategy,
                    m.missing_data_mechanism = $missing_data_mechanism,
                    m.cronbach_alpha = $cronbach_alpha,
                    m.icc = $icc,
                    m.kappa = $kappa,
                    m.reliability_other = $reliability_other,
                    m.construct_validity = $construct_validity,
                    m.convergent_validity = $convergent_validity,
                    m.discriminant_validity = $discriminant_validity,
                    m.criterion_validity = $criterion_validity,
                    m.quant_methods = $quant_methods,
                    m.qual_methods = $qual_methods,
                    m.mixed_integration = $mixed_integration,
                    m.assumption_checks = $assumption_checks,
                    m.controls_fixed_effects = $controls_fixed_effects,
                    m.evaluation_metrics = $evaluation_metrics,
                    m.baselines = $baselines,
                    m.robustness_checks = $robustness_checks,
                    m.software = $software,
                    m.packages = $packages,
                    m.hardware_cpu = $hardware_cpu,
                    m.hardware_gpu = $hardware_gpu,
                    m.hardware_ram_gb = $hardware_ram_gb,
                    m.data_splitting_strategy = $data_splitting_strategy,
                    m.cv_folds = $cv_folds,
                    m.training_runtime = $training_runtime,
                    m.inference_runtime = $inference_runtime,
                    m.code_url = $code_url,
                    m.data_url = $data_url,
                    m.preregistration_id = $preregistration_id,
                    m.advantages = $advantages,
                    m.limitations = $limitations,
                    m.threats_to_validity = $threats_to_validity,
                    m.irb_id = $irb_id,
                    m.consent = $consent,
                    m.compensation = $compensation,
                    m.confidence = $confidence,
                    m.extraction_notes = $extraction_notes,
                    m.created_at = datetime()
                MERGE (p)-[:HAS_METHODOLOGY]->(m)
            """, 
            paper_id=paper_id,
            type=methodology.get("type", ""),
            design=methodology.get("design", []),
            unit_of_analysis=methodology.get("unit_of_analysis", []),
            domain=context.get("domain", ""),
            setting=context.get("setting", ""),
            geography=context.get("geography", ""),
            timeframe_start=timeframe.get("start", ""),
            timeframe_end=timeframe.get("end", ""),
            timeframe_granularity=timeframe.get("granularity", ""),
            timeframe_notes=timeframe.get("notes", ""),
            sampling_frame=sampling.get("frame", ""),
            sampling_technique=sampling.get("technique", ""),
            inclusion_criteria=sampling.get("inclusion_criteria", []),
            exclusion_criteria=sampling.get("exclusion_criteria", []),
            sample_size_overall=sampling.get("sample_sizes", {}).get("overall"),
            power_analysis=sampling.get("power_analysis", ""),
            data_sources=[str(source) for source in data.get("sources", [])],
            acquisition_mode=data.get("acquisition", {}).get("mode", ""),
            acquisition_details=data.get("acquisition", {}).get("details", ""),
            preprocessing_cleaning=data.get("preprocessing", {}).get("cleaning", []),
            preprocessing_imputation=data.get("preprocessing", {}).get("imputation", ""),
            preprocessing_transformations=data.get("preprocessing", {}).get("transformations", []),
            missing_data_strategy=data.get("missing_data", {}).get("strategy", ""),
            missing_data_mechanism=data.get("missing_data", {}).get("assumed_mechanism", ""),
            cronbach_alpha=measurement_quality.get("reliability", {}).get("cronbach_alpha"),
            icc=measurement_quality.get("reliability", {}).get("icc"),
            kappa=measurement_quality.get("reliability", {}).get("kappa"),
            reliability_other=measurement_quality.get("reliability", {}).get("other", ""),
            construct_validity=measurement_quality.get("validity", {}).get("construct", ""),
            convergent_validity=measurement_quality.get("validity", {}).get("convergent", ""),
            discriminant_validity=measurement_quality.get("validity", {}).get("discriminant", ""),
            criterion_validity=measurement_quality.get("validity", {}).get("criterion", ""),
            quant_methods=analysis.get("quant_methods", []),
            qual_methods=analysis.get("qual_methods", []),
            mixed_integration=analysis.get("mixed_integration", ""),
            assumption_checks=analysis.get("assumption_checks", []),
            controls_fixed_effects=analysis.get("controls_fixed_effects", []),
            evaluation_metrics=analysis.get("evaluation_metrics", []),
            baselines=analysis.get("baselines", []),
            robustness_checks=analysis.get("robustness_checks", []),
            software=[str(sw) for sw in implementation.get("software", [])],
            packages=[str(pkg) for pkg in implementation.get("packages", [])],
            hardware_cpu=implementation.get("hardware", {}).get("cpu", ""),
            hardware_gpu=implementation.get("hardware", {}).get("gpu", ""),
            hardware_ram_gb=implementation.get("hardware", {}).get("ram_gb"),
            data_splitting_strategy=implementation.get("data_splitting", {}).get("strategy", ""),
            cv_folds=implementation.get("data_splitting", {}).get("cv_folds"),
            training_runtime=implementation.get("runtime", {}).get("training", ""),
            inference_runtime=implementation.get("runtime", {}).get("inference", ""),
            code_url=implementation.get("reproducibility", {}).get("code_url", ""),
            data_url=implementation.get("reproducibility", {}).get("data_url", ""),
            preregistration_id=implementation.get("reproducibility", {}).get("preregistration_id", ""),
            advantages=methodology.get("advantages", []),
            limitations=methodology.get("limitations", []),
            threats_to_validity=methodology.get("threats_to_validity", []),
            irb_id=ethics_irb.get("irb_id", ""),
            consent=ethics_irb.get("consent", ""),
            compensation=ethics_irb.get("compensation", ""),
            confidence=methodology.get("confidence", 0.0),
            extraction_notes=methodology.get("extraction_notes", ""))
            
            # Create specific methodology entities
            self._create_methodology_entities(session, paper_id, methodology)
    
    def _extract_year_from_paper_id(self, paper_id: str) -> int:
        """Extract year from paper ID like '1988_305'"""
        try:
            return int(paper_id.split('_')[0])
        except:
            return 0
    
    def _create_methodology_entities(self, session, paper_id: str, methodology: Dict[str, Any]):
        """Create specific entities for methodology components"""
        analysis = methodology.get("analysis", {})
        
        # Create quantitative methods entities
        for method in analysis.get("quant_methods", []):
            if method:
                session.run("""
                    MATCH (m:Methodology {paper_id: $paper_id})
                    MERGE (qm:QuantitativeMethod {name: $method})
                    SET qm.method_type = 'quantitative'
                    MERGE (m)-[:USES_QUANTITATIVE_METHOD]->(qm)
                """, paper_id=paper_id, method=method)
        
        # Create qualitative methods entities
        for method in analysis.get("qual_methods", []):
            if method:
                session.run("""
                    MATCH (m:Methodology {paper_id: $paper_id})
                    MERGE (qm:QualitativeMethod {name: $method})
                    SET qm.method_type = 'qualitative'
                    MERGE (m)-[:USES_QUALITATIVE_METHOD]->(qm)
                """, paper_id=paper_id, method=method)
        
        # Create design entities
        for design in methodology.get("design", []):
            if design:
                session.run("""
                    MATCH (m:Methodology {paper_id: $paper_id})
                    MERGE (d:ResearchDesign {name: $design})
                    MERGE (m)-[:USES_DESIGN]->(d)
                """, paper_id=paper_id, design=design)

class MethodologyProcessor:
    """Main processor for methodology extraction and ingestion"""
    
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
        self.extractor = OllamaMethodologyExtractor(model=ollama_model)
        self.pdf_processor = PDFProcessor()
        self.ingester = Neo4jMethodologyIngester(neo4j_uri, neo4j_user, neo4j_password)
    
    def process_paper(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single paper for methodology extraction"""
        paper_id = pdf_path.stem
        logger.info(f"Processing methodology for: {paper_id}")
        
        try:
            # Extract text from PDF
            text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            if not text:
                raise Exception(f"Failed to extract text from {pdf_path}")
            
            # Extract methodology section
            method_text = self.extractor.extract_methodology_section(text)
            if not method_text:
                raise Exception("No methodology section found")
            
            logger.info(f"Extracted methodology section ({len(method_text)} chars)")
            
            # Extract structured methodology
            methodology_data = self.extractor.extract_structured_methodology(method_text, paper_id)
            
            # Ingest into Neo4j
            self.ingester.ingest_methodology(methodology_data)
            
            logger.info(f"✓ Successfully processed methodology for {paper_id}")
            return methodology_data
            
        except Exception as e:
            logger.error(f"✗ Failed to process {paper_id}: {e}")
            raise

def main():
    """Test the methodology extraction system"""
    # Set environment variables
    os.environ['NEO4J_URI'] = 'neo4j+s://fe285b91.databases.neo4j.io'
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'xdklBwzfLJIVzuRAzQElOXbC1pZADJS5PfGVL_SDQMw'
    
    processor = MethodologyProcessor(ollama_model='llama3.1:8b')
    
    # Test with a sample paper
    test_paper = Path('./1985-1989/1988_305.pdf')
    if test_paper.exists():
        print(f"🧪 Testing methodology extraction with: {test_paper.name}")
        
        try:
            result = processor.process_paper(test_paper)
            print(f"✅ Successfully extracted methodology")
            print(f"📊 Methodology type: {result['methodology']['type']}")
            print(f"🔬 Design: {result['methodology']['design']}")
            print(f"📈 Quant methods: {result['methodology']['analysis']['quant_methods']}")
            print(f"📝 Qual methods: {result['methodology']['analysis']['qual_methods']}")
            print(f"🎯 Confidence: {result['methodology']['confidence']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Test paper not found")

if __name__ == "__main__":
    main()
