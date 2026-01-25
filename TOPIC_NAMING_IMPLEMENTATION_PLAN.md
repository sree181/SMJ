# Topic Naming Implementation Plan

## Overview

Generate descriptive topic names using OpenAI (as a senior strategy management professor) and persist them to Neo4j for reuse across queries and visualizations.

---

## Architecture Design

### 1. Neo4j Schema Design

**New Node Type: `Topic`**

Properties:
- `topic_id`: Unique identifier (format: `{interval}_{cluster_id}`, e.g., `1985-1989_0`)
- `name`: Generated topic name (e.g., "Strategic Alliances and Partnerships")
- `cluster_id`: Original cluster ID within the interval
- `interval`: Time period (e.g., "1985-1989")
- `start_year`: Start year of interval
- `end_year`: End year of interval
- `paper_count`: Number of papers in this topic
- `coherence`: Topic coherence score (0-1)
- `generated_at`: Timestamp when name was generated
- `generation_method`: "openai" or "fallback"

**Relationships:**
- `(Paper)-[:BELONGS_TO_TOPIC]->(Topic)`: Links papers to their topic cluster
- `(Topic)-[:REPRESENTED_BY]->(Paper)`: Links to representative paper

**Indexes:**
- `CREATE INDEX topic_id_index FOR (t:Topic) ON (t.topic_id)`
- `CREATE INDEX topic_interval_index FOR (t:Topic) ON (t.interval)`

---

## Implementation Steps

### Step 1: Create Topic Name Generation Function

**Location**: `advanced_analytics_endpoints.py`

**Function**: `_generate_topic_name_with_openai(cluster_papers, interval)`

**Input**:
- `cluster_papers`: List of (paper_id, title, abstract) tuples
- `interval`: Time period string (e.g., "1985-1989")

**Process**:
1. Collect paper titles and abstracts (top 5-10 papers for context)
2. Create role-based prompt as senior strategy management professor
3. Call OpenAI API
4. Extract and validate topic name
5. Return name

**Prompt Template**:
```
You are a senior professor of Strategic Management with 30+ years of research experience. 
You are analyzing a cluster of research papers from Strategic Management Journal to identify 
the core research topic they represent.

Time Period: {interval}

Papers in this cluster:
{paper_titles_and_abstracts}

Based on your expertise in strategic management research, provide a concise, descriptive 
topic name (2-5 words) that captures the central research theme of these papers. 

The name should:
- Be specific and meaningful to strategy researchers
- Use standard academic terminology
- Capture the core theoretical or empirical focus
- Be concise (avoid long phrases)

Respond with ONLY the topic name, nothing else.
```

**Example Output**: "Strategic Alliances and Partnerships", "Resource-Based Competitive Advantage", "CEO Characteristics and Firm Performance"

---

### Step 2: Modify `calculate_topic_evolution` Method

**Changes**:
1. After clustering, for each topic:
   - Check if topic name exists in Neo4j (by `topic_id`)
   - If exists, use stored name
   - If not, generate name using OpenAI
   - Store name in Neo4j
   - Store topic node and relationships

2. Add topic name to topic dictionary:
   ```python
   topics.append({
       'cluster_id': cluster_id,
       'topic_id': f"{interval}_{cluster_id}",
       'name': topic_name,  # NEW: Generated or retrieved name
       'paper_count': len(cluster_papers),
       'coherence': float(coherence),
       'representative_paper': {...},
       'paper_ids': [...]
   })
   ```

---

### Step 3: Neo4j Persistence Logic

**Function**: `_persist_topic_to_neo4j(topic_data, interval, start_year, end_year)`

