# Relationship Visualization - Knowledge Graph Structure

## Visual Overview

```
                    ┌─────────┐
                    │  Paper  │ (Core Entity)
                    └────┬────┘
                         │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌────────┐        ┌────────┐       ┌──────────┐
   │ Method │        │ Theory │       │ResearchQ │
   └───┬────┘        └───┬────┘       └────┬─────┘
       │                 │                  │
       │ SIMILAR_TO      │ RELATED_TO       │ RELATED_TO
       │ EVOLVED_FROM    │ EXTENDS          │ ANSWERS
       │                 │                  │
       ▼                 ▼                  ▼
   ┌────────┐        ┌────────┐       ┌──────────┐
   │ Method │        │ Theory │       │ResearchQ │
   └────────┘        └────────┘       └──────────┘
```

## Complete Relationship Map

### Paper (Central Hub)

```
Paper
  │
  ├─[:USES_METHOD {confidence, primary}]─→ Method
  │                                           │
  │                                           ├─[:SIMILAR_TO]─→ Method
  │                                           └─[:EVOLVED_FROM]─→ Method
  │
  ├─[:USES_THEORY {role}]─→ Theory
  │                           │
  │                           ├─[:RELATED_TO]─→ Theory
  │                           └─[:EXTENDS]─→ Theory
  │
  ├─[:ADDRESSES {primary}]─→ ResearchQuestion
  │                            │
  │                            ├─[:RELATED_TO]─→ ResearchQuestion
  │                            └─[:ANSWERS]─→ ResearchQuestion
  │
  ├─[:USES_VARIABLE {role}]─→ Variable
  │                             │
  │                             ├─[:RELATED_TO]─→ Variable
  │                             ├─[:MODERATES]─→ Variable
  │                             └─[:MEDIATES]─→ Variable
  │
  ├─[:REPORTS_FINDING]─→ Finding
  │                        │
  │                        ├─[:RELATED_TO]─→ Finding
  │                        ├─[:CONTRADICTS]─→ Finding
  │                        └─[:SUPPORTS]─→ Theory
  │
  ├─[:MAKES_CONTRIBUTION]─→ Contribution
  │                           │
  │                           └─[:BUILDS_ON]─→ Contribution
  │
  ├─[:USES_SOFTWARE]─→ Software
  │                      ↑
  │                      │
  │                  Method─[:IMPLEMENTED_IN]─┘
  │
  ├─[:USES_DATASET]─→ Dataset
  │
  ├─[:CITES]─→ Paper
  ├─[:SIMILAR_TO {dimensions}]─→ Paper
  ├─[:EXTENDS]─→ Paper
  └─[:REPLICATES]─→ Paper

Author─[:AUTHORED]─→ Paper
```

## Relationship Categories

### 1. Paper-to-Entity (8 relationships)
All entities connect TO Paper (Paper is the central hub):

- `Paper → Method` (USES_METHOD)
- `Paper → Theory` (USES_THEORY)
- `Paper → ResearchQuestion` (ADDRESSES)
- `Paper → Variable` (USES_VARIABLE)
- `Paper → Finding` (REPORTS_FINDING)
- `Paper → Contribution` (MAKES_CONTRIBUTION)
- `Paper → Software` (USES_SOFTWARE)
- `Paper → Dataset` (USES_DATASET)

### 2. Paper-to-Paper (4 relationships)
Papers connect to other papers:

- `Paper → Paper` (CITES) - Citation network
- `Paper → Paper` (SIMILAR_TO) - Multi-dimensional similarity
- `Paper → Paper` (EXTENDS) - Builds on
- `Paper → Paper` (REPLICATES) - Replication studies

### 3. Entity-to-Entity (12 relationships)
Entities connect to similar entities:

**Methods:**
- `Method → Method` (SIMILAR_TO)
- `Method → Method` (EVOLVED_FROM)

**Theories:**
- `Theory → Theory` (RELATED_TO)
- `Theory → Theory` (EXTENDS)

**Variables:**
- `Variable → Variable` (RELATED_TO)
- `Variable → Variable` (MODERATES)
- `Variable → Variable` (MEDIATES)

**Findings:**
- `Finding → Finding` (RELATED_TO)
- `Finding → Finding` (CONTRADICTS)
- `Finding → Theory` (SUPPORTS)

**Research Questions:**
- `ResearchQuestion → ResearchQuestion` (RELATED_TO)
- `ResearchQuestion → ResearchQuestion` (ANSWERS)

