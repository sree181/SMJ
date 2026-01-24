#!/usr/bin/env python3
"""
Conflict Resolution System
Resolves conflicts when re-extracting entities (e.g., same entity extracted differently)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    HIGHEST_CONFIDENCE = "highest_confidence"  # Prefer higher confidence
    MOST_RECENT = "most_recent"  # Prefer more recent extraction
    MERGE = "merge"  # Merge compatible fields
    MANUAL_REVIEW = "manual_review"  # Flag for manual review

class ConflictResolver:
    """Resolves conflicts between existing and new extractions"""
    
    def __init__(self, default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.HIGHEST_CONFIDENCE):
        self.default_strategy = default_strategy
    
    def resolve_conflict(self, 
                        existing_entity: Dict[str, Any],
                        new_entity: Dict[str, Any],
                        entity_type: str,
                        strategy: Optional[ConflictResolutionStrategy] = None) -> Tuple[Dict[str, Any], str]:
        """
        Resolve conflict between existing and new entity
        
        Args:
            existing_entity: Existing entity in database
            new_entity: Newly extracted entity
            entity_type: Type of entity (theory, method, etc.)
            strategy: Resolution strategy (uses default if None)
        
        Returns:
            Tuple of (resolved_entity, resolution_reason)
        """
        strategy = strategy or self.default_strategy
        
        # Check if entities are actually different
        if self._are_identical(existing_entity, new_entity, entity_type):
            return existing_entity, "identical"
        
        # Check if entities are compatible (can be merged)
        if strategy == ConflictResolutionStrategy.MERGE:
            if self._are_compatible(existing_entity, new_entity, entity_type):
                merged = self._merge_entities(existing_entity, new_entity, entity_type)
                return merged, "merged"
        
        # Apply resolution strategy
        if strategy == ConflictResolutionStrategy.HIGHEST_CONFIDENCE:
            return self._resolve_by_confidence(existing_entity, new_entity, entity_type)
        elif strategy == ConflictResolutionStrategy.MOST_RECENT:
            return self._resolve_by_recency(existing_entity, new_entity, entity_type)
        elif strategy == ConflictResolutionStrategy.MANUAL_REVIEW:
            return self._flag_for_review(existing_entity, new_entity, entity_type)
        else:
            # Default: highest confidence
            return self._resolve_by_confidence(existing_entity, new_entity, entity_type)
    
    def _are_identical(self, entity1: Dict[str, Any], entity2: Dict[str, Any], 
                      entity_type: str) -> bool:
        """Check if two entities are identical"""
        # Get primary identifier based on type
        if entity_type == "theory":
            name1 = entity1.get("theory_name", "").lower().strip()
            name2 = entity2.get("theory_name", "").lower().strip()
        elif entity_type == "method":
            name1 = f"{entity1.get('method_name', '')}_{entity1.get('method_type', '')}".lower()
            name2 = f"{entity2.get('method_name', '')}_{entity2.get('method_type', '')}".lower()
        else:
            # Generic comparison
            name1 = str(entity1.get("name", "")).lower().strip()
            name2 = str(entity2.get("name", "")).lower().strip()
        
        return name1 == name2 and name1 != ""
    
    def _are_compatible(self, entity1: Dict[str, Any], entity2: Dict[str, Any],
                       entity_type: str) -> bool:
        """Check if two entities are compatible (can be merged)"""
        # Same name but different metadata
        if not self._are_identical(entity1, entity2, entity_type):
            return False
        
        # Check if fields are compatible (not contradictory)
        conflicting_fields = []
        
        if entity_type == "theory":
            # Role can differ (primary vs supporting is OK to merge)
            # But description should not contradict
            desc1 = entity1.get("description", "").lower()
            desc2 = entity2.get("description", "").lower()
            if desc1 and desc2 and desc1 != desc2:
                # Check if descriptions are similar (not contradictory)
                if not self._similar_text(desc1, desc2, threshold=0.7):
                    conflicting_fields.append("description")
        elif entity_type == "method":
            # Method type must match
            if entity1.get("method_type") != entity2.get("method_type"):
                conflicting_fields.append("method_type")
        
        return len(conflicting_fields) == 0
    
    def _merge_entities(self, entity1: Dict[str, Any], entity2: Dict[str, Any],
                       entity_type: str) -> Dict[str, Any]:
        """Merge two compatible entities"""
        merged = entity1.copy()
        
        # Prefer non-null values from new entity
        for key, value in entity2.items():
            if value is not None and value != "":
                if key not in merged or merged[key] is None or merged[key] == "":
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged.get(key), list):
                    # Merge lists (unique values)
                    merged[key] = list(set(merged[key] + value))
        
        # Update confidence to average
        conf1 = entity1.get("confidence", 0.5)
        conf2 = entity2.get("confidence", 0.5)
        merged["confidence"] = (conf1 + conf2) / 2
        
        # Update timestamp
        merged["updated_at"] = datetime.now().isoformat()
        merged["merge_count"] = merged.get("merge_count", 0) + 1
        
        return merged
    
    def _resolve_by_confidence(self, entity1: Dict[str, Any], entity2: Dict[str, Any],
                               entity_type: str) -> Tuple[Dict[str, Any], str]:
        """Resolve by choosing entity with higher confidence"""
        conf1 = entity1.get("confidence", 0.5)
        conf2 = entity2.get("confidence", 0.5)
        
        if conf2 > conf1:
            return entity2, f"new_entity_higher_confidence ({conf2:.2f} > {conf1:.2f})"
        else:
            return entity1, f"existing_entity_higher_confidence ({conf1:.2f} >= {conf2:.2f})"
    
    def _resolve_by_recency(self, entity1: Dict[str, Any], entity2: Dict[str, Any],
                            entity_type: str) -> Tuple[Dict[str, Any], str]:
        """Resolve by choosing more recent entity"""
        time1 = entity1.get("extracted_at") or entity1.get("created_at", "")
        time2 = entity2.get("extracted_at") or entity2.get("created_at", datetime.now().isoformat())
        
        try:
            dt1 = datetime.fromisoformat(time1) if time1 else datetime.min
            dt2 = datetime.fromisoformat(time2) if time2 else datetime.now()
            
            if dt2 > dt1:
                return entity2, "new_entity_more_recent"
            else:
                return entity1, "existing_entity_more_recent"
        except Exception:
            # If timestamp parsing fails, prefer new entity
            return entity2, "new_entity_default"
    
    def _flag_for_review(self, entity1: Dict[str, Any], entity2: Dict[str, Any],
                         entity_type: str) -> Tuple[Dict[str, Any], str]:
        """Flag conflict for manual review"""
        # Keep existing but mark for review
        entity1["needs_review"] = True
        entity1["conflict_with"] = entity2
        entity1["conflict_timestamp"] = datetime.now().isoformat()
        
        return entity1, "flagged_for_manual_review"
    
    def _similar_text(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two texts are similar (simple word overlap)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold

# Global instance
_resolver = None

def get_resolver() -> ConflictResolver:
    """Get singleton conflict resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = ConflictResolver()
    return _resolver

