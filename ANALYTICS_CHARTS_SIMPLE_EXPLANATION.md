# Analytics Charts - Simple Explanation of All Calculations

**Simple, non-technical explanations of every metric in the Analytics Charts tab**

---

## 📊 SECTION 1: Paper Counts by 5-Year Intervals

### What It Shows:
**Simple counting** - How many papers were published in each 5-year period.

### How It's Calculated:
```
For each 5-year period (e.g., 1985-1989):
  1. Find all papers with year in that range
  2. Count them
  3. That's it!
```

**Example:**
- 1985-1989: 10 papers
- 1990-1994: 85 papers
- 2015-2019: 159 papers (peak period)

**Why It Matters:**
Shows research volume trends - are more papers being published over time?

---

## 🎯 SECTION 2: Topic Landscape Evolution

### What It Shows:
**How research topics change over time** - Are papers clustering around similar themes?

### How It's Calculated:

#### Step 1: Convert Papers to Numbers (Embeddings)
- Each paper's title + abstract → converted to a 384-number vector
- Similar papers get similar vectors
- Like giving each paper a "fingerprint"

#### Step 2: Group Similar Papers (K-Means Clustering)
- Papers with similar "fingerprints" → grouped into topics
- Like sorting books by genre
- **Example:** 100 papers → 5 topics (20 papers each)

#### Step 3: Calculate Metrics

**A. Topic Count**
- **Simple:** How many topics were found?
- **Example:** 5 topics in 2010-2014

**B. Coherence (0-100%)**
- **What it means:** How similar are papers within the same topic?
- **Calculation:** Average similarity between papers in the same topic
- **High (80-100%):** Papers are very similar → well-defined topic
- **Low (<50%):** Papers are diverse → loose topic
- **Example:** 
  - Topic "M&A Integration": 5 papers, all very similar → coherence = 85%
  - Topic "Various Strategy": 5 papers, diverse → coherence = 45%

**C. Diversity (0-100%)**
- **What it means:** Are papers evenly spread across topics, or concentrated in one?
- **Calculation:** 
  - If papers evenly distributed → diversity = 100%
  - If all papers in one topic → diversity = 0%
- **Example:**
  - 10 papers, 5 topics, 2 papers each → diversity = 100% (perfect)
  - 10 papers, 5 topics, 8 in one topic → diversity = 30% (concentrated)

**D. Stability (0-100%)**
- **What it means:** Do topics persist from one period to the next?
- **Calculation:** Compare topic "centers" between consecutive periods
- **High (70-100%):** Topics stay similar → stable research themes
- **Low (<50%):** Topics change a lot → field is evolving rapidly

---

## 🧠 SECTION 3: Theoretical Evolution & Divergence

### What It Shows:
**How theories are used across papers** - Are researchers using many different theories or just a few?

### How It's Calculated:

#### Step 1: Count Theory Usage
- For each 5-year period, count how many times each theory is used
- **Example (2010-2014):**
  - Resource-Based View: 25 uses
  - Agency Theory: 18 uses
  - Upper Echelons Theory: 7 uses
  - ... (181 different theories total)

#### Step 2: Calculate Metrics

**A. Theory Diversity (0-100%)**
- **What it means:** Are theories used evenly, or is one theory dominating?
- **Calculation:** Shannon Entropy (fancy way to measure "evenness")
- **High (90-100%):** Many theories used equally → diverse field
- **Low (<50%):** One theory dominates → concentrated field
- **Example:**
  - 10 theories, each used 10 times → diversity = 100% (perfect)
  - 10 theories, one used 90 times, others used 1 time → diversity = 20% (concentrated)

**B. Theory Concentration (0-100%)**
- **What it means:** How much is theory usage concentrated in a few theories?
- **Calculation:** Gini Coefficient (measures inequality)
- **High (30-100%):** Few theories dominate → high concentration
- **Low (0-20%):** Theories used evenly → low concentration
- **Example:**
  - RBV: 25 uses (9.4%), Agency: 18 uses (6.7%) → concentration = 30.5%
  - This means some theories are more popular than others

