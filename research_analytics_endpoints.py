#!/usr/bin/env python3
"""
Research Analytics API Endpoints for SMJ Literature Analysis

Adds endpoints for:
1. Fragmentation/Coherence analysis
2. Theory→Phenomena and Phenomena→Theory mappings
3. Temporal methodology evolution
4. Author network analysis
5. Descriptive statistics by period

These endpoints integrate with the existing api_server.py
"""

import os
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Import LLMClient from api_server - use lazy import to avoid circular dependency
# LLMClient will be imported only when needed, not at module level
def get_llm_client():
    """Lazy import of LLMClient to avoid circular dependency"""
    from api_server import LLMClient
    return LLMClient()

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for research analytics endpoints
router = APIRouter(prefix="/api/research", tags=["Research Analytics"])

# Time periods for analysis
TIME_PERIODS = [
    ("1985-1989", 1985, 1989),
    ("1990-1994", 1990, 1994),
    ("1995-1999", 1995, 1999),
    ("2000-2004", 2000, 2004),
    ("2005-2009", 2005, 2009),
    ("2010-2014", 2010, 2014),
    ("2015-2019", 2015, 2019),
    ("2020-2024", 2020, 2024),
]


# ============================================================================
# Response Models
# ============================================================================

class FragmentationMetrics(BaseModel):
    """Topical fragmentation/coherence metrics"""
    period: str
    total_papers: int
    unique_theories: int
    theories_per_paper: float
    theory_concentration_gini: float = Field(description="Gini coefficient: 0=dispersed, 1=concentrated")
    top_5_theory_share: float = Field(description="Share of papers using top 5 theories")
    coherence_score: float = Field(description="0-1, higher=more coherent/less fragmented")
    fragmentation_index: float = Field(description="0-1, higher=more fragmented")
    dominant_theories: List[Dict[str, Any]]
    emerging_theories: List[str]
    declining_theories: List[str]


class TheoryPhenomenonMapping(BaseModel):
    """Single theory to multiple phenomena mapping"""
    theory_name: str
    phenomena_count: int
    phenomena: List[Dict[str, Any]]
    coverage_breadth: float = Field(description="How broadly theory is applied")
    primary_phenomenon: Optional[str]


class PhenomenonTheoryMapping(BaseModel):
    """Multiple theories explaining single phenomenon"""
    phenomenon_name: str
    theories_count: int
    theories: List[Dict[str, Any]]
    theoretical_pluralism: float = Field(description="Degree of multi-theory explanation")
    dominant_theory: Optional[str]


class MethodEvolution(BaseModel):
    """Methodology evolution over time"""
    period: str
    quantitative_count: int
    qualitative_count: int
    mixed_count: int
    quantitative_ratio: float
    qualitative_ratio: float
    mixed_ratio: float
    top_methods: List[Dict[str, Any]]
    emerging_methods: List[str]


class AuthorMetrics(BaseModel):
    """Key author metrics"""
    author_name: str
    paper_count: int
    first_publication: Optional[int]
    last_publication: Optional[int]
    career_span: int
    primary_theories: List[str]
    primary_methods: List[str]
    top_collaborators: List[Dict[str, Any]]
    collaboration_count: int


class DescriptiveStats(BaseModel):
    """Comprehensive descriptive statistics for a period"""
    period: str
    paper_count: int

    # Theory stats
    theory_total_uses: int
    unique_theories: int
    theories_per_paper: float
    top_theories: List[Dict[str, Any]]

    # Method stats
    method_total_uses: int
    unique_methods: int
    methods_per_paper: float
    top_methods: List[Dict[str, Any]]
    method_type_distribution: Dict[str, float]

    # Phenomenon stats
    phenomenon_total: int
    unique_phenomena: int
    top_phenomena: List[Dict[str, Any]]

    # Author stats
    unique_authors: int
    avg_authors_per_paper: float
    collaboration_rate: float

    # Variable stats
    avg_variables_per_paper: float


# ============================================================================
# Helper Functions
# ============================================================================

