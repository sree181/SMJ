# Topical Fragmentation Analysis Endpoint

## Overview

New LLM-powered endpoint for comprehensive topical fragmentation analysis that answers: **Is the strategic management field fragmented, convergent, or coherent?**

## Endpoint

```
GET /api/research/fragmentation/{period}/analysis
```

### Parameters

- `period`: Time period string (e.g., "2015-2019", "2020-2024")

### Response

```json
{
  "metrics": {
    "period": "2015-2019",
    "total_papers": 150,
    "unique_theories": 45,
    "theories_per_paper": 1.8,
    "theory_concentration_gini": 0.65,
    "top_5_theory_share": 0.42,
    "coherence_score": 0.42,
    "fragmentation_index": 0.58,
    "dominant_theories": [...],
    "emerging_theories": [...],
    "declining_theories": [...]
  },
  "analysis": "Comprehensive LLM-generated analysis...",
  "conclusion": "fragmented|convergent|coherent",
  "evidence": {
    "theory_phenomenon_patterns": [...],
    "method_distribution": {...},
    "co_usage_patterns": [...],
    "temporal_context": {...}
  }
}
```

## Features

1. **Comprehensive Metrics**: Uses existing fragmentation metrics (Gini coefficient, top 5 share, coherence score)

2. **Additional Context**:
   - Theory-phenomenon connection patterns
   - Method diversity distribution
   - Theory co-usage patterns (theories used together)
   - Temporal comparison with previous period

3. **LLM Analysis**: 
   - Interprets metrics in context
   - Analyzes connection patterns
   - Examines method-theory relationships
   - Evaluates temporal trends
   - Provides expert-level assessment

4. **Clear Conclusion**: Classifies field as:
   - **Fragmented**: Many diverse theories, low concentration
   - **Convergent**: Field converging around dominant theories
   - **Coherent**: Balanced landscape with clear patterns

## Usage Example

```bash
# Analyze fragmentation for 2015-2019
curl "http://localhost:5000/api/research/fragmentation/2015-2019/analysis"

# Analyze fragmentation for 2020-2024
curl "http://localhost:5000/api/research/fragmentation/2020-2024/analysis"
```

## Implementation Details

- **Neo4j Queries**: Extracts theory usage, method distribution, co-usage patterns, and temporal data
- **LLM Integration**: Uses `LLMClient` from `api_server.py` to generate comprehensive analysis
- **Data Normalization**: Handles edge cases and missing data gracefully

## Testing

1. Start the backend server:
   ```bash
   cd "Strategic Management Journal"
   source ../smj/bin/activate
   python api_server.py
   ```

2. Test the endpoint:
   ```bash
   curl "http://localhost:5000/api/research/fragmentation/2020-2024/analysis" | jq
   ```

## Related Endpoints

- `GET /api/research/fragmentation/{period}` - Raw metrics only (no LLM)
- `GET /api/research/fragmentation/all` - Metrics for all periods
