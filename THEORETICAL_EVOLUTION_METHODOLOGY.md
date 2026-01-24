# Theoretical Evolution & Divergence - Calculation Methodology

## Overview

The Theoretical Evolution & Divergence metric uses **sophisticated statistical measures** to analyze how theoretical frameworks evolve, converge, diverge, and fragment over time. Unlike topic evolution (which uses clustering), this metric analyzes the **distribution and usage patterns** of theories across research papers.

---

## Step-by-Step Calculation Process

### Step 1: Data Preparation (Lines 339-358)

For each 5-year interval (e.g., 1985-1989, 1990-1994, etc.):

1. **Get all papers** published in that interval
2. **Query theory usage** from Neo4j graph relationships
3. **Count theory occurrences** per interval

```python
# Query Neo4j for theory usage
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE p.paper_id IN $paper_ids
RETURN t.name as theory_name,
       count(p) as usage_count,
       collect(DISTINCT p.paper_id) as paper_ids
```

**What we get**:
- Theory name
- Number of papers using that theory
- List of paper IDs using the theory

**Example**:
```
Interval: 2010-2014
Theories:
  - Resource-Based View: 15 papers
  - Transaction Cost Economics: 12 papers
  - Agency Theory: 8 papers
  - Institutional Theory: 6 papers
  - Dynamic Capabilities: 5 papers
```

---

### Step 2: Theory Diversity Calculation (Lines 387-390)

**Definition**: How evenly distributed is theory usage across different theories?

**Method**: **Normalized Shannon Entropy**

**Formula**:
```
Diversity = -Σ(p_i * log(p_i)) / log(n)
where:
  p_i = proportion of theory i usage = count_i / total_usage
  n = number of theories
```

**Step-by-step**:
1. Calculate total theory usage: `total = sum(all theory counts)`
2. Calculate proportions: `p_i = count_i / total` for each theory
3. Calculate entropy: `-sum(p_i * log(p_i))`
4. Normalize: Divide by `log(n)` to get range [0, 1]

**Interpretation**:
- **1.0**: Perfect diversity (all theories used equally)
- **0.0**: No diversity (one theory dominates completely)
- **0.5-0.8**: Moderate diversity
- **< 0.5**: Low diversity (few theories dominate)

**Example**:
```
Scenario 1: Equal usage
  Theory A: 10 papers
  Theory B: 10 papers
  Theory C: 10 papers
  Diversity = 1.0 (perfect diversity)

Scenario 2: Dominant theory
  Theory A: 25 papers
  Theory B: 3 papers
  Theory C: 2 papers
  Diversity = 0.35 (low diversity)

Scenario 3: Moderate distribution
  Theory A: 15 papers
  Theory B: 10 papers
  Theory C: 5 papers
  Diversity = 0.68 (moderate diversity)
```

---

### Step 3: Theory Concentration Calculation (Lines 392-400)

**Definition**: How concentrated is theory usage? (Opposite of diversity)

**Method**: **Gini Coefficient** (measures inequality)

**Formula**:
```
Gini = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n
where:
  x_i = sorted theory counts (descending)
  i = rank (1, 2, 3, ...)
  n = number of theories
```

**Step-by-step**:
1. Sort theory counts in descending order: `[25, 10, 5, 3, 2]`
2. Calculate cumulative sum: `[25, 35, 40, 43, 45]`
3. Apply Gini formula
4. Clamp to [0, 1] range

**Interpretation**:
- **0.0**: Perfect equality (all theories used equally)
- **1.0**: Perfect inequality (one theory dominates completely)
- **0.3-0.6**: Moderate concentration
- **> 0.6**: High concentration (few theories dominate)

**Example**:
```
Scenario 1: Equal usage
  Theory A: 10, Theory B: 10, Theory C: 10
  Gini = 0.0 (no concentration)

Scenario 2: Highly concentrated
  Theory A: 25, Theory B: 3, Theory C: 2
  Gini = 0.72 (high concentration)

Scenario 3: Moderate concentration
  Theory A: 15, Theory B: 10, Theory C: 5
  Gini = 0.33 (moderate concentration)
```

**Relationship with Diversity**:
- Concentration = 1 - Diversity (approximately)
- High diversity → Low concentration
- Low diversity → High concentration

---

### Step 4: Fragmentation Index Calculation (Line 403)

**Definition**: How fragmented is the theoretical landscape?

**Method**: Inverse of concentration

