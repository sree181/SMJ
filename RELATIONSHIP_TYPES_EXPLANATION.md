# Relationship Types Explanation: Theory-Phenomenon Connections

## Overview

There are three different relationship types that connect theories and phenomena in the Neo4j database. Each serves a different purpose in the knowledge graph.

---

## 1. STUDIES_PHENOMENON
**Pattern**: `(Paper)-[:STUDIES_PHENOMENON]->(Phenomenon)`

### Purpose
Direct relationship indicating that a **paper studies a phenomenon**.

### When Created
- Created during paper ingestion when a paper extracts/mentions a phenomenon
- One relationship per paper-phenomenon pair

### Properties
- `context`: How the phenomenon is studied in the paper
- `section`: Where in the paper the phenomenon appears (introduction, methods, results, etc.)

### Example
```
Paper: "Strategic management during financial crisis"
Phenomenon: "Resource allocation patterns during financial crises"

(Paper {paper_id: "2010_353"})-[:STUDIES_PHENOMENON {
    context: "Examined how firms allocate resources during financial crises",
    section: "introduction"
}]->(Phenomenon {phenomenon_name: "Resource allocation patterns during financial crises"})
```

### Count
- **1,474 relationships** (as of latest inventory)
- Each represents one paper studying one phenomenon

---

## 2. EXPLAINS_PHENOMENON
**Pattern**: `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)`

### Purpose
Indicates that a **theory explains a phenomenon**, as established by a specific paper.

### When Created
- Created when a paper **both**:
  1. Uses a theory (has `USES_THEORY` relationship)
  2. Studies a phenomenon (has `STUDIES_PHENOMENON` relationship)
- **Multiple relationships can exist** between the same theory-phenomenon pair (one per paper)

### Properties
- `paper_id`: Which paper establishes this connection
- `theory_role`: How theory is used (primary, supporting, challenging, extending)
- `section`: Where connection is made
- `connection_strength`: Calculated score (0.0-1.0) based on 5 factors:
  - `role_weight`: Theory role importance (0.0-0.4)
  - `section_score`: Section alignment (0.0-0.2)
  - `keyword_score`: Keyword overlap (0.0-0.2)
  - `semantic_score`: Semantic similarity (0.0-0.2)
  - `explicit_bonus`: Explicit mentions (0.0-0.1)
- `paper_count`: Number of papers (usually 1 for individual relationships)
- `paper_ids`: List of paper IDs (usually single element)
- `created_at`: When relationship was created
- `updated_at`: When relationship was last updated

### Example
```
Theory: "Resource-Based View"
Phenomenon: "Resource allocation patterns during financial crises"
Paper: "2010_353"

(Theory {name: "Resource-Based View"})-[:EXPLAINS_PHENOMENON {
    paper_id: "2010_353",
    theory_role: "primary",
    section: "introduction",
    connection_strength: 0.75,
    role_weight: 0.3,
    section_score: 0.15,
    keyword_score: 0.15,
    semantic_score: 0.12,
    explicit_bonus: 0.03,
    paper_count: 1,
    paper_ids: ["2010_353"]
}]->(Phenomenon {phenomenon_name: "Resource allocation patterns during financial crises"})
```

### Count
- **3,640 relationships** (as of latest inventory)
- Multiple relationships can exist between same theory-phenomenon pair (one per paper)

### Key Difference from STUDIES_PHENOMENON
- **STUDIES_PHENOMENON**: Paper → Phenomenon (direct, what paper studies)
- **EXPLAINS_PHENOMENON**: Theory → Phenomenon (inferred, which theory explains which phenomenon)

---

## 3. EXPLAINS_PHENOMENON_AGGREGATED
**Pattern**: `(Theory)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(Phenomenon)`

### Purpose
**Aggregated summary** of all `EXPLAINS_PHENOMENON` relationships between a theory-phenomenon pair.

### When Created
- Created by `fix_explains_relationships.py` script
- Aggregates all individual `EXPLAINS_PHENOMENON` relationships
- **One relationship per theory-phenomenon pair** (regardless of how many papers establish it)

### Properties
- `avg_strength`: Average connection strength across all papers
- `paper_count`: Total number of papers establishing this connection
- `paper_ids`: Combined list of all paper IDs that establish this connection
- `updated_at`: When aggregation was last updated

### Example
```
Theory: "Resource-Based View"
Phenomenon: "Resource allocation patterns during financial crises"

# If 5 papers establish this connection:
(Theory {name: "Resource-Based View"})-[:EXPLAINS_PHENOMENON_AGGREGATED {
    avg_strength: 0.68,  # Average of 5 individual strengths
    paper_count: 5,      # Total papers
    paper_ids: ["2010_353", "2012_445", "2015_678", "2018_901", "2020_234"]
}]->(Phenomenon {phenomenon_name: "Resource allocation patterns during financial crises"})
```

### Count
- **3,635 relationships** (as of latest inventory)
- One per unique theory-phenomenon pair

### Key Difference from EXPLAINS_PHENOMENON
- **EXPLAINS_PHENOMENON**: Individual relationships (one per paper)
- **EXPLAINS_PHENOMENON_AGGREGATED**: Summary relationship (one per theory-phenomenon pair)

---

## Relationship Hierarchy

```
Paper "2010_353"
  ├─[:USES_THEORY]-> Theory "Resource-Based View"
  └─[:STUDIES_PHENOMENON]-> Phenomenon "Resource allocation patterns"

Theory "Resource-Based View"
  └─[:EXPLAINS_PHENOMENON {paper_id: "2010_353"}]-> Phenomenon "Resource allocation patterns"
     (Individual relationship from this paper)

Theory "Resource-Based View"
  └─[:EXPLAINS_PHENOMENON_AGGREGATED {paper_count: 5}]-> Phenomenon "Resource allocation patterns"
     (Aggregated summary of all 5 papers)
```

---

## When to Use Each

### Use STUDIES_PHENOMENON when:
- Finding which papers study a phenomenon
- Getting paper-level phenomenon data
- Understanding direct paper-phenomenon connections

### Use EXPLAINS_PHENOMENON when:
- Finding which theories explain a phenomenon (with paper-level detail)
- Getting detailed connection strength per paper
- Understanding how individual papers connect theories to phenomena

### Use EXPLAINS_PHENOMENON_AGGREGATED when:
- Finding overall theory-phenomenon connections (regardless of paper)
- Getting summary statistics (average strength, total papers)
- Performance optimization (fewer relationships to query)
- API endpoints that need aggregated data

---

## Summary Table

| Relationship | Direction | Purpose | Count | Granularity |
|--------------|-----------|---------|-------|-------------|
| **STUDIES_PHENOMENON** | Paper → Phenomenon | Direct paper-phenomenon link | 1,474 | Paper level |
| **EXPLAINS_PHENOMENON** | Theory → Phenomenon | Theory explains phenomenon (per paper) | 3,640 | Paper level |
| **EXPLAINS_PHENOMENON_AGGREGATED** | Theory → Phenomenon | Aggregated theory-phenomenon summary | 3,635 | Theory-Phenomenon pair level |

---

## Notes

1. **EXPLAINS_PHENOMENON** relationships are created during paper ingestion when both theory and phenomenon are present
2. **EXPLAINS_PHENOMENON_AGGREGATED** relationships are created by the `fix_explains_relationships.py` script
3. The aggregated version is useful for API endpoints that need fast queries without iterating through all individual relationships
4. Individual `EXPLAINS_PHENOMENON` relationships preserve paper-level detail (which paper, what strength, etc.)
