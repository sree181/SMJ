# Canonical Problem & Theory-Level Measures Implementation

## Overview

Successfully implemented 5 sophisticated research metrics:

1. **Canonical Coverage Ratio** - Ratio of canonical papers by year
2. **Canonical Centrality** - Eigenvector centrality and PageRank for canonical vs non-canonical papers
3. **Theoretical Concentration Index (HHI)** - Herfindahl-Hirschman Index for theory usage
4. **Theory-Problem Alignment Score** - Alignment between theories and phenomena
5. **Integrative Theory Centrality** - Betweenness centrality of papers using each theory

---

## 1. Canonical Coverage Ratio

### Formula
```
Coverage = (# papers with canonical_problem = 1) / (Total papers)
```

### Implementation
- **Backend**: `calculate_canonical_coverage_ratio(start_year, end_year)`
- **Endpoint**: `GET /api/analytics/canonical/coverage?start_year=1985&end_year=2025`

### Notes
- Assumes Paper nodes have a `canonical_problem` property (boolean or 0/1)
- If property doesn't exist, returns 0 for all years
- Computed by year (not by interval)

### Response Format
```json
{
  "coverage_by_year": [
    {
      "year": 2020,
      "total_papers": 150,
      "canonical_papers": 45,
      "coverage_ratio": 0.30
    }
  ],
  "summary": {
    "avg_coverage": 0.25,
    "total_canonical_papers": 500,
    "total_papers": 2000
  }
}
```

---

## 2. Canonical Centrality

### Computation
1. Create subgraph of canonical papers
2. Compute eigenvector centrality and PageRank
3. Compare to non-canonical papers

### Implementation
- **Backend**: `calculate_canonical_centrality()`
- **Endpoint**: `GET /api/analytics/canonical/centrality`
- **Requires**: NetworkX library

### Metrics
- **Eigenvector Centrality**: Measures influence based on connections to influential nodes
- **PageRank**: Measures importance based on link structure
- **Comparison Ratios**: Canonical vs non-canonical averages

### Response Format
```json
{
  "canonical_centrality": {
    "eigenvector": {"paper_id": 0.123, ...},
    "pagerank": {"paper_id": 0.045, ...},
    "avg_eigenvector": 0.15,
    "avg_pagerank": 0.08,
    "paper_count": 500
  },
  "non_canonical_centrality": {
    "eigenvector": {"paper_id": 0.056, ...},
    "pagerank": {"paper_id": 0.023, ...},
    "avg_eigenvector": 0.06,
    "avg_pagerank": 0.03,
    "paper_count": 1500
  },
  "comparison": {
    "eigenvector_ratio": 2.5,
    "pagerank_ratio": 2.67
  }
}
```

---

## 3. Theoretical Concentration Index (HHI)

### Formula
```
HHI = Σ(share_i)²
where share_i = usage_count_i / total_usage
```

### Interpretation
- **High HHI (>0.25)**: High concentration → Few theories dominate
- **Moderate HHI (0.15-0.25)**: Moderate concentration
- **Low HHI (<0.15)**: Fragmented → Theories more evenly distributed

### Implementation
- **Backend**: `calculate_theoretical_concentration_index(start_year, end_year)`
- **Endpoint**: `GET /api/analytics/theories/concentration-index?start_year=1985&end_year=2025`

### Response Format
```json
{
  "intervals": [
    {
      "interval": "2020-2024",
      "hhi": 0.18,
      "theory_count": 45,
      "total_usage": 500,
      "interpretation": "moderate_concentration",
      "top_theories": [
        ["Theory A", 120],
        ["Theory B", 95]
      ]
    }
  ],
  "summary": {
    "avg_hhi": 0.20,
    "trend": "increasing"
  }
}
```

---

## 4. Theory-Problem Alignment Score

### Computation
Measures how well theories align with problems (phenomena).
- Higher alignment = theories that explain many phenomena
- **Note**: Interprets "problem" as "phenomenon" based on available data