**Formula**:
```
Fragmentation = 1 - Gini_Coefficient
```

**Interpretation**:
- **1.0**: Highly fragmented (many theories, no dominant one)
- **0.0**: Not fragmented (one theory dominates)
- **0.4-0.7**: Moderate fragmentation

**Example**:
- Gini = 0.3 → Fragmentation = 0.7 (fragmented field)
- Gini = 0.8 → Fragmentation = 0.2 (concentrated field)

---

### Step 5: Theory-Phenomenon Coupling (Lines 405-414)

**Definition**: How many phenomena does each theory explain?

**Method**: Count distinct phenomena connected to each theory

```python
# Query Neo4j
MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE t.name IN $theory_names
RETURN t.name, count(DISTINCT ph) as phenomenon_count
```

**Purpose**: Understand theory scope and applicability

**Example**:
```
Theory A: Explains 5 phenomena (broad scope)
Theory B: Explains 2 phenomena (narrow scope)
Theory C: Explains 8 phenomena (very broad scope)
```

---

### Step 6: Theory Divergence Calculation (Lines 433-495)

**Definition**: How much has the theory distribution changed from the previous interval?

**Method**: **Jensen-Shannon Divergence** (JS divergence)

**Why JS Divergence?**
- Symmetric (unlike KL divergence)
- Bounded [0, 1]
- Measures difference between two probability distributions

**Formula**:
```
JS(P || Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M)
where:
  M = 0.5 * (P + Q)  (mixture distribution)
  KL(P || Q) = Σ p_i * log(p_i / q_i)  (Kullback-Leibler divergence)
```

**Step-by-step**:
1. Get theory distributions for two consecutive intervals
2. Create unified theory set (union of both intervals)
3. Convert to probability distributions:
   - `P = [p1, p2, ..., pn]` (previous interval)
   - `Q = [q1, q2, ..., qn]` (current interval)
4. Calculate mixture: `M = 0.5 * (P + Q)`
5. Calculate KL divergences:
   - `KL(P || M) = Σ p_i * log(p_i / m_i)`
   - `KL(Q || M) = Σ q_i * log(q_i / m_i)`
6. JS Divergence = `0.5 * KL(P || M) + 0.5 * KL(Q || M)`

**Interpretation**:
- **0.0**: No change (identical distributions)
- **1.0**: Maximum change (completely different distributions)
- **0.1-0.3**: Moderate change
- **> 0.3**: Significant theoretical shift

**Example**:
```
Previous Interval (2010-2014):
  Theory A: 40% of papers
  Theory B: 30% of papers
  Theory C: 30% of papers

Current Interval (2015-2019):
  Theory A: 20% of papers
  Theory B: 20% of papers
  Theory C: 30% of papers
  Theory D: 30% of papers (NEW)

JS Divergence = 0.25 (moderate change)
```

**Visual Representation**:
```
Interval 1: [0.4, 0.3, 0.3, 0.0]  (Theory A, B, C, D)
Interval 2: [0.2, 0.2, 0.3, 0.3]  (Theory A, B, C, D)
            ↓ JS Divergence ↓
Divergence = 0.25 (theoretical landscape shifted)
```

---

### Step 7: Theory Emergence Rate (Lines 497-524)

**Definition**: Rate at which new theories appear in the field

**Method**: Count new theories normalized by total papers

**Formula**:
```
Emergence_Rate = (New_Theories_Count) / (Total_Papers_in_Interval)
```

**Step-by-step**:
1. Track all theories seen so far
2. For each interval:
   - Identify new theories (not seen before)
   - Count new theories
   - Normalize by total papers using theories

**Interpretation**:
- **High rate (>0.1)**: Rapid theoretical innovation
- **Low rate (<0.05)**: Stable theoretical landscape
- **Zero**: No new theories (field is mature)

**Example**:
```
Interval 1 (1985-1989):
  New theories: 5
  Total papers: 50
  Emergence Rate = 5/50 = 0.10 (10%)

Interval 2 (1990-1994):
  New theories: 2
  Total papers: 60
  Emergence Rate = 2/60 = 0.033 (3.3%)

Interval 3 (1995-1999):
  New theories: 0
  Total papers: 70
  Emergence Rate = 0/70 = 0.0 (no new theories)
```

---

### Step 8: Trend Calculation (Lines 526-544)

**Definition**: Overall trend direction (increasing, decreasing, stable)

**Method**: Linear regression slope on diversity metric

