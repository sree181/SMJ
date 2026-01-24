# Temporal Evolution System - Complete Guide

## Overview

The temporal evolution system captures how the Strategic Management field evolves across 5-year periods (2020-2024, 2015-2019, etc.). It enables analysis of:
- Theory evolution (which theories are emerging/declining)
- Method evolution (how methods change over time)
- Research question evolution
- Method-theory co-evolution
- Temporal trends and patterns

---

## Architecture

### 1. Time Period Nodes

**Node Type**: `TimePeriod`

**Properties**:
- `period_name`: "2020-2024", "2015-2019", etc.
- `start_year`: 2020, 2015, etc.
- `end_year`: 2024, 2019, etc.
- `duration_years`: 5

**Purpose**: Represent 5-year buckets for temporal analysis

---

### 2. Paper-Time Period Links

**Relationship**: `(Paper)-[:BELONGS_TO_PERIOD]->(TimePeriod)`

**Properties**:
- `period_name`: Period name
- `year`: Publication year

**Purpose**: Link papers to their time period

---

### 3. Temporal Entity Usage

**Relationships**:
- `(TimePeriod)-[:HAS_THEORY_USAGE]->(Theory)`
- `(TimePeriod)-[:HAS_METHOD_USAGE]->(Method)`
- `(TimePeriod)-[:HAS_RESEARCH_QUESTION_USAGE]->(ResearchQuestion)`

**Properties**:
- `paper_count`: Number of papers using entity in this period
- `usage_frequency`: Frequency of usage

**Purpose**: Track entity usage per time period

---

### 4. Evolution Relationships

**Relationship**: `(TimePeriod)-[:EVOLVES_TO]->(TimePeriod)`

**Properties**:
- `entity_type`: "theory", "method", etc.
- `entity_name`: Name of entity
- `period1_count`: Usage in first period
- `period2_count`: Usage in second period
- `change`: Absolute change
- `change_percentage`: Percentage change
- `evolution_type`: "increasing", "decreasing", "stable"

**Purpose**: Track how entities evolve between periods

---

### 5. Temporal Trends

**Node Type**: `TemporalTrend`

**Properties**:
- `entity_type`: "theory", "method"
- `entity_name`: Name of entity
- `trend_type`: "emerging", "declining", "stable"
- `trends`: Array of trend data across periods
- `total_increase` / `total_decrease`: Aggregate change

**Purpose**: Identify long-term trends

---

## Setup

### Run Complete Setup:

```bash
python3 temporal_evolution_system.py
```

This will:
1. Create time period nodes
2. Link papers to time periods
3. Add temporal properties to relationships
4. Compute entity usage per period
5. Create evolution relationships
6. Identify temporal trends

---

## Example Queries

### 1. Theory Evolution Over Time

**Question**: "How has Resource-Based View usage changed from 2020-2024 vs 2015-2019?"

```cypher
MATCH (tp:TimePeriod)-[r:HAS_THEORY_USAGE]->(t:Theory {name: "Resource-Based View"})
RETURN tp.period_name as period,
       tp.start_year as start_year,
       tp.end_year as end_year,
       r.paper_count as paper_count
ORDER BY tp.start_year DESC
```

**Result**: Shows RBV usage across all periods

---

### 2. Emerging Theories

**Question**: "What theories are emerging (increasing) in 2020-2024?"

```cypher
MATCH (tp1:TimePeriod {period_name: "2015-2019"})-[evol:EVOLVES_TO]->(tp2:TimePeriod {period_name: "2020-2024"})
WHERE evol.entity_type = 'theory'
  AND evol.evolution_type = 'increasing'
  AND evol.change_percentage > 50
RETURN evol.entity_name as theory_name,
       evol.period1_count as previous_count,
       evol.period2_count as current_count,
       evol.change_percentage as change_pct
ORDER BY evol.change_percentage DESC
```

**Result**: Theories with >50% increase from 2015-2019 to 2020-2024

---

### 3. Period Comparison

**Question**: "Compare theory usage in 2020-2024 vs 2015-2019"

```cypher
MATCH (tp1:TimePeriod {period_name: "2015-2019"})-[r1:HAS_THEORY_USAGE]->(t:Theory)
MATCH (tp2:TimePeriod {period_name: "2020-2024"})-[r2:HAS_THEORY_USAGE]->(t)
RETURN t.name as theory_name,
       r1.paper_count as period1_count,
       r2.paper_count as period2_count,
       r2.paper_count - r1.paper_count as change,
       ((r2.paper_count - r1.paper_count) / r1.paper_count * 100.0) as change_pct
ORDER BY abs(r2.paper_count - r1.paper_count) DESC
LIMIT 20
```

