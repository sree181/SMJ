#!/usr/bin/env python3
"""
Entity Normalization Module
Normalizes entity names to canonical forms to prevent duplicates
Based on Neo4j best practices for entity resolution

Enhanced with embedding-based similarity matching for unknown variations.
"""

import re
import logging
from typing import Dict, Optional, Tuple, List
from difflib import SequenceMatcher
import numpy as np

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for embedding-based matching
_EMBEDDING_MODEL = None
_EMBEDDINGS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    _EMBEDDINGS_AVAILABLE = True
except ImportError:
    pass


def _get_embedding_model():
    """Lazy load embedding model"""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None and _EMBEDDINGS_AVAILABLE:
        try:
            _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded embedding model for entity normalization")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
    return _EMBEDDING_MODEL

class EntityNormalizer:
    """
    Normalizes entity names to canonical forms
    Prevents duplicate nodes for same entities with different names
    """
    
    def __init__(self, use_embeddings: bool = True):
        """
        Initialize normalizer

        Args:
            use_embeddings: Whether to use embedding-based similarity for unknown entities
        """
        self.use_embeddings = use_embeddings and _EMBEDDINGS_AVAILABLE
        self._embedding_cache = {}  # Cache for entity embeddings

        # Comprehensive theory normalization mappings
        self.theory_mappings = {
            # Resource-Based View family
            "rbv": "Resource-Based View",
            "resource based view": "Resource-Based View",
            "resource-based view (rbv)": "Resource-Based View",
            "resource-based theory": "Resource-Based View",
            "rbt": "Resource-Based View",
            "resource based theory": "Resource-Based View",
            "barney's rbv": "Resource-Based View",

            # Dynamic Capabilities
            "dynamic capabilities": "Dynamic Capabilities Theory",
            "dynamic capabilities theory": "Dynamic Capabilities Theory",
            "dynamic capability": "Dynamic Capabilities Theory",
            "dynamic capability theory": "Dynamic Capabilities Theory",
            "dc": "Dynamic Capabilities Theory",
            "teece's dynamic capabilities": "Dynamic Capabilities Theory",

            # Knowledge-Based View
            "kbv": "Knowledge-Based View",
            "knowledge based view": "Knowledge-Based View",
            "knowledge-based theory": "Knowledge-Based View",

            # Upper Echelons Theory
            "uet": "Upper Echelons Theory",
            "upper echelons": "Upper Echelons Theory",
            "upper echelons theory (uet)": "Upper Echelons Theory",
            "hambrick and mason": "Upper Echelons Theory",
            "tmt theory": "Upper Echelons Theory",

            # Institutional Theory
            "institutional theory": "Institutional Theory",
            "neo-institutional theory": "Institutional Theory",
            "neo institutional theory": "Institutional Theory",
            "institutional isomorphism": "Institutional Theory",
            "dimaggio and powell": "Institutional Theory",
            "institutional logic": "Institutional Theory",

            # Agency Theory
            "agency theory": "Agency Theory",
            "principal-agent theory": "Agency Theory",
            "principal agent theory": "Agency Theory",
            "agency perspective": "Agency Theory",
            "jensen and meckling": "Agency Theory",

            # Transaction Cost Economics
            "tce": "Transaction Cost Economics",
            "transaction cost economics": "Transaction Cost Economics",
            "transaction cost theory": "Transaction Cost Economics",
            "tct": "Transaction Cost Economics",
            "williamson's tce": "Transaction Cost Economics",

            # Organizational Learning
            "organizational learning": "Organizational Learning Theory",
            "organizational learning theory": "Organizational Learning Theory",
            "ol": "Organizational Learning Theory",
            "learning organization": "Organizational Learning Theory",

            # Absorptive Capacity
            "absorptive capacity": "Absorptive Capacity",
            "acap": "Absorptive Capacity",
            "cohen and levinthal": "Absorptive Capacity",

            # Stakeholder Theory
            "stakeholder theory": "Stakeholder Theory",
            "stakeholder perspective": "Stakeholder Theory",
            "freeman's stakeholder theory": "Stakeholder Theory",

            # Contingency Theory
            "contingency theory": "Contingency Theory",
            "contingency perspective": "Contingency Theory",
            "strategic contingency": "Contingency Theory",

            # Behavioral Theory
            "behavioral theory of the firm": "Behavioral Theory of the Firm",
            "btf": "Behavioral Theory of the Firm",
            "cyert and march": "Behavioral Theory of the Firm",

            # Social Network Theory
            "social network theory": "Social Network Theory",
            "network theory": "Social Network Theory",
            "network perspective": "Social Network Theory",

            # Social Capital
            "social capital theory": "Social Capital Theory",
            "social capital": "Social Capital Theory",

            # Organizational Ecology
            "organizational ecology": "Organizational Ecology",
            "population ecology": "Organizational Ecology",
            "hannan and freeman": "Organizational Ecology",

            # Attention-Based View
            "attention-based view": "Attention-Based View",
            "abv": "Attention-Based View",
            "ocasio's abv": "Attention-Based View",

            # Sensemaking
            "sensemaking": "Sensemaking Theory",
            "sensemaking theory": "Sensemaking Theory",
            "weick's sensemaking": "Sensemaking Theory",

            # Real Options
            "real options theory": "Real Options Theory",
            "real options": "Real Options Theory",

            # Game Theory
            "game theory": "Game Theory",
            "strategic games": "Game Theory",

            # Signaling Theory
            "signaling theory": "Signaling Theory",
            "signal theory": "Signaling Theory",

            # Legitimacy
            "legitimacy theory": "Legitimacy Theory",
            "organizational legitimacy": "Legitimacy Theory",

            # Stewardship
            "stewardship theory": "Stewardship Theory",
            "stewardship perspective": "Stewardship Theory",
        }
        
        # Comprehensive method normalization mappings
        self.method_mappings = {
            # Regression variations
            "ols": "Ordinary Least Squares",
            "ols regression": "Ordinary Least Squares",
            "linear regression": "Ordinary Least Squares",
            "least squares": "Ordinary Least Squares",
            "multiple regression": "Multiple Regression",
            "multivariate regression": "Multiple Regression",
            "logistic regression": "Logistic Regression",
            "logit": "Logistic Regression",
            "logit regression": "Logistic Regression",
            "probit": "Probit Regression",
            "probit regression": "Probit Regression",
            "poisson regression": "Poisson Regression",
            "negative binomial": "Negative Binomial Regression",
            "negbin": "Negative Binomial Regression",
            "tobit": "Tobit Regression",
            "tobit regression": "Tobit Regression",

            # Panel data methods
            "fixed effects": "Fixed Effects Regression",
            "fe": "Fixed Effects Regression",
            "fixed effects regression": "Fixed Effects Regression",
            "firm fixed effects": "Fixed Effects Regression",
            "random effects": "Random Effects Regression",
            "re": "Random Effects Regression",
            "gls": "Generalized Least Squares",
            "panel data": "Panel Data Analysis",
            "panel regression": "Panel Data Analysis",
            "longitudinal analysis": "Panel Data Analysis",

            # GMM and dynamic models
            "gmm": "Generalized Method of Moments",
            "generalized method of moments": "Generalized Method of Moments",
            "system gmm": "Generalized Method of Moments",
            "dynamic gmm": "Generalized Method of Moments",
            "arellano-bond": "Generalized Method of Moments",

            # Causal inference
            "did": "Difference-in-Differences",
            "difference in differences": "Difference-in-Differences",
            "diff-in-diff": "Difference-in-Differences",
            "dd": "Difference-in-Differences",
            "natural experiment": "Natural Experiment",

            # Instrumental variables
            "iv": "Instrumental Variables",
            "instrumental variables": "Instrumental Variables",
            "iv regression": "Instrumental Variables",
            "2sls": "Two-Stage Least Squares",
            "two-stage least squares": "Two-Stage Least Squares",
            "tsls": "Two-Stage Least Squares",

            # Selection models
            "heckman": "Heckman Selection Model",
            "heckman selection": "Heckman Selection Model",
            "selection model": "Heckman Selection Model",
            "propensity score matching": "Propensity Score Matching",
            "psm": "Propensity Score Matching",
            "matching": "Propensity Score Matching",

            # Regression discontinuity
            "rdd": "Regression Discontinuity",
            "regression discontinuity": "Regression Discontinuity",
            "rd design": "Regression Discontinuity",

            # Structural equation modeling
            "sem": "Structural Equation Modeling",
            "structural equation modeling": "Structural Equation Modeling",
            "structural equations": "Structural Equation Modeling",
            "path analysis": "Path Analysis",
            "path modeling": "Path Analysis",
            "cfa": "Confirmatory Factor Analysis",
            "confirmatory factor analysis": "Confirmatory Factor Analysis",

            # Multilevel
            "hlm": "Hierarchical Linear Modeling",
            "hierarchical linear modeling": "Hierarchical Linear Modeling",
            "multilevel modeling": "Hierarchical Linear Modeling",
            "mixed effects": "Hierarchical Linear Modeling",
            "random coefficient": "Hierarchical Linear Modeling",

            # Survival analysis
            "survival analysis": "Survival Analysis",
            "hazard model": "Survival Analysis",
            "duration analysis": "Survival Analysis",
            "cox": "Cox Proportional Hazards",
            "cox regression": "Cox Proportional Hazards",
            "cox proportional hazards": "Cox Proportional Hazards",
            "event history analysis": "Event History Analysis",

            # Event study
            "event study": "Event Study",
            "event study methodology": "Event Study",
            "abnormal returns": "Event Study",

            # Qualitative methods
            "case study": "Case Study",
            "case study method": "Case Study",
            "single case": "Case Study",
            "multiple case study": "Multiple Case Study",
            "comparative case study": "Multiple Case Study",
            "grounded theory": "Grounded Theory",
            "grounded theory method": "Grounded Theory",
            "gtm": "Grounded Theory",
            "content analysis": "Content Analysis",
            "qualitative content analysis": "Content Analysis",
            "thematic analysis": "Thematic Analysis",
            "theme analysis": "Thematic Analysis",
            "interviews": "Interviews",
            "semi-structured interviews": "Interviews",
            "in-depth interviews": "Interviews",
            "ethnography": "Ethnography",
            "ethnographic study": "Ethnography",
            "participant observation": "Ethnography",

            # Meta-analysis
            "meta-analysis": "Meta-Analysis",
            "meta-analytic": "Meta-Analysis",
            "quantitative review": "Meta-Analysis",

            # Machine learning
            "machine learning": "Machine Learning",
            "ml": "Machine Learning",
            "random forest": "Random Forest",
            "rf": "Random Forest",
            "svm": "Support Vector Machine",
            "support vector machine": "Support Vector Machine",
            "neural network": "Neural Network",
            "nn": "Neural Network",
            "deep learning": "Neural Network",
            "xgboost": "XGBoost",
            "gradient boosting": "Gradient Boosting",

            # Text analysis
            "nlp": "Natural Language Processing",
            "natural language processing": "Natural Language Processing",
            "text mining": "Natural Language Processing",
            "topic modeling": "Topic Modeling",
            "lda": "Topic Modeling",
            "latent dirichlet allocation": "Topic Modeling",

            # Survey
            "survey": "Survey Research",
            "survey methodology": "Survey Research",
            "questionnaire": "Survey Research",
        }
        
        # Software normalization
        self.software_mappings = {
            "stata": "Stata",
            "r": "R",
            "r studio": "R",
            "rstudio": "R",
            "python": "Python",
            "spss": "SPSS",
            "sas": "SAS",
            "matlab": "MATLAB",
            "mplus": "Mplus",
            "amos": "AMOS",
        }
    
    def normalize_theory(self, theory_name: str) -> str:
        """Normalize theory name to canonical form"""
        if not theory_name or not isinstance(theory_name, str):
            return ""
        
        # Clean and lowercase for matching
        cleaned = self._clean_name(theory_name)
        lower_cleaned = cleaned.lower()
        
        # Remove common suffixes/prefixes for matching
        # e.g., "Dynamic Capabilities Theory" -> "Dynamic Capabilities"
        normalized_for_matching = lower_cleaned
        if normalized_for_matching.endswith(" theory"):
            normalized_for_matching = normalized_for_matching[:-7].strip()
        if normalized_for_matching.endswith(" framework"):
            normalized_for_matching = normalized_for_matching[:-10].strip()
        if normalized_for_matching.endswith(" perspective"):
            normalized_for_matching = normalized_for_matching[:-12].strip()
        
        # Check exact mappings (both original and normalized)
        if lower_cleaned in self.theory_mappings:
            return self.theory_mappings[lower_cleaned]
        if normalized_for_matching in self.theory_mappings:
            return self.theory_mappings[normalized_for_matching]
        
        # Check partial matches (e.g., "Resource-Based View" in "Resource-Based View (RBV)")
        # But be careful: only match if it's a direct variation, not a substring in a longer name
        for key, canonical in self.theory_mappings.items():
            # Direct match: key equals cleaned name (exact)
            if key == lower_cleaned or key == normalized_for_matching:
                return canonical
            
            # Check if cleaned name starts with key + space/parenthesis (e.g., "Resource-Based View (RBV)")
            # This catches variations like "Resource-Based View (RBV)" but not "Adner's Resource-Based View"
            if lower_cleaned.startswith(key + " ") or lower_cleaned.startswith(key + "("):
                return canonical
            
            # Check if key starts with cleaned name + space/parenthesis (reverse)
            if key.startswith(lower_cleaned + " ") or key.startswith(lower_cleaned + "("):
                return canonical
            
            # Check normalized version with same logic
            if normalized_for_matching.startswith(key + " ") or normalized_for_matching.startswith(key + "("):
                return canonical
            if key.startswith(normalized_for_matching + " ") or key.startswith(normalized_for_matching + "("):
                return canonical
        
        # Special handling for RBV variations (only if it's a direct variation)
        # Check if it's exactly "rbv" or starts with "rbv" followed by space/parenthesis
        if lower_cleaned == "rbv":
            return "Resource-Based View"
        if lower_cleaned.startswith("rbv ") or lower_cleaned.startswith("rbv("):
            if "resource" in lower_cleaned or "based" in lower_cleaned:
                return "Resource-Based View"
        # Check if it's "Resource-Based View" with RBV in parentheses
        if "resource" in lower_cleaned and "based" in lower_cleaned and "rbv" in lower_cleaned:
            # Make sure it's not a longer theory name
            if len(lower_cleaned) < 50:  # Reasonable length for RBV variations
                return "Resource-Based View"
        
        # Special handling for Dynamic Capabilities variations (only direct variations)
        # Only match if it's exactly "dynamic capabilities" or starts with it
        if lower_cleaned == "dynamic capabilities" or lower_cleaned == "dynamic capabilities theory":
            return "Dynamic Capabilities Theory"
        if lower_cleaned.startswith("dynamic capabilities ") or lower_cleaned.startswith("dynamic capabilities("):
            # Only if it's a short variation (not a long specific theory name)
            if len(lower_cleaned) < 60:  # Reasonable length for DC variations
                return "Dynamic Capabilities Theory"
        
        # If no match, return cleaned original (title case)
        return cleaned
    
    def normalize_method(self, method_name: str) -> str:
        """Normalize method name to canonical form"""
        if not method_name or not isinstance(method_name, str):
            return ""
        
        cleaned = self._clean_name(method_name)
        lower_cleaned = cleaned.lower()
        
        # Check exact mappings
        if lower_cleaned in self.method_mappings:
            return self.method_mappings[lower_cleaned]
        
        # Check partial matches
        for key, canonical in self.method_mappings.items():
            if key in lower_cleaned or lower_cleaned in key:
                return canonical
        
        # If no match, return cleaned original
        return cleaned
    
    def normalize_software(self, software_name: str) -> str:
        """Normalize software name to canonical form"""
        if not software_name or not isinstance(software_name, str):
            return ""
        
        cleaned = self._clean_name(software_name)
        lower_cleaned = cleaned.lower()
        
        # Check exact mappings
        if lower_cleaned in self.software_mappings:
            return self.software_mappings[lower_cleaned]
        
        # Check partial matches
        for key, canonical in self.software_mappings.items():
            if key in lower_cleaned:
                return canonical
        
        return cleaned
    
    def normalize_variable(self, variable_name: str) -> str:
        """Normalize variable name (less aggressive, preserve specificity)"""
        if not variable_name or not isinstance(variable_name, str):
            return ""
        
        # Just clean, don't map (variables are more specific)
        return self._clean_name(variable_name)
    
    def normalize_phenomenon(self, phenomenon_name: str) -> str:
        """
        Normalize phenomenon name to canonical form
        Phenomena are more specific than theories, so normalization is conservative
        """
        if not phenomenon_name or not isinstance(phenomenon_name, str):
            return ""
        
        # Clean the name
        cleaned = self._clean_name(phenomenon_name)
        lower_cleaned = cleaned.lower()
        
        # Remove common suffixes that don't change meaning
        # e.g., "Resource allocation patterns" -> "Resource allocation"
        # But be conservative - only remove if it's clearly a generic suffix
        normalized = cleaned
        
        # Remove trailing "patterns" or "variations" if they're generic
        # But keep if they're part of the phenomenon name (e.g., "Pattern recognition")
        if lower_cleaned.endswith(" patterns") and len(lower_cleaned) > 15:
            # Only remove if it's clearly a suffix (not part of core name)
            normalized = re.sub(r'\s+patterns$', '', normalized, flags=re.IGNORECASE)
        if lower_cleaned.endswith(" variations") and len(lower_cleaned) > 15:
            normalized = re.sub(r'\s+variations$', '', normalized, flags=re.IGNORECASE)
        
        # Remove common location/context suffixes that are often redundant
        # e.g., "Economic nationalism in court rulings" -> "Economic nationalism"
        # But only if the suffix is clearly a context descriptor
        normalized = re.sub(r'\s+in\s+(court|legal|regulatory|judicial|administrative).*$', '', 
                           normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+during\s+(financial|economic|market).*$', '', 
                           normalized, flags=re.IGNORECASE)
        
        # Normalize whitespace again after removals
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # If normalization removed too much (less than 3 words), keep original
        if len(normalized.split()) < 3 and len(cleaned.split()) >= 3:
            normalized = cleaned
        
        return normalized
    
    def _clean_name(self, name: str) -> str:
        """Clean entity name: remove extra whitespace, normalize punctuation"""
        if not name:
            return ""
        
        # Remove leading/trailing whitespace
        name = name.strip()
        
        # Normalize multiple spaces to single space
        name = re.sub(r'\s+', ' ', name)
        
        # Normalize common punctuation variations
        name = name.replace('–', '-')  # En dash to hyphen
        name = name.replace('—', '-')  # Em dash to hyphen
        name = name.replace('"', '"')  # Smart quotes
        name = name.replace('"', '"')
        name = name.replace(''', "'")
        name = name.replace(''', "'")
        
        # Title case for theories and methods (preserve acronyms)
        # Split on spaces, capitalize each word, but preserve all-caps words
        words = name.split()
        normalized_words = []
        for word in words:
            if word.isupper() and len(word) <= 5:  # Likely acronym
                normalized_words.append(word)
            else:
                normalized_words.append(word.title())
        
        return ' '.join(normalized_words)
    
    def find_similar_entities(self, entity_name: str, entity_type: str, threshold: float = 0.85) -> Optional[str]:
        """
        Find similar entities using string similarity
        Returns canonical name if similarity > threshold, else None
        
        NOTE: For production, this should be enhanced with embeddings
        See: neo4j_best_practices_implementation.py for embedding-based similarity
        """
        if entity_type == "Theory":
            mappings = self.theory_mappings
            normalize_func = self.normalize_theory
        elif entity_type == "Method":
            mappings = self.method_mappings
            normalize_func = self.normalize_method
        elif entity_type == "Software":
            mappings = self.software_mappings
            normalize_func = self.normalize_software
        else:
            return None
        
        normalized = normalize_func(entity_name)
        if normalized != entity_name:
            return normalized
        
        # Check similarity with existing mappings
        entity_lower = entity_name.lower()
        best_match = None
        best_similarity = 0.0
        
        for key, canonical in mappings.items():
            similarity = SequenceMatcher(None, entity_lower, key).ratio()
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = canonical
        
        return best_match if best_match else None
    
    def normalize_with_embeddings(self, entity_name: str, entity_type: str, 
                                   embedding_similarity_func=None) -> str:
        """
        Hybrid normalization: String matching + Embeddings
        
        Args:
            entity_name: Entity name to normalize
            entity_type: Type of entity (Theory, Method, etc.)
            embedding_similarity_func: Function to find similar entities via embeddings
                                      Should return (canonical_name, similarity) or None
        
        Returns:
            Normalized canonical name
        """
        # Step 1: Try exact string matching (fast, deterministic)
        normalized = None
        if entity_type == "Theory":
            normalized = self.normalize_theory(entity_name)
        elif entity_type == "Method":
            normalized = self.normalize_method(entity_name)
        elif entity_type == "Software":
            normalized = self.normalize_software(entity_name)
        
        if normalized and normalized != entity_name:
            return normalized  # Found in dictionary
        
        # Step 2: Try embedding-based similarity (catches unknown variations)
        if embedding_similarity_func:
            similar_entity = embedding_similarity_func(entity_name, entity_type, threshold=0.85)
            if similar_entity:
                return similar_entity  # Found similar entity via embedding
        
        # Step 3: Return cleaned original (new entity, not in dictionary)
        return self._clean_name(entity_name)

# Global instance
_normalizer = None

def get_normalizer() -> EntityNormalizer:
    """Get singleton normalizer instance"""
    global _normalizer
    if _normalizer is None:
        _normalizer = EntityNormalizer()
    return _normalizer

