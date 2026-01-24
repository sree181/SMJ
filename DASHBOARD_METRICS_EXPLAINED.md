# 📊 Dashboard Metrics Explained - Simple Guide

**For Non-Technical Users**

This document explains every metric in the dashboard in simple, easy-to-understand terms. The order matches the dashboard tabs exactly.

---

## 📑 TAB 1: Analytics Charts

This tab shows three main visualizations with key metrics about research papers, topics, and theories.

---

### 1. Research Volume Evolution (Bar Chart)

**What it shows:** How many research papers were published in each 5-year period.

**How it's calculated:**
- Count all papers published between 1985-1989, 1990-1994, 1995-1999, etc.
- Each bar represents one 5-year period
- Height of bar = number of papers

**What it means:**
- **Rising bars** = More research being published (field is growing)
- **Falling bars** = Less research (field may be declining)
- **Peak period** = The 5-year period with the most papers

**Example:**
- 1985-1989: 10 papers
- 2015-2019: 159 papers
- **Interpretation:** Research volume increased 15x over 30 years

**Key Numbers Shown:**
- **Total Papers:** Sum of all papers across all periods
- **Avg per Interval:** Average papers per 5-year period
- **Peak Period:** The period with the most papers

---

### 2. Topic Landscape Evolution (Area Chart)

**What it shows:** How research topics change over time - are they becoming more diverse or more focused?

**Three Metrics:**

#### A. Topic Count
**What it is:** Number of distinct research topics in each 5-year period.

**How it's calculated:**
1. Take all papers in a 5-year period
2. Use AI to group similar papers together (clustering)
3. Count how many groups (topics) exist

**What it means:**
- **High count** = Many different topics (field is broad)
- **Low count** = Few topics (field is focused)
- **Increasing** = Field is expanding into new areas
- **Decreasing** = Field is consolidating

**Example:**
- 2010-2014: 8 topics
- 2015-2019: 12 topics
- **Interpretation:** Field expanded from 8 to 12 research areas

---

#### B. Coherence (%)
**What it is:** How similar are papers within the same topic? (Do papers in a topic really belong together?)

**How it's calculated:**
1. For each topic, measure how similar all papers are to each other
2. Average similarity = coherence
3. Convert to percentage (0-100%)

**What it means:**
- **High coherence (80-100%)** = Papers in a topic are very similar → Well-defined topic
- **Low coherence (<50%)** = Papers are diverse → Topic might be too broad or poorly defined
- **Increasing** = Topics becoming more focused
- **Decreasing** = Topics becoming more scattered

**Example:**
- Coherence = 75%
- **Interpretation:** Papers within topics are 75% similar - topics are well-defined

---

#### C. Diversity (%)
**What it is:** How evenly are papers distributed across topics? (Are papers spread out or concentrated in a few topics?)

**How it's calculated:**
1. Count papers in each topic
2. Calculate how evenly distributed they are
3. Perfect distribution = 100% diversity
4. All papers in one topic = 0% diversity

**What it means:**
- **High diversity (80-100%)** = Papers spread evenly across many topics
- **Low diversity (<50%)** = Most papers in a few topics (concentrated)
- **Increasing** = Field becoming more diverse
- **Decreasing** = Field becoming more focused

**Example:**
- Diversity = 65%
- **Interpretation:** Papers are moderately distributed across topics (not too concentrated, not too spread out)

---

### 3. Theoretical Evolution & Divergence (Line Chart)

**What it shows:** How theories (like "Resource-Based View" or "Agency Theory") are used over time - are they diversifying or converging?

**Five Metrics:**

#### A. Diversity (%)
**What it is:** How evenly are theories used across papers? (Are many theories used equally, or do a few dominate?)

**How it's calculated:**
1. Count how many papers use each theory
2. Calculate how evenly distributed theory usage is
3. Perfect distribution = 100% diversity

**What it means:**
- **High diversity (80-100%)** = Many theories used equally (field is diverse)
- **Low diversity (<50%)** = Few theories dominate (field is concentrated)
- **Increasing** = Field is diversifying (more theories being used)
- **Decreasing** = Field is converging (fewer theories dominating)

**Example:**
- Diversity = 72%
- **Interpretation:** Theories are fairly evenly distributed - no single theory dominates

---

#### B. Concentration (%)
**What it is:** Opposite of diversity - how concentrated is theory usage? (Do a few theories dominate?)

**How it's calculated:**
- Uses Gini coefficient (measures inequality)
- High concentration = Few theories dominate
- Low concentration = Theories used equally

