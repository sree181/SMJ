#!/usr/bin/env python3
"""
API Endpoints for Connection Strength Features
Professional, scalable endpoints for Theory-Phenomenon connections
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ConnectionResponse(BaseModel):
    """Single connection response"""
    theory: Dict[str, Any]
    phenomenon: Dict[str, Any]
    connection_strength: float
    factor_scores: Dict[str, float]
    paper_id: str
    theory_role: str
    section: str

class ConnectionsListResponse(BaseModel):
    """List of connections with pagination"""
    connections: List[ConnectionResponse]
    total: int
    limit: int
    offset: int

class AggregatedConnectionResponse(BaseModel):
    """Aggregated connection response"""
    theory: Dict[str, Any]
    phenomenon: Dict[str, Any]
    avg_strength: float
    paper_count: int
    max_strength: float
    min_strength: float
    std_strength: Optional[float] = None
    avg_factor_scores: Dict[str, float]
    paper_ids: List[str]

class AggregatedConnectionsListResponse(BaseModel):
    """List of aggregated connections"""
    aggregated_connections: List[AggregatedConnectionResponse]
    total: int

class ConnectionStrengthDistributionResponse(BaseModel):
    """Connection strength distribution"""
    distribution: Dict[str, Dict[str, Any]]
    statistics: Dict[str, Any]

class TopConnectionsResponse(BaseModel):
    """Top connections response"""
    top_connections: List[Dict[str, Any]]

class FactorBreakdownResponse(BaseModel):
    """Factor breakdown response"""
    connection: Dict[str, Any]
    factors: Dict[str, Dict[str, Any]]

class PhenomenaListResponse(BaseModel):
    """List of phenomena"""
    phenomena: List[Dict[str, Any]]
    total: int

class PhenomenonDetailResponse(BaseModel):
    """Detailed phenomenon information"""
    phenomenon: Dict[str, Any]
    theories: List[Dict[str, Any]]
    papers: List[Dict[str, Any]]
    statistics: Dict[str, Any]

# Router for connection strength endpoints
router = APIRouter(prefix="/api/connections", tags=["connections"])

def get_neo4j_service():
    """Get Neo4j service instance (import from api_server)"""
    # This will be injected from api_server
    pass

@router.get("/theory-phenomenon", response_model=ConnectionsListResponse)
async def get_theory_phenomenon_connections(
    theory_name: Optional[str] = Query(None, description="Filter by theory name"),
    phenomenon_name: Optional[str] = Query(None, description="Filter by phenomenon name"),
    min_strength: float = Query(0.3, ge=0.0, le=1.0, description="Minimum connection strength"),
    max_strength: float = Query(1.0, ge=0.0, le=1.0, description="Maximum connection strength"),
    paper_id: Optional[str] = Query(None, description="Filter by paper ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Get Theory-Phenomenon connections with strength
    
    Returns all connections matching the filters, with pagination support.
    """
    # This will be implemented in api_server.py
    pass

@router.get("/theory-phenomenon/{theory_name}", response_model=Dict[str, Any])
async def get_phenomena_for_theory(
    theory_name: str,
    min_strength: float = Query(0.3, ge=0.0, le=1.0)
):
    """
    Get all phenomena explained by a specific theory
    """
    pass

@router.get("/phenomenon-theory/{phenomenon_name}", response_model=Dict[str, Any])
async def get_theories_for_phenomenon(
    phenomenon_name: str,
    min_strength: float = Query(0.3, ge=0.0, le=1.0)
):
    """
    Get all theories explaining a specific phenomenon
    """
    pass

@router.get("/aggregated", response_model=AggregatedConnectionsListResponse)
async def get_aggregated_connections(
    theory_name: Optional[str] = Query(None),
    phenomenon_name: Optional[str] = Query(None),
    min_paper_count: int = Query(2, ge=1),
    sort_by: str = Query("avg_strength", regex="^(avg_strength|paper_count|max_strength)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get aggregated connection strength statistics across papers
    """
    pass

@router.get("/{connection_id}/factors", response_model=FactorBreakdownResponse)
async def get_connection_factors(
    connection_id: str
):
    """
    Get detailed factor breakdown for a connection
    Connection ID format: "{theory_name}::{phenomenon_name}::{paper_id}"
    """
    pass

# Analytics router
analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@analytics_router.get("/connection-strength-distribution", response_model=ConnectionStrengthDistributionResponse)
async def get_connection_strength_distribution():
    """
    Get distribution of connection strengths
    """
    pass

@analytics_router.get("/top-connections", response_model=TopConnectionsResponse)
async def get_top_connections(
    n: int = Query(10, ge=1, le=100),
    type: str = Query("all", regex="^(all|aggregated|individual)$"),
    min_paper_count: Optional[int] = Query(None, ge=1)
):
    """
    Get top N connections by strength
    """
    pass

# Phenomena router
phenomena_router = APIRouter(prefix="/api/phenomena", tags=["phenomena"])

@phenomena_router.get("", response_model=PhenomenaListResponse)
async def list_phenomena(
    domain: Optional[str] = Query(None),
    phenomenon_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List all phenomena with optional filters
    """
    pass

@phenomena_router.get("/{phenomenon_name}", response_model=PhenomenonDetailResponse)
async def get_phenomenon_detail(phenomenon_name: str):
    """
    Get detailed information about a phenomenon
    """
    pass

