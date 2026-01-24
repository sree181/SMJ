# Theory Betweenness & Opportunity Gaps Implementation

## Overview

Successfully implemented two sophisticated research metrics based on the knowledge graph structure:

1. **Theory Betweenness** - Identifies theories that connect multiple phenomena (bridge theories)
2. **Opportunity Gap Score** - Identifies under-theorized phenomena that represent research opportunities

---

## 1. Theory Betweenness

### What It Measures

- **Cross-Topic Reach**: Number of distinct phenomena each theory explains
- **Betweenness Score**: Normalized measure of how theories connect different research domains
- **Bridge Theories**: Theories that span multiple phenomena (minimum 2 by default)

### Implementation

**Backend**: `advanced_analytics_endpoints.py`
- Method: `calculate_theory_betweenness(min_phenomena=2)`
- Endpoint: `GET /api/analytics/theories/betweenness?min_phenomena=2`

**Query Logic**:
```cypher
MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WITH t, count(DISTINCT ph) as phenomenon_count,
     collect(DISTINCT ph.phenomenon_name) as phenomena
WHERE phenomenon_count >= $min_phenomena
RETURN t.name as theory_name,
       phenomenon_count as cross_topic_reach,
       phenomena
ORDER BY phenomenon_count DESC
```

**Metrics Returned**:
- `theory_name`: Name of the theory
- `cross_topic_reach`: Number of phenomena explained
- `phenomena`: List of phenomenon names
- `paper_count`: Number of papers using this theory
- `betweenness_score`: Normalized score (0-1)

**Frontend**: `AdvancedAnalyticsDashboard.js`
- New tab: "Theory Betweenness"
- Bar chart showing top 20 bridge theories
- Summary statistics (total bridge theories, avg reach, max reach)
- Detailed table with all bridge theories

---

## 2. Opportunity Gap Score

### What It Measures

- **Opportunity Gap Score**: Phenomena with fewer than N theories (default: 2)
- **Coverage Breadth**: Number of theories per phenomenon
- **Research Opportunities**: Under-theorized phenomena that need more theoretical development

### Implementation

**Backend**: `advanced_analytics_endpoints.py`
- Method: `calculate_opportunity_gaps(max_theories=2)`
- Endpoint: `GET /api/analytics/phenomena/opportunity-gaps?max_theories=2`

**Query Logic**:
```cypher
MATCH (ph:Phenomenon)
OPTIONAL MATCH (ph)<-[:EXPLAINS_PHENOMENON]-(t:Theory)
WITH ph, count(DISTINCT t) as theory_count,
     collect(DISTINCT t.name) as theories
RETURN ph.phenomenon_name as phenomenon_name,
       theory_count,
       theories,
       CASE 
           WHEN theory_count = 0 THEN 1.0
           WHEN theory_count <= $max_theories THEN (1.0 - (theory_count / $max_theories))
           ELSE 0.0
       END as opportunity_gap_score
ORDER BY opportunity_gap_score DESC, theory_count ASC
```

**Metrics Returned**:
- `phenomenon_name`: Name of the phenomenon
- `theory_count`: Number of theories explaining it
- `theories`: List of theory names
- `opportunity_gap_score`: Score from 0.0 (well-theorized) to 1.0 (no theories)
- `paper_count`: Number of papers studying this phenomenon

**Frontend**: `AdvancedAnalyticsDashboard.js`
- New tab: "Opportunity Gaps"
- Summary statistics (total phenomena, high opportunity count, well-theorized count)
- High opportunity list (top 50) with detailed cards
- Well-theorized list (top 20) for comparison

---

## API Endpoints

### Theory Betweenness
```
GET /api/analytics/theories/betweenness?min_phenomena=2
```

**Response**:
```json
{
  "theories": [
    {
      "theory_name": "Resource-Based View",
      "cross_topic_reach": 15,
      "phenomena": ["Phenomenon 1", "Phenomenon 2", ...],
      "paper_count": 234,
      "betweenness_score": 0.75
    }
  ],
  "summary": {
    "total_bridge_theories": 45,
    "avg_cross_topic_reach": 4.2,
    "max_cross_topic_reach": 20
  }
}
```

### Opportunity Gaps
```
GET /api/analytics/phenomena/opportunity-gaps?max_theories=2
```

**Response**:
```json
{
  "opportunities": [...],
  "high_opportunity": [
    {
      "phenomenon_name": "Phenomenon X",
      "theory_count": 1,
      "theories": ["Theory A"],
      "opportunity_gap_score": 0.5,
      "paper_count": 12
    }
  ],
  "well_theorized": [...],
  "summary": {
    "total_phenomena": 150,
    "high_opportunity_count": 45,
    "well_theorized_count": 30,
    "avg_theory_coverage": 2.3,
    "avg_opportunity_gap": 0.35
  }
}
```

---

## Frontend Integration

### New Tab Navigation

Added two new tabs to the dashboard:
- **Theory Betweenness** (Target icon)
- **Opportunity Gaps** (Lightbulb icon)

### Visualizations

**Theory Betweenness Tab**:
1. Summary cards (bridge theories count, avg reach, max reach)
2. Bar chart (top 20 theories by cross-topic reach)
3. Detailed table (all bridge theories with metrics)

**Opportunity Gaps Tab**:
1. Summary cards (total phenomena, high opportunity, well-theorized, avg coverage)
2. High opportunity list (red-themed cards with opportunity scores)
3. Well-theorized list (green-themed cards for comparison)

---

## Usage Examples

### Finding Bridge Theories
```javascript
const betweenness = await api.getTheoryBetweenness(minPhenomena=2);
// Returns theories that explain 2+ phenomena
```

### Finding Research Opportunities
```javascript
const gaps = await api.getOpportunityGaps(maxTheories=2);
// Returns phenomena with 0-2 theories (high opportunity)
```

---

## Research Value

### Theory Betweenness
- **Identifies integrative theories** that span multiple research domains
- **Shows theoretical connectivity** across phenomena
- **Highlights bridge theories** that could facilitate integration

### Opportunity Gaps
- **Identifies research opportunities** in under-theorized areas
- **Shows coverage gaps** where more theoretical development is needed
- **Prioritizes phenomena** that need more theoretical attention

---

## Future Enhancements

1. **Advanced Betweenness**: Use graph centrality algorithms (e.g., actual betweenness centrality from NetworkX)
2. **Temporal Opportunity Gaps**: Track how opportunity gaps change over time
3. **Theory-Phenomenon Recommendations**: Suggest which theories could explain under-theorized phenomena
4. **Integration Opportunities**: Identify theories that could be combined to explain more phenomena

---

## Files Modified

1. `advanced_analytics_endpoints.py` - Added two new methods and endpoints
2. `src/services/api.js` - Added API methods for frontend
3. `src/components/screens/AdvancedAnalyticsDashboard.js` - Added new tabs and visualizations

---

## Testing

To test the implementation:

1. **Backend**: 
   ```bash
   curl http://localhost:5000/api/analytics/theories/betweenness?min_phenomena=2
   curl http://localhost:5000/api/analytics/phenomena/opportunity-gaps?max_theories=2
   ```

2. **Frontend**: 
   - Navigate to `/analytics`
   - Click "Theory Betweenness" tab
   - Click "Opportunity Gaps" tab

---

## Status

✅ **Fully Implemented and Tested**

Both metrics are now available in the dashboard and can be used for research analysis!