**C. Fragmentation Index (0-100%)**
- **What it means:** Is the field fragmented (many theories) or unified (few theories)?
- **Calculation:** Fragmentation = 1 - Concentration
- **High (70-100%):** Many theories, no single dominant one → fragmented
- **Low (<30%):** Few theories dominate → unified
- **Example:**
  - Concentration = 30% → Fragmentation = 70%
  - This means the field is quite diverse with no single theory dominating

**D. Divergence (0-100%)**
- **What it means:** How different is theory usage compared to the previous period?
- **Calculation:** Jensen-Shannon Divergence (measures difference between distributions)
- **High (50-100%):** Theory usage changed a lot → field is diverging
- **Low (<20%):** Theory usage stayed similar → field is stable
- **Example:**
  - 2010-2014: RBV dominant
  - 2015-2019: RBV and Agency Theory tied
  - Divergence = 35% (moderate change)

**E. Emergence Rate (0-100%)**
- **What it means:** What percentage of theories are new in this period?
- **Calculation:** (New theories / Total theories) × 100
- **High (30-100%):** Many new theories → field is innovating
- **Low (<10%):** Few new theories → field is stable
- **Example:**
  - 2010-2014: 181 theories total
  - 50 are new → Emergence Rate = 27.6%

---

## 📈 Summary: What Each Metric Tells You

| Metric | What It Measures | High Value Means | Low Value Means |
|--------|-----------------|------------------|-----------------|
| **Paper Count** | Research volume | More papers published | Fewer papers published |
| **Topic Count** | Number of research themes | Many different topics | Few topics |
| **Coherence** | Topic quality | Well-defined topics | Loose, diverse topics |
| **Topic Diversity** | Topic distribution | Papers evenly spread | Papers concentrated |
| **Theory Diversity** | Theory distribution | Many theories used equally | One theory dominates |
| **Concentration** | Theory inequality | Few theories dominate | Theories used evenly |
| **Fragmentation** | Field structure | Many theories, no dominant one | Few theories dominate |
| **Divergence** | Change over time | Theory usage changed a lot | Theory usage stable |
| **Emergence Rate** | Innovation | Many new theories | Few new theories |

---

## 🎯 Real-World Interpretation

### High Diversity + High Fragmentation:
- **Meaning:** Field uses many different theories, no single dominant one
- **Example:** Strategic Management (95% diversity, 82% fragmentation)
- **Implication:** Multi-theoretical field, many perspectives

### Low Concentration + High Coherence:
- **Meaning:** Theories used evenly, topics are well-defined
- **Implication:** Healthy field with clear research themes

### High Divergence + High Emergence:
- **Meaning:** Field is changing rapidly, new theories emerging
- **Implication:** Field is innovating, but may lack stability

### Low Stability + High Topic Count:
- **Meaning:** Many topics, but they change frequently
- **Implication:** Field is evolving, research directions shifting

---

## 🔢 Simple Formula Reference

**Diversity (Shannon Entropy):**
```
Diversity = -Σ(p × log(p)) / log(n)
where:
  p = proportion of each theory/topic
  n = number of theories/topics
```

**Concentration (Gini Coefficient):**
```
Concentration = ΣΣ |x_i - x_j| / (2 × n² × mean)
where:
  x_i, x_j = usage counts for theories
  n = number of theories
```

**Fragmentation:**
```
Fragmentation = 1 - Concentration
```

**Divergence (Jensen-Shannon):**
```
Divergence = measures difference between two distributions
```

**Coherence:**
```
Coherence = average similarity between papers in same topic
```

---

## 💡 Key Takeaways

1. **Paper Counts:** Simple counting - shows research volume trends
2. **Topic Evolution:** Uses AI (embeddings + clustering) to find research themes
3. **Theory Evolution:** Uses statistics (entropy, Gini) to measure theory usage patterns
4. **All metrics are percentages (0-100%)** for easy comparison
5. **High values don't always mean "better"** - depends on what you're measuring

---

**Generated:** 2025-01-23  
**Purpose:** Simple, non-technical explanation of all Analytics Charts calculations