def get_neo4j_driver():
    """Get Neo4j driver"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, password))


def calculate_gini(values: List[int]) -> float:
    """Calculate Gini coefficient (0=equal, 1=concentrated)"""
    if not values or sum(values) == 0:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)
    cumsum = 0
    total = sum(sorted_values)

    for i, val in enumerate(sorted_values):
        cumsum += val

    # Gini formula
    numerator = 2 * sum((i + 1) * val for i, val in enumerate(sorted_values))
    denominator = n * total

    if denominator == 0:
        return 0.0

    return (numerator / denominator) - (n + 1) / n


# ============================================================================
# 1. FRAGMENTATION/COHERENCE ANALYSIS
# ============================================================================

@router.get("/fragmentation/{period}", response_model=FragmentationMetrics)
async def get_fragmentation_analysis(period: str):
    """
    Analyze topical fragmentation vs coherence for a time period

    Measures whether the field is converging around dominant paradigms
    or fragmenting into diverse theoretical approaches.
    """
    # Parse period
    start_year, end_year = None, None
    for p, s, e in TIME_PERIODS:
        if p == period:
            start_year, end_year = s, e
            break

    if not start_year:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}. Use format like '2015-2019'")

    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            # Get paper count
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                RETURN count(p) as total
            """, {"start": start_year, "end": end_year})
            paper_count = result.single()["total"]

            if paper_count == 0:
                raise HTTPException(status_code=404, detail=f"No papers found for period {period}")

            # Get theory usage counts
            result = session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH t.name as theory, count(DISTINCT p) as paper_count
                RETURN theory, paper_count
                ORDER BY paper_count DESC
            """, {"start": start_year, "end": end_year})

            theory_counts = {}
            for record in result:
                theory_counts[record["theory"]] = record["paper_count"]

            unique_theories = len(theory_counts)
            total_theory_uses = sum(theory_counts.values())
            theories_per_paper = total_theory_uses / paper_count if paper_count > 0 else 0

            # Calculate Gini coefficient
            gini = calculate_gini(list(theory_counts.values()))

            # Top 5 theory share
            sorted_counts = sorted(theory_counts.values(), reverse=True)
            top_5_total = sum(sorted_counts[:5])
            top_5_share = top_5_total / total_theory_uses if total_theory_uses > 0 else 0

            # Coherence score (based on concentration)
            coherence = top_5_share
            fragmentation = 1 - coherence

            # Dominant theories
            dominant = [
                {"theory": t, "paper_count": c, "share": c / paper_count}
                for t, c in sorted(theory_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Get previous period for emerging/declining analysis
            emerging = []
            declining = []

            if start_year > 1985:
                prev_start = start_year - 5
                prev_end = start_year - 1

                result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.publication_year >= $start AND p.publication_year <= $end
                    WITH t.name as theory, count(DISTINCT p) as paper_count
                    RETURN theory, paper_count
                """, {"start": prev_start, "end": prev_end})

                prev_counts = {r["theory"]: r["paper_count"] for r in result}

                for theory, count in theory_counts.items():
                    prev_count = prev_counts.get(theory, 0)
                    if prev_count == 0 and count >= 3:
                        emerging.append(theory)
                    elif prev_count > 0:
                        growth = (count - prev_count) / prev_count
                        if growth > 0.5 and count >= 3:
                            emerging.append(theory)
                        elif growth < -0.3:
                            declining.append(theory)

            return FragmentationMetrics(
                period=period,
                total_papers=paper_count,
                unique_theories=unique_theories,
                theories_per_paper=round(theories_per_paper, 2),
                theory_concentration_gini=round(gini, 3),
                top_5_theory_share=round(top_5_share, 3),
                coherence_score=round(coherence, 3),
                fragmentation_index=round(fragmentation, 3),
                dominant_theories=dominant,
                emerging_theories=emerging[:5],
                declining_theories=declining[:5]
            )

    finally:
        driver.close()


@router.get("/fragmentation/all", response_model=List[FragmentationMetrics])
async def get_fragmentation_over_time():
    """Get fragmentation analysis for all time periods"""
    results = []
    for period, _, _ in TIME_PERIODS:
        try:
            metrics = await get_fragmentation_analysis(period)
            results.append(metrics)
        except HTTPException:
            continue  # Skip periods with no data
    return results


class FragmentationAnalysisResponse(BaseModel):
    """Comprehensive fragmentation analysis with LLM-generated insights"""
    metrics: FragmentationMetrics
    analysis: str = Field(description="LLM-generated comprehensive analysis")
    conclusion: str = Field(description="Overall conclusion: fragmented, convergent, or coherent")
    evidence: Dict[str, Any] = Field(description="Supporting evidence from the data")


