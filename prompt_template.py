#!/usr/bin/env python3
"""
Standardized Prompt Template System
Provides consistent prompt structure across all extraction tasks
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ExtractionType(Enum):
    """Types of extraction tasks"""
    METADATA = "metadata"
    THEORY = "theory"
    METHOD = "method"
    RESEARCH_QUESTION = "research_question"
    VARIABLE = "variable"
    FINDING = "finding"
    CONTRIBUTION = "contribution"
    SOFTWARE = "software"
    DATASET = "dataset"
    CITATION = "citation"
    PHENOMENON = "phenomenon"

@dataclass
class PromptExample:
    """Few-shot example for prompts"""
    input_text: str
    output_json: Dict[str, Any]
    description: Optional[str] = None

class StandardizedPromptTemplate:
    """Standardized prompt template for all extraction tasks"""
    
    def __init__(self):
        self.version = "2.0"
        self.examples = self._load_examples()
    
    def _load_examples(self) -> Dict[ExtractionType, List[PromptExample]]:
        """Load few-shot examples for each extraction type"""
        return {
            ExtractionType.THEORY: [
                PromptExample(
                    input_text="This paper uses Resource-Based View (RBV) as its main theoretical framework to explain firm performance differences.",
                    output_json={
                        "theories": [{
                            "theory_name": "Resource-Based View",
                            "role": "primary",
                            "section": "introduction",
                            "usage_context": "Main theoretical framework to explain firm performance",
                            "domain": "strategic_management"
                        }]
                    },
                    description="Primary theory example"
                ),
                PromptExample(
                    input_text="We draw on Agency Theory and Institutional Theory to support our arguments about corporate governance.",
                    output_json={
                        "theories": [
                            {
                                "theory_name": "Agency Theory",
                                "role": "supporting",
                                "section": "literature_review",
                                "usage_context": "Supporting arguments about corporate governance",
                                "domain": "strategic_management"
                            },
                            {
                                "theory_name": "Institutional Theory",
                                "role": "supporting",
                                "section": "literature_review",
                                "usage_context": "Supporting arguments about corporate governance",
                                "domain": "strategic_management"
                            }
                        ]
                    },
                    description="Multiple supporting theories"
                ),
                PromptExample(
                    input_text="The literature review mentions various theories including RBV, Dynamic Capabilities, and Transaction Cost Economics, but these are not used in our analysis.",
                    output_json={
                        "theories": []
                    },
                    description="Theories mentioned but not used - should return empty"
                )
            ],
            ExtractionType.METHOD: [
                PromptExample(
                    input_text="We use Ordinary Least Squares (OLS) regression to estimate the relationship between firm resources and performance.",
                    output_json={
                        "methods": [{
                            "method_name": "Ordinary Least Squares",
                            "method_type": "quantitative",
                            "confidence": 0.95,
                            "description": "OLS regression to estimate relationship"
                        }]
                    },
                    description="Single quantitative method"
                ),
                PromptExample(
                    input_text="Data were collected through semi-structured interviews with 15 executives. We analyzed the data using thematic analysis.",
                    output_json={
                        "methods": [
                            {
                                "method_name": "Semi-Structured Interviews",
                                "method_type": "qualitative",
                                "confidence": 0.9,
                                "description": "Data collection method"
                            },
                            {
                                "method_name": "Thematic Analysis",
                                "method_type": "qualitative",
                                "confidence": 0.9,
                                "description": "Data analysis method"
                            }
                        ]
                    },
                    description="Qualitative methods"
                )
            ],
            ExtractionType.RESEARCH_QUESTION: [
                PromptExample(
                    input_text="Our research question is: How do firms achieve competitive advantage through resource allocation?",
                    output_json={
                        "research_questions": [{
                            "question": "How do firms achieve competitive advantage through resource allocation?",
                            "question_type": "explanatory",
                            "section": "introduction",
                            "domain": "strategic_management"
                        }]
                    },
                    description="Single research question"
                ),
                PromptExample(
                    input_text="This study addresses two questions: (1) What factors influence firm performance? (2) Under what conditions do these factors matter?",
                    output_json={
                        "research_questions": [
                            {
                                "question": "What factors influence firm performance?",
                                "question_type": "descriptive",
                                "section": "introduction",
                                "domain": "strategic_management"
                            },
                            {
                                "question": "Under what conditions do these factors matter?",
                                "question_type": "explanatory",
                                "section": "introduction",
                                "domain": "strategic_management"
                            }
                        ]
                    },
                    description="Multiple research questions"
                )
            ],
            ExtractionType.VARIABLE: [
                PromptExample(
                    input_text="Our dependent variable is firm performance, measured by return on assets (ROA). The main independent variable is R&D intensity.",
                    output_json={
                        "variables": [
                            {
                                "variable_name": "Firm Performance",
                                "variable_type": "dependent",
                                "measurement": "Return on assets (ROA)",
                                "operationalization": "ROA"
                            },
                            {
                                "variable_name": "R&D Intensity",
                                "variable_type": "independent",
                                "measurement": "R&D expenditure divided by sales",
                                "operationalization": "R&D/Sales"
                            }
                        ]
                    },
                    description="Dependent and independent variables"
                )
            ],
            ExtractionType.METADATA: [
                PromptExample(
                    input_text="Title: Strategic Resource Allocation in Competitive Markets\nAuthors: John Smith, Jane Doe\nAbstract: This paper examines how firms allocate resources...",
                    output_json={
                        "paper_metadata": {
                            "title": "Strategic Resource Allocation in Competitive Markets",
                            "abstract": "This paper examines how firms allocate resources...",
                            "publication_year": 2023
                        },
                        "authors": [
                            {"full_name": "John Smith", "given_name": "John", "family_name": "Smith", "position": 1},
                            {"full_name": "Jane Doe", "given_name": "Jane", "family_name": "Doe", "position": 2}
                        ]
                    },
                    description="Basic metadata extraction"
                )
            ],
            ExtractionType.CITATION: [
                PromptExample(
                    input_text="References:\nBarney, J. (1991). Firm resources and sustained competitive advantage. Journal of Management, 17(1), 99-120.",
                    output_json={
                        "citations": [{
                            "cited_title": "Firm resources and sustained competitive advantage",
                            "cited_authors": ["Barney, J."],
                            "cited_year": 1991,
                            "cited_journal": "Journal of Management",
                            "citation_type": "theoretical",
                            "section": "literature_review"
                        }]
                    },
                    description="Single citation"
                )
            ],
            ExtractionType.PHENOMENON: [
                PromptExample(
                    input_text="This study examines the phenomenon of economic nationalism in court rulings against foreign firms. We investigate how domestic courts systematically favor domestic firms over foreign firms in legal disputes.",
                    output_json={
                        "phenomena": [{
                            "phenomenon_name": "Economic nationalism in court rulings",
                            "phenomenon_type": "behavior",
                            "domain": "strategic_management",
                            "description": "Systematic favoritism of domestic firms over foreign firms in legal disputes",
                            "section": "introduction",
                            "context": "Examined through court rulings and legal disputes"
                        }]
                    },
                    description="Single phenomenon"
                ),
                PromptExample(
                    input_text="We study two phenomena: (1) the resource allocation patterns of firms during financial crises, and (2) the strategic responses of firms to market disruptions. Resource-Based View helps explain why some firms maintain investments while others cut back.",
                    output_json={
                        "phenomena": [
                            {
                                "phenomenon_name": "Resource allocation patterns during financial crises",
                                "phenomenon_type": "pattern",
                                "domain": "strategic_management",
                                "description": "How firms allocate resources during financial crises",
                                "section": "introduction",
                                "context": "Studied through firm investment decisions"
                            },
                            {
                                "phenomenon_name": "Strategic responses to market disruptions",
                                "phenomenon_type": "behavior",
                                "domain": "strategic_management",
                                "description": "How firms respond strategically to market disruptions",
                                "section": "introduction",
                                "context": "Examined through firm strategic actions"
                            }
                        ]
                    },
                    description="Multiple phenomena with theory connection"
                ),
                PromptExample(
                    input_text="The literature review discusses various organizational behaviors, but our study focuses specifically on the phenomenon of organizational learning in response to competitive threats.",
                    output_json={
                        "phenomena": [{
                            "phenomenon_name": "Organizational learning in response to competitive threats",
                            "phenomenon_type": "behavior",
                            "domain": "strategic_management",
                            "description": "How organizations learn and adapt when facing competitive threats",
                            "section": "introduction",
                            "context": "Main focus of the study"
                        }]
                    },
                    description="Focused phenomenon extraction"
                )
            ]
        }
    
    def build_prompt(self, 
                    extraction_type: ExtractionType,
                    input_text: str,
                    task_description: str,
                    json_schema: Dict[str, Any],
                    rules: List[str],
                    paper_id: Optional[str] = None) -> str:
        """
        Build standardized prompt with consistent structure
        
        Args:
            extraction_type: Type of extraction
            input_text: Text to extract from
            task_description: Description of extraction task
            json_schema: Expected JSON output schema
            rules: List of extraction rules
            paper_id: Optional paper ID for context
        
        Returns:
            Complete prompt string
        """
        # Header
        prompt = f"""You are an expert research methodology analyst specializing in Strategic Management Journal papers.