**Result**: Top 20 theories with biggest changes between periods

---

### 4. Method Evolution

**Question**: "How has OLS Regression usage evolved?"

```cypher
MATCH (tp:TimePeriod)-[r:HAS_METHOD_USAGE]->(m:Method {name: "Ordinary Least Squares"})
RETURN tp.period_name as period,
       r.paper_count as paper_count
ORDER BY tp.start_year DESC
```

**Result**: OLS usage across all periods

---

### 5. Method-Theory Co-evolution

**Question**: "How has OLS + RBV combination changed over time?"

```cypher
MATCH (p1:Paper)-[:BELONGS_TO_PERIOD]->(tp1:TimePeriod {period_name: "2015-2019"})
MATCH (p1)-[:USES_THEORY {role: 'primary'}]->(t:Theory {name: "Resource-Based View"})
MATCH (p1)-[:USES_METHOD]->(m:Method {name: "Ordinary Least Squares"})

MATCH (p2:Paper)-[:BELONGS_TO_PERIOD]->(tp2:TimePeriod {period_name: "2020-2024"})
MATCH (p2)-[:USES_THEORY {role: 'primary'}]->(t)
MATCH (p2)-[:USES_METHOD]->(m)

RETURN count(DISTINCT p1) as period1_count,
       count(DISTINCT p2) as period2_count,
       count(DISTINCT p2) - count(DISTINCT p1) as change
```

**Result**: Count of papers using OLS + RBV in each period

---

### 6. Temporal Trends

**Question**: "What are the emerging trends?"

```cypher
MATCH (tt:TemporalTrend {trend_type: "emerging"})
WHERE tt.entity_type = 'theory'
RETURN tt.entity_name as entity_name,
       tt.total_increase as total_change,
       size(tt.trends) as trend_count
ORDER BY tt.total_increase DESC
LIMIT 10
```

**Result**: Top 10 emerging theories

---

## Integration with Current Framework

### Enhanced Relationships

All relationships now have temporal properties:
- `year`: Publication year
- `period`: Time period (e.g., "2020-2024")

**Example**:
```cypher
MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
WHERE r.period = "2020-2024"
RETURN t.name, count(p) as count
```

---

### Temporal Indexes

**Recommended indexes**:
```cypher
CREATE INDEX paper_year_index FOR (p:Paper) ON (p.publication_year)
CREATE INDEX relationship_period_index FOR ()-[r:USES_THEORY]-() ON (r.period)
```

---

## Use Cases

### 1. Research Gap Analysis
**Query**: "What theories were popular in 2015-2019 but declined in 2020-2024?"
→ Identifies research gaps or declining areas

### 2. Trend Identification
**Query**: "What are the emerging theories in recent years?"
→ Identifies hot topics

### 3. Method Evolution
**Query**: "How have quantitative methods evolved over time?"
→ Tracks methodological trends

### 4. Theory-Method Patterns
**Query**: "What methods are commonly used with RBV in 2020-2024?"
→ Identifies contemporary research patterns

### 5. Comparative Analysis
**Query**: "Compare theory usage between 2020-2024 and 2015-2019"
→ Shows field evolution

---

## Benefits

1. **Temporal Context**: All entities have temporal context
2. **Evolution Tracking**: See how field evolves over time
3. **Trend Analysis**: Identify emerging/declining areas
4. **Period Comparison**: Compare any two periods
5. **Co-evolution**: Track method-theory combinations over time
6. **Research Planning**: Identify gaps and trends for future research

---

## Next Steps

1. **Run Setup**: Execute `temporal_evolution_system.py`
2. **Test Queries**: Use `temporal_evolution_queries.py` for examples
3. **Integrate with Agent**: Add temporal queries to chatbot
4. **Create Dashboards**: Visualize temporal trends
5. **Monitor Evolution**: Track changes as new papers are added

---

## Example Output

### Theory Evolution Analysis:
```
Theory Evolution: Resource-Based View
======================================================================
2020-2024 (2020-2024): 45 papers
2015-2019 (2015-2019): 52 papers
2010-2014 (2010-2014): 48 papers
2005-2009 (2005-2009): 38 papers
```

### Emerging Theories:
```
Emerging Theories in 2020-2024
======================================================================
Dynamic Capabilities Theory: 12 → 28 (+133.3%)
Stakeholder Theory: 8 → 18 (+125.0%)
Institutional Theory: 15 → 30 (+100.0%)
```

---

## Status

✅ **Fully Implemented**
- Time period nodes
- Paper-time period links
- Temporal entity usage
- Evolution relationships
- Temporal trends
- Example queries

**Ready for use!**