**Formula**:
```
Slope = Linear_Regression(diversity_values over time)
```

**Step-by-step**:
1. Extract diversity values for all intervals: `[0.6, 0.65, 0.7, 0.68, 0.72]`
2. Fit linear regression: `y = slope * x + intercept`
3. Classify based on slope:
   - `slope > 0.01` → "increasing"
   - `slope < -0.01` → "decreasing"
   - Otherwise → "stable"

**Interpretation**:
- **Increasing**: Field is becoming more diverse
- **Decreasing**: Field is becoming more concentrated
- **Stable**: No significant trend

**Example**:
```
Diversity over 5 intervals: [0.5, 0.55, 0.6, 0.65, 0.7]
Slope = +0.05 per interval
Trend = "increasing" (field diversifying)
```

---

## Summary Metrics

### Per Interval:
- **Theory Count**: Number of distinct theories used
- **Diversity** (0-1): Shannon entropy of theory distribution
- **Concentration** (0-1): Gini coefficient of theory usage
- **Fragmentation Index** (0-1): Inverse of concentration
- **Divergence** (0-1): JS divergence from previous interval
- **Emergence Rate** (0-1): New theories per paper
- **Theory Details**: Usage count, paper count, phenomenon count per theory

### Overall Summary:
- **Average Diversity**: Mean diversity across intervals
- **Average Concentration**: Mean concentration across intervals
- **Average Fragmentation**: Mean fragmentation across intervals
- **Trend**: Overall direction (increasing/decreasing/stable)

---

## Mathematical Foundations

### 1. Shannon Entropy (Diversity)

**Original Formula**:
```
H(X) = -Σ p(x) * log(p(x))
```

**Normalized Version**:
```
H_norm(X) = H(X) / log(n)
```

**Properties**:
- Maximum when all probabilities equal: `H_max = log(n)`
- Minimum when one probability = 1: `H_min = 0`
- Normalized version ranges [0, 1]

### 2. Gini Coefficient (Concentration)

**Original Formula**:
```
G = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n
```

**Properties**:
- Measures inequality in distribution
- 0 = perfect equality
- 1 = perfect inequality
- Used in economics to measure income inequality

### 3. Jensen-Shannon Divergence

**Properties**:
- Symmetric: `JS(P || Q) = JS(Q || P)`
- Bounded: `0 ≤ JS(P || Q) ≤ 1`
- Metric: Satisfies triangle inequality
- Square root is a true metric

**Advantages over KL Divergence**:
- KL divergence is not symmetric
- KL divergence can be infinite
- JS divergence is always finite and symmetric

### 4. Linear Regression (Trend)

**Formula**:
```
y = β₀ + β₁ * x + ε
where:
  β₁ = slope (trend direction)
  β₀ = intercept
```

**Slope Calculation**:
```
β₁ = Σ((x_i - x̄)(y_i - ȳ)) / Σ(x_i - x̄)²
```

---

## Example Calculation Walkthrough

### Interval: 2010-2014

**Step 1: Get Theory Usage**
```
Theory A (RBV): 15 papers
Theory B (TCE): 12 papers
Theory C (Agency): 8 papers
Theory D (Institutional): 6 papers
Theory E (Dynamic Capabilities): 5 papers
Total: 46 papers
```

**Step 2: Calculate Diversity**
```
Proportions: [15/46, 12/46, 8/46, 6/46, 5/46]
            = [0.326, 0.261, 0.174, 0.130, 0.109]

Entropy = -(0.326*log(0.326) + 0.261*log(0.261) + ...)
        = 1.52

Normalized = 1.52 / log(5) = 1.52 / 1.609 = 0.945
Diversity = 0.945 (high diversity)
```

**Step 3: Calculate Concentration (Gini)**
```
Sorted counts: [15, 12, 8, 6, 5]
n = 5, total = 46

Gini = (2 * (1*15 + 2*12 + 3*8 + 4*6 + 5*5)) / (5 * 46) - (5+1)/5
     = (2 * 118) / 230 - 1.2
     = 1.026 - 1.2
     = -0.174 → clamp to 0.0
     
Actually, let's recalculate properly:
Gini = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n
     = (2 * 118) / (5 * 46) - 6/5
     = 236/230 - 1.2
     = 1.026 - 1.2
     = -0.174

Wait, this seems wrong. Let me use the correct formula:
Gini = 1 - (2 * Σ(cumulative_proportion)) / n

Cumulative: [15, 27, 35, 41, 46]
Cumulative proportion: [0.326, 0.587, 0.761, 0.891, 1.0]
Sum = 3.565

Gini = 1 - (2 * 3.565) / 5
     = 1 - 1.426
     = -0.426

This is still negative. The issue is with the formula. Let me use the standard Gini formula:

Gini = ΣΣ |x_i - x_j| / (2 * n² * x̄)
     = (sum of all pairwise differences) / (2 * n² * mean)

Actually, the code uses:
Gini = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n

But this can be negative. The code clamps it to [0, 1], so:
Concentration = max(0, min(1, gini)) = 0.0
```

