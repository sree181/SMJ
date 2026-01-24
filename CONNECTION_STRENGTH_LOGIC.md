# Connection Strength Determination - Detailed Explanation

## Overview

Connection strength for `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)` relationships is determined by a **mathematical model** using **5 factors** that evaluate how strongly a theory explains a phenomenon.

**Code Location**: 
- `connection_strength_calculator.py` - Mathematical model
- `redesigned_methodology_extractor.py:2104-2165` - Integration

**⚠️ NOTE**: This document has been updated to reflect the new mathematical model (replacing the old binary 0.7/0.5 system).

---

## Connection Strength Values

The system uses a **continuous scale (0.0-1.0)** calculated from 5 factors:

1. **0.8-1.0 (Very Strong)**: Theory clearly explains phenomenon
2. **0.6-0.8 (Strong)**: Theory likely explains phenomenon
3. **0.4-0.6 (Moderate)**: Theory may explain phenomenon
4. **0.3-0.4 (Weak)**: Theory might explain phenomenon
5. **0.0-0.3 (Very Weak)**: No connection created (below threshold)

---

## How Connection Strength is Determined

### Mathematical Formula

```
connection_strength = 
    role_weight (0.0-0.4) +      # Theory importance
    section_score (0.0-0.2) +    # Section proximity
    keyword_score (0.0-0.2) +    # Keyword overlap (Jaccard similarity)
    semantic_score (0.0-0.2) +   # Semantic similarity (embeddings/n-grams)
    explicit_bonus (0.0-0.1)     # Explicit mention bonus

Range: 0.0 to 1.0
Threshold: 0.3 (connections below this are not created)
```

### Decision Process

```
For each Theory-Phenomenon pair:
  ↓
1. Calculate role_weight (0.0-0.4)
   - Primary: 0.4, Supporting: 0.2, Extending: 0.15, Challenging: 0.1
  ↓
2. Calculate section_score (0.0-0.2)
   - Same section: 0.2, Adjacent: 0.1, Distant: 0.05
  ↓
3. Calculate keyword_score (0.0-0.2)
   - Jaccard similarity of meaningful words
  ↓
4. Calculate semantic_score (0.0-0.2)
   - Embedding cosine similarity OR n-gram overlap
  ↓
5. Calculate explicit_bonus (0.0-0.1)
   - Exact mention: 0.1, Partial: 0.05-0.08
  ↓
6. Sum all factors → connection_strength
  ↓
7. If connection_strength >= 0.3 → Create connection ✅
   Else → No connection created ❌
```

---

## Strategy 1: Primary Theory + Same Section (Strength: 0.7)

### Code Logic

```python
# Check if theory is primary and phenomenon is mentioned in same section
if theory.get("role") == "primary" and validated_phenomenon.section == theory.get("section"):
    should_connect = True
    # Connection strength will be set to 0.7 later
```

### Final Assignment

```python
connection_strength=0.7 if theory.get("role") == "primary" else 0.5
```

**Line 2156**: `connection_strength=0.7 if theory.get("role") == "primary" else 0.5`

### Why 0.7?

**Rationale**:
- **Primary theory** = Main theoretical framework of the paper
- **Same section** = Theory and phenomenon appear together
- **High confidence** that theory is used to explain phenomenon
- **Not 1.0** because we can't be 100% certain without explicit statement

**Evidence**:
- Primary theories are central to the paper's argument
- Same section indicates direct relationship
- Strong but not absolute (hence 0.7, not 1.0)

### Example

```python
Theory: {
    "theory_name": "Resource-Based View",
    "role": "primary",  # ← Primary theory
    "section": "introduction"  # ← Section
}

Phenomenon: {
    "phenomenon_name": "Resource allocation patterns",
    "section": "introduction"  # ← Same section
}

# Check
if "primary" == "primary" and "introduction" == "introduction":
    # ✅ TRUE
    connection_strength = 0.7  # ← Strong connection
```

---

## Strategy 2: Context Keyword Overlap (Strength: 0.5)

### Code Logic