@router.get("/fragmentation/{period}/analysis", response_model=FragmentationAnalysisResponse)
async def get_fragmentation_analysis_with_llm(period: str):
    """
    Comprehensive topical fragmentation analysis with LLM-generated insights
    
    Answers: Is the field fragmented, convergent, or coherent?
    Uses Neo4j data + LLM to provide expert-level analysis.
    """
    # Get base metrics
    metrics = await get_fragmentation_analysis(period)
    
    # Parse period for additional queries
    start_year, end_year = None, None
    for p, s, e in TIME_PERIODS:
        if p == period:
            start_year, end_year = s, e
            break
    
    driver = get_neo4j_driver()
    llm_client = get_llm_client()
    
    try:
        with driver.session() as session:
            # Get additional context for LLM analysis
            
            # 1. Theory-phenomenon connection patterns
            result = session.run("""
                MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WHERE p.year >= $start AND p.year <= $end
                WITH t.name as theory, ph.phenomenon_name as phenomenon, count(DISTINCT p) as paper_count
                RETURN theory, collect({phenomenon: phenomenon, papers: paper_count}) as phenomena
                ORDER BY size(phenomena) DESC
                LIMIT 10
            """, {"start": start_year, "end": end_year})
            
            theory_phenomenon_patterns = []
            for record in result:
                theory_phenomenon_patterns.append({
                    "theory": record["theory"],
                    "phenomena_count": len(record["phenomena"]),
                    "phenomena": record["phenomena"][:5]  # Top 5
                })
            
            # 2. Method diversity
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WHERE p.year >= $start AND p.year <= $end
                WITH m.type as method_type, count(DISTINCT p) as paper_count
                RETURN method_type, paper_count
                ORDER BY paper_count DESC
            """, {"start": start_year, "end": end_year})
            
            method_distribution = {r["method_type"]: r["paper_count"] for r in result}
            
            # 3. Theory co-usage patterns (theories used together)
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.year >= $start AND p.year <= $end
                WITH p, collect(t.name) as theories
                WHERE size(theories) > 1
                UNWIND theories as theory1
                UNWIND theories as theory2
                WHERE theory1 < theory2
                RETURN theory1, theory2, count(*) as co_usage_count
                ORDER BY co_usage_count DESC
                LIMIT 10
            """, {"start": start_year, "end": end_year})
            
            co_usage_patterns = [
                {"theory1": r["theory1"], "theory2": r["theory2"], "count": r["co_usage_count"]}
                for r in result
            ]
            
            # 4. Temporal comparison (if not first period)
            temporal_context = {}
            if start_year > 1985:
                prev_start = start_year - 5
                prev_end = start_year - 1
                
                result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE p.year >= $start AND p.year <= $end
                    WITH t.name as theory, count(DISTINCT p) as paper_count
                    RETURN theory, paper_count
                    ORDER BY paper_count DESC
                    LIMIT 10
                """, {"start": prev_start, "end": prev_end})
                
                prev_top_theories = {r["theory"]: r["paper_count"] for r in result}
                temporal_context = {
                    "previous_period": f"{prev_start}-{prev_end}",
                    "previous_top_theories": prev_top_theories,
                    "stability": len(set([t["theory"] for t in metrics.dominant_theories[:5]]) & set(prev_top_theories.keys())) / 5.0
                }
            
            # Prepare comprehensive context for LLM
            context_data = {
                "period": period,
                "metrics": {
                    "total_papers": metrics.total_papers,
                    "unique_theories": metrics.unique_theories,
                    "theories_per_paper": metrics.theories_per_paper,
                    "gini_coefficient": metrics.theory_concentration_gini,
                    "top_5_share": metrics.top_5_theory_share,
                    "coherence_score": metrics.coherence_score,
                    "fragmentation_index": metrics.fragmentation_index
                },
                "dominant_theories": metrics.dominant_theories[:10],
                "emerging_theories": metrics.emerging_theories,
                "declining_theories": metrics.declining_theories,
                "theory_phenomenon_patterns": theory_phenomenon_patterns,
                "method_distribution": method_distribution,
                "co_usage_patterns": co_usage_patterns,
                "temporal_context": temporal_context
            }
            
            # Generate LLM analysis
            query = f"""
            Based on the following data about strategic management research from {period}, 
            analyze whether the field shows:
            1. **Fragmentation**: Many diverse theories with low concentration, high diversity
            2. **Convergence**: Field converging around dominant theories, increasing concentration
            3. **Coherence**: Balanced theoretical landscape with clear patterns and connections
            
            Provide a comprehensive analysis that:
            - Interprets the metrics (Gini coefficient, top 5 share, coherence score)
            - Analyzes theory-phenomenon connection patterns
            - Examines method diversity and its relationship to theoretical diversity
            - Considers theory co-usage patterns (theories used together)
            - Evaluates temporal trends (if available)
            - Concludes with a clear assessment: Is the field fragmented, convergent, or coherent?
            """
            
            analysis = llm_client.generate_answer(query, context_data, persona=None)
            
            # Generate conclusion (fragmented/convergent/coherent)
            conclusion_prompt = f"""
            Based on this fragmentation analysis data:
            - Coherence score: {metrics.coherence_score} (0=fragmented, 1=coherent)
            - Fragmentation index: {metrics.fragmentation_index} (0=coherent, 1=fragmented)
            - Gini coefficient: {metrics.theory_concentration_gini} (0=dispersed, 1=concentrated)
            - Top 5 theory share: {metrics.top_5_theory_share}
            
            Classify the field as ONE of: "fragmented", "convergent", or "coherent"
            Provide only the classification word.
            """
            
            conclusion_response = llm_client.generate_answer(conclusion_prompt, context_data, persona=None)
            conclusion = conclusion_response.strip().lower()
            
            # Normalize conclusion
            if "fragmented" in conclusion:
                conclusion = "fragmented"
            elif "convergent" in conclusion or "converging" in conclusion:
                conclusion = "convergent"
            elif "coherent" in conclusion:
                conclusion = "coherent"
            else:
                # Default based on metrics
                if metrics.coherence_score > 0.6:
                    conclusion = "coherent"
                elif metrics.coherence_score > 0.4:
                    conclusion = "convergent"
                else:
                    conclusion = "fragmented"
            
            return FragmentationAnalysisResponse(
                metrics=metrics,
                analysis=analysis,
                conclusion=conclusion,
                evidence={
                    "theory_phenomenon_patterns": theory_phenomenon_patterns[:5],
                    "method_distribution": method_distribution,
                    "co_usage_patterns": co_usage_patterns[:5],
                    "temporal_context": temporal_context
                }
            )
    
    finally:
        driver.close()


# ============================================================================
# 2. THEORY-PHENOMENON RELATIONSHIPS
# ============================================================================

@router.get("/theory-phenomena", response_model=List[TheoryPhenomenonMapping])
async def get_theory_to_phenomena_mappings(
    min_papers: int = Query(default=2, description="Minimum papers for inclusion")
):
    """
    Get single theory → multiple phenomena mappings

    Identifies theories that explain multiple phenomena across papers.
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WITH t.name as theory,
                     collect(DISTINCT {name: ph.phenomenon_name, count: count(p)}) as phenomena_raw,
                     count(DISTINCT p) as total_papers,
                     count(DISTINCT ph) as phenomena_count
                WHERE total_papers >= $min_papers
                UNWIND phenomena_raw as ph_data
                WITH theory, phenomena_count, total_papers,
                     collect(DISTINCT ph_data) as phenomena
                RETURN theory, phenomena_count, total_papers, phenomena
                ORDER BY phenomena_count DESC
                LIMIT 50
            """, {"min_papers": min_papers})

            mappings = []
            for record in result:
                theory = record["theory"]
                phenomena_count = record["phenomena_count"]
                phenomena = record["phenomena"]

                # Get primary phenomenon (most frequent)
                primary = max(phenomena, key=lambda x: x.get("count", 0)) if phenomena else None

                mappings.append(TheoryPhenomenonMapping(
                    theory_name=theory,
                    phenomena_count=phenomena_count,
                    phenomena=phenomena[:10],  # Limit to top 10
                    coverage_breadth=min(1.0, phenomena_count / 10),
                    primary_phenomenon=primary.get("name") if primary else None
                ))

            return mappings

    finally:
        driver.close()


@router.get("/phenomena-theories", response_model=List[PhenomenonTheoryMapping])
async def get_phenomena_to_theories_mappings(
    min_papers: int = Query(default=2, description="Minimum papers for inclusion")
):
    """
    Get multiple theories → single phenomenon mappings

    Identifies phenomena explained by multiple theories (theoretical pluralism).
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WITH ph.phenomenon_name as phenomenon,
                     collect(DISTINCT {name: t.name, count: count(p)}) as theories_raw,
                     count(DISTINCT p) as total_papers,
                     count(DISTINCT t) as theories_count
                WHERE total_papers >= $min_papers
                UNWIND theories_raw as t_data
                WITH phenomenon, theories_count, total_papers,
                     collect(DISTINCT t_data) as theories
                RETURN phenomenon, theories_count, total_papers, theories
                ORDER BY theories_count DESC
                LIMIT 50
            """, {"min_papers": min_papers})

            mappings = []
            for record in result:
                phenomenon = record["phenomenon"]
                theories_count = record["theories_count"]
                theories = record["theories"]

                # Get dominant theory
                dominant = max(theories, key=lambda x: x.get("count", 0)) if theories else None

                mappings.append(PhenomenonTheoryMapping(
                    phenomenon_name=phenomenon,
                    theories_count=theories_count,
                    theories=theories[:10],
                    theoretical_pluralism=min(1.0, theories_count / 5),
                    dominant_theory=dominant.get("name") if dominant else None
                ))

            return mappings

    finally:
        driver.close()


@router.get("/theory-phenomenon-matrix")
async def get_theory_phenomenon_matrix():
    """
    Get theory-phenomenon co-occurrence matrix

    Returns matrix data for heatmap visualization.
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)<-[:USES_THEORY]-(p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WITH t.name as theory, ph.phenomenon_name as phenomenon, count(p) as count
                RETURN theory, phenomenon, count
                ORDER BY count DESC
            """)

            matrix = defaultdict(lambda: defaultdict(int))
            theories = set()
            phenomena = set()

            for record in result:
                theory = record["theory"]
                phenomenon = record["phenomenon"]
                count = record["count"]

                matrix[theory][phenomenon] = count
                theories.add(theory)
                phenomena.add(phenomenon)

            # Sort by frequency
            theories = sorted(theories, key=lambda t: sum(matrix[t].values()), reverse=True)[:20]
            phenomena = sorted(phenomena, key=lambda p: sum(matrix[t].get(p, 0) for t in theories), reverse=True)[:20]

            # Build matrix data
            matrix_data = []
            for theory in theories:
                row = [matrix[theory].get(ph, 0) for ph in phenomena]
                matrix_data.append(row)

            return {
                "theories": theories,
                "phenomena": phenomena,
                "matrix": matrix_data,
                "max_value": max(max(row) for row in matrix_data) if matrix_data else 0
            }

    finally:
        driver.close()


# ============================================================================
# 3. TEMPORAL METHODOLOGY EVOLUTION
# ============================================================================

@router.get("/methodology-evolution/{period}", response_model=MethodEvolution)
async def get_methodology_evolution(period: str):
    """
    Get methodology evolution for a specific time period

    Tracks quantitative vs qualitative vs mixed methods over time.
    """
    start_year, end_year = None, None
    for p, s, e in TIME_PERIODS:
        if p == period:
            start_year, end_year = s, e
            break

    if not start_year:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            # Get method type distribution
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH p, m.type as method_type
                RETURN method_type, count(DISTINCT p) as paper_count
            """, {"start": start_year, "end": end_year})

            type_counts = {"quantitative": 0, "qualitative": 0, "mixed": 0}
            for record in result:
                mtype = (record["method_type"] or "").lower()
                if "quant" in mtype:
                    type_counts["quantitative"] += record["paper_count"]
                elif "qual" in mtype:
                    type_counts["qualitative"] += record["paper_count"]
                elif "mixed" in mtype:
                    type_counts["mixed"] += record["paper_count"]

            total = sum(type_counts.values()) or 1

            # Get top methods
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH m.name as method, count(p) as count
                RETURN method, count
                ORDER BY count DESC
                LIMIT 10
            """, {"start": start_year, "end": end_year})

            top_methods = [{"method": r["method"], "count": r["count"]} for r in result]

            # Find emerging methods (compared to previous period)
            emerging = []
            if start_year > 1985:
                prev_start = start_year - 5
                prev_end = start_year - 1

                result = session.run("""
                    MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                    WHERE p.publication_year >= $start AND p.publication_year <= $end
                    WITH m.name as method, count(p) as count
                    RETURN method, count
                """, {"start": prev_start, "end": prev_end})

                prev_counts = {r["method"]: r["count"] for r in result}

                # Current period
                result = session.run("""
                    MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                    WHERE p.publication_year >= $start AND p.publication_year <= $end
                    WITH m.name as method, count(p) as count
                    RETURN method, count
                """, {"start": start_year, "end": end_year})

                for record in result:
                    method = record["method"]
                    count = record["count"]
                    prev_count = prev_counts.get(method, 0)

                    if prev_count == 0 and count >= 2:
                        emerging.append(method)
                    elif prev_count > 0 and (count - prev_count) / prev_count > 0.5:
                        emerging.append(method)

            return MethodEvolution(
                period=period,
                quantitative_count=type_counts["quantitative"],
                qualitative_count=type_counts["qualitative"],
                mixed_count=type_counts["mixed"],
                quantitative_ratio=round(type_counts["quantitative"] / total, 3),
                qualitative_ratio=round(type_counts["qualitative"] / total, 3),
                mixed_ratio=round(type_counts["mixed"] / total, 3),
                top_methods=top_methods,
                emerging_methods=emerging[:5]
            )

    finally:
        driver.close()


@router.get("/methodology-evolution/all", response_model=List[MethodEvolution])
async def get_methodology_evolution_all():
    """Get methodology evolution for all time periods"""
    results = []
    for period, _, _ in TIME_PERIODS:
        try:
            evolution = await get_methodology_evolution(period)
            results.append(evolution)
        except HTTPException:
            continue
    return results


# ============================================================================
# 4. AUTHOR NETWORK ANALYSIS
# ============================================================================

@router.get("/authors/top", response_model=List[AuthorMetrics])
async def get_top_authors(
    limit: int = Query(default=50, description="Number of authors to return"),
    min_papers: int = Query(default=3, description="Minimum papers for inclusion")
):
    """
    Get top authors with their metrics

    Includes publication history, preferred theories/methods, and collaboration network.
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            # Get author basic stats
            result = session.run("""
                MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
                WITH a.name as author,
                     count(p) as paper_count,
                     min(p.publication_year) as first_year,
                     max(p.publication_year) as last_year
                WHERE paper_count >= $min_papers
                RETURN author, paper_count, first_year, last_year
                ORDER BY paper_count DESC
                LIMIT $limit
            """, {"min_papers": min_papers, "limit": limit})

            authors_data = list(result)

            author_metrics = []
            for record in authors_data:
                author = record["author"]

                # Get primary theories
                theories_result = session.run("""
                    MATCH (a:Author {name: $author})<-[:AUTHORED_BY]-(p:Paper)-[:USES_THEORY]->(t:Theory)
                    WITH t.name as theory, count(p) as count
                    RETURN theory
                    ORDER BY count DESC
                    LIMIT 3
                """, {"author": author})
                theories = [r["theory"] for r in theories_result]

                # Get primary methods
                methods_result = session.run("""
                    MATCH (a:Author {name: $author})<-[:AUTHORED_BY]-(p:Paper)-[:USES_METHOD]->(m:Method)
                    WITH m.name as method, count(p) as count
                    RETURN method
                    ORDER BY count DESC
                    LIMIT 3
                """, {"author": author})
                methods = [r["method"] for r in methods_result]

                # Get collaborators
                collab_result = session.run("""
                    MATCH (a:Author {name: $author})<-[:AUTHORED_BY]-(p:Paper)-[:AUTHORED_BY]->(coauthor:Author)
                    WHERE coauthor.name <> $author
                    WITH coauthor.name as collaborator, count(p) as papers
                    RETURN collaborator, papers
                    ORDER BY papers DESC
                    LIMIT 5
                """, {"author": author})
                collaborators = [{"name": r["collaborator"], "papers": r["papers"]} for r in collab_result]

                # Count total collaborators
                collab_count_result = session.run("""
                    MATCH (a:Author {name: $author})<-[:AUTHORED_BY]-(p:Paper)-[:AUTHORED_BY]->(coauthor:Author)
                    WHERE coauthor.name <> $author
                    RETURN count(DISTINCT coauthor) as total
                """, {"author": author})
                collab_count = collab_count_result.single()["total"]

                first_year = record["first_year"] or 1985
                last_year = record["last_year"] or 2024

                author_metrics.append(AuthorMetrics(
                    author_name=author,
                    paper_count=record["paper_count"],
                    first_publication=first_year,
                    last_publication=last_year,
                    career_span=last_year - first_year + 1,
                    primary_theories=theories,
                    primary_methods=methods,
                    top_collaborators=collaborators,
                    collaboration_count=collab_count
                ))

            return author_metrics

    finally:
        driver.close()


