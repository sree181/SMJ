# Topic Naming Implementation - Complete ✅

## Overview

Successfully implemented OpenAI-based topic name generation with Neo4j persistence. Topic clusters are now named by a "senior strategy management professor" persona and stored in Neo4j for reuse.

---

## Implementation Summary

### 1. ✅ Backend Functions Created

**File**: `advanced_analytics_endpoints.py`

#### `_generate_topic_name_with_openai(cluster_papers, interval)`
- **Purpose**: Generate descriptive topic names using OpenAI
- **Role**: Senior professor of Strategic Management (30+ years experience)
- **Input**: List of (paper_id, title, abstract) tuples from cluster
- **Output**: Concise topic name (2-5 words)
- **Fallback**: Uses representative paper title if OpenAI fails
- **Cost**: ~100-200 tokens per topic (~$0.01-0.02 per full calculation)

#### `_get_topic_names_from_neo4j(interval, cluster_ids)`
- **Purpose**: Retrieve existing topic names to avoid regeneration
- **Returns**: Dictionary mapping cluster_id → topic name
- **Benefit**: Cost savings by reusing existing names

#### `_persist_topic_to_neo4j(topic_data, interval, start_year, end_year)`
- **Purpose**: Store Topic nodes and relationships in Neo4j
- **Creates**:
  - `Topic` node with properties (name, cluster_id, interval, etc.)
  - `(Paper)-[:BELONGS_TO_TOPIC]->(Topic)` relationships
  - `(Topic)-[:REPRESENTED_BY]->(Paper)` relationship

---

### 2. ✅ Neo4j Schema

**New Node Type**: `Topic`

**Properties**:
- `topic_id`: Unique ID (format: `{interval}_{cluster_id}`)
- `name`: Generated topic name
- `cluster_id`: Cluster ID within interval
- `interval`: Time period (e.g., "1985-1989")
- `start_year`, `end_year`: Interval boundaries
- `paper_count`: Number of papers in cluster
- `coherence`: Topic coherence score
- `generated_at`: Timestamp
- `generation_method`: "openai" or "fallback"

**Relationships**:
- `(Paper)-[:BELONGS_TO_TOPIC]->(Topic)`: Links papers to topics
- `(Topic)-[:REPRESENTED_BY]->(Paper)`: Links to representative paper

**Indexes** (created by `create_topic_indexes.py`):
- `topic_id_index`: On `Topic.topic_id`
- `topic_interval_index`: On `Topic.interval`
- `topic_interval_cluster_index`: Composite on `(interval, cluster_id)`

---

### 3. ✅ Integration with `calculate_topic_evolution`

**Modified Flow**:
1. Perform K-means clustering (existing)
2. **NEW**: Check Neo4j for existing topic names
3. **NEW**: For each topic:
   - If name exists → use it
   - If not → generate with OpenAI
   - Fallback to representative paper title if generation fails
4. **NEW**: Persist topic to Neo4j
5. Return topics with `name` field included

**API Response Structure**:
```json
{
  "intervals": [
    {
      "interval": "1985-1989",
      "topics": [
        {
          "cluster_id": 0,
          "topic_id": "1985-1989_0",
          "name": "Strategic Alliances and Partnerships",  // NEW
          "paper_count": 12,
          "coherence": 0.78,
          "representative_paper": {...},
          "paper_ids": [...]
        }
      ]
    }
  ]
}
```

---

### 4. ✅ Frontend Updates

**File**: `AdvancedAnalyticsDashboard.js`

**Changes**:
- Pie chart labels now use `topic.name` (generated name)
- Falls back to representative paper title if name not available
- Tooltip shows full topic name
- Topic list displays:
  - Generated name prominently
  - Representative paper title in parentheses (if different)
  - Coherence percentage

**Display Priority**:
1. Generated topic name (if available)
2. Representative paper title (fallback)
3. "Topic X" (last resort)

---

### 5. ✅ Index Creation Script

**File**: `create_topic_indexes.py`

**Purpose**: One-time setup to create Neo4j indexes

**Usage**:
```bash
python3 create_topic_indexes.py
```

**Creates**:
- Index on `topic_id` (unique lookups)
- Index on `interval` (time-based queries)
- Composite index on `(interval, cluster_id)` (efficient lookups)

---

## OpenAI Prompt Design

