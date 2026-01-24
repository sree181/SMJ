# Advanced Analytics Dashboard

## Overview

A comprehensive dashboard with sophisticated metrics powered by Graph RAG, analyzing research trends from 1985-2025 in 5-year intervals.

---

## Features

### 1. Paper Counts by 5-Year Intervals

**Endpoint**: `GET /api/analytics/papers/by-interval`

**Metrics**:
- Total papers per interval
- Paper distribution over time
- Peak intervals identification

**Visualization**: Bar chart showing paper counts

---

### 2. Topic Evolution (1985-2025)

**Endpoint**: `GET /api/analytics/topics/evolution`

**Sophisticated Metrics**:

#### Topic Clustering
- **K-means clustering** on paper embeddings (384-dim vectors)
- Optimal cluster count determined per interval
- Representative papers identified (closest to centroid)

#### Coherence
- Average cosine similarity within each topic cluster
- Measures how similar papers are within a topic
- Higher = more coherent topic

#### Diversity
- Shannon entropy of topic distribution
- Measures topic diversity (0 = single topic, 1 = maximum diversity)
- Higher = more diverse research landscape

#### Stability
- Cosine similarity of topic centroids across intervals
- Measures how topics persist over time
- Higher = more stable topics

#### Emerging Topics
- New topic clusters not present in previous interval
- Identified by centroid similarity < 0.7 threshold

#### Declining Topics
- Topic clusters from previous interval not found in current
- Indicates topics losing research attention

**Visualization**: Area chart with topic count, coherence, diversity, stability

---

### 3. Theoretical Evolution & Divergence (1985-2025)

**Endpoint**: `GET /api/analytics/theories/evolution-divergence`

**Sophisticated Metrics**:

#### Diversity (Shannon Entropy)
- Measures distribution of theory usage
- 0 = single dominant theory, 1 = maximum diversity
- Higher = more diverse theoretical landscape

#### Concentration (Gini Coefficient)
- Measures inequality in theory usage
- 0 = equal usage, 1 = one theory dominates
- Higher = more concentrated field

#### Fragmentation Index
- Inverse of concentration (1 - Gini)
- Measures field fragmentation
- Higher = more fragmented (many theories, none dominant)

#### Divergence (Jensen-Shannon Divergence)
- Measures change in theory distribution between intervals
- 0 = identical distribution, 1 = completely different
- Higher = more theoretical change/divergence

#### Emergence Rate
- New theories per interval normalized by total papers
- Measures rate of theoretical innovation
- Higher = more new theories emerging

#### Theory-Phenomenon Coupling
- Number of phenomena each theory explains
- Measures theoretical scope
- Higher = theory explains more phenomena

**Visualization**: Multi-line chart with diversity, concentration, fragmentation, divergence, emergence rate

---

## Technical Implementation

### Backend

**File**: `advanced_analytics_endpoints.py`

**Key Components**:
- `AdvancedAnalytics` class with Graph RAG integration
- Embedding-based topic clustering
- Sophisticated statistical metrics
- Temporal analysis across intervals

**Dependencies**:
- `sentence-transformers` (embeddings)
- `scikit-learn` (clustering, similarity)
- `numpy`, `scipy` (statistical calculations)
- `neo4j` (graph database)

### Frontend

**File**: `src/components/screens/AdvancedAnalyticsDashboard.js`

**Features**:
- Real-time data loading
- Interactive charts (Recharts)
- Summary statistics cards
- Emerging/declining topics display
- Top theories by interval

**Charts**:
- Bar chart: Paper counts
- Area chart: Topic evolution metrics
- Line chart: Theory evolution metrics

---

## API Endpoints

### 1. Paper Counts
```
GET /api/analytics/papers/by-interval?start_year=1985&end_year=2025
```

**Response**:
```json
{
  "intervals": [
    {
      "interval": "1985-1989",
      "start_year": 1985,
      "end_year": 1989,
      "count": 10,
      "paper_ids": ["1985_123", ...]
    },
    ...
  ]
}
```

### 2. Topic Evolution
```
GET /api/analytics/topics/evolution?start_year=1985&end_year=2025
```

