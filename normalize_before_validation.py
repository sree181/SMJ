#!/usr/bin/env python3
"""
Data Normalization Before Validation
Normalizes extracted data to match validation requirements
Maps GPT-4 field names to expected Pydantic model field names
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def normalize_theory_data(theory: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize theory data before validation"""
    if not theory:
        return None
    
    normalized = theory.copy()
    
    # Map field names: GPT-4 sometimes uses 'name' instead of 'theory_name'
    if 'theory_name' not in normalized or not normalized.get('theory_name'):
        if 'name' in normalized and normalized.get('name'):
            normalized['theory_name'] = normalized['name']
        else:
            logger.warning(f"Theory missing name: {normalized}")
            return None
    
    # Normalize role to lowercase and map variations
    if 'role' not in normalized or not normalized.get('role'):
        # Default to 'supporting' if role is missing
        normalized['role'] = 'supporting'
    else:
        role = str(normalized['role']).lower().strip()
        role_mapping = {
            'primary': 'primary',
            'supporting': 'supporting',
            'challenging': 'challenging',
            'extending': 'extending',
            'main': 'primary',
            'secondary': 'supporting',
            'alternative': 'supporting'
        }
        normalized['role'] = role_mapping.get(role, 'supporting')
    
    return normalized

def normalize_method_data(method: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize method data before validation"""
    if not method:
        return None
    
    normalized = method.copy()
    
    # Map field names: GPT-4 sometimes uses 'type', 'method', or 'name' instead of 'method_name'
    if 'method_name' not in normalized or not normalized.get('method_name'):
        if 'name' in normalized and normalized.get('name'):
            normalized['method_name'] = normalized['name']
        elif 'method' in normalized and normalized.get('method'):
            normalized['method_name'] = normalized['method']
        elif 'type' in normalized and normalized.get('type'):
            # Use 'type' as method_name if it's descriptive (not just "quantitative", etc.)
            method_type = normalized.get('type', '')
            if method_type not in ['quantitative', 'qualitative', 'mixed', 'computational', 'experimental']:
                normalized['method_name'] = method_type
            else:
                logger.warning(f"Method missing name: {normalized}")
                return None
        else:
            logger.warning(f"Method missing name: {normalized}")
            return None
    
    # Ensure confidence exists and is a number
    if 'confidence' not in normalized:
        normalized['confidence'] = 0.8  # Default confidence
    else:
        conf = normalized['confidence']
        if isinstance(conf, str):
            # Try to parse string confidence
            conf_lower = conf.lower()
            if conf_lower in ['high', 'very high']:
                normalized['confidence'] = 0.9
            elif conf_lower in ['medium', 'moderate']:
                normalized['confidence'] = 0.7
            elif conf_lower in ['low']:
                normalized['confidence'] = 0.5
            else:
                normalized['confidence'] = 0.8
        elif not isinstance(conf, (int, float)):
            normalized['confidence'] = 0.8
    
    # Ensure method_type exists
    if 'method_type' not in normalized:
        # Try to infer from method_name or default
        method_name_lower = str(normalized.get('method_name', '')).lower()
        if any(x in method_name_lower for x in ['survey', 'regression', 'statistical', 'quantitative']):
            normalized['method_type'] = 'quantitative'
        elif any(x in method_name_lower for x in ['interview', 'case study', 'qualitative', 'ethnography']):
            normalized['method_type'] = 'qualitative'
        else:
            normalized['method_type'] = 'mixed'
    
    return normalized

def normalize_phenomenon_data(phenomenon: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize phenomenon data before validation"""
    if not phenomenon:
        return None
    
    normalized = phenomenon.copy()
    
    # Map field names: GPT-4 sometimes uses 'name' instead of 'phenomenon_name'
    if 'phenomenon_name' not in normalized or not normalized.get('phenomenon_name'):
        if 'name' in normalized and normalized.get('name'):
            normalized['phenomenon_name'] = normalized['name']
        else:
            logger.warning(f"Phenomenon missing name: {normalized}")
            return None
    
    return normalized

def normalize_variable_data(variable: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize variable data before validation"""
    if not variable:
        return None
    
    normalized = variable.copy()
    
    # Map field names: GPT-4 sometimes uses 'name' instead of 'variable_name'
    if 'variable_name' not in normalized or not normalized.get('variable_name'):
        if 'name' in normalized and normalized.get('name'):
            normalized['variable_name'] = normalized['name']
        else:
            logger.warning(f"Variable missing name: {normalized}")
            return None
    
    # Map variable_type: GPT-4 sometimes uses 'type' instead of 'variable_type'
    if 'variable_type' not in normalized or not normalized.get('variable_type'):
        if 'type' in normalized and normalized.get('type'):
            var_type = str(normalized['type']).lower().strip()
            # Map common variations
            type_mapping = {
                'dependent': 'dependent',
                'independent': 'independent',
                'control': 'control',
                'moderator': 'moderator',
                'mediator': 'mediator',
                'instrumental': 'instrumental',
                'dependant': 'dependent',  # Common typo
            }
            normalized['variable_type'] = type_mapping.get(var_type, 'independent')
        else:
            logger.warning(f"Variable missing type: {normalized}")
            return None
    
    return normalized

def normalize_finding_data(finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize finding data before validation"""
    if not finding:
        return None
    
    normalized = finding.copy()
    
    # Map field names: GPT-4 sometimes uses 'result' instead of 'finding_text'
    if 'finding_text' not in normalized or not normalized.get('finding_text'):
        if 'result' in normalized and normalized.get('result'):
            normalized['finding_text'] = normalized['result']
        else:
            logger.warning(f"Finding missing text: {normalized}")
            return None
    
    return normalized

def normalize_contribution_data(contribution: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize contribution data before validation"""
    if not contribution:
        return None
    
    normalized = contribution.copy()
    
    # Map field names: GPT-4 sometimes uses 'details' instead of 'contribution_text'
    if 'contribution_text' not in normalized or not normalized.get('contribution_text'):
        if 'details' in normalized and normalized.get('details'):
            normalized['contribution_text'] = normalized['details']
        elif 'text' in normalized and normalized.get('text'):
            normalized['contribution_text'] = normalized['text']
        else:
            logger.warning(f"Contribution missing text: {normalized}")
            return None
    
    # Map contribution_type: GPT-4 sometimes uses 'type' instead of 'contribution_type'
    if 'contribution_type' not in normalized or not normalized.get('contribution_type'):
        if 'type' in normalized and normalized.get('type'):
            contrib_type = str(normalized['type']).lower().strip()
            type_mapping = {
                'theoretical': 'theoretical',
                'empirical': 'empirical',
                'methodological': 'methodological',
                'practical': 'practical',
            }
            normalized['contribution_type'] = type_mapping.get(contrib_type, 'theoretical')
        else:
            normalized['contribution_type'] = 'theoretical'  # Default
    
    return normalized

def normalize_author_data(author: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize author data before validation"""
    if not author:
        return None
    
    normalized = author.copy()
    
    # Generate author_id if missing
    if 'author_id' not in normalized or not normalized.get('author_id'):
        full_name = normalized.get('full_name', '')
        if full_name:
            # Generate ID from full name
            import re
            author_id = re.sub(r'[^a-z0-9]+', '_', full_name.lower())
            normalized['author_id'] = author_id
        else:
            logger.warning(f"Author missing full_name: {normalized}")
            return None
    
    # Normalize position: should be integer (1, 2, 3, etc.)
    if 'position' in normalized:
        position = normalized['position']
        if isinstance(position, str):
            # Try to extract number from string
            import re
            numbers = re.findall(r'\d+', position)
            if numbers:
                normalized['position'] = int(numbers[0])
            else:
                # If no number, try to infer from common patterns
                position_lower = position.lower()
                if 'first' in position_lower or 'lead' in position_lower:
                    normalized['position'] = 1
                elif 'second' in position_lower:
                    normalized['position'] = 2
                elif 'third' in position_lower:
                    normalized['position'] = 3
                else:
                    # Default to 1 if can't parse
                    normalized['position'] = 1
        elif not isinstance(position, int):
            normalized['position'] = 1  # Default
    else:
        normalized['position'] = 1  # Default
    
    # Handle affiliations vs affiliation
    if 'affiliation' in normalized and 'affiliations' not in normalized:
        normalized['affiliations'] = [normalized['affiliation']]
    elif 'affiliations' in normalized and not isinstance(normalized['affiliations'], list):
        normalized['affiliations'] = [normalized['affiliations']]
    elif 'affiliations' not in normalized:
        normalized['affiliations'] = []
    
    return normalized
    normalized = method.copy()
    
    # Normalize data_sources to list
    if 'data_sources' in normalized:
        data_sources = normalized['data_sources']
        if isinstance(data_sources, str):
            # Convert string to list
            if data_sources.strip():
                normalized['data_sources'] = [data_sources.strip()]
            else:
                normalized['data_sources'] = []
        elif data_sources is None:
            normalized['data_sources'] = []
        # If already a list, keep it
    
    # Ensure method_name exists
    if 'method_name' not in normalized or not normalized.get('method_name'):
        if 'name' in normalized:
            normalized['method_name'] = normalized['name']
        else:
            logger.warning(f"Method missing name: {normalized}")
            return None
    
    # Ensure method_type exists
    if 'method_type' not in normalized or not normalized.get('method_type'):
        # Try to infer from method_name
        method_name = normalized.get('method_name', '').lower()
        if any(x in method_name for x in ['regression', 'ols', 'panel', 'econometric']):
            normalized['method_type'] = 'quantitative'
        elif any(x in method_name for x in ['case study', 'interview', 'qualitative']):
            normalized['method_type'] = 'qualitative'
        elif any(x in method_name for x in ['mixed', 'multi-method']):
            normalized['method_type'] = 'mixed'
        else:
            normalized['method_type'] = 'quantitative'  # Default
    
    # Ensure confidence exists
    if 'confidence' not in normalized or normalized.get('confidence') is None:
        normalized['confidence'] = 0.8  # Default confidence
    
    return normalized

def normalize_variable_data(variable: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize variable data before validation"""
    normalized = variable.copy()
    
    # Normalize variable_type to lowercase
    if 'variable_type' in normalized:
        var_type = str(normalized['variable_type']).lower().strip()
        # Map common variations
        type_mapping = {
            'dependent': 'dependent',
            'independent': 'independent',
            'control': 'control',
            'moderator': 'moderator',
            'mediator': 'mediator',
            'instrumental': 'instrumental',
            'dv': 'dependent',
            'iv': 'independent',
            'cv': 'control'
        }
        normalized['variable_type'] = type_mapping.get(var_type, 'independent')  # Default
    
    # Ensure variable_name exists
    if 'variable_name' not in normalized or not normalized.get('variable_name'):
        if 'name' in normalized:
            normalized['variable_name'] = normalized['name']
        else:
            logger.warning(f"Variable missing name: {normalized}")
            return None
    
    return normalized

def normalize_author_data(author: Dict[str, Any], paper_id: str, position: int) -> Dict[str, Any]:
    """Normalize author data before validation"""
    normalized = author.copy()
    
    # Generate author_id if missing
    if 'author_id' not in normalized or not normalized.get('author_id'):
        # Generate from name and paper_id
        full_name = normalized.get('full_name', '')
        if not full_name:
            # Try to construct from given/family name
            given = normalized.get('given_name', '')
            family = normalized.get('family_name', '')
            full_name = f"{given} {family}".strip()
        
        if full_name:
            # Create author_id: firstname_lastname_paperid
            name_parts = full_name.lower().split()
            if len(name_parts) >= 2:
                author_id = f"{name_parts[0]}_{name_parts[-1]}_{paper_id}"
            else:
                author_id = f"{name_parts[0]}_{paper_id}"
            normalized['author_id'] = author_id
        else:
            normalized['author_id'] = f"author_{position}_{paper_id}"
    
    # Ensure full_name exists
    if 'full_name' not in normalized or not normalized.get('full_name'):
        given = normalized.get('given_name', '')
        family = normalized.get('family_name', '')
        if given or family:
            normalized['full_name'] = f"{given} {family}".strip()
        else:
            logger.warning(f"Author missing name: {normalized}")
            return None
    
    # Ensure position is set
    if 'position' not in normalized:
        normalized['position'] = position
    
    return normalized

def normalize_all_entities(extraction_result: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
    """Normalize all entities in extraction result"""
    normalized = extraction_result.copy()
    
    # Normalize theories
    if 'theories' in normalized and normalized['theories']:
        normalized['theories'] = [
            normalize_theory_data(t) 
            for t in normalized['theories'] 
            if normalize_theory_data(t) is not None
        ]
    
    # Normalize methods
    if 'methods' in normalized and normalized['methods']:
        normalized['methods'] = [
            normalize_method_data(m) 
            for m in normalized['methods'] 
            if normalize_method_data(m) is not None
        ]
    
    # Normalize variables
    if 'variables' in normalized and normalized['variables']:
        normalized['variables'] = [
            normalize_variable_data(v) 
            for v in normalized['variables'] 
            if normalize_variable_data(v) is not None
        ]
    
    # Normalize authors
    if 'authors' in normalized and normalized['authors']:
        normalized['authors'] = [
            normalize_author_data(a, paper_id, i+1) 
            for i, a in enumerate(normalized['authors'])
            if normalize_author_data(a, paper_id, i+1) is not None
        ]
    
    return normalized