@router.get("/authors/collaboration-network")
async def get_collaboration_network(
    min_collaborations: int = Query(default=2, description="Minimum joint papers"),
    limit: int = Query(default=200, description="Maximum edges to return")
):
    """
    Get author collaboration network for visualization

    Returns nodes (authors) and edges (collaborations) for network graph.
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (a1:Author)<-[:AUTHORED_BY]-(p:Paper)-[:AUTHORED_BY]->(a2:Author)
                WHERE a1.name < a2.name
                WITH a1.name as author1, a2.name as author2, count(p) as collaborations
                WHERE collaborations >= $min_collabs
                RETURN author1, author2, collaborations
                ORDER BY collaborations DESC
                LIMIT $limit
            """, {"min_collabs": min_collaborations, "limit": limit})

            nodes = set()
            edges = []

            for record in result:
                author1 = record["author1"]
                author2 = record["author2"]
                weight = record["collaborations"]

                nodes.add(author1)
                nodes.add(author2)
                edges.append({
                    "source": author1,
                    "target": author2,
                    "weight": weight
                })

            # Get paper counts for node sizing
            node_list = []
            for author in nodes:
                result = session.run("""
                    MATCH (a:Author {name: $author})<-[:AUTHORED_BY]-(p:Paper)
                    RETURN count(p) as papers
                """, {"author": author})
                papers = result.single()["papers"]
                node_list.append({"id": author, "label": author, "papers": papers})

            return {
                "nodes": node_list,
                "edges": edges,
                "node_count": len(node_list),
                "edge_count": len(edges)
            }

    finally:
        driver.close()


