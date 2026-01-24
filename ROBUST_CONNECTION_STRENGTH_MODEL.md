# Robust Mathematical Connection Strength Model

## Overview

A multi-factor mathematical model for calculating connection strength between theories and phenomena, replacing the simple binary (0.7/0.5) approach with a weighted scoring system.

---

## Mathematical Formula

### Connection Strength Formula

```
connection_strength = Σ(factor_i × weight_i) + bonus

Where:
- factor_i = Individual factor score (0.0-1.0)
- weight_i = Weight for that factor
- bonus = Explicit mention bonus (0.0-0.1)
```

### Final Formula

```
connection_strength = 
    role_weight +           (0.0-0.4)
    section_score +         (0.0-0.2)
    keyword_score +         (0.0-0.2)
    semantic_score +        (0.0-0.2)
    explicit_bonus          (0.0-0.1)
    
Range: 0.0 to 1.0
```

---

## Factor Breakdown

### Factor 1: Theory Role Weight (0.0-0.4)

**Purpose**: Primary theories are more central to explaining phenomena

**Formula**:
```
role_weight = {
    "primary": 0.4,
    "supporting": 0.2,
    "extending": 0.15,
    "challenging": 0.1
}
```

**Rationale**:
- Primary theories = 40% base weight (main framework)
- Supporting theories = 20% base weight
- Extending/challenging = Lower weights

**Example**:
- Primary theory → 0.4
- Supporting theory → 0.2

---

### Factor 2: Section Overlap (0.0-0.2)

**Purpose**: Same section = stronger connection (theory and phenomenon appear together)

**Formula**:
```
if theory_section == phenomenon_section:
    section_score = 0.2
else:
    # Calculate section distance
    distance = |section_position(theory) - section_position(phenomenon)|
    section_score = {
        0: 0.2,   # Same section
        1: 0.1,   # Adjacent sections
        >1: 0.05  # Distant sections
    }
```

**Section Hierarchy**:
```
introduction → 1
literature_review → 2
methodology → 3
results → 4
discussion → 5
```

**Example**:
- Both in "introduction" → 0.2
- "introduction" and "literature_review" → 0.1 (adjacent)
- "introduction" and "results" → 0.05 (distant)

---

### Factor 3: Keyword Overlap (0.0-0.2)

**Purpose**: Shared meaningful words indicate semantic relationship

**Formula**:
```
1. Extract meaningful words (length > 3, not stopwords)
2. Calculate Jaccard similarity:
   J(A, B) = |A ∩ B| / |A ∪ B|
3. Scale to 0.0-0.2:
   - J ≥ 0.5 → 0.2 (strong overlap)
   - 0.2 ≤ J < 0.5 → 0.1 (moderate)
   - 0 < J < 0.2 → 0.05 (weak)
   - J = 0 → 0.0
```

**Jaccard Similarity**:
- Measures set similarity
- Range: 0.0 (no overlap) to 1.0 (identical)
- Formula: `intersection / union`

**Example**:
```
Theory: "explains how firms allocate resources during crises"
Phenomenon: "resource allocation patterns during financial crises"

Meaningful words:
Theory: {explains, firms, allocate, resources, during, crises}
Phenomenon: {resource, allocation, patterns, during, financial, crises}

Intersection: {during, crises} = 2
Union: {explains, firms, allocate, resources, resource, allocation, patterns, during, financial, crises} = 10

Jaccard = 2/10 = 0.2 → section_score = 0.1 (moderate)
```

---

### Factor 4: Semantic Similarity (0.0-0.2)

**Purpose**: Deep semantic understanding using embeddings

**Option A: Embedding-Based (if available)**
```
1. Generate embeddings using SentenceTransformer
2. Calculate cosine similarity:
   similarity = cosine_similarity(embedding_theory, embedding_phenomenon)
3. Scale to 0.0-0.2:
   - similarity ≥ 0.7 → 0.2 (very similar)
   - 0.5 ≤ similarity < 0.7 → 0.15 (similar)
   - 0.3 ≤ similarity < 0.5 → 0.1 (somewhat similar)
   - 0.1 ≤ similarity < 0.3 → 0.05 (weak)
   - similarity < 0.1 → 0.0
```

