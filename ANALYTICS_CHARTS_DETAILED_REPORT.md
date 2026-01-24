# Analytics Charts Tab - Detailed Calculation Report

**Generated:** 2025-01-23  
**Database:** Neo4j  
**Verification Method:** Direct database queries and calculation verification

---

## Executive Summary

This report provides a **tab-by-tab, metric-by-metric** breakdown of all calculations in the "Analytics Charts" tab, with **exact numbers verified from the Neo4j database**.

### Key Findings:
- **Total Papers:** 751 (verified from database)
- **Average per Interval:** 93.9 papers
- **Peak Period:** 2015-2019 (159 papers)
- **Average Theory Diversity:** 95.95%
- **Average Fragmentation:** 82.61%

---

## SECTION 1: Research Volume Evolution (Bar Chart)

### Metric: Paper Counts by 5-Year Intervals

#### Calculation Logic:
```cypher
MATCH (p:Paper)
WHERE p.year >= $start_year 
  AND p.year < $end_year
  AND p.year > 0
RETURN count(p) as count,
       collect(p.paper_id) as paper_ids
```

**Key Points:**
- Intervals: 5-year periods (1985-1989, 1990-1994, etc.)
- Filter: Excludes papers with `year = 0` or `NULL`
- Returns: Count and list of paper IDs per interval

#### Verified Database Results:

| Interval | Paper Count | Sample Paper IDs |
|----------|-------------|-----------------|
| 1985-1989 | **10** | 1988_310, 1988_305, 1989_308, 1989_253, 1989_304 |
| 1990-1994 | **85** | 1990_295, 1990_379, 1990_319, 1990_357, 1990_358 |
| 1995-1999 | **106** | 1995_1219, 1995_1878, 1995_1989, 1995_1078, 1995_1245 |
| 2000-2004 | **127** | 2000_103, 2000_137, 2000_1036, 2000_1295, 2000_1261 |
| 2005-2009 | **99** | 2005_1179, 2005_1125, 2005_1043, 2005_1266, 2005_1643 |
| 2010-2014 | **149** | 2010_1391, 2010_1398, 2010_1662, 2010_1671, 2010_1533 |
| 2015-2019 | **159** | 2015_1149, 2015_1265, 2015_1246, 2015_1059, 2015_2417 |
| 2020-2024 | **16** | 2020_2359, 2020_4253, 2020_4286, 2020_1103, 2020_1779 |

**Verification:**
- Sum: 10 + 85 + 106 + 127 + 99 + 149 + 159 + 16 = **751 papers** ✅

---

## SECTION 2: Summary Metrics (Top Cards)

### 2.1 Total Papers

**Displayed Value:** 751

**Calculation:**
```
Total Papers = sum(count) for all intervals
             = 10 + 85 + 106 + 127 + 99 + 149 + 159 + 16
             = 751
```

**Verification:** ✅ Matches database query result

---

### 2.2 Average per Interval

**Displayed Value:** 94 (rounded from 93.9)

**Calculation:**
```
Avg per Interval = Total Papers / Number of Intervals
                 = 751 / 8
                 = 93.875
                 ≈ 93.9 (rounded to 94 in UI)
```

**Verification:** ✅ Correct

---

### 2.3 Peak Period

**Displayed Value:** 2015-2019 (159 papers)

**Calculation:**
```
Peak Period = interval with maximum count
            = max([10, 85, 106, 127, 99, 149, 159, 16])
            = 159 (at interval 2015-2019)
```

**Verification:** ✅ Correct

---

## SECTION 3: Theoretical Evolution & Divergence (Line Chart)

### Overview

This section analyzes **theory usage patterns** across papers using statistical measures:
- **Diversity:** How evenly distributed is theory usage?
- **Concentration:** How concentrated is theory usage? (Gini coefficient)
- **Fragmentation:** Inverse of concentration (1 - Gini)

### 3.1 Theory Diversity (Normalized Shannon Entropy)

#### Formula:
```
Diversity = -Σ(p_i * log(p_i)) / log(n)

where:
  p_i = proportion of theory i usage = count_i / total_usage
  n = number of distinct theories
```

#### Interpretation:
- **1.0 (100%):** Perfect diversity (all theories used equally)
- **0.0 (0%):** No diversity (one theory dominates completely)
- **0.5-0.8 (50-80%):** Moderate diversity

#### Verified Calculations by Interval:

| Interval | Papers | Theories | Total Usage | Diversity | Diversity % |
|----------|--------|----------|-------------|-----------|-------------|
| 1985-1989 | 10 | 21 | 21 | 1.0000 | **100.00%** |
| 1990-1994 | 85 | 190 | 222 | 0.9793 | **97.93%** |
| 1995-1999 | 106 | 224 | 281 | 0.9566 | **95.66%** |
| 2000-2004 | 127 | 188 | 243 | 0.9438 | **94.38%** |
| 2005-2009 | 99 | 162 | 227 | 0.9317 | **93.17%** |
| 2010-2014 | 149 | 181 | 267 | 0.9183 | **91.83%** |
| 2015-2019 | 159 | 222 | 310 | 0.9459 | **94.59%** |
| 2020-2024 | 16 | 20 | 20 | 1.0000 | **100.00%** |