**What it means:**
- **High concentration (60-100%)** = Few theories dominate the field
- **Low concentration (<40%)** = Theories used more equally
- **Increasing** = Field becoming more concentrated
- **Decreasing** = Field becoming more diverse

**Example:**
- Concentration = 35%
- **Interpretation:** Theories are not highly concentrated - usage is relatively equal

---

#### C. Fragmentation (%)
**What it is:** How fragmented is the theoretical landscape? (Are there many theories with no clear leader?)

**How it's calculated:**
- Fragmentation = 1 - Concentration
- High fragmentation = Many theories, no dominant one
- Low fragmentation = One or few theories dominate

**What it means:**
- **High fragmentation (70-100%)** = Many theories, field is fragmented
- **Low fragmentation (<30%)** = Few theories dominate, field is unified
- **Increasing** = Field becoming more fragmented
- **Decreasing** = Field becoming more unified

**Example:**
- Fragmentation = 65%
- **Interpretation:** Field is moderately fragmented - many theories exist but some are more popular

---

#### D. Divergence (%)
**What it is:** How much has theory usage changed from the previous 5-year period?

**How it's calculated:**
1. Compare theory distribution in current period vs. previous period
2. Measure how different they are (Jensen-Shannon divergence)
3. 0% = No change, 100% = Completely different

**What it means:**
- **High divergence (50-100%)** = Theory usage changed significantly
- **Low divergence (<20%)** = Theory usage stayed similar
- **Increasing** = Field is changing rapidly
- **Decreasing** = Field is stabilizing

**Example:**
- Divergence = 15%
- **Interpretation:** Theory usage changed moderately from previous period

---

#### E. Emergence Rate (%)
**What it is:** How many new theories appear per paper? (Rate of new theory introduction)

**How it's calculated:**
- Count new theories that didn't exist in previous period
- Divide by total papers in current period
- Convert to percentage

**What it means:**
- **High rate (5-10%)** = Many new theories being introduced
- **Low rate (<2%)** = Few new theories (field is stable)
- **Increasing** = Field is innovating rapidly
- **Decreasing** = Field is consolidating

**Example:**
- Emergence Rate = 3.2%
- **Interpretation:** About 3 new theories appear for every 100 papers

---

## 📑 TAB 2: Theory Proportions

**What it shows:** Pie charts showing what percentage of papers use each theory in each 5-year period.

**How it's calculated:**
1. For each 5-year period, count papers using each theory
2. Calculate percentage: (papers using theory / total papers) × 100
3. Display as pie chart (each slice = one theory)

**What it means:**
- **Large slice** = Theory used in many papers (popular)
- **Small slice** = Theory used in few papers (niche)
- **Many small slices** = Field is fragmented
- **Few large slices** = Field is concentrated

**Example:**
- 2015-2019:
  - Resource-Based View: 25% (quarter of all papers)
  - Agency Theory: 15%
  - Transaction Cost Economics: 12%
  - Others: 48%
- **Interpretation:** RBV is the most popular theory, but field is still diverse

---

## 📑 TAB 3: Theory Betweenness

**What it shows:** Which theories act as "bridges" connecting different research areas?

**What is Betweenness?**
- Measures how often a theory appears on the "shortest path" between different phenomena
- High betweenness = Theory connects many different research areas
- Low betweenness = Theory is isolated or specialized

**How it's calculated:**
1. Build a network: Theories ↔ Phenomena (what theories explain what phenomena)
2. For each theory, count how many "paths" go through it
3. Normalize to 0-1 scale

**What it means:**
- **High betweenness (0.5-1.0)** = Theory connects many areas (central, integrative)
- **Low betweenness (<0.2)** = Theory is specialized or isolated
- **Increasing** = Theory becoming more central
- **Decreasing** = Theory becoming more specialized

**Example:**
- Resource-Based View: Betweenness = 0.65
- Niche Theory: Betweenness = 0.08
- **Interpretation:** RBV connects many research areas, while niche theory is isolated

---

## 📑 TAB 4: Opportunity Gaps

**What it shows:** Research opportunities - phenomena that could be studied with more theories, or theories that could explain more phenomena.

**Two Types of Gaps:**

### A. Theory-Phenomenon Gaps
**What it is:** Phenomena that are studied by few theories (opportunity to apply more theories)

**How it's calculated:**
1. Count how many theories explain each phenomenon
2. Identify phenomena with few theories (e.g., < 2 theories)
3. These are "opportunities"