# ============================================================================
# 5. DESCRIPTIVE STATISTICS BY PERIOD
# ============================================================================

@router.get("/statistics/{period}", response_model=DescriptiveStats)
async def get_descriptive_statistics(period: str):
    """
    Get comprehensive descriptive statistics for a time period
    """
    start_year, end_year = None, None
    for p, s, e in TIME_PERIODS:
        if p == period:
            start_year, end_year = s, e
            break

    if not start_year:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            # Paper count
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                RETURN count(p) as total
            """, {"start": start_year, "end": end_year})
            paper_count = result.single()["total"]

            if paper_count == 0:
                raise HTTPException(status_code=404, detail=f"No data for period {period}")

            # Theory stats
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH t.name as theory, count(p) as count
                RETURN count(theory) as unique_theories,
                       sum(count) as total_uses,
                       collect({theory: theory, count: count}) as all_theories
            """, {"start": start_year, "end": end_year})
            record = result.single()
            unique_theories = record["unique_theories"]
            theory_total = record["total_uses"]
            all_theories = record["all_theories"]
            top_theories = sorted(all_theories, key=lambda x: x["count"], reverse=True)[:10]

            # Method stats
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH m.name as method, m.type as type, count(p) as count
                RETURN count(method) as unique_methods,
                       sum(count) as total_uses,
                       collect({method: method, count: count, type: type}) as all_methods
            """, {"start": start_year, "end": end_year})
            record = result.single()
            unique_methods = record["unique_methods"]
            method_total = record["total_uses"]
            all_methods = record["all_methods"]
            top_methods = sorted(all_methods, key=lambda x: x["count"], reverse=True)[:10]

            # Method type distribution
            type_dist = {"quantitative": 0, "qualitative": 0, "mixed": 0, "other": 0}
            for m in all_methods:
                mtype = (m.get("type") or "other").lower()
                if "quant" in mtype:
                    type_dist["quantitative"] += m["count"]
                elif "qual" in mtype:
                    type_dist["qualitative"] += m["count"]
                elif "mixed" in mtype:
                    type_dist["mixed"] += m["count"]
                else:
                    type_dist["other"] += m["count"]

            total_typed = sum(type_dist.values()) or 1
            type_dist = {k: round(v / total_typed, 3) for k, v in type_dist.items()}

            # Phenomenon stats
            result = session.run("""
                MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH ph.phenomenon_name as phenomenon, count(p) as count
                RETURN count(phenomenon) as unique_phenomena,
                       sum(count) as total,
                       collect({phenomenon: phenomenon, count: count}) as all_phenomena
            """, {"start": start_year, "end": end_year})
            record = result.single()
            unique_phenomena = record["unique_phenomena"]
            phenomenon_total = record["total"]
            all_phenomena = record["all_phenomena"]
            top_phenomena = sorted(all_phenomena, key=lambda x: x["count"], reverse=True)[:10]

            # Author stats
            result = session.run("""
                MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                WITH p, count(a) as author_count
                RETURN count(DISTINCT p) as papers_with_authors,
                       avg(author_count) as avg_authors,
                       sum(CASE WHEN author_count > 1 THEN 1 ELSE 0 END) * 1.0 / count(p) as collab_rate
            """, {"start": start_year, "end": end_year})
            record = result.single()
            avg_authors = record["avg_authors"] or 0
            collab_rate = record["collab_rate"] or 0

            result = session.run("""
                MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
                WHERE p.publication_year >= $start AND p.publication_year <= $end
                RETURN count(DISTINCT a) as unique_authors
            """, {"start": start_year, "end": end_year})
            unique_authors = result.single()["unique_authors"]

            # Variable stats (if available)
            avg_variables = 0
            try:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.publication_year >= $start AND p.publication_year <= $end
                    OPTIONAL MATCH (p)-[:EMPLOYS_VARIABLE]->(v:Variable)
                    WITH p, count(v) as var_count
                    RETURN avg(var_count) as avg_vars
                """, {"start": start_year, "end": end_year})
                avg_variables = result.single()["avg_vars"] or 0
            except:
                pass

            return DescriptiveStats(
                period=period,
                paper_count=paper_count,
                theory_total_uses=theory_total,
                unique_theories=unique_theories,
                theories_per_paper=round(theory_total / paper_count, 2),
                top_theories=top_theories,
                method_total_uses=method_total,
                unique_methods=unique_methods,
                methods_per_paper=round(method_total / paper_count, 2),
                top_methods=top_methods,
                method_type_distribution=type_dist,
                phenomenon_total=phenomenon_total,
                unique_phenomena=unique_phenomena,
                top_phenomena=top_phenomena,
                unique_authors=unique_authors,
                avg_authors_per_paper=round(avg_authors, 2),
                collaboration_rate=round(collab_rate, 3),
                avg_variables_per_paper=round(avg_variables, 2)
            )

    finally:
        driver.close()