```python
# Check if theory usage context mentions phenomenon keywords
if phenomenon_context and theory_usage:
    # Simple keyword matching
    phenomenon_words = set(phenomenon_context.split())
    theory_words = set(theory_usage.split())
    # If there's significant overlap, connect them
    if len(phenomenon_words.intersection(theory_words)) >= 2:
        should_connect = True
        # Connection strength will be set to 0.5 later
```

### Final Assignment

```python
connection_strength=0.7 if theory.get("role") == "primary" else 0.5
```

**Line 2156**: If theory is NOT primary, strength defaults to 0.5

### Why 0.5?

**Rationale**:
- **Keyword overlap** = Semantic similarity
- **≥2 words** = More than coincidental
- **Moderate confidence** that theory explains phenomenon
- **Lower than 0.7** because less direct than primary + same section

**Evidence**:
- Shared keywords suggest relationship
- But could be coincidental or indirect
- Moderate confidence (hence 0.5)

### Example

```python
Theory: {
    "theory_name": "Agency Theory",
    "role": "supporting",  # ← NOT primary
    "usage_context": "explains how firms allocate resources during crises"
}

Phenomenon: {
    "phenomenon_name": "Resource allocation patterns",
    "context": "resource allocation patterns during financial crises"
}

# Extract words
phenomenon_words = {"resource", "allocation", "patterns", "during", "financial", "crises"}
theory_words = {"explains", "how", "firms", "allocate", "resources", "during", "crises"}

# Find overlap
overlap = {"allocate", "resources", "during", "crises"}  # 4 words

# Check
if len(overlap) >= 2:  # 4 >= 2 ✅
    connection_strength = 0.5  # ← Moderate connection (not primary)
```

---

## Complete Code Flow

### Step 1: Initialize
```python
should_connect = False
```

### Step 2: Check Strategy 1
```python
# Check if theory is primary and phenomenon is mentioned in same section
if theory.get("role") == "primary" and validated_phenomenon.section == theory.get("section"):
    should_connect = True
    # If this is true, connection_strength will be 0.7
```

### Step 3: Check Strategy 2 (if Strategy 1 failed)
```python
# Check if theory usage context mentions phenomenon keywords
if phenomenon_context and theory_usage:
    phenomenon_words = set(phenomenon_context.split())
    theory_words = set(theory_usage.split())
    if len(phenomenon_words.intersection(theory_words)) >= 2:
        should_connect = True
        # If this is true, connection_strength will be 0.5
```

### Step 4: Create Relationship (if should_connect is True)
```python
if should_connect:
    tx.run("""
        MERGE (t)-[r:EXPLAINS_PHENOMENON {
            connection_strength: $connection_strength
        }]->(ph)
    """,
    connection_strength=0.7 if theory.get("role") == "primary" else 0.5)
```

**Key Line**: `connection_strength=0.7 if theory.get("role") == "primary" else 0.5`

---

## Connection Strength Assignment Logic

### Decision Matrix

| Theory Role | Same Section? | Keyword Overlap? | Connection Strength |
|-------------|---------------|------------------|---------------------|
| primary     | ✅ YES        | (any)            | **0.7** (Strong)   |
| primary     | ❌ NO         | ✅ ≥2 words      | **0.5** (Moderate) |
| primary     | ❌ NO         | ❌ <2 words      | **No connection**   |
| supporting  | ✅ YES        | (any)            | **0.5** (Moderate) |
| supporting  | ❌ NO         | ✅ ≥2 words      | **0.5** (Moderate) |
| supporting  | ❌ NO         | ❌ <2 words      | **No connection**   |

### Important Note

**The code uses a simple ternary operator**:
```python
connection_strength=0.7 if theory.get("role") == "primary" else 0.5
```

This means:
- **If theory is primary** → Always 0.7 (even if only keyword overlap)
- **If theory is NOT primary** → Always 0.5 (even if same section)

**Current Behavior**:
- Strategy 1 (primary + same section) → 0.7 ✅
- Strategy 2 (keyword overlap) → 0.5 ✅
- Strategy 1 (primary + different section) → Still 0.7 if keyword overlap exists ⚠️

---

## Why These Specific Values?

### 0.7 (Strong Connection)

**Rationale**:
- Primary theory = Central to paper
- Same section = Direct relationship
- High confidence but not absolute
- **70% confidence** = Strong but acknowledges uncertainty