**What it means:**
- **High gap** = Phenomenon understudied (opportunity for new research)
- **Low gap** = Phenomenon well-studied (many theories applied)

**Example:**
- "Digital Transformation": Only 1 theory applied
- **Interpretation:** Opportunity to apply other theories (e.g., RBV, Dynamic Capabilities)

---

### B. Theory-Phenomenon Coverage Gaps
**What it is:** Theories that explain few phenomena (opportunity to expand theory application)

**How it's calculated:**
1. Count how many phenomena each theory explains
2. Identify theories explaining few phenomena (e.g., < 3 phenomena)
3. These are "opportunities"

**What it means:**
- **High gap** = Theory narrowly applied (opportunity to expand)
- **Low gap** = Theory broadly applied (explains many phenomena)

**Example:**
- "Real Options Theory": Explains only 2 phenomena
- **Interpretation:** Opportunity to apply this theory to more phenomena

---

## 📑 TAB 5: Integration Mechanism

**What it shows:** How theories are combined together in research papers.

**What is Integration?**
- When a paper uses multiple theories together
- Measures how theories are "integrated" or "combined"

**How it's calculated:**
1. For each paper, count how many theories it uses
2. Papers using 2+ theories = "integrated"
3. Calculate percentage of integrated papers per period

**What it means:**
- **High integration (60-100%)** = Many papers combine theories (field is integrative)
- **Low integration (<40%)** = Most papers use single theory (field is specialized)
- **Increasing** = Field becoming more integrative
- **Decreasing** = Field becoming more specialized

**Example:**
- 2015-2019: 65% of papers use 2+ theories
- **Interpretation:** Field is highly integrative - researchers combine theories

---

## 📑 TAB 6: Cumulative Theory & Knowledge Accumulation

**What it shows:** How knowledge accumulates over time - are theories building on each other or starting fresh?

**What is Cumulative Knowledge?**
- When new research builds on previous theories
- Measures whether theories are reused and built upon

**How it's calculated:**
1. Track which theories appear in each period
2. Count "new" theories (first appearance) vs. "reused" theories (appeared before)
3. Calculate cumulative percentage

**What it means:**
- **High cumulative (70-100%)** = Most theories are reused (knowledge building)
- **Low cumulative (<50%)** = Many new theories (field is reinventing)
- **Increasing** = Field is building on previous knowledge
- **Decreasing** = Field is introducing many new theories

**Example:**
- Cumulative = 78%
- **Interpretation:** 78% of theories are reused from previous periods - field is building knowledge

---

## 📑 TAB 7: Canonical Problem Analysis

**What it shows:** Analysis of "canonical" papers - papers that are central to the field.

**What is a Canonical Paper?**
- A paper that is highly connected (cited by many, uses many theories/phenomena)
- Central to the research network
- In this dashboard: Papers with 5+ connections (theories + phenomena)

**Two Metrics:**

### A. Canonical Coverage Ratio (%)
**What it is:** What percentage of papers are "canonical" (highly connected)?

**How it's calculated:**
- Count papers with 5+ connections (theories + phenomena)
- Divide by total papers
- Convert to percentage

**What it means:**
- **High coverage (30-50%)** = Many papers are central (field is well-connected)
- **Low coverage (<15%)** = Few papers are central (field is fragmented)
- **Increasing** = Field becoming more connected
- **Decreasing** = Field becoming more fragmented

**Example:**
- Coverage = 25%
- **Interpretation:** 1 in 4 papers is highly connected to the field

---

### B. Canonical Centrality
**What it is:** How central are canonical papers compared to non-canonical papers?

**How it's calculated:**
1. Build network of paper connections
2. Calculate "centrality" (how central each paper is in the network)
3. Compare average centrality: Canonical papers vs. Non-canonical papers

**What it means:**
- **High centrality** = Canonical papers are much more central (expected)
- **Low difference** = Canonical papers not much more central (unexpected)
- **Increasing** = Canonical papers becoming more central
- **Decreasing** = Field becoming more decentralized

**Example:**
- Canonical papers: Average centrality = 0.45
- Non-canonical papers: Average centrality = 0.12
- **Interpretation:** Canonical papers are 3.75x more central (as expected)

---

## 📑 TAB 8: Theoretical Concentration Index (HHI)

**What it shows:** How concentrated is theory usage? (Similar to Concentration metric, but uses Herfindahl-Hirschman Index)