### Implementation
- **Backend**: `calculate_theory_problem_alignment()`
- **Endpoint**: `GET /api/analytics/theories/problem-alignment`

### Response Format
```json
{
  "alignments": [
    {
      "theory_name": "Resource-Based View",
      "alignment_score": 15,
      "phenomena": ["Phenomenon 1", "Phenomenon 2", ...],
      "paper_count": 234
    }
  ],
  "summary": {
    "total_theories": 50,
    "avg_alignment": 4.2,
    "max_alignment": 20
  }
}
```

---

## 5. Integrative Theory Centrality

### Computation
1. Identify papers using each theory
2. Compute betweenness centrality of those papers
3. Average per theory

### Implementation
- **Backend**: `calculate_integrative_theory_centrality()`
- **Endpoint**: `GET /api/analytics/theories/integrative-centrality`
- **Requires**: NetworkX library

### Metrics
- **Average Betweenness**: Average betweenness centrality of papers using each theory
- Higher values = theories used by papers that bridge different research areas

### Response Format
```json
{
  "theory_centrality": {
    "Theory A": {
      "avg_betweenness": 0.045,
      "paper_count": 120,
      "papers_with_centrality": 115
    }
  },
  "summary": {
    "total_theories": 50,
    "avg_betweenness": 0.025,
    "max_betweenness": 0.08
  }
}
```

---

## API Endpoints Summary

| Measure | Endpoint | Parameters |
|---------|----------|------------|
| Canonical Coverage | `/api/analytics/canonical/coverage` | `start_year`, `end_year` |
| Canonical Centrality | `/api/analytics/canonical/centrality` | None |
| HHI Concentration | `/api/analytics/theories/concentration-index` | `start_year`, `end_year` |
| Theory-Problem Alignment | `/api/analytics/theories/problem-alignment` | None |
| Integrative Centrality | `/api/analytics/theories/integrative-centrality` | None |

---

## Dependencies

### Required
- **NetworkX**: For centrality calculations (eigenvector, PageRank, betweenness)
  ```bash
  pip install networkx
  ```

### Optional
- **SciPy**: Already used for other analytics (clustering, etc.)

---

## Notes & Limitations

### Canonical Problem Property
- The `canonical_problem` property may not exist in all Paper nodes
- If missing, canonical measures will return 0 or empty results
- **To add canonical_problem**:
  ```cypher
  MATCH (p:Paper)
  SET p.canonical_problem = false  // or true based on your criteria
  ```

### Graph Structure
- Centrality measures require paper-to-paper relationships
- Currently uses any relationship type between papers
- For better results, consider:
  - Citation relationships (`CITES`)
  - Semantic similarity relationships
  - Co-author relationships

### Performance
- Centrality calculations can be slow for large graphs (>10k nodes)
- Consider caching results or computing incrementally
- NetworkX is efficient but may need optimization for very large graphs

---

## Usage Examples

### Python
```python
import requests

# Canonical Coverage
response = requests.get('http://localhost:5000/api/analytics/canonical/coverage?start_year=2000&end_year=2020')
coverage = response.json()

# HHI Concentration
response = requests.get('http://localhost:5000/api/analytics/theories/concentration-index')
hhi = response.json()

# Theory Alignment
response = requests.get('http://localhost:5000/api/analytics/theories/problem-alignment')
alignment = response.json()
```

### JavaScript (Frontend)
```javascript
// Using the API service
const coverage = await api.getCanonicalCoverage(2000, 2020);
const hhi = await api.getTheoreticalConcentration();
const alignment = await api.getTheoryProblemAlignment();
```

---

## Status

✅ **All 5 Measures Implemented**

- ✅ Canonical Coverage Ratio
- ✅ Canonical Centrality (eigenvector + PageRank)
- ✅ Theoretical Concentration Index (HHI)
- ✅ Theory-Problem Alignment Score
- ✅ Integrative Theory Centrality

**Next Steps**: Add frontend visualizations for these measures in the dashboard.