@router.get("/statistics/all", response_model=List[DescriptiveStats])
async def get_all_statistics():
    """Get descriptive statistics for all time periods"""
    results = []
    for period, _, _ in TIME_PERIODS:
        try:
            stats = await get_descriptive_statistics(period)
            results.append(stats)
        except HTTPException:
            continue
    return results


@router.get("/statistics/summary")
async def get_overall_summary():
    """
    Get summary statistics across all periods

    Useful for overall field characterization.
    """
    driver = get_neo4j_driver()

    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                OPTIONAL MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                OPTIONAL MATCH (p)-[:AUTHORED_BY]->(a:Author)
                WITH count(DISTINCT p) as total_papers,
                     count(DISTINCT t) as total_theories,
                     count(DISTINCT m) as total_methods,
                     count(DISTINCT ph) as total_phenomena,
                     count(DISTINCT a) as total_authors
                RETURN total_papers, total_theories, total_methods, total_phenomena, total_authors
            """)
            record = result.single()

            # Get year range
            year_result = session.run("""
                MATCH (p:Paper)
                RETURN min(p.publication_year) as min_year, max(p.publication_year) as max_year
            """)
            year_record = year_result.single()

            return {
                "total_papers": record["total_papers"],
                "total_theories": record["total_theories"],
                "total_methods": record["total_methods"],
                "total_phenomena": record["total_phenomena"],
                "total_authors": record["total_authors"],
                "year_range": {
                    "start": year_record["min_year"],
                    "end": year_record["max_year"]
                },
                "periods_covered": len(TIME_PERIODS)
            }

    finally:
        driver.close()


# ============================================================================
# Include router in main app (add this to api_server.py):
# from research_analytics_endpoints import router as research_router
# app.include_router(research_router)
# ============================================================================