**Role**: Senior Professor of Strategic Management

**Prompt Structure**:
```
You are a senior professor of Strategic Management with 30+ years of research experience...

Time Period: {interval}

Papers in this cluster:
{paper_titles_and_abstracts}

Based on your expertise, provide a concise, descriptive topic name (2-5 words)...
```

**Requirements**:
- Specific and meaningful to strategy researchers
- Standard academic terminology
- Captures core theoretical/empirical focus
- Concise (2-5 words)
- Reflects dominant theme

**Example Outputs**:
- "Strategic Alliances and Partnerships"
- "Resource-Based Competitive Advantage"
- "CEO Characteristics and Firm Performance"
- "Innovation and Dynamic Capabilities"

---

## Cost Analysis

**Per Topic**:
- Input: ~100-200 tokens (paper titles + abstracts)
- Output: ~10-20 tokens (topic name)
- **Total**: ~110-220 tokens per topic

**Per Full Calculation** (8 intervals × 10 topics = 80 topics):
- **Total tokens**: ~8,800-17,600
- **Cost**: ~$0.01-0.02 (using gpt-4-turbo-preview)

**Optimization**:
- Names cached in Neo4j (one-time generation)
- Only new topics trigger OpenAI calls
- Subsequent queries use cached names (zero cost)

---

## Error Handling & Fallbacks

1. **OpenAI API fails** → Use representative paper title
2. **OpenAI returns invalid response** → Use representative paper title
3. **Topic name too long** → Truncate to 60 characters
4. **No papers in cluster** → Use "Topic {cluster_id}"
5. **Neo4j persistence fails** → Log error but continue (name still returned in API)

---

## Testing Checklist

- [ ] Run `create_topic_indexes.py` to create Neo4j indexes
- [ ] Call `/api/analytics/topics/evolution` endpoint
- [ ] Verify topic names are generated and stored
- [ ] Check Neo4j for Topic nodes
- [ ] Verify frontend displays topic names in pie charts
- [ ] Test fallback behavior (disable OpenAI API key)
- [ ] Verify names are reused on subsequent calls

---

## Next Steps

1. **Run index creation script**:
   ```bash
   python3 create_topic_indexes.py
   ```

2. **Test topic evolution endpoint**:
   - First call will generate names (takes longer, costs ~$0.01-0.02)
   - Subsequent calls will use cached names (fast, no cost)

3. **Verify in UI**:
   - Go to "Topics Proportions" tab
   - Pie charts should show generated topic names
   - Tooltips should show full names

4. **Monitor logs**:
   - Check for "Generated topic name: ..." messages
   - Check for "Using existing topic name for ..." messages
   - Verify Neo4j persistence success

---

## Files Modified

1. `advanced_analytics_endpoints.py`:
   - Added `_generate_topic_name_with_openai()`
   - Added `_get_topic_names_from_neo4j()`
   - Added `_persist_topic_to_neo4j()`
   - Modified `calculate_topic_evolution()` to integrate naming

2. `src/components/screens/AdvancedAnalyticsDashboard.js`:
   - Updated pie chart to use `topic.name`
   - Updated topic list to display generated names
   - Added fallback logic

3. `create_topic_indexes.py` (NEW):
   - Script to create Neo4j indexes

---

## Benefits

✅ **Better UX**: Descriptive names instead of "Topic 1", "Topic 2"  
✅ **Persistence**: Names stored in Neo4j for future queries  
✅ **Consistency**: Same topic = same name across queries  
✅ **Queryability**: Can query topics by name in Neo4j  
✅ **Academic Quality**: Expert-generated names  
✅ **Cost Efficient**: One-time generation, cached forever  

---

## Example Neo4j Queries

**Find all topics in an interval**:
```cypher
MATCH (t:Topic {interval: "1985-1989"})
RETURN t.name, t.paper_count, t.coherence
ORDER BY t.paper_count DESC
```

**Find papers in a specific topic**:
```cypher
MATCH (t:Topic {name: "Strategic Alliances and Partnerships"})<-[:BELONGS_TO_TOPIC]-(p:Paper)
RETURN p.title, p.year
ORDER BY p.year
```

**Find topics across intervals**:
```cypher
MATCH (t:Topic)
WHERE t.name CONTAINS "Strategic"
RETURN t.name, t.interval, t.paper_count
ORDER BY t.interval
```
