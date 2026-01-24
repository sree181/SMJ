# How Connection Strength is Stored in Neo4j

## Overview

When we create a connection between a Theory and a Phenomenon, we store all the connection strength information directly on the relationship in Neo4j.

---

## Graph Structure

### Nodes
- **Theory** node: Represents a theoretical framework (e.g., "Resource-Based View")
- **Phenomenon** node: Represents a research phenomenon (e.g., "Resource allocation patterns")

### Relationship
- **EXPLAINS_PHENOMENON**: The relationship connecting Theory to Phenomenon

---

## Relationship Properties

When we create the `EXPLAINS_PHENOMENON` relationship, we store **8 properties** on it:

### 1. `connection_strength` (Float)
- **What it is**: The final calculated score (0.0 to 1.0)
- **Example**: `0.850`
- **Purpose**: The main score that tells you how strong the connection is

### 2. `role_weight` (Float)
- **What it is**: Points from Clue 1 (Theory importance)
- **Example**: `0.400`
- **Purpose**: Shows how much the theory's role contributed to the score

### 3. `section_score` (Float)
- **What it is**: Points from Clue 2 (Section proximity)
- **Example**: `0.200`
- **Purpose**: Shows how much being in the same section contributed

### 4. `keyword_score` (Float)
- **What it is**: Points from Clue 3 (Keyword overlap)
- **Example**: `0.200`
- **Purpose**: Shows how much shared words contributed

### 5. `semantic_score` (Float)
- **What it is**: Points from Clue 4 (Semantic similarity)
- **Example**: `0.150`
- **Purpose**: Shows how much meaning similarity contributed

### 6. `explicit_bonus` (Float)
- **What it is**: Points from Clue 5 (Explicit mention)
- **Example**: `0.050`
- **Purpose**: Shows how much explicit mention contributed

### 7. `paper_id` (String)
- **What it is**: ID of the paper where this connection was found
- **Example**: `"paper_2020_001"`
- **Purpose**: Tracks which paper(s) contain this connection

### 8. `theory_role` (String)
- **What it is**: The role of the theory in the paper
- **Example**: `"primary"` or `"supporting"`
- **Purpose**: Records how the theory was used

### 9. `section` (String, Optional)
- **What it is**: The section where the theory was mentioned
- **Example**: `"introduction"` or `"literature_review"`
- **Purpose**: Records where in the paper this connection appears

---

## Visual Representation

```
┌─────────────────┐
│  Theory Node    │
│                 │
│  name:          │
│  "Resource-     │
│   Based View"   │
└────────┬────────┘
         │
         │ EXPLAINS_PHENOMENON
         │ {
         │   connection_strength: 0.850,
         │   role_weight: 0.400,
         │   section_score: 0.200,
         │   keyword_score: 0.200,
         │   semantic_score: 0.150,
         │   explicit_bonus: 0.050,
         │   paper_id: "paper_2020_001",
         │   theory_role: "primary",
         │   section: "introduction"
         │ }
         │
         ▼
┌─────────────────┐
│ Phenomenon Node │
│                 │
│  phenomenon_    │
│  name:          │
│  "Resource      │
│   allocation    │
│   patterns"     │
└─────────────────┘
```

---

## Actual Neo4j Cypher Query

Here's the exact code that creates the relationship:

```cypher
MATCH (t:Theory {name: $theory_name})
MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
MERGE (t)-[r:EXPLAINS_PHENOMENON {
    paper_id: $paper_id,
    theory_role: $theory_role,
    section: $section,
    connection_strength: $connection_strength,
    role_weight: $role_weight,
    section_score: $section_score,
    keyword_score: $keyword_score,
    semantic_score: $semantic_score,
    explicit_bonus: $explicit_bonus
}]->(ph)
```

---

## Example: What Gets Stored

### Input Data
- **Theory**: "Resource-Based View" (primary, in introduction)
- **Phenomenon**: "Resource allocation patterns" (in introduction)
- **Paper ID**: "paper_2020_001"

### Calculated Scores
- `connection_strength`: 0.850
- `role_weight`: 0.400
- `section_score`: 0.200
- `keyword_score`: 0.200
- `semantic_score`: 0.150
- `explicit_bonus`: 0.050

### What Gets Stored in Neo4j

```cypher
(:Theory {name: "Resource-Based View"})
  -[:EXPLAINS_PHENOMENON {
    connection_strength: 0.850,
    role_weight: 0.400,
    section_score: 0.200,
    keyword_score: 0.200,
    semantic_score: 0.150,
    explicit_bonus: 0.050,
    paper_id: "paper_2020_001",
    theory_role: "primary",
    section: "introduction"
  }]->
(:Phenomenon {phenomenon_name: "Resource allocation patterns"})
```

