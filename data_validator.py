#!/usr/bin/env python3
"""
Data Validation Module
Validates extracted data before Neo4j ingestion
Based on Pydantic models for type safety
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ValidationError
import re

logger = logging.getLogger(__name__)

class PaperMetadata(BaseModel):
    """Validated paper metadata"""
    paper_id: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=1000)
    abstract: Optional[str] = Field(None, max_length=10000)
    publication_year: Optional[int] = Field(None, ge=1900, le=2100)
    journal: Optional[str] = Field(None, max_length=200)
    doi: Optional[str] = Field(None, max_length=100)
    keywords: Optional[List[str]] = Field(default_factory=list)
    volume: Optional[int] = Field(None, ge=1, le=1000)
    issue: Optional[int] = Field(None, ge=1, le=100)
    pages: Optional[str] = Field(None, max_length=50)
    paper_type: Optional[str] = Field(None, max_length=50)
    
    @validator('doi')
    def validate_doi(cls, v):
        if v and not v.startswith('10.'):
            logger.warning(f"Invalid DOI format: {v}")
            return None
        return v
    
    @validator('paper_type')
    def validate_paper_type(cls, v):
        if v:
            valid_types = [
                'empirical_quantitative', 'empirical_qualitative', 
                'theoretical', 'review', 'meta-analysis', 'research_note'
            ]
            if v not in valid_types:
                logger.warning(f"Unknown paper type: {v}")
                return None
        return v

class AuthorData(BaseModel):
    """Validated author data"""
    author_id: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)
    given_name: Optional[str] = Field(None, max_length=100)
    family_name: Optional[str] = Field(None, max_length=100)
    middle_initial: Optional[str] = Field(None, max_length=10)
    position: Optional[int] = Field(None, ge=1, le=50)
    corresponding_author: bool = Field(default=False)
    email: Optional[str] = Field(None, max_length=200)
    orcid: Optional[str] = Field(None, max_length=20)
    
    @validator('position', pre=True)
    def normalize_position(cls, v):
        """Normalize position to integer"""
        if v is None:
            return None
        if isinstance(v, int):
            return v if 1 <= v <= 50 else None
        if isinstance(v, str):
            # Try to extract number from string
            match = re.search(r'\d+', v)
            if match:
                pos = int(match.group())
                return pos if 1 <= pos <= 50 else None
            # If string is "Author" or similar, return None (will use order from list)
            return None
        return None
    
    @validator('email')
    def validate_email(cls, v):
        if v:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                logger.warning(f"Invalid email format: {v}")
                return None
        return v
    
    @validator('orcid')
    def validate_orcid(cls, v):
        if v:
            orcid_pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
            if not re.match(orcid_pattern, v):
                logger.warning(f"Invalid ORCID format: {v}")
                return None
        return v

class TheoryData(BaseModel):
    """Validated theory data"""
    theory_name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., pattern='^(primary|supporting|challenging|extending)$')
    domain: Optional[str] = Field(None, max_length=100)
    theory_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    section: Optional[str] = Field(None, max_length=50)
    usage_context: Optional[str] = Field(None, max_length=1000)

class MethodData(BaseModel):
    """Validated method data"""
    method_name: str = Field(..., min_length=1, max_length=200)
    method_type: str = Field(..., max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0)
    software: Optional[List[str]] = Field(default_factory=list)
    sample_size: Optional[str] = Field(None, max_length=100)
    data_sources: Optional[List[str]] = Field(default_factory=list)
    time_period: Optional[str] = Field(None, max_length=100)
    
    @validator('data_sources', pre=True)
    def normalize_data_sources(cls, v):
        """Convert string data_sources to list"""
        if v is None:
            return []
        if isinstance(v, str):
            # If it's a placeholder string, return empty list
            if v.lower() in ['not specified', 'not explicitly mentioned', 'n/a', 'na', 'none', '']:
                return []
            # Otherwise, treat as single-item list
            return [v]
        if isinstance(v, list):
            return v
        return []

class ResearchQuestionData(BaseModel):
    """Validated research question data"""
    question: str = Field(..., min_length=10, max_length=500)
    question_type: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)
    section: Optional[str] = Field(None, max_length=50)

class VariableData(BaseModel):
    """Validated variable data"""
    variable_name: str = Field(..., min_length=1, max_length=200)
    variable_type: str = Field(..., pattern='^(dependent|independent|control|moderator|mediator)$')
    measurement: Optional[str] = Field(None, max_length=500)
    operationalization: Optional[str] = Field(None, max_length=1000)
    domain: Optional[str] = Field(None, max_length=100)
    
    @validator('variable_type', pre=True)
    def normalize_variable_type(cls, v):
        """Normalize variable_type values"""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            # Map common variations
            if v_lower in ['dependent', 'dependant']:
                return 'dependent'
            elif v_lower in ['independent', 'independant']:
                return 'independent'
            elif v_lower in ['control', 'controlled']:
                return 'control'
            elif v_lower in ['moderator', 'moderating']:
                return 'moderator'
            elif v_lower in ['mediator', 'mediating']:
                return 'mediator'
        return v
    
    class Config:
        # Allow 'type' field to be mapped to 'variable_type'
        extra = 'allow'

class FindingData(BaseModel):
    """Validated finding data"""
    finding_text: str = Field(..., min_length=10, max_length=2000)
    finding_type: Optional[str] = Field(None, max_length=50)
    significance: Optional[str] = Field(None, max_length=100)
    effect_size: Optional[str] = Field(None, max_length=100)
    section: Optional[str] = Field(None, max_length=50)

class ContributionData(BaseModel):
    """Validated contribution data"""
    contribution_text: str = Field(..., min_length=10, max_length=2000)
    contribution_type: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=50)

class SoftwareData(BaseModel):
    """Validated software data"""
    software_name: str = Field(..., min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)
    software_type: Optional[str] = Field(None, max_length=50)
    usage: Optional[str] = Field(None, max_length=500)

class DatasetData(BaseModel):
    """Validated dataset data"""
    dataset_name: str = Field(..., min_length=1, max_length=200)
    dataset_type: Optional[str] = Field(None, max_length=50)
    time_period: Optional[str] = Field(None, max_length=100)
    sample_size: Optional[str] = Field(None, max_length=100)
    access: Optional[str] = Field(None, max_length=200)

class PhenomenonData(BaseModel):
    """Validated phenomenon data"""
    phenomenon_name: str = Field(..., min_length=1, max_length=200)
    phenomenon_type: Optional[str] = Field(None, max_length=50)  # e.g., "behavior", "pattern", "event", "trend"
    domain: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    section: Optional[str] = Field(None, max_length=50)
    context: Optional[str] = Field(None, max_length=1000)  # How phenomenon is studied

class DataValidator:
    """Validates extracted data before Neo4j ingestion"""
    
    @staticmethod
    def validate_paper_metadata(data: Dict[str, Any]) -> Optional[PaperMetadata]:
        """Validate paper metadata"""
        try:
            return PaperMetadata(**data)
        except ValidationError as e:
            logger.error(f"Paper metadata validation failed: {e}")
            return None
    
    @staticmethod
    def validate_author(data: Dict[str, Any]) -> Optional[AuthorData]:
        """Validate author data"""
        try:
            return AuthorData(**data)
        except ValidationError as e:
            logger.warning(f"Author validation failed: {e}")
            return None
    
    @staticmethod
    def validate_theory(data: Dict[str, Any]) -> Optional[TheoryData]:
        """Validate theory data"""
        try:
            return TheoryData(**data)
        except ValidationError as e:
            logger.warning(f"Theory validation failed: {e}")
            return None
    
    @staticmethod
    def validate_method(data: Dict[str, Any]) -> Optional[MethodData]:
        """Validate method data"""
        try:
            # Ensure confidence is in valid range
            if 'confidence' in data:
                data['confidence'] = max(0.0, min(1.0, float(data['confidence'])))
            return MethodData(**data)
        except ValidationError as e:
            logger.warning(f"Method validation failed: {e}")
            return None
    
    @staticmethod
    def validate_research_question(data: Dict[str, Any]) -> Optional[ResearchQuestionData]:
        """Validate research question data"""
        try:
            return ResearchQuestionData(**data)
        except ValidationError as e:
            logger.warning(f"Research question validation failed: {e}")
            return None
    
    @staticmethod
    def validate_variable(data: Dict[str, Any]) -> Optional[VariableData]:
        """Validate variable data"""
        try:
            return VariableData(**data)
        except ValidationError as e:
            logger.warning(f"Variable validation failed: {e}")
            return None
    
    @staticmethod
    def validate_finding(data: Dict[str, Any]) -> Optional[FindingData]:
        """Validate finding data"""
        try:
            return FindingData(**data)
        except ValidationError as e:
            logger.warning(f"Finding validation failed: {e}")
            return None
    
    @staticmethod
    def validate_contribution(data: Dict[str, Any]) -> Optional[ContributionData]:
        """Validate contribution data"""
        try:
            return ContributionData(**data)
        except ValidationError as e:
            logger.warning(f"Contribution validation failed: {e}")
            return None
    
    @staticmethod
    def validate_software(data: Dict[str, Any]) -> Optional[SoftwareData]:
        """Validate software data"""
        try:
            return SoftwareData(**data)
        except ValidationError as e:
            logger.warning(f"Software validation failed: {e}")
            return None
    
    @staticmethod
    def validate_dataset(data: Dict[str, Any]) -> Optional[DatasetData]:
        """Validate dataset data"""
        try:
            return DatasetData(**data)
        except ValidationError as e:
            logger.warning(f"Dataset validation failed: {e}")
            return None
    
    @staticmethod
    def validate_phenomenon(data: Dict[str, Any]) -> Optional[PhenomenonData]:
        """Validate phenomenon data"""
        try:
            return PhenomenonData(**data)
        except ValidationError as e:
            logger.warning(f"Phenomenon validation failed: {e}")
            return None