**Contributions:**
- `Contribution → Contribution` (BUILDS_ON)

**Methods to Software:**
- `Method → Software` (IMPLEMENTED_IN)

### 4. Author Relationships (1 relationship)
- `Author → Paper` (AUTHORED)

## Total Relationship Count

- **Paper-to-Entity**: 8 relationships
- **Paper-to-Paper**: 4 relationships
- **Entity-to-Entity**: 12 relationships
- **Author-to-Paper**: 1 relationship
- **Method-to-Software**: 1 relationship

**Total: 26 unique relationship types**

## Relationship Properties Summary

### Paper → Method
- `confidence` (0.0-1.0)
- `primary` (boolean)
- `context` (string)

### Paper → Theory
- `role` ("primary", "supporting", "challenging")
- `section` (string)

### Paper → Variable
- `role` ("dependent", "independent", "control", "moderator", "mediator")
- `measurement` (string)
- `operationalization` (string)

### Paper → ResearchQuestion
- `primary` (boolean)
- `section` (string)

### Paper → Finding
- `significance` (string)
- `effect_size` (float)
- `section` (string)

### Paper → Contribution
- `novelty_level` ("incremental", "moderate", "significant")
- `validated` (boolean)

### Paper → Software
- `version` (string)
- `primary` (boolean)

### Paper → Dataset
- `time_period` (string)
- `geography` (string)

### Paper → Paper (SIMILAR_TO)
- `similarity_score` (0.0-1.0)
- `similarity_dimensions` (array)
- `methodological_similarity` (float)
- `theoretical_similarity` (float)
- `topical_similarity` (float)

### Method → Method (SIMILAR_TO)
- `similarity_score` (0.0-1.0)
- `similarity_type` (string)

### Theory → Theory (RELATED_TO)
- `relationship_type` (string)
- `strength` (float)

### Variable → Variable (MODERATES)
- `moderation_type` (string)
- `direction` (string)

### Variable → Variable (MEDIATES)
- `mediation_type` (string)
- `effect_size` (float)

### Finding → Finding (CONTRADICTS)
- `contradiction_type` (string)
- `explanation` (string)

### Finding → Theory (SUPPORTS)
- `support_type` (string)
- `evidence_type` (string)

## Query Patterns

### Pattern 1: Direct Paper Query
```
Paper → Entity
```
**Example**: Find all methods used in papers from 2020

### Pattern 2: Entity-to-Entity Query
```
Paper → Entity1 → Entity2
```
**Example**: Papers using methods similar to OLS

### Pattern 3: Multi-Hop Query
```
Paper → Entity1 → Entity2 → Entity3 → Paper
```
**Example**: Papers using theories supported by findings from papers using similar methods

### Pattern 4: Circular Query
```
Paper → Entity → Entity → Paper
```
**Example**: Papers similar to papers using similar methods

## Implementation Phases

### Phase 1: Core (Current)
- Paper → Method
- Paper → Software
- Method → Method (SIMILAR_TO)

### Phase 2: Research Elements
- Paper → Theory
- Paper → ResearchQuestion
- Paper → Variable
- Theory → Theory (RELATED_TO, EXTENDS)

### Phase 3: Findings & Contributions
- Paper → Finding
- Paper → Contribution
- Finding → Finding (RELATED_TO, CONTRADICTS)
- Finding → Theory (SUPPORTS)
- Contribution → Contribution (BUILDS_ON)

### Phase 4: Advanced
- Paper → Paper (all 4 types)
- Variable → Variable (MODERATES, MEDIATES)
- ResearchQuestion → ResearchQuestion (RELATED_TO, ANSWERS)
- Author → Paper (AUTHORED)
- Paper → Dataset (USES_DATASET)
- Method → Software (IMPLEMENTED_IN)

## Benefits of This Structure

1. **Centralized**: Paper is the hub, all entities connect to it
2. **Semantic Richness**: Entities connect to similar entities
3. **Multi-dimensional**: Multiple relationship types enable complex queries
4. **Temporal**: Can track evolution through time
5. **Scalable**: Structure supports thousands of papers
6. **Query-Optimized**: Direct relationships enable fast queries

## Conclusion

This relationship structure provides:
- ✅ **26 relationship types** connecting 10 node types
- ✅ **Multi-dimensional connections** for rich queries
- ✅ **Semantic relationships** between concepts
- ✅ **Temporal tracking** for evolution analysis
- ✅ **Research gap identification** through sparse connections

All relationships are designed to support real research queries and enable comprehensive literature analysis.

