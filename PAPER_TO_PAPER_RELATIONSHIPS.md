# Paper-to-Paper Relationships - Domain-Driven Design

## Overview

For a literature review knowledge graph that will power a chatbot, we need relationships between papers that enable:
1. **Research Gap Identification**: Find what's missing or understudied
2. **Literature Synthesis**: Connect related work across time and topics
3. **Contradiction Detection**: Identify conflicting findings
4. **Evolution Tracking**: Understand how research streams develop
5. **Contextual Retrieval**: Find papers relevant to user queries

## Current State Analysis

### Existing Entity-Level Relationships
- Paper → Method (USES_METHOD)
- Paper → Theory (USES_THEORY)
- Paper → ResearchQuestion (ADDRESSES)
- Paper → Variable (USES_VARIABLE)
- Paper → Finding (REPORTS)
- Paper → Contribution (MAKES)

**Gap**: No direct Paper → Paper relationships exist yet!

## Proposed Paper-to-Paper Relationships

### 1. **CITES** (Citation Relationship)
**Relationship**: `(Paper)-[:CITES]->(Paper)`
**Properties**:
- `citation_type`: "theoretical", "methodological", "empirical", "general"
- `section`: Where cited ("introduction", "literature_review", "discussion")
- `purpose`: "foundation", "comparison", "extension", "critique"

**Domain Purpose**:
- Track citation networks
- Find foundational papers
- Identify highly cited work
- Understand knowledge flow

**Chatbot Queries Enabled**:
- "What papers cite this paper?"
- "What foundational papers does this build on?"
- "Show me papers that cite both X and Y"

**Implementation**: Extract from references section using LLM

---

### 2. **USES_SAME_THEORY** (Theoretical Similarity)
**Relationship**: `(Paper)-[:USES_SAME_THEORY]->(Paper)`
**Properties**:
- `theory_name`: Name of shared theory
- `similarity_score`: 0.0-1.0 (if multiple theories shared)
- `temporal_gap`: Years between papers

**Domain Purpose**:
- Find papers using same theoretical framework
- Track theory evolution
- Identify theoretical clusters

**Chatbot Queries Enabled**:
- "Find papers using the same theory as this paper"
- "How has Resource-Based View been applied over time?"
- "What papers combine Theory X and Theory Y?"

**Implementation**: 
- Papers sharing primary theories (role="primary")
- Can be computed from existing USES_THEORY relationships

---

### 3. **USES_SAME_METHOD** (Methodological Similarity)
**Relationship**: `(Paper)-[:USES_SAME_METHOD]->(Paper)`
**Properties**:
- `method_name`: Name of shared method
- `similarity_score`: 0.0-1.0
- `temporal_gap`: Years between papers

**Domain Purpose**:
- Find papers using same methodology
- Track method evolution
- Enable methodological comparisons

**Chatbot Queries Enabled**:
- "What papers use the same method as this?"
- "How has OLS regression been applied in strategic management?"
- "Find papers using both regression and case studies"

**Implementation**: 
- Papers sharing methods (already have SAME_METHOD for methods)
- Can be computed from existing USES_METHOD relationships

---

### 4. **ADDRESSES_SIMILAR_QUESTION** (Question Similarity)
**Relationship**: `(Paper)-[:ADDRESSES_SIMILAR_QUESTION]->(Paper)`
**Properties**:
- `similarity_score`: 0.0-1.0 (LLM-based semantic similarity)
- `question_type_match`: Boolean (same question type)
- `temporal_gap`: Years between papers

**Domain Purpose**:
- Find papers addressing similar research questions
- Identify question evolution
- Detect research gaps (questions with few papers)

**Chatbot Queries Enabled**:
- "What papers ask similar questions?"
- "How has this research question evolved?"
- "What questions are understudied?"

**Implementation**: 
- LLM-based semantic similarity between research questions
- Papers with questions in same domain

---

### 5. **CONTRADICTS** (Contradictory Findings)
**Relationship**: `(Paper)-[:CONTRADICTS]->(Paper)`
**Properties**:
- `contradiction_type`: "finding", "theory", "methodology", "interpretation"
- `severity`: "minor", "moderate", "major"
- `context`: Brief description of contradiction