**Response**:
```json
{
  "intervals": [
    {
      "interval": "1985-1989",
      "topics": [
        {
          "cluster_id": 0,
          "paper_count": 5,
          "coherence": 0.75,
          "representative_paper": {
            "paper_id": "1985_123",
            "title": "..."
          }
        }
      ],
      "topic_count": 3,
      "coherence": 0.72,
      "diversity": 0.85,
      "stability": 0.65,
      "emerging_topics": [...],
      "declining_topics": [...]
    }
  ],
  "summary": {
    "total_intervals": 8,
    "avg_topics_per_interval": 4.2,
    "avg_coherence": 0.70,
    "avg_diversity": 0.82
  }
}
```

### 3. Theory Evolution & Divergence
```
GET /api/analytics/theories/evolution-divergence?start_year=1985&end_year=2025
```

**Response**:
```json
{
  "intervals": [
    {
      "interval": "1985-1989",
      "theories": {
        "Resource-Based View": {
          "usage_count": 15,
          "paper_count": 12,
          "phenomenon_count": 8
        }
      },
      "theory_count": 25,
      "diversity": 0.78,
      "concentration": 0.35,
      "fragmentation_index": 0.65,
      "divergence": 0.12,
      "emergence_rate": 0.05
    }
  ],
  "summary": {
    "total_intervals": 8,
    "avg_diversity": 0.75,
    "avg_concentration": 0.40,
    "avg_fragmentation": 0.60,
    "trend": "increasing"
  }
}
```

---

## Accessing the Dashboard

### Via Frontend
1. Navigate to: `http://localhost:3000/analytics`
2. Or click "Analytics Dashboard" button on main dashboard

### Via API
- Direct API calls to endpoints above
- Use with custom frontend or analysis tools

---

## Metrics Interpretation

### Topic Evolution Metrics

**Coherence (0-1)**:
- > 0.7: Highly coherent topics
- 0.5-0.7: Moderately coherent
- < 0.5: Fragmented topics

**Diversity (0-1)**:
- > 0.8: Very diverse research
- 0.5-0.8: Moderate diversity
- < 0.5: Concentrated research

**Stability (0-1)**:
- > 0.7: Stable topics over time
- 0.4-0.7: Moderate stability
- < 0.4: Rapidly changing topics

### Theory Evolution Metrics

**Diversity (0-1)**:
- > 0.8: Many theories, balanced usage
- 0.5-0.8: Moderate diversity
- < 0.5: Few dominant theories

**Concentration (0-1)**:
- > 0.6: Highly concentrated (few theories dominate)
- 0.3-0.6: Moderate concentration
- < 0.3: Distributed (many theories)

**Fragmentation (0-1)**:
- > 0.7: Highly fragmented field
- 0.4-0.7: Moderate fragmentation
- < 0.4: Coherent field

**Divergence (0-1)**:
- > 0.3: Significant theoretical change
- 0.1-0.3: Moderate change
- < 0.1: Stable theoretical landscape

---

## Performance Considerations

### Computation Time
- **Paper counts**: < 1 second
- **Topic evolution**: 30-60 seconds (clustering + embeddings)
- **Theory evolution**: 5-10 seconds (statistical calculations)

### Optimization
- Results can be cached for faster subsequent requests
- Clustering can be pre-computed and stored
- Embeddings are already generated (fast retrieval)

---

## Future Enhancements

1. **Caching**: Cache results for faster loading
2. **Pre-computation**: Pre-compute metrics for common intervals
3. **Interactive Filters**: Filter by theory, method, phenomenon
4. **Export**: Export data as CSV/JSON
5. **Comparative Analysis**: Compare different time periods
6. **Predictive Analytics**: Forecast future trends
7. **Network Analysis**: Theory-phenomenon network evolution

---

## Troubleshooting

### Slow Loading
- First request may take 30-60 seconds (computing metrics)
- Subsequent requests are faster (Neo4j caching)
- Consider pre-computing for common intervals

### Missing Data
- Ensure embeddings are generated (`generate_all_embeddings.py`)
- Check Neo4j has papers with years
- Verify theories and phenomena are ingested

### Clustering Issues
- Need at least 3 papers per interval for clustering
- Very small intervals may have limited metrics

---

## Summary

The Advanced Analytics Dashboard provides:
- ✅ Paper counts by 5-year intervals
- ✅ Topic evolution with sophisticated metrics
- ✅ Theoretical evolution and divergence analysis
- ✅ Graph RAG-powered insights
- ✅ Interactive visualizations
- ✅ Comprehensive statistical analysis

**Access**: `http://localhost:3000/analytics`
