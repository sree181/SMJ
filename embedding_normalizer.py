#!/usr/bin/env python3
"""
Embedding-Based Entity Normalization System
Uses semantic similarity for robust entity resolution in SMJ literature analysis
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CanonicalEntity:
    """Canonical entity with metadata"""
    name: str
    entity_type: str  # Theory, Method, Phenomenon, Software
    aliases: List[str] = field(default_factory=list)
    domain: str = ""
    description: str = ""
    embedding: Optional[np.ndarray] = None
    usage_count: int = 0
    first_seen_year: Optional[int] = None
    papers: List[str] = field(default_factory=list)


@dataclass
class NormalizationResult:
    """Result of normalization attempt"""
    original: str
    normalized: str
    similarity: float
    method: str  # "exact", "dictionary", "embedding", "new"
    confidence: float
    alternatives: List[Tuple[str, float]] = field(default_factory=list)


class EmbeddingNormalizer:
    """
    Advanced entity normalizer using embeddings for semantic similarity
    Supports continuous learning from validated examples
    """

    # Comprehensive Strategic Management theory dictionary
    THEORY_DICTIONARY = {
        # Resource-Based View family
        "resource-based view": ["rbv", "resource based view", "resource-based theory", "rbt",
                                "resource based theory", "resource-based view (rbv)",
                                "the resource-based view", "barney's rbv"],
        "dynamic capabilities": ["dynamic capabilities theory", "dc", "dynamic capability",
                                "teece's dynamic capabilities", "dynamic capabilities framework"],
        "knowledge-based view": ["kbv", "knowledge based view", "knowledge-based theory"],

        # Organizational theories
        "institutional theory": ["neo-institutional theory", "institutional perspective",
                                "new institutionalism", "institutional isomorphism",
                                "dimaggio and powell", "institutional logic"],
        "transaction cost economics": ["tce", "transaction cost theory", "tct",
                                       "williamson's tce", "transaction costs"],
        "agency theory": ["principal-agent theory", "principal agent theory",
                         "agency perspective", "agency problem", "jensen and meckling"],
        "stakeholder theory": ["stakeholder perspective", "freeman's stakeholder theory",
                              "stakeholder management"],
        "upper echelons theory": ["uet", "upper echelons", "hambrick and mason",
                                 "top management team theory", "tmt theory"],

        # Behavioral theories
        "behavioral theory of the firm": ["btf", "cyert and march", "behavioral theory"],
        "organizational learning": ["organizational learning theory", "ol",
                                   "learning organization", "march's learning"],
        "absorptive capacity": ["acap", "cohen and levinthal", "absorptive capacity theory"],

        # Strategy theories
        "competitive advantage": ["porter's competitive advantage", "sustainable competitive advantage",
                                 "sca", "competitive positioning"],
        "five forces": ["porter's five forces", "industry forces", "five forces model",
                       "competitive forces"],
        "positioning theory": ["strategic positioning", "porter's positioning"],

        # Network and social theories
        "social network theory": ["network theory", "social networks", "network perspective"],
        "social capital theory": ["social capital", "relational capital"],
        "embeddedness": ["structural embeddedness", "relational embeddedness", "granovetter"],

        # Governance theories
        "corporate governance": ["governance theory", "board governance"],
        "stewardship theory": ["stewardship perspective"],

        # Evolution and ecology
        "organizational ecology": ["population ecology", "hannan and freeman",
                                  "ecological perspective"],
        "evolutionary theory": ["evolutionary economics", "nelson and winter"],

        # Attention and cognition
        "attention-based view": ["abv", "attention based view", "ocasio's abv"],
        "sensemaking": ["sensemaking theory", "weick's sensemaking"],
        "managerial cognition": ["cognitive perspective", "executive cognition"],

        # Economic theories
        "real options theory": ["real options", "strategic options"],
        "game theory": ["strategic games", "game theoretic"],
        "information economics": ["information asymmetry", "signaling theory"],

        # Other important theories
        "contingency theory": ["contingency perspective", "strategic contingency"],
        "configurational theory": ["configuration theory", "strategic configurations"],
        "imitation": ["mimetic isomorphism", "competitive imitation"],
        "legitimacy theory": ["organizational legitimacy", "legitimacy perspective"],
        "identity theory": ["organizational identity", "identity perspective"],
    }

    # Methodology dictionary
    METHOD_DICTIONARY = {
        # Regression methods
        "ordinary least squares": ["ols", "ols regression", "linear regression", "least squares"],
        "multiple regression": ["multivariate regression", "mreg"],
        "logistic regression": ["logit", "logit regression", "binary logistic"],
        "probit regression": ["probit", "probit model"],
        "tobit regression": ["tobit", "censored regression"],
        "poisson regression": ["poisson", "count regression"],
        "negative binomial regression": ["negative binomial", "negbin"],

        # Panel data methods
        "fixed effects": ["fe", "fixed effects regression", "within estimator",
                         "entity fixed effects", "firm fixed effects"],
        "random effects": ["re", "random effects model", "gls random effects"],
        "panel data analysis": ["panel regression", "longitudinal analysis"],
        "generalized method of moments": ["gmm", "dynamic gmm", "system gmm", "arellano-bond"],

        # Causal inference
        "difference-in-differences": ["did", "diff-in-diff", "difference in differences",
                                      "dd", "natural experiment"],
        "instrumental variables": ["iv", "2sls", "two-stage least squares", "iv regression"],
        "regression discontinuity": ["rdd", "rd design", "regression discontinuity design"],
        "propensity score matching": ["psm", "matching", "propensity matching"],
        "heckman selection": ["heckman", "selection model", "heckman correction"],

        # Structural models
        "structural equation modeling": ["sem", "structural equations", "lisrel", "amos sem"],
        "path analysis": ["path model", "path modeling"],
        "confirmatory factor analysis": ["cfa", "factor analysis"],
        "hierarchical linear modeling": ["hlm", "multilevel modeling", "mixed effects",
                                        "random coefficient", "multilevel regression"],

        # Survival and event
        "survival analysis": ["hazard model", "duration analysis", "time-to-event"],
        "cox proportional hazards": ["cox model", "cox regression", "proportional hazards"],
        "event study": ["event study methodology", "abnormal returns"],

        # Qualitative methods
        "case study": ["case study method", "single case", "multiple case study",
                      "comparative case study", "case analysis"],
        "grounded theory": ["grounded theory method", "gtm", "glaserian", "straussian"],
        "content analysis": ["qualitative content analysis", "text analysis"],
        "thematic analysis": ["theme analysis", "thematic coding"],
        "interviews": ["semi-structured interviews", "in-depth interviews", "qualitative interviews"],
        "ethnography": ["ethnographic study", "participant observation"],

        # Meta-analysis
        "meta-analysis": ["meta-analytic", "quantitative review", "hedges and olkin"],

        # Machine learning
        "machine learning": ["ml", "predictive modeling"],
        "random forest": ["rf", "ensemble trees"],
        "support vector machine": ["svm", "support vector"],
        "neural network": ["nn", "deep learning", "artificial neural network"],
        "natural language processing": ["nlp", "text mining", "computational linguistics"],
        "topic modeling": ["lda", "latent dirichlet allocation"],
    }

    # Software dictionary
    SOFTWARE_DICTIONARY = {
        "stata": ["stata 14", "stata 15", "stata 16", "stata 17", "statacorp"],
        "r": ["r statistical", "r studio", "rstudio", "r programming", "cran"],
        "python": ["python 3", "python programming", "anaconda"],
        "spss": ["ibm spss", "spss statistics", "pasw"],
        "sas": ["sas institute", "sas enterprise"],
        "matlab": ["mathworks matlab"],
        "mplus": ["mplus software", "muthen"],
        "amos": ["ibm amos", "amos graphics"],
        "lisrel": ["lisrel software"],
        "eviews": ["eviews software"],
        "nvivo": ["qsr nvivo", "nvivo qualitative"],
        "atlas.ti": ["atlas ti", "atlasti"],
        "maxqda": ["maxqda software"],
        "heckman": ["heckman model"],
    }

    def __init__(self,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.85,
                 cache_dir: Path = None):
        """
        Initialize the embedding normalizer

        Args:
            embedding_model: Sentence transformer model name
            similarity_threshold: Minimum similarity for automatic matching
            cache_dir: Directory to cache embeddings
        """
        self.similarity_threshold = similarity_threshold
        self.cache_dir = cache_dir or Path("normalization_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize embedding model
        self.model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(embedding_model)
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")

        # Build canonical entity databases
        self.canonical_entities: Dict[str, Dict[str, CanonicalEntity]] = {
            "Theory": {},
            "Method": {},
            "Software": {},
            "Phenomenon": {}
        }

        # Build lookup dictionaries (lowercase -> canonical)
        self.lookup_tables: Dict[str, Dict[str, str]] = {
            "Theory": {},
            "Method": {},
            "Software": {},
            "Phenomenon": {}
        }

        # Initialize from dictionaries
        self._build_canonical_database()

        # Embedding cache
        self.embedding_cache: Dict[str, np.ndarray] = {}

        # Load cached embeddings
        self._load_embedding_cache()

        # Statistics
        self.stats = {
            "exact_matches": 0,
            "dictionary_matches": 0,
            "embedding_matches": 0,
            "new_entities": 0,
            "total_normalizations": 0
        }

    def _build_canonical_database(self):
        """Build canonical entity database from dictionaries"""

        # Build theory database
        for canonical, aliases in self.THEORY_DICTIONARY.items():
            entity = CanonicalEntity(
                name=canonical.title(),
                entity_type="Theory",
                aliases=[a.lower() for a in aliases],
                domain="strategic_management"
            )
            self.canonical_entities["Theory"][canonical.lower()] = entity

            # Build lookup table
            self.lookup_tables["Theory"][canonical.lower()] = canonical.title()
            for alias in aliases:
                self.lookup_tables["Theory"][alias.lower()] = canonical.title()

        # Build method database
        for canonical, aliases in self.METHOD_DICTIONARY.items():
            entity = CanonicalEntity(
                name=canonical.title(),
                entity_type="Method",
                aliases=[a.lower() for a in aliases],
                domain="research_methodology"
            )
            self.canonical_entities["Method"][canonical.lower()] = entity

            self.lookup_tables["Method"][canonical.lower()] = canonical.title()
            for alias in aliases:
                self.lookup_tables["Method"][alias.lower()] = canonical.title()

        # Build software database
        for canonical, aliases in self.SOFTWARE_DICTIONARY.items():
            entity = CanonicalEntity(
                name=canonical.title() if len(canonical) > 2 else canonical.upper(),
                entity_type="Software",
                aliases=[a.lower() for a in aliases]
            )
            self.canonical_entities["Software"][canonical.lower()] = entity

            normalized_name = canonical.title() if len(canonical) > 2 else canonical.upper()
            self.lookup_tables["Software"][canonical.lower()] = normalized_name
            for alias in aliases:
                self.lookup_tables["Software"][alias.lower()] = normalized_name

        logger.info(f"Built canonical database: {len(self.canonical_entities['Theory'])} theories, "
                   f"{len(self.canonical_entities['Method'])} methods, "
                   f"{len(self.canonical_entities['Software'])} software")

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text, using cache if available"""
        if not self.model:
            return None

        cache_key = text.lower().strip()
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            self.embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    def _compute_all_canonical_embeddings(self, entity_type: str):
        """Pre-compute embeddings for all canonical entities of a type"""
        if not self.model:
            return

        for key, entity in self.canonical_entities[entity_type].items():
            if entity.embedding is None:
                # Create rich text representation
                text = f"{entity.name}"
                if entity.aliases:
                    text += f" ({', '.join(entity.aliases[:3])})"

                entity.embedding = self._get_embedding(text)

    def _find_by_embedding(self,
                           text: str,
                           entity_type: str,
                           threshold: float = None) -> Optional[Tuple[str, float]]:
        """Find most similar canonical entity by embedding"""
        if not self.model:
            return None

        threshold = threshold or self.similarity_threshold

        # Get embedding for input text
        query_embedding = self._get_embedding(text)
        if query_embedding is None:
            return None

        # Ensure canonical embeddings exist
        self._compute_all_canonical_embeddings(entity_type)

        # Find most similar
        best_match = None
        best_similarity = 0.0

        for key, entity in self.canonical_entities[entity_type].items():
            if entity.embedding is None:
                continue

            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                entity.embedding.reshape(1, -1)
            )[0][0]

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entity.name

        if best_similarity >= threshold:
            return (best_match, best_similarity)
        return None

    def normalize(self,
                  entity_name: str,
                  entity_type: str,
                  context: str = "") -> NormalizationResult:
        """
        Normalize an entity name to its canonical form

        Args:
            entity_name: Entity name to normalize
            entity_type: Type of entity (Theory, Method, Software, Phenomenon)
            context: Additional context for better matching

        Returns:
            NormalizationResult with normalized name and metadata
        """
        self.stats["total_normalizations"] += 1

        if not entity_name or not isinstance(entity_name, str):
            return NormalizationResult(
                original=str(entity_name) if entity_name else "",
                normalized="",
                similarity=0.0,
                method="invalid",
                confidence=0.0
            )

        # Clean input
        cleaned = self._clean_text(entity_name)
        cleaned_lower = cleaned.lower()

        # Step 1: Exact dictionary match (fastest)
        lookup_table = self.lookup_tables.get(entity_type, {})
        if cleaned_lower in lookup_table:
            self.stats["exact_matches"] += 1
            return NormalizationResult(
                original=entity_name,
                normalized=lookup_table[cleaned_lower],
                similarity=1.0,
                method="exact",
                confidence=1.0
            )

        # Step 2: Partial dictionary match
        for key, canonical in lookup_table.items():
            # Check if input starts with or ends with a known key
            if cleaned_lower.startswith(key + " ") or cleaned_lower.endswith(" " + key):
                self.stats["dictionary_matches"] += 1
                return NormalizationResult(
                    original=entity_name,
                    normalized=canonical,
                    similarity=0.95,
                    method="dictionary",
                    confidence=0.95
                )

            # Check if key is contained in input (for variations like "RBV (Resource-Based View)")
            if key in cleaned_lower and len(key) > 5:  # Avoid short matches
                self.stats["dictionary_matches"] += 1
                return NormalizationResult(
                    original=entity_name,
                    normalized=canonical,
                    similarity=0.9,
                    method="dictionary",
                    confidence=0.9
                )

        # Step 3: Embedding-based similarity match
        if self.model and entity_type in self.canonical_entities:
            result = self._find_by_embedding(cleaned, entity_type)
            if result:
                canonical, similarity = result
                self.stats["embedding_matches"] += 1

                # Find alternatives above a lower threshold
                alternatives = self._find_alternatives(cleaned, entity_type, top_k=3)

                return NormalizationResult(
                    original=entity_name,
                    normalized=canonical,
                    similarity=similarity,
                    method="embedding",
                    confidence=similarity,
                    alternatives=alternatives
                )

        # Step 4: No match found - return cleaned version as new entity
        self.stats["new_entities"] += 1
        return NormalizationResult(
            original=entity_name,
            normalized=cleaned,
            similarity=0.0,
            method="new",
            confidence=0.5  # Moderate confidence for new entities
        )

    def _find_alternatives(self,
                           text: str,
                           entity_type: str,
                           top_k: int = 3) -> List[Tuple[str, float]]:
        """Find top-k similar canonical entities"""
        if not self.model:
            return []

        query_embedding = self._get_embedding(text)
        if query_embedding is None:
            return []

        similarities = []
        for key, entity in self.canonical_entities[entity_type].items():
            if entity.embedding is not None:
                sim = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    entity.embedding.reshape(1, -1)
                )[0][0]
                similarities.append((entity.name, float(sim)))

        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _clean_text(self, text: str) -> str:
        """Clean entity text for matching"""
        if not text:
            return ""

        # Strip whitespace
        text = text.strip()

        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)

        # Normalize punctuation
        text = text.replace('–', '-')
        text = text.replace('—', '-')
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace(''', "'")
        text = text.replace(''', "'")

        # Title case, preserving acronyms
        words = text.split()
        normalized_words = []
        for word in words:
            if word.isupper() and len(word) <= 5:
                normalized_words.append(word)
            else:
                normalized_words.append(word.title())

        return ' '.join(normalized_words)

    def normalize_theory(self, theory_name: str, context: str = "") -> str:
        """Convenience method for theory normalization"""
        result = self.normalize(theory_name, "Theory", context)
        return result.normalized

    def normalize_method(self, method_name: str, context: str = "") -> str:
        """Convenience method for method normalization"""
        result = self.normalize(method_name, "Method", context)
        return result.normalized

    def normalize_software(self, software_name: str, context: str = "") -> str:
        """Convenience method for software normalization"""
        result = self.normalize(software_name, "Software", context)
        return result.normalized

    def normalize_phenomenon(self, phenomenon_name: str, context: str = "") -> str:
        """Convenience method for phenomenon normalization"""
        result = self.normalize(phenomenon_name, "Phenomenon", context)
        return result.normalized

    def add_canonical_entity(self,
                            name: str,
                            entity_type: str,
                            aliases: List[str] = None,
                            domain: str = "") -> bool:
        """
        Add a new canonical entity to the database

        Args:
            name: Canonical entity name
            entity_type: Entity type
            aliases: List of aliases
            domain: Domain/category

        Returns:
            True if added successfully
        """
        if entity_type not in self.canonical_entities:
            return False

        key = name.lower()
        if key in self.canonical_entities[entity_type]:
            # Update existing entity with new aliases
            existing = self.canonical_entities[entity_type][key]
            if aliases:
                existing.aliases.extend([a.lower() for a in aliases if a.lower() not in existing.aliases])
            return True

        # Create new entity
        entity = CanonicalEntity(
            name=name,
            entity_type=entity_type,
            aliases=[a.lower() for a in (aliases or [])],
            domain=domain
        )

        # Generate embedding
        if self.model:
            text = f"{name}"
            if aliases:
                text += f" ({', '.join(aliases[:3])})"
            entity.embedding = self._get_embedding(text)

        self.canonical_entities[entity_type][key] = entity

        # Update lookup table
        self.lookup_tables[entity_type][key] = name
        for alias in (aliases or []):
            self.lookup_tables[entity_type][alias.lower()] = name

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get normalization statistics"""
        total = self.stats["total_normalizations"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "exact_match_rate": self.stats["exact_matches"] / total * 100,
            "dictionary_match_rate": self.stats["dictionary_matches"] / total * 100,
            "embedding_match_rate": self.stats["embedding_matches"] / total * 100,
            "new_entity_rate": self.stats["new_entities"] / total * 100,
            "canonical_entities": {
                k: len(v) for k, v in self.canonical_entities.items()
            }
        }

    def _load_embedding_cache(self):
        """Load cached embeddings from disk"""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    self.embedding_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")

    def save_embedding_cache(self):
        """Save embedding cache to disk"""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self.embedding_cache, f)
            logger.info(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def export_canonical_database(self, output_path: Path):
        """Export canonical entity database to JSON"""
        export_data = {}
        for entity_type, entities in self.canonical_entities.items():
            export_data[entity_type] = {
                name: {
                    "name": entity.name,
                    "aliases": entity.aliases,
                    "domain": entity.domain,
                    "usage_count": entity.usage_count
                }
                for name, entity in entities.items()
            }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
        logger.info(f"Exported canonical database to {output_path}")


# Singleton instance
_embedding_normalizer = None


def get_embedding_normalizer() -> EmbeddingNormalizer:
    """Get singleton embedding normalizer instance"""
    global _embedding_normalizer
    if _embedding_normalizer is None:
        _embedding_normalizer = EmbeddingNormalizer()
    return _embedding_normalizer


if __name__ == "__main__":
    # Test the normalizer
    normalizer = get_embedding_normalizer()

    test_cases = [
        ("RBV", "Theory"),
        ("Resource-Based View (RBV)", "Theory"),
        ("resource based theory", "Theory"),
        ("Dynamic Capabilities Framework", "Theory"),
        ("OLS regression", "Method"),
        ("Fixed Effects Model", "Method"),
        ("Difference in Differences", "Method"),
        ("stata", "Software"),
        ("R statistical software", "Software"),
    ]

    print("\nNormalization Test Results:")
    print("-" * 80)
    for entity, entity_type in test_cases:
        result = normalizer.normalize(entity, entity_type)
        print(f"{entity:40} -> {result.normalized:30} ({result.method}, sim={result.similarity:.2f})")

    print("\nStatistics:")
    print(json.dumps(normalizer.get_statistics(), indent=2))