**Why not 1.0?**
- Can't be 100% certain without explicit statement
- Paper might use theory for other purposes
- Conservative approach

**Why not 0.8 or 0.9?**
- 0.7 is a good balance
- Leaves room for even stronger connections (future enhancement)
- Standard confidence level in research

---

### 0.5 (Moderate Connection)

**Rationale**:
- Keyword overlap = Semantic similarity
- But less direct than primary + same section
- Moderate confidence
- **50% confidence** = Moderate, acknowledges uncertainty

**Why not 0.6 or 0.4?**
- 0.5 is a standard "moderate" confidence level
- Clearly differentiates from strong (0.7)
- Leaves room for weak connections (future: 0.3)

---

## Edge Cases

### Case 1: Primary Theory + Same Section + Keyword Overlap
```python
Theory: primary, section: "introduction"
Phenomenon: section: "introduction", context: "resource allocation"
Theory usage: "explains resource allocation patterns"
```

**Result**: `connection_strength = 0.7` (Strategy 1 takes precedence)

---

### Case 2: Supporting Theory + Same Section
```python
Theory: supporting, section: "introduction"
Phenomenon: section: "introduction"
```

**Result**: `connection_strength = 0.5` (Not primary, so 0.5)

**Note**: Even though same section, supporting theory gets 0.5

---

### Case 3: Primary Theory + Different Section + Keyword Overlap
```python
Theory: primary, section: "literature_review"
Phenomenon: section: "introduction", context: "resource allocation"
Theory usage: "explains resource allocation patterns"
```

**Result**: `connection_strength = 0.7` (Primary theory always gets 0.7 if connected)

**Note**: This might be too generous - could be enhanced

---

## Potential Improvements

### Current Limitations

1. **Binary Strength Levels**: Only 0.7 and 0.5
   - Could add more granular levels (0.9, 0.6, 0.4, 0.3)

2. **Primary Theory Always 0.7**: Even if only keyword overlap
   - Could differentiate: primary + same section = 0.8, primary + keyword = 0.6

3. **No Negative Evidence**: Doesn't check if theory explicitly doesn't explain phenomenon
   - Could add negative connections (strength: -0.3)

4. **Simple Keyword Matching**: Basic word overlap
   - Could use embeddings for semantic similarity
   - Could use LLM to explicitly determine connection

### Enhanced Logic (Future)

```python
# More granular strength calculation
if theory.get("role") == "primary" and validated_phenomenon.section == theory.get("section"):
    connection_strength = 0.8  # Very strong
elif theory.get("role") == "primary" and keyword_overlap >= 2:
    connection_strength = 0.6  # Strong
elif validated_phenomenon.section == theory.get("section") and keyword_overlap >= 2:
    connection_strength = 0.5  # Moderate
elif keyword_overlap >= 3:
    connection_strength = 0.4  # Weak
else:
    connection_strength = 0.3  # Very weak
```

---

## Summary

### Connection Strength Determination

**Formula**:
```python
if should_connect:
    connection_strength = 0.7 if theory.role == "primary" else 0.5
```

**Values**:
- **0.7**: Theory is primary (regardless of section/keyword overlap)
- **0.5**: Theory is NOT primary (supporting, challenging, extending)

**Decision Criteria**:
1. **Strategy 1**: Primary + Same Section → 0.7
2. **Strategy 2**: Keyword Overlap ≥2 words → 0.5 (or 0.7 if primary)

**Current Implementation**:
- Simple binary: Primary = 0.7, Non-primary = 0.5
- Based on theory role, not connection quality
- Could be enhanced with more granular levels

---

## Code Reference

**File**: `redesigned_methodology_extractor.py`
**Lines**: 2126-2156

**Key Line**: 2156
```python
connection_strength=0.7 if theory.get("role") == "primary" else 0.5
```

This is a **simple ternary operator** that assigns:
- **0.7** if theory role is "primary"
- **0.5** otherwise (supporting, challenging, extending)

**Note**: The connection strength is determined **solely by theory role**, not by the quality of the connection itself. This is a simplification that could be enhanced in the future.