**What is HHI?**
- Measures market concentration (used in economics)
- Adapted to measure theory concentration
- Range: 0-1 (or 0-10,000 if using standard HHI scale)

**How it's calculated:**
1. Calculate each theory's "market share" (percentage of total usage)
2. Square each share
3. Sum all squared shares
4. Normalize to 0-1 scale

**What it means:**
- **High HHI (0.5-1.0)** = Few theories dominate (highly concentrated)
- **Low HHI (<0.3)** = Theories used more equally (low concentration)
- **Increasing** = Field becoming more concentrated
- **Decreasing** = Field becoming more diverse

**Example:**
- HHI = 0.35
- **Interpretation:** Moderate concentration - some theories more popular but not dominated by one

---

## 📑 TAB 9: Theory-Problem Alignment

**What it shows:** How well do theories align with the problems/phenomena they're used to study?

**What is Alignment?**
- Measures whether theories are used appropriately for the phenomena they study
- High alignment = Theories match problems well
- Low alignment = Mismatch between theories and problems

**How it's calculated:**
1. For each theory-phenomenon pair, measure how often they appear together
2. Compare to expected frequency (if random)
3. Calculate alignment score

**What it means:**
- **High alignment (70-100%)** = Theories well-matched to problems
- **Low alignment (<50%)** = Theories not well-matched (opportunity for better alignment)
- **Increasing** = Field improving theory-problem matching
- **Decreasing** = Field becoming less aligned

**Example:**
- Alignment = 68%
- **Interpretation:** Theories are moderately well-aligned with the problems they study

---

## 📑 TAB 10: Integrative Theory Centrality

**What it shows:** How central are papers that use theories? (Do theory-using papers act as bridges?)

**What is Integrative Centrality?**
- Measures how central papers are that use a particular theory
- High centrality = Theory-using papers connect different research areas
- Low centrality = Theory-using papers are isolated

**How it's calculated:**
1. Build network of paper connections (based on shared theories/phenomena)
2. For each theory, find papers using it
3. Calculate average "betweenness centrality" of those papers
4. This is the theory's integrative centrality

**What it means:**
- **High centrality (0.5-1.0)** = Theory-using papers are central (theory is integrative)
- **Low centrality (<0.2)** = Theory-using papers are isolated (theory is specialized)
- **Increasing** = Theory becoming more integrative
- **Decreasing** = Theory becoming more specialized

**Example:**
- Resource-Based View: Integrative centrality = 0.58
- **Interpretation:** Papers using RBV are central in the network - RBV is an integrative theory

---

## 📊 Summary: What Each Tab Tells You

| Tab | Main Question | Key Insight |
|-----|--------------|-------------|
| **Analytics Charts** | How is the field evolving? | Research volume, topic diversity, theory usage patterns |
| **Theory Proportions** | Which theories are most popular? | Visual breakdown of theory usage over time |
| **Theory Betweenness** | Which theories connect different areas? | Identifies integrative vs. specialized theories |
| **Opportunity Gaps** | Where are research opportunities? | Understudied phenomena, underused theories |
| **Integration Mechanism** | Are theories being combined? | Measures field's integrative vs. specialized nature |
| **Cumulative Theory** | Is knowledge building or reinventing? | Tracks knowledge accumulation over time |
| **Canonical Analysis** | Which papers are central? | Identifies core papers and their centrality |
| **HHI Concentration** | How concentrated is theory usage? | Measures field's concentration (similar to Concentration metric) |
| **Theory-Problem Alignment** | Do theories match problems? | Measures appropriateness of theory application |
| **Integrative Centrality** | Are theory-using papers central? | Identifies theories that create connections |

---

## 🎯 Quick Reference: What to Look For

### Healthy Field Indicators:
- ✅ Increasing research volume
- ✅ Moderate diversity (60-80%)
- ✅ Moderate fragmentation (50-70%)
- ✅ High integration (60%+)
- ✅ High cumulative knowledge (70%+)
- ✅ Moderate concentration (30-50%)

### Concerning Indicators:
- ⚠️ Declining research volume
- ⚠️ Very low diversity (<40%)
- ⚠️ Very high concentration (>70%)
- ⚠️ Low integration (<40%)
- ⚠️ Low cumulative knowledge (<50%)

---

**End of Guide**

*For technical details, see: `ANALYTICS_CHARTS_DETAILED_REPORT.md`, `TOPIC_EVOLUTION_METHODOLOGY.md`, `THEORETICAL_EVOLUTION_METHODOLOGY.md`*