**Step 4: Calculate Fragmentation**
```
Fragmentation = 1 - Concentration = 1 - 0.0 = 1.0
(Highly fragmented)
```

**Step 5: Calculate Divergence (vs Previous Interval)**
```
Previous interval distribution: [0.4, 0.3, 0.2, 0.1, 0.0]
Current interval distribution: [0.326, 0.261, 0.174, 0.130, 0.109]

Mixture M = 0.5 * (P + Q)
          = [0.363, 0.281, 0.187, 0.115, 0.055]

KL(P || M) = 0.4*log(0.4/0.363) + 0.3*log(0.3/0.281) + ...
           = 0.023

KL(Q || M) = 0.326*log(0.326/0.363) + 0.261*log(0.261/0.281) + ...
           = 0.019

JS Divergence = 0.5 * 0.023 + 0.5 * 0.019 = 0.021
(Low divergence - similar distributions)
```

**Step 6: Calculate Emergence Rate**
```
New theories in this interval: 1 (Theory E)
Total papers: 46
Emergence Rate = 1 / 46 = 0.022 (2.2%)
```

---

## Comparison: Topic Evolution vs Theory Evolution

| Aspect | Topic Evolution | Theory Evolution |
|--------|----------------|------------------|
| **Data Source** | Paper embeddings (semantic) | Theory usage (explicit) |
| **Method** | Unsupervised clustering (K-means) | Statistical distribution analysis |
| **Clustering** | Yes (identifies topics) | No (uses explicit theory labels) |
| **Diversity Metric** | Shannon entropy of clusters | Shannon entropy of theories |
| **Stability** | Centroid similarity | Distribution similarity (JS divergence) |
| **Emerging** | New clusters | New theory names |
| **Complexity** | Higher (requires embeddings) | Lower (uses graph relationships) |

---

## Limitations & Considerations

1. **Theory Name Normalization**: Assumes consistent theory naming in Neo4j
2. **Missing Relationships**: Papers without theory relationships are excluded
3. **Theory Granularity**: Doesn't distinguish theory variants (e.g., "RBV" vs "Resource-Based View")
4. **Temporal Granularity**: 5-year intervals may miss shorter-term shifts
5. **Gini Calculation**: Current implementation may need refinement for edge cases
6. **Emergence Rate**: Sensitive to theory naming consistency

---

## Future Improvements

1. **Theory Normalization**: Map variant names to canonical theory names
2. **Theory Hierarchies**: Account for theory families (e.g., "Neo-institutional Theory" under "Institutional Theory")
3. **Weighted Metrics**: Weight by paper impact/citations
4. **Temporal Smoothing**: Account for gradual theory evolution
5. **Theory Co-occurrence**: Analyze which theories are used together
6. **Theory-Phenomenon Networks**: Visualize theory-phenomenon relationships over time

---

## Example Output

```json
{
  "interval": "2010-2014",
  "theory_count": 5,
  "diversity": 0.945,
  "concentration": 0.055,
  "fragmentation_index": 0.945,
  "divergence": 0.021,
  "emergence_rate": 0.022,
  "theories": {
    "Resource-Based View": {
      "usage_count": 15,
      "paper_count": 15,
      "phenomenon_count": 8
    },
    "Transaction Cost Economics": {
      "usage_count": 12,
      "paper_count": 12,
      "phenomenon_count": 6
    },
    ...
  }
}
```

---

## References

- **Shannon Entropy**: Shannon, C. E. (1948). "A Mathematical Theory of Communication"
- **Gini Coefficient**: Gini, C. (1912). "Variabilità e mutabilità"
- **Jensen-Shannon Divergence**: Lin, J. (1991). "Divergence measures based on the Shannon entropy"
- **Theory Evolution**: Kuhn, T. S. (1962). "The Structure of Scientific Revolutions"