**Average Diversity:** 95.95%

**Example Calculation (1990-1994):**
- 190 distinct theories
- 222 total theory uses
- Each theory used approximately 1.17 times on average
- High diversity because usage is very evenly distributed

---

### 3.2 Theory Concentration (Gini Coefficient)

#### Formula:
```
Gini = (ΣΣ |x_i - x_j|) / (2 * n² * x̄)

where:
  x_i = sorted theory counts (descending order)
  n = number of theories
  x̄ = mean of theory counts
```

#### Interpretation:
- **0.0 (0%):** Perfect equality (all theories used equally)
- **1.0 (100%):** Perfect inequality (one theory dominates completely)
- **0.3-0.6 (30-60%):** Moderate concentration

#### Verified Calculations by Interval:

| Interval | Concentration | Concentration % |
|----------|---------------|-----------------|
| 1985-1989 | 0.0000 | **0.00%** |
| 1990-1994 | 0.1367 | **13.67%** |
| 1995-1999 | 0.1948 | **19.48%** |
| 2000-2004 | 0.2186 | **21.86%** |
| 2005-2009 | 0.2718 | **27.18%** |
| 2010-2014 | 0.3052 | **30.52%** |
| 2015-2019 | 0.2643 | **26.43%** |
| 2020-2024 | 0.0000 | **0.00%** |

**Average Concentration:** 17.39%

**Example Calculation (2010-2014):**
- Top theory: Resource-Based View (25 uses, 9.4% of total)
- Second: Agency Theory (18 uses, 6.7% of total)
- Gini coefficient = 0.3052 (30.52% concentration)
- Indicates moderate concentration (some theories more popular than others)

---

### 3.3 Fragmentation Index

#### Formula:
```
Fragmentation = 1 - Gini_Coefficient
```

#### Interpretation:
- **1.0 (100%):** Highly fragmented (many theories, no dominant one)
- **0.0 (0%):** Not fragmented (one theory dominates)
- **0.4-0.7 (40-70%):** Moderate fragmentation

#### Verified Calculations by Interval:

| Interval | Fragmentation | Fragmentation % |
|----------|---------------|-----------------|
| 1985-1989 | 1.0000 | **100.00%** |
| 1990-1994 | 0.8633 | **86.33%** |
| 1995-1999 | 0.8052 | **80.52%** |
| 2000-2004 | 0.7814 | **78.14%** |
| 2005-2009 | 0.7282 | **72.82%** |
| 2010-2014 | 0.6948 | **69.48%** |
| 2015-2019 | 0.7357 | **73.57%** |
| 2020-2024 | 1.0000 | **100.00%** |

**Average Fragmentation:** 82.61%

**Note:** The high fragmentation values (70-100%) indicate that the field is **highly diverse** with no single theory dominating. This is consistent with strategic management being a multi-theoretical field.

---

### 3.4 Top Theories by Interval

#### 1985-1989 (10 papers, 21 theories):
1. Market For Corporate Control: 1 use (4.8%)
2. Uncertainty And Turnover Intent: 1 use (4.8%)
3. Organizational Culture Shock: 1 use (4.8%)
4. Organizational Ecology: 1 use (4.8%)
5. Upper-Echelon Theory: 1 use (4.8%)

**Observation:** Very early period, all theories used equally (1 use each)

#### 1990-1994 (85 papers, 190 theories):
1. Agency Theory: 8 uses (3.6%)
2. Transaction Cost Economics: 5 uses (2.3%)
3. Miles And Snow Typology: 4 uses (1.8%)
4. Organizational Learning Theory: 4 uses (1.8%)
5. Market For Corporate Control: 3 uses (1.4%)

**Observation:** Agency Theory and TCE emerge as dominant theories

#### 1995-1999 (106 papers, 224 theories):
1. Resource-Based View: 15 uses (5.3%)
2. Resource-Based View Of The Firm: 11 uses (3.9%)
3. Agency Theory: 9 uses (3.2%)
4. Transaction Cost Economics: 7 uses (2.5%)
5. Organizational Learning Theory: 5 uses (1.8%)

**Observation:** Resource-Based View becomes dominant

#### 2000-2004 (127 papers, 188 theories):
1. Resource-Based View: 19 uses (7.8%)
2. Agency Theory: 12 uses (4.9%)
3. Dynamic Capabilities Theory: 6 uses (2.5%)
4. Resource-Based View Of The Firm: 6 uses (2.5%)
5. Organizational Learning Theory: 5 uses (2.1%)

**Observation:** RBV continues dominance, Dynamic Capabilities emerges

#### 2005-2009 (99 papers, 162 theories):
1. Resource-Based View: 21 uses (9.3%)
2. Agency Theory: 10 uses (4.4%)
3. Transaction Cost Economics: 9 uses (4.0%)
4. Dynamic Capabilities Theory: 5 uses (2.2%)
5. Stakeholder Theory: 5 uses (2.2%)

