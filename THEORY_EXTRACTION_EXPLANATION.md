# Theory Extraction - Complete Explanation

## Overview

Theory extraction identifies and extracts theoretical frameworks, concepts, and theories used in research papers. This enables comprehensive analysis of theoretical foundations across the literature.

## Extraction Prompt Explanation

### Prompt Structure

```
Extract theories and theoretical frameworks from this Strategic Management Journal paper.

RULES: Extract EXACT theory names as they appear. Do NOT summarize or rewrite.
```

**Why**: Ensures we get exact theory names (e.g., "Resource-Based View" not "resource based view")

### Where to Look

```
Paper text (first 20,000 chars - Introduction + Literature Review)
```

**Why**: 
- Introduction: Theories are typically introduced here
- Literature Review: Comprehensive discussion of theories
- 20k chars: Covers both sections without being too slow

### What to Extract

1. **Theory Names**: Exact names as written
   - Examples: "Resource-Based View", "RBV", "Agency Theory"
   - Handles abbreviations: If both "Resource-Based View" and "RBV" appear, extract both

2. **Theory Role**: How theory is used
   - `primary`: Main theoretical framework (e.g., paper tests RBV)
   - `supporting`: Used to support arguments (e.g., "consistent with Agency Theory")
   - `challenging`: Theories critiqued (e.g., "RBV has limitations...")
   - `extending`: Theories built upon (e.g., "extending RBV to...")

3. **Usage Context**: Brief description of how theory is used
   - Example: "Used to explain firm performance differences"
   - Example: "Extended to include dynamic capabilities"

4. **Section**: Where theory appears
   - `introduction`: Theory introduced
   - `literature_review`: Theory discussed in detail
   - `discussion`: Theory applied or extended

### Common Theories Reference

The prompt includes a list of common Strategic Management theories to help the LLM:
- Resource-Based View (RBV)
- Dynamic Capabilities
- Agency Theory
- Transaction Cost Economics
- Institutional Theory
- Stakeholder Theory
- Upper Echelons Theory
- Organizational Learning Theory
- Network Theory
- Contingency Theory

**Why**: Helps LLM recognize theory names even if written differently

## Nodes Created

### Theory Node
**Properties**:
- `name` (string): Theory name (e.g., "Resource-Based View")
- `domain` (string): Research domain (default: "strategic_management")
- `theory_type` (string): "framework", "concept", "model", "perspective"
- `description` (string): Brief description if provided in paper

**Example**:
```cypher
(:Theory {
  name: "Resource-Based View",
  domain: "strategic_management",
  theory_type: "framework",
  description: "Theory explaining firm performance through unique resources"
})
```

## Relationships Created

### 1. Paper → Theory
**Relationship**: `(Paper)-[:USES_THEORY]->(Theory)`
**Properties**:
- `role` (string): "primary", "supporting", "challenging", "extending"
- `section` (string): "introduction", "literature_review", "discussion"
- `usage_context` (string): How theory is used in the paper

**Example**:
```cypher
(Paper {paper_id: "2025_4359"})-[:USES_THEORY {
  role: "primary",
  section: "introduction",
  usage_context: "Used as main theoretical framework to explain restaurant exits"
}]->(Theory {name: "Resource-Based View"})
```

### 2. Theory → Theory (Future)
**Relationships**:
- `(Theory)-[:RELATED_TO {relationship_type, strength}]->(Theory)`
- `(Theory)-[:EXTENDS {extension_type, year}]->(Theory)`

**Note**: These will be created in a separate step after all papers are processed, using LLM to identify relationships between theories.

## Extraction Flow

```
1. Extract text (first 20k chars)
   ↓
2. Send to LLM with theory extraction prompt
   ↓
3. LLM identifies theories and their roles
   ↓
4. Parse JSON response
   ↓
5. Validate theory names (not empty)
   ↓
6. Create Theory nodes in Neo4j
   ↓
7. Create USES_THEORY relationships
```

## Example Extraction

### Input Paper Text:
```
Introduction
This paper builds on Resource-Based View (RBV) to explain firm performance.
We also draw on Agency Theory to understand governance mechanisms.
Our theoretical framework extends RBV by incorporating dynamic capabilities.
```

### Extracted Output:
```json
{
  "theories": [
    {
      "theory_name": "Resource-Based View",
      "theory_type": "framework",
      "domain": "strategic_management",
      "role": "primary",
      "section": "introduction",
      "usage_context": "Main theoretical framework to explain firm performance",
      "description": "Theory explaining firm performance through unique resources"
    },
    {
      "theory_name": "Agency Theory",
      "theory_type": "framework",
      "domain": "strategic_management",
      "role": "supporting",
      "section": "introduction",
      "usage_context": "Used to understand governance mechanisms",
      "description": null
    },
    {
      "theory_name": "Dynamic Capabilities",
      "theory_type": "framework",
      "domain": "strategic_management",
      "role": "extending",
      "section": "introduction",
      "usage_context": "Extended RBV by incorporating dynamic capabilities",
      "description": null
    }
  ]
}
```

### Neo4j Graph Created:
```
(Paper)-[:USES_THEORY {role: "primary"}]->(Theory {name: "Resource-Based View"})
(Paper)-[:USES_THEORY {role: "supporting"}]->(Theory {name: "Agency Theory"})
(Paper)-[:USES_THEORY {role: "extending"}]->(Theory {name: "Dynamic Capabilities"})
```

## Query Examples

### 1. Find Papers Using a Theory
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.year, t.name
ORDER BY p.year
```

### 2. Find Primary Theories
```cypher
MATCH (p:Paper)-[r:USES_THEORY {role: "primary"}]->(t:Theory)
RETURN t.name, count(p) as paper_count
ORDER BY paper_count DESC
```

### 3. Theory Evolution Over Time
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.year, count(p) as count
ORDER BY p.year
```

### 4. Papers Using Multiple Theories
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WITH p, collect(t.name) as theories
WHERE size(theories) > 2
RETURN p.title, theories
```

## Benefits

1. **Theoretical Gap Identification**: Find theories with few papers
2. **Theory Evolution**: Track how theories are used over time
3. **Theory Relationships**: Identify complementary or competing theories
4. **Research Streams**: Find papers using similar theoretical frameworks
5. **Literature Review**: Quickly identify theoretical foundations

## Implementation Status

- ✅ Theory extraction method created
- ✅ Prompt designed and optimized
- ✅ Neo4j ingestion logic added
- ⏳ Testing on sample papers (next step)