---

## Querying the Data

### Find All Connections with Their Strengths

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
RETURN t.name AS theory,
       ph.phenomenon_name AS phenomenon,
       r.connection_strength AS strength
ORDER BY r.connection_strength DESC
```

### Find Strong Connections Only (≥ 0.7)

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE r.connection_strength >= 0.7
RETURN t.name AS theory,
       ph.phenomenon_name AS phenomenon,
       r.connection_strength AS strength
ORDER BY r.connection_strength DESC
```

### Get Full Breakdown of Factors

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE r.connection_strength >= 0.6
RETURN t.name AS theory,
       ph.phenomenon_name AS phenomenon,
       r.connection_strength AS total_strength,
       r.role_weight AS role,
       r.section_score AS section,
       r.keyword_score AS keywords,
       r.semantic_score AS semantic,
       r.explicit_bonus AS explicit
ORDER BY r.connection_strength DESC
```

### Find Connections for a Specific Paper

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE r.paper_id = "paper_2020_001"
RETURN t.name AS theory,
       ph.phenomenon_name AS phenomenon,
       r.connection_strength AS strength
```

### Analyze Why a Connection is Strong

```cypher
MATCH (t:Theory {name: "Resource-Based View"})
      -[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
RETURN ph.phenomenon_name AS phenomenon,
       r.connection_strength AS strength,
       r.role_weight AS "Role (40%)",
       r.section_score AS "Section (20%)",
       r.keyword_score AS "Keywords (20%)",
       r.semantic_score AS "Semantic (20%)",
       r.explicit_bonus AS "Explicit (10%)"
ORDER BY r.connection_strength DESC
```

---

## Data Types

| Property | Type | Range/Values |
|----------|------|--------------|
| `connection_strength` | Float | 0.0 to 1.0 |
| `role_weight` | Float | 0.0 to 0.4 |
| `section_score` | Float | 0.0 to 0.2 |
| `keyword_score` | Float | 0.0 to 0.2 |
| `semantic_score` | Float | 0.0 to 0.2 |
| `explicit_bonus` | Float | 0.0 to 0.1 |
| `paper_id` | String | Any paper ID |
| `theory_role` | String | "primary", "supporting", "extending", "challenging" |
| `section` | String | "introduction", "literature_review", "methodology", etc. |

---

## Why Store All Factors?

### Transparency
- You can see **exactly why** a connection got its score
- No "black box" - everything is visible

### Analysis
- You can analyze which factors contribute most
- Identify patterns (e.g., "strong connections usually have high role_weight")

### Debugging
- If a connection seems wrong, you can check each factor
- Helps improve the algorithm

### Research
- Researchers can study which factors matter most
- Can validate the scoring system

---

## Storage Efficiency

### Space Used
- Each relationship stores 9 properties
- Each property is a small value (float or string)
- **Total**: ~200-300 bytes per relationship

### Example
- 1000 Theory-Phenomenon connections
- ~250 KB total storage
- **Very efficient!**

---

## Multiple Papers, Same Connection

If the same Theory-Phenomenon connection appears in multiple papers, we create **separate relationships** for each paper:

```
(:Theory {name: "Resource-Based View"})
  -[:EXPLAINS_PHENOMENON {paper_id: "paper_2020_001", connection_strength: 0.850}]->
  (:Phenomenon {phenomenon_name: "Resource allocation patterns"})
  
  -[:EXPLAINS_PHENOMENON {paper_id: "paper_2021_005", connection_strength: 0.720}]->
  (:Phenomenon {phenomenon_name: "Resource allocation patterns"})
```

This allows us to:
- Track which papers contain each connection
- See if connection strength varies across papers
- Aggregate statistics (e.g., "average strength across all papers")

---

## Summary

**What we store**: 9 properties on each `EXPLAINS_PHENOMENON` relationship
- 1 total score (`connection_strength`)
- 5 factor scores (role_weight, section_score, keyword_score, semantic_score, explicit_bonus)
- 3 metadata fields (paper_id, theory_role, section)

**Why we store it this way**:
- ✅ Transparent (see exactly why each connection got its score)
- ✅ Queryable (can filter, sort, analyze by any factor)
- ✅ Efficient (small storage footprint)
- ✅ Traceable (know which paper each connection came from)

**Result**: A complete, transparent record of every Theory-Phenomenon connection with full scoring details!