**Domain Purpose**:
- Identify conflicting findings
- Track theoretical debates
- Find unresolved questions

**Chatbot Queries Enabled**:
- "What papers contradict this finding?"
- "Are there conflicting results on this topic?"
- "What debates exist in this area?"

**Implementation**: 
- LLM-based analysis comparing findings
- Papers with opposite finding types (positive vs negative)
- Papers challenging same theories

---

### 6. **EXTENDS** (Extension/Development)
**Relationship**: `(Paper)-[:EXTENDS]->(Paper)`
**Properties**:
- `extension_type`: "theoretical", "empirical", "methodological", "contextual"
- `explicit`: Boolean (explicitly states extension vs inferred)
- `temporal_gap`: Years between papers

**Domain Purpose**:
- Track how research builds on previous work
- Identify research streams
- Find foundational papers

**Chatbot Queries Enabled**:
- "What papers extend this work?"
- "What foundational papers does this build on?"
- "Show me the evolution of this research stream"

**Implementation**: 
- Citation analysis (papers that cite and extend)
- LLM analysis of contribution statements
- Temporal ordering (later papers extending earlier)

---

### 7. **REPLICATES** (Replication Studies)
**Relationship**: `(Paper)-[:REPLICATES]->(Paper)`
**Properties**:
- `replication_type`: "exact", "conceptual", "methodological"
- `context`: "same", "different", "extended"
- `outcome`: "confirmed", "disconfirmed", "mixed"

**Domain Purpose**:
- Track replication studies
- Assess result robustness
- Identify well-replicated findings

**Chatbot Queries Enabled**:
- "Has this finding been replicated?"
- "What replication studies exist?"
- "Are these results robust?"

**Implementation**: 
- LLM analysis identifying replication language
- Similar methods + similar questions
- Explicit replication statements

---

### 8. **USES_SAME_VARIABLES** (Variable Similarity)
**Relationship**: `(Paper)-[:USES_SAME_VARIABLES]->(Paper)`
**Properties**:
- `variable_overlap`: Number of shared variables
- `variable_types`: Array of shared variable types
- `similarity_score`: 0.0-1.0

**Domain Purpose**:
- Find papers using same variables
- Track variable usage patterns
- Enable variable-based comparisons

**Chatbot Queries Enabled**:
- "What papers use the same variables?"
- "How is Firm Performance measured across papers?"
- "Find papers with similar variable sets"

**Implementation**: 
- Compute from existing USES_VARIABLE relationships
- Variable name normalization (e.g., "Firm Performance" = "Performance")

---

### 9. **TEMPORAL_SEQUENCE** (Chronological Ordering)
**Relationship**: `(Paper)-[:TEMPORAL_SEQUENCE]->(Paper)`
**Properties**:
- `time_gap`: Years between papers
- `sequence_type`: "immediate", "recent", "distant"
- `context`: "same_topic", "same_theory", "same_method"

**Domain Purpose**:
- Understand temporal evolution
- Track research streams over time
- Identify recent developments

**Chatbot Queries Enabled**:
- "What came after this paper?"
- "Show me recent developments in this area"
- "How has this topic evolved over time?"

**Implementation**: 
- Simple temporal ordering based on publication_year
- Can be combined with other relationships

---

### 10. **SEMANTIC_SIMILARITY** (Overall Similarity)
**Relationship**: `(Paper)-[:SEMANTIC_SIMILARITY]->(Paper)`
**Properties**:
- `similarity_score`: 0.0-1.0 (LLM-based)
- `dimensions`: Array of similarity dimensions ("theory", "method", "question", "finding")
- `overall_match`: Boolean (high overall similarity)

**Domain Purpose**:
- Find most similar papers
- Enable "find similar papers" functionality
- Support recommendation system

**Chatbot Queries Enabled**:
- "Find papers similar to this one"
- "What papers are most related?"
- "Recommend papers based on this"

**Implementation**: 
- LLM-based semantic analysis of abstracts + titles
- Multi-dimensional similarity (theory, method, question, finding)
- Can be computed post-ingestion