TASK: {task_description}

"""
        
        # Input text
        prompt += f"""INPUT TEXT:
{input_text}

"""
        
        # Rules section
        prompt += "EXTRACTION RULES:\n"
        for i, rule in enumerate(rules, 1):
            prompt += f"{i}. {rule}\n"
        prompt += "\n"
        
        # Examples section (few-shot learning)
        if extraction_type in self.examples:
            prompt += "EXAMPLES:\n\n"
            for i, example in enumerate(self.examples[extraction_type][:3], 1):  # Use first 3 examples
                if example.description:
                    prompt += f"Example {i} ({example.description}):\n"
                else:
                    prompt += f"Example {i}:\n"
                prompt += f"Input: {example.input_text[:200]}...\n"
                prompt += f"Output: {self._format_json_example(example.output_json)}\n\n"
        
        # Output schema
        prompt += "OUTPUT FORMAT (JSON):\n"
        prompt += self._format_json_schema(json_schema)
        prompt += "\n"
        
        # Validation instructions
        prompt += """VALIDATION:
- Extract ONLY what is EXPLICITLY stated in the input text
- Use exact names/text as written - do NOT paraphrase or summarize
- If a field is not found, use null or [] as appropriate
- Return ONLY valid JSON (no markdown, no comments, no extra text)
- Ensure all required fields are present
"""
        
        return prompt
    
    def _format_json_example(self, json_obj: Dict[str, Any]) -> str:
        """Format JSON example for prompt"""
        import json
        return json.dumps(json_obj, indent=2, ensure_ascii=False)
    
    def _format_json_schema(self, schema: Dict[str, Any]) -> str:
        """Format JSON schema for prompt"""
        import json
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    def get_examples(self, extraction_type: ExtractionType) -> List[PromptExample]:
        """Get examples for a specific extraction type"""
        return self.examples.get(extraction_type, [])

# Global instance
_template = None

def get_prompt_template() -> StandardizedPromptTemplate:
    """Get singleton prompt template instance"""
    global _template
    if _template is None:
        _template = StandardizedPromptTemplate()
    return _template