**Option B: Enhanced Keyword (fallback)**
```
1. Extract n-grams (bigrams, trigrams)
2. Calculate weighted overlap:
   total_overlap = bigram_overlap × 0.5 + trigram_overlap × 1.0
3. Scale to 0.0-0.2:
   - total_overlap ≥ 3 → 0.2
   - total_overlap ≥ 2 → 0.15
   - total_overlap ≥ 1 → 0.1
   - total_overlap > 0 → 0.05
```

**Example (Embedding)**:
```
Theory: "explains firm performance differences"
Phenomenon: "firm performance variations across industries"

Cosine similarity: 0.75
→ semantic_score = 0.2 (very similar)
```

---

### Factor 5: Explicit Mention Bonus (0.0-0.1)

**Purpose**: Bonus if theory explicitly mentions phenomenon

**Formula**:
```
if phenomenon_name in theory_context:
    explicit_bonus = 0.1
else:
    # Check key words from phenomenon name
    match_ratio = matching_words / total_phenomenon_words
    explicit_bonus = {
        match_ratio ≥ 0.8: 0.08
        0.5 ≤ match_ratio < 0.8: 0.05
        match_ratio < 0.5: 0.0
    }
```

**Example**:
```
Theory: "explains economic nationalism in court rulings"
Phenomenon: "Economic nationalism in court rulings"

Exact match → explicit_bonus = 0.1
```

---

## Complete Example Calculation

### Input Data

**Theory**:
```python
{
    "theory_name": "Resource-Based View",
    "role": "primary",
    "section": "introduction",
    "usage_context": "explains how firms allocate resources during financial crises"
}
```

**Phenomenon**:
```python
{
    "phenomenon_name": "Resource allocation patterns during financial crises",
    "section": "introduction",
    "context": "Studied through firm investment decisions",
    "description": "How firms allocate resources during financial crises"
}
```

### Calculation

**Factor 1: Role Weight**
```
role = "primary" → role_weight = 0.4
```

**Factor 2: Section Overlap**
```
theory_section = "introduction"
phenomenon_section = "introduction"
→ section_score = 0.2 (same section)
```

**Factor 3: Keyword Overlap**
```
Theory words: {explains, firms, allocate, resources, during, crises}
Phenomenon words: {studied, through, firm, investment, decisions, how, firms, allocate, resources, during, financial, crises}

Intersection: {firms, allocate, resources, during, crises} = 5
Union: {explains, firms, allocate, resources, during, crises, studied, through, firm, investment, decisions, how, financial} = 13

Jaccard = 5/13 = 0.38
→ keyword_score = 0.1 (moderate, 0.2 ≤ J < 0.5)
```

**Factor 4: Semantic Similarity**
```
Cosine similarity = 0.65 (calculated via embeddings)
→ semantic_score = 0.15 (similar, 0.5 ≤ sim < 0.7)
```

**Factor 5: Explicit Mention**
```
Phenomenon name: "Resource allocation patterns during financial crises"
Theory context: "explains how firms allocate resources during financial crises"

Key words match: "allocate", "resources", "during", "crises"
Match ratio = 4/5 = 0.8
→ explicit_bonus = 0.08
```

### Final Score

```
connection_strength = 
    0.4 +    # role_weight
    0.2 +    # section_score
    0.1 +    # keyword_score
    0.15 +   # semantic_score
    0.08     # explicit_bonus
    = 0.93
```

**Result**: Very strong connection (0.93)

---

## Connection Strength Interpretation

### Strength Levels