---

## Relationship Priority for Implementation

### Phase 1: High-Value, Easy to Compute
1. **USES_SAME_THEORY** - From existing Theory nodes
2. **USES_SAME_METHOD** - From existing Method nodes
3. **USES_SAME_VARIABLES** - From existing Variable nodes
4. **TEMPORAL_SEQUENCE** - From publication_year

### Phase 2: High-Value, Requires LLM
5. **ADDRESSES_SIMILAR_QUESTION** - LLM semantic similarity
6. **SEMANTIC_SIMILARITY** - LLM analysis of abstracts
7. **EXTENDS** - LLM analysis of contributions/citations

### Phase 3: Specialized, Requires Deep Analysis
8. **CITES** - Extract from references section
9. **CONTRADICTS** - LLM comparison of findings
10. **REPLICATES** - LLM identification of replication language

---

## Chatbot Query Patterns Enabled

### Research Gap Queries
- "What research questions have few papers?" → ADDRESSES_SIMILAR_QUESTION
- "What theories are understudied?" → USES_SAME_THEORY
- "What methods are rarely used together?" → USES_SAME_METHOD

### Literature Synthesis Queries
- "How has this topic evolved?" → TEMPORAL_SEQUENCE + EXTENDS
- "What are the main research streams?" → EXTENDS + USES_SAME_THEORY
- "Show me papers building on this work" → EXTENDS + CITES

### Comparison Queries
- "Compare papers using same method" → USES_SAME_METHOD
- "What papers have similar findings?" → SEMANTIC_SIMILARITY
- "Find contradictory results" → CONTRADICTS

### Discovery Queries
- "Find papers similar to this" → SEMANTIC_SIMILARITY
- "What papers cite this?" → CITES
- "What foundational papers exist?" → EXTENDS (reverse)

---

## Implementation Strategy

### Immediate (Before Batch Processing)
1. Implement **USES_SAME_THEORY** (computed from existing data)
2. Implement **USES_SAME_METHOD** (computed from existing data)
3. Implement **TEMPORAL_SEQUENCE** (computed from publication_year)

### Post-Ingestion (After All Papers Processed)
4. Compute **ADDRESSES_SIMILAR_QUESTION** (LLM batch processing)
5. Compute **SEMANTIC_SIMILARITY** (LLM batch processing)
6. Extract **CITES** relationships (from references section)

### Advanced (Future Enhancement)
7. Compute **CONTRADICTS** (LLM comparison)
8. Compute **EXTENDS** (LLM analysis)
9. Compute **REPLICATES** (LLM identification)

---

## Graph Structure Visualization

```
Paper A (2020)
  ├─[:USES_THEORY {role: "primary"}]→ Theory: RBV
  ├─[:ADDRESSES]→ ResearchQuestion: "How do firms achieve competitive advantage?"
  ├─[:USES_METHOD]→ Method: OLS Regression
  │
  ├─[:USES_SAME_THEORY]→ Paper B (2022)  [Both use RBV]
  ├─[:USES_SAME_METHOD]→ Paper C (2021)  [Both use OLS]
  ├─[:ADDRESSES_SIMILAR_QUESTION]→ Paper D (2023)  [Similar questions]
  ├─[:EXTENDS]→ Paper E (2018)  [Builds on earlier work]
  ├─[:CONTRADICTS]→ Paper F (2019)  [Conflicting findings]
  └─[:SEMANTIC_SIMILARITY {score: 0.85}]→ Paper G (2021)  [Overall similar]
```

---

## Recommendations

1. **Start with Phase 1 relationships** - Can be computed immediately from existing nodes
2. **Add Phase 2 relationships post-ingestion** - Requires batch LLM processing
3. **Use relationship weights** - Similarity scores enable ranking
4. **Maintain temporal context** - Always include temporal_gap property
5. **Enable bidirectional queries** - Both directions useful for chatbot

This structure enables a powerful literature review chatbot that can:
- Answer "what papers are similar?"
- Identify research gaps
- Track research evolution
- Find contradictory findings
- Synthesize literature streams

