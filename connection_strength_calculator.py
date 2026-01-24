#!/usr/bin/env python3
"""
Mathematical Connection Strength Calculator
Computes robust connection strength between theories and phenomena
using multiple factors and weighted scoring
"""

import re
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ConnectionStrengthCalculator:
    """
    Calculates connection strength between theories and phenomena
    using a multi-factor mathematical model
    """
    
    def __init__(self, use_embeddings: bool = False):
        """
        Initialize calculator
        
        Args:
            use_embeddings: Whether to use semantic embeddings for similarity
                           (requires sentence-transformers if True)
        """
        self.use_embeddings = use_embeddings
        self.embedding_model = None
        
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✓ Embedding model loaded for semantic similarity")
            except ImportError:
                logger.warning("sentence-transformers not available, using keyword-based only")
                self.use_embeddings = False
    
    def calculate_strength(self, 
                          theory: Dict[str, Any], 
                          phenomenon: Dict[str, Any],
                          paper_data: Optional[Dict[str, Any]] = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate connection strength between theory and phenomenon
        
        Args:
            theory: Theory data with role, section, usage_context, etc.
            phenomenon: Phenomenon data with section, context, description, etc.
            paper_data: Optional paper data for additional context
        
        Returns:
            Tuple of (connection_strength, factor_scores)
            - connection_strength: Final score (0.0-1.0)
            - factor_scores: Breakdown of individual factor scores
        """
        
        # Input validation
        if not theory or not isinstance(theory, dict):
            logger.warning("Invalid theory input: not a dictionary or None")
            return 0.0, {}
        
        if not phenomenon or not isinstance(phenomenon, dict):
            logger.warning("Invalid phenomenon input: not a dictionary or None")
            return 0.0, {}
        
        # Validate required fields
        if not theory.get("role") and not theory.get("usage_context"):
            logger.warning("Theory missing both role and usage_context")
            return 0.0, {}
        
        if not phenomenon.get("phenomenon_name"):
            logger.warning("Phenomenon missing name")
            return 0.0, {}
        
        # Ensure string fields are strings (not None)
        theory = {k: (v if v is not None else "") for k, v in theory.items()}
        phenomenon = {k: (v if v is not None else "") for k, v in phenomenon.items()}
        
        # Factor 1: Theory Role Weight (0.0-0.4)
        role_weight = self._calculate_role_weight(theory.get("role", "supporting"))
        
        # Factor 2: Section Overlap (0.0-0.2)
        section_score = self._calculate_section_overlap(
            theory.get("section", ""),
            phenomenon.get("section", "")
        )
        
        # Factor 3: Keyword Overlap (0.0-0.2)
        keyword_score = self._calculate_keyword_overlap(
            theory.get("usage_context", ""),
            phenomenon.get("context", ""),
            phenomenon.get("description", "")
        )
        
        # Factor 4: Semantic Similarity (0.0-0.2)
        semantic_score = 0.0
        if self.use_embeddings and self.embedding_model:
            semantic_score = self._calculate_semantic_similarity(
                theory.get("usage_context", ""),
                phenomenon.get("context", ""),
                phenomenon.get("description", "")
            )
        else:
            # Fallback: Use enhanced keyword matching
            semantic_score = self._calculate_enhanced_keyword_similarity(
                theory.get("usage_context", ""),
                phenomenon.get("context", ""),
                phenomenon.get("description", "")
            )
        
        # Factor 5: Explicit Mention (0.0-0.1 bonus)
        explicit_bonus = self._calculate_explicit_mention(
            theory.get("usage_context", ""),
            phenomenon.get("phenomenon_name", ""),
            phenomenon.get("description", "")
        )
        
        # Calculate weighted sum
        connection_strength = (
            role_weight +           # 0.0-0.4
            section_score +         # 0.0-0.2
            keyword_score +         # 0.0-0.2
            semantic_score +        # 0.0-0.2
            explicit_bonus          # 0.0-0.1
        )
        
        # Ensure strength is in valid range [0.0, 1.0]
        connection_strength = max(0.0, min(1.0, connection_strength))
        
        # Factor scores for debugging/transparency
        factor_scores = {
            "role_weight": role_weight,
            "section_score": section_score,
            "keyword_score": keyword_score,
            "semantic_score": semantic_score,
            "explicit_bonus": explicit_bonus,
            "total": connection_strength
        }
        
        return connection_strength, factor_scores
    
    def _calculate_role_weight(self, role: str) -> float:
        """
        Factor 1: Theory Role Weight (0.0-0.4)
        
        Primary theories get higher base weight because they're central to the paper
        """
        role_weights = {
            "primary": 0.4,      # Primary theory: 40% base weight
            "supporting": 0.2,   # Supporting theory: 20% base weight
            "extending": 0.15,   # Extending theory: 15% base weight
            "challenging": 0.1,  # Challenging theory: 10% base weight
        }
        return role_weights.get(role, 0.1)
    
    def _calculate_section_overlap(self, theory_section: str, phenomenon_section: str) -> float:
        """
        Factor 2: Section Overlap (0.0-0.2)
        
        Same section = stronger connection (theory and phenomenon appear together)
        """
        if not theory_section or not phenomenon_section:
            return 0.0
        
        if theory_section.lower() == phenomenon_section.lower():
            return 0.2  # Same section: 20% boost
        else:
            # Different sections: partial score based on proximity
            section_hierarchy = {
                "introduction": 1,
                "literature_review": 2,
                "methodology": 3,
                "results": 4,
                "discussion": 5
            }
            
            theory_pos = section_hierarchy.get(theory_section.lower(), 99)
            phenomenon_pos = section_hierarchy.get(phenomenon_section.lower(), 99)
            
            # Closer sections get higher score
            distance = abs(theory_pos - phenomenon_pos)
            if distance == 0:
                return 0.2
            elif distance == 1:
                return 0.1  # Adjacent sections
            else:
                return 0.05  # Distant sections
    
    def _calculate_keyword_overlap(self, 
                                   theory_context: str, 
                                   phenomenon_context: str,
                                   phenomenon_description: str) -> float:
        """
        Factor 3: Keyword Overlap (0.0-0.2)
        
        Counts shared meaningful words between theory usage and phenomenon context
        """
        if not theory_context or not (phenomenon_context or phenomenon_description):
            return 0.0
        
        # Combine phenomenon context and description
        phenomenon_text = f"{phenomenon_context} {phenomenon_description}".lower()
        theory_text = theory_context.lower()
        
        # Extract meaningful words (length > 3, not stopwords)
        stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                    'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were',
                    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                    'will', 'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that'}
        
        def extract_meaningful_words(text: str) -> set:
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            return set(w for w in words if w not in stopwords)
        
        theory_words = extract_meaningful_words(theory_text)
        phenomenon_words = extract_meaningful_words(phenomenon_text)
        
        if not theory_words or not phenomenon_words:
            return 0.0
        
        # Calculate Jaccard similarity (intersection / union)
        intersection = len(theory_words & phenomenon_words)
        union = len(theory_words | phenomenon_words)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Scale to 0.0-0.2 range
        # Jaccard similarity of 0.5+ = strong overlap (0.2)
        # Jaccard similarity of 0.2-0.5 = moderate (0.1)
        # Jaccard similarity < 0.2 = weak (0.05)
        if jaccard_similarity >= 0.5:
            return 0.2
        elif jaccard_similarity >= 0.2:
            return 0.1
        elif jaccard_similarity > 0:
            return 0.05
        else:
            return 0.0
    
    def _calculate_semantic_similarity(self,
                                      theory_context: str,
                                      phenomenon_context: str,
                                      phenomenon_description: str) -> float:
        """
        Factor 4: Semantic Similarity using Embeddings (0.0-0.2)
        
        Uses sentence transformers to compute cosine similarity
        """
        if not self.embedding_model:
            return 0.0
        
        try:
            # Combine phenomenon context and description
            phenomenon_text = f"{phenomenon_context} {phenomenon_description}".strip()
            
            if not theory_context or not phenomenon_text:
                return 0.0
            
            # Generate embeddings
            theory_embedding = self.embedding_model.encode(theory_context, convert_to_tensor=True)
            phenomenon_embedding = self.embedding_model.encode(phenomenon_text, convert_to_tensor=True)
            
            # Calculate cosine similarity
            from torch.nn.functional import cosine_similarity
            similarity = cosine_similarity(theory_embedding.unsqueeze(0), 
                                         phenomenon_embedding.unsqueeze(0)).item()
            
            # Cosine similarity ranges from -1 to 1, but for text it's usually 0 to 1
            # Scale to 0.0-0.2 range
            # Similarity > 0.7 = very similar (0.2)
            # Similarity 0.5-0.7 = similar (0.15)
            # Similarity 0.3-0.5 = somewhat similar (0.1)
            # Similarity < 0.3 = not similar (0.05 or 0.0)
            if similarity >= 0.7:
                return 0.2
            elif similarity >= 0.5:
                return 0.15
            elif similarity >= 0.3:
                return 0.1
            elif similarity >= 0.1:
                return 0.05
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _calculate_enhanced_keyword_similarity(self,
                                              theory_context: str,
                                              phenomenon_context: str,
                                              phenomenon_description: str) -> float:
        """
        Factor 4 (Fallback): Enhanced Keyword Similarity (0.0-0.2)
        
        More sophisticated keyword matching when embeddings not available
        """
        if not theory_context or not (phenomenon_context or phenomenon_description):
            return 0.0
        
        phenomenon_text = f"{phenomenon_context} {phenomenon_description}".lower()
        theory_text = theory_context.lower()
        
        # Extract n-grams (1-3 word phrases) for better matching
        def extract_ngrams(text: str, n: int = 2) -> set:
            words = text.split()
            ngrams = set()
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                if len(ngram) > 5:  # Only meaningful phrases
                    ngrams.add(ngram)
            return ngrams
        
        # Extract bigrams and trigrams
        theory_bigrams = extract_ngrams(theory_text, 2)
        theory_trigrams = extract_ngrams(theory_text, 3)
        phenomenon_bigrams = extract_ngrams(phenomenon_text, 2)
        phenomenon_trigrams = extract_ngrams(phenomenon_text, 3)
        
        # Calculate overlap
        bigram_overlap = len(theory_bigrams & phenomenon_bigrams)
        trigram_overlap = len(theory_trigrams & phenomenon_trigrams)
        
        # Weighted score: trigrams worth more (more specific)
        total_overlap = bigram_overlap * 0.5 + trigram_overlap * 1.0
        
        # Scale to 0.0-0.2
        if total_overlap >= 3:
            return 0.2
        elif total_overlap >= 2:
            return 0.15
        elif total_overlap >= 1:
            return 0.1
        else:
            return 0.05 if total_overlap > 0 else 0.0
    
    def _calculate_explicit_mention(self,
                                   theory_context: str,
                                   phenomenon_name: str,
                                   phenomenon_description: str) -> float:
        """
        Factor 5: Explicit Mention Bonus (0.0-0.1)
        
        Checks if theory context explicitly mentions phenomenon name or key terms
        """
        if not theory_context or not phenomenon_name:
            return 0.0
        
        theory_lower = theory_context.lower()
        phenomenon_lower = phenomenon_name.lower()
        
        # Check for exact phrase match (strongest signal)
        if phenomenon_lower in theory_lower:
            return 0.1  # Explicit mention: 10% bonus
        
        # Check for key words from phenomenon name
        phenomenon_words = [w for w in phenomenon_lower.split() if len(w) > 4]
        matches = sum(1 for word in phenomenon_words if word in theory_lower)
        
        if len(phenomenon_words) == 0:
            return 0.0
        
        # If most words from phenomenon name appear in theory context
        match_ratio = matches / len(phenomenon_words)
        if match_ratio >= 0.8:
            return 0.08  # Strong mention
        elif match_ratio >= 0.5:
            return 0.05  # Moderate mention
        else:
            return 0.0
    
    def should_create_connection(self, 
                                connection_strength: float,
                                threshold: float = 0.3) -> bool:
        """
        Determine if connection should be created based on strength threshold
        
        Args:
            connection_strength: Calculated strength (0.0-1.0)
            threshold: Minimum strength to create connection (default: 0.3)
        
        Returns:
            True if connection should be created
        """
        return connection_strength >= threshold

# Global instance
_calculator = None

def get_strength_calculator(use_embeddings: bool = False) -> ConnectionStrengthCalculator:
    """Get singleton calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = ConnectionStrengthCalculator(use_embeddings=use_embeddings)
    return _calculator