**Cypher Query**:
```cypher
// Create or update Topic node
MERGE (t:Topic {topic_id: $topic_id})
SET t.name = $name,
    t.cluster_id = $cluster_id,
    t.interval = $interval,
    t.start_year = $start_year,
    t.end_year = $end_year,
    t.paper_count = $paper_count,
    t.coherence = $coherence,
    t.generated_at = datetime(),
    t.generation_method = $generation_method

// Link representative paper
WITH t
MATCH (p:Paper {paper_id: $representative_paper_id})
MERGE (t)-[:REPRESENTED_BY]->(p)

// Link all papers in cluster
WITH t
UNWIND $paper_ids AS paper_id
MATCH (p:Paper {paper_id: paper_id})
MERGE (p)-[:BELONGS_TO_TOPIC]->(t)
```

---

### Step 4: Retrieve Existing Topic Names

**Function**: `_get_topic_names_from_neo4j(interval, cluster_ids)`

**Cypher Query**:
```cypher
MATCH (t:Topic)
WHERE t.interval = $interval AND t.cluster_id IN $cluster_ids
RETURN t.topic_id, t.name, t.cluster_id
```

**Purpose**: Avoid regenerating names for existing topics (cost savings)

---

### Step 5: Update API Response

The `calculate_topic_evolution` method already returns topics. We just need to ensure `name` is included:

```python
{
    'interval': '1985-1989',
    'topics': [
        {
            'cluster_id': 0,
            'topic_id': '1985-1989_0',
            'name': 'Strategic Alliances and Partnerships',  # NEW
            'paper_count': 12,
            'coherence': 0.78,
            'representative_paper': {...},
            'paper_ids': [...]
        },
        ...
    ]
}
```

---

### Step 6: Update Frontend

**File**: `AdvancedAnalyticsDashboard.js`

**Changes**:
1. Use `topic.name` instead of representative paper title
2. Fallback to representative paper title if name not available
3. Display topic name in:
   - Pie chart labels
   - Tooltips
   - Topic list below charts

---

## Error Handling & Fallbacks

### Fallback Strategy:
1. **If OpenAI API fails**: Use representative paper title
2. **If OpenAI returns invalid response**: Use representative paper title
3. **If topic name too long**: Truncate to 50 characters
4. **If no papers in cluster**: Use "Topic {cluster_id}"

### Caching Strategy:
- Check Neo4j first before calling OpenAI
- Store generated names to avoid repeated API calls
- Batch generate names for efficiency (optional)

---

## Cost Considerations

**OpenAI API Costs**:
- ~100-200 tokens per topic name generation
- If 8 intervals × 10 topics = 80 topics
- ~8,000-16,000 tokens per full calculation
- Cost: ~$0.01-0.02 per full topic evolution calculation

**Optimization**:
- Only generate names for new topics
- Cache names in Neo4j
- Reuse names across queries

---

## Benefits

1. **Better UX**: Descriptive names instead of "Topic 1", "Topic 2"
2. **Persistence**: Names stored in Neo4j for future queries
3. **Consistency**: Same topic gets same name across queries
4. **Queryability**: Can query topics by name in Neo4j
5. **Academic Quality**: Names generated by "expert" persona

---

## Implementation Order

1. ✅ Create topic name generation function
2. ✅ Add Neo4j persistence logic
3. ✅ Modify `calculate_topic_evolution` to generate/store names
4. ✅ Update API response structure
5. ✅ Update frontend to use topic names
6. ✅ Test with sample data
7. ✅ Deploy and verify

---

## Example Flow

```
1. calculate_topic_evolution() called
2. K-means clustering identifies topics
3. For each topic:
   a. Check Neo4j: Does topic_id exist?
   b. If yes: Retrieve name from Neo4j
   c. If no: 
      - Collect paper titles/abstracts
      - Call OpenAI with professor prompt
      - Extract topic name
      - Store in Neo4j
      - Create Topic node and relationships
4. Return topics with names in API response
5. Frontend displays topic names in pie charts
```

---

## Testing Strategy

1. **Unit Test**: Topic name generation function
2. **Integration Test**: Neo4j persistence
3. **End-to-End Test**: Full flow from clustering to UI display
4. **Cost Test**: Verify OpenAI API usage is reasonable