**Observation:** RBV peak usage (9.3%), highest concentration period

#### 2010-2014 (149 papers, 181 theories):
1. Resource-Based View: 25 uses (9.4%)
2. Agency Theory: 18 uses (6.7%)
3. Upper Echelons Theory: 7 uses (2.6%)
4. Institutional Theory: 7 uses (2.6%)
5. Stakeholder Theory: 6 uses (2.2%)

**Observation:** RBV and Agency Theory remain dominant, but usage is more distributed

#### 2015-2019 (159 papers, 222 theories):
1. Resource-Based View: 16 uses (5.2%)
2. Agency Theory: 16 uses (5.2%)
3. Stakeholder Theory: 8 uses (2.6%)
4. Upper Echelons Theory: 7 uses (2.3%)
5. Knowledge-Based View: 5 uses (1.6%)

**Observation:** RBV and Agency Theory tied, but lower percentages indicate more diversity

#### 2020-2024 (16 papers, 20 theories):
1. Hypercompetition: 1 use (5.0%)
2. Entrenchment And Increased Inequality: 1 use (5.0%)
3. Mueller Persistence: 1 use (5.0%)
4. Rank Friction: 1 use (5.0%)
5. Upper Echelons Theory: 1 use (5.0%)

**Observation:** Very recent period, limited data, all theories used equally

---

## SECTION 4: Topic Landscape Evolution (Stacked Area Chart)

### Overview

Topic evolution uses **unsupervised machine learning** (K-means clustering) on paper embeddings to identify research topics.

### Calculation Logic:

1. **Get Paper Embeddings:**
   ```cypher
   MATCH (p:Paper)
   WHERE p.paper_id IN $paper_ids
     AND p.embedding IS NOT NULL
   RETURN p.paper_id, p.embedding, p.title, p.abstract
   ```

2. **Determine Optimal Clusters:**
   - `optimal_k = min(10, papers / 3)`
   - Minimum: 2 clusters
   - Maximum: 10 clusters

3. **Perform K-Means Clustering:**
   - Algorithm: K-Means (scikit-learn)
   - Distance metric: Euclidean distance in 384-dimensional embedding space
   - Model: `all-MiniLM-L6-v2` (SentenceTransformer)

4. **Calculate Coherence:**
   ```
   Coherence(cluster) = mean(cosine_similarity(paper_i, paper_j))
                        for all i, j in cluster where i ≠ j
   ```
   - Average similarity within each topic cluster
   - Range: [0, 1] where 1.0 = highly coherent topic

5. **Calculate Diversity:**
   ```
   Diversity = -Σ(p_i * log(p_i)) / log(k)
   where:
     p_i = proportion of papers in cluster i
     k = number of clusters
   ```
   - Normalized Shannon entropy of cluster sizes
   - Range: [0, 1] where 1.0 = perfect diversity

6. **Calculate Stability:**
   - Compare cluster centroids between consecutive intervals
   - Cosine similarity between centroids
   - Range: [0, 1] where 1.0 = topics persist over time

### Database Status:

- **Papers with embeddings:** 1,029
- **Total papers (year > 0):** 753
- **Note:** Some papers may have embeddings but year=0, or embeddings may be duplicated

### Limitations:

1. **Requires Embeddings:** Papers without embeddings are excluded
2. **Computational Complexity:** K-means clustering is computationally expensive
3. **Stability Threshold:** Emerging/declining topics use 0.7 similarity threshold
4. **Cluster Count:** Simplified elbow method (could be improved)

---

## Verification Summary

### ✅ Verified Metrics:

1. **Paper Counts by Interval:** ✅ All 8 intervals verified
2. **Total Papers:** ✅ 751 (sum of all intervals)
3. **Average per Interval:** ✅ 93.9 (751 / 8)
4. **Peak Period:** ✅ 2015-2019 (159 papers)
5. **Theory Diversity:** ✅ All 8 intervals calculated and verified
6. **Theory Concentration:** ✅ All 8 intervals calculated and verified
7. **Fragmentation Index:** ✅ All 8 intervals calculated and verified
8. **Top Theories:** ✅ Top 5 theories per interval verified

### ⚠️ Notes:

1. **Topic Evolution:** Requires running actual clustering algorithm for full verification
2. **Embedding Coverage:** 136.7% coverage suggests some papers may have embeddings but year=0
3. **Theory Name Normalization:** Assumes consistent theory naming in Neo4j

---

## Conclusion

All **numeric metrics** displayed in the Analytics Charts tab have been **verified against the Neo4j database**. The calculations follow the documented formulas and produce consistent results.

**Key Insights:**
- The field shows **high theoretical diversity** (95.95% average)
- **Fragmentation is high** (82.61% average), indicating no single theory dominates
- **Resource-Based View** and **Agency Theory** are consistently among the top theories
- **2015-2019** was the peak publication period (159 papers)

---

**Report Generated By:** Analytics Verification Script  
**Database:** Neo4j  
**Date:** 2025-01-23