| Range | Interpretation | Action |
|-------|----------------|--------|
| 0.8 - 1.0 | **Very Strong** | High confidence, theory clearly explains phenomenon |
| 0.6 - 0.8 | **Strong** | Good confidence, theory likely explains phenomenon |
| 0.4 - 0.6 | **Moderate** | Some confidence, theory may explain phenomenon |
| 0.3 - 0.4 | **Weak** | Low confidence, connection uncertain |
| 0.0 - 0.3 | **Very Weak** | No connection created (below threshold) |

### Default Threshold

**Threshold: 0.3**
- Connections with strength < 0.3 are not created
- Prevents weak/uncertain connections
- Can be adjusted based on needs

---

## Advantages Over Simple Binary Model

### 1. **Granular Scoring**
- **Old**: Only 0.7 or 0.5
- **New**: Continuous scale 0.0-1.0
- More nuanced understanding

### 2. **Multiple Factors**
- **Old**: Only theory role
- **New**: 5 factors considered
- More comprehensive evaluation

### 3. **Mathematical Rigor**
- **Old**: Simple if-else
- **New**: Weighted formula with Jaccard similarity, cosine similarity
- More objective and reproducible

### 4. **Transparency**
- **Old**: No explanation
- **New**: Factor scores stored in relationship
- Can analyze why connection was made

### 5. **Flexibility**
- **Old**: Fixed values
- **New**: Adjustable weights and thresholds
- Can tune for different use cases

---

## Implementation

### File: `connection_strength_calculator.py`

**Class**: `ConnectionStrengthCalculator`

**Key Method**: `calculate_strength(theory, phenomenon, paper_data)`

**Returns**: `(connection_strength, factor_scores)`

### Integration

**File**: `redesigned_methodology_extractor.py`
**Lines**: After phenomenon creation

**Usage**:
```python
from connection_strength_calculator import get_strength_calculator

calculator = get_strength_calculator(use_embeddings=False)
strength, factors = calculator.calculate_strength(theory, phenomenon, paper_data)

if calculator.should_create_connection(strength, threshold=0.3):
    # Create relationship with calculated strength
```

---

## Example Queries with Strength

### Find Strong Connections Only
```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE r.connection_strength >= 0.7
RETURN t.name, ph.phenomenon_name, r.connection_strength
ORDER BY r.connection_strength DESC
```

### Analyze Connection Factors
```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
RETURN t.name, ph.phenomenon_name, 
       r.connection_strength,
       r.role_weight,
       r.section_score,
       r.keyword_score,
       r.semantic_score,
       r.explicit_bonus
ORDER BY r.connection_strength DESC
```

### Find Connections by Strength Range
```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE r.connection_strength >= 0.6 AND r.connection_strength < 0.8
RETURN t.name, ph.phenomenon_name, r.connection_strength
```

---

## Future Enhancements

### 1. **LLM-Based Validation**
- Use LLM to explicitly verify if theory explains phenomenon
- Add as additional factor or validation step

### 2. **Temporal Weighting**
- Recent connections weighted higher
- Accounts for theory evolution

### 3. **Citation-Based Strength**
- If multiple papers connect same theory-phenomenon → higher strength
- Consensus-based scoring

### 4. **Domain-Specific Weights**
- Different weights for different research domains
- Tuned for strategic management context

### 5. **Machine Learning**
- Train model on validated connections
- Learn optimal weights from data

---

## Summary

### Mathematical Model

**Formula**:
```
strength = role_weight + section_score + keyword_score + semantic_score + explicit_bonus
```

**Factors**:
1. Role Weight (0.0-0.4): Theory importance
2. Section Overlap (0.0-0.2): Proximity in paper
3. Keyword Overlap (0.0-0.2): Jaccard similarity
4. Semantic Similarity (0.0-0.2): Embedding cosine similarity
5. Explicit Mention (0.0-0.1): Direct reference bonus

**Range**: 0.0 to 1.0
**Threshold**: 0.3 (connections below this are not created)

**Status**: ✅ Implemented and ready to use!

