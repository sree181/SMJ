# Theory Node Extraction - Design Document

## Overview

Theory extraction identifies theoretical frameworks, concepts, and theories used in research papers. This enables:
- Tracking which theories are used across papers
- Finding papers using the same theoretical frameworks
- Identifying theoretical gaps
- Understanding theory evolution over time

## Theory Node Structure

### Node: Theory
**Properties**:
- `name` (string): Theory name (e.g., "Resource-Based View", "Agency Theory")
- `domain` (string): Research domain (e.g., "strategic_management", "organizational_behavior")
- `description` (string): Brief description of the theory
- `theory_type` (string): "framework", "concept", "model", "perspective"
- `first_mentioned_year` (integer): When theory was first mentioned in literature (if known)

**Example**:
```cypher
(:Theory {
  name: "Resource-Based View",
  domain: "strategic_management",
  description: "Theory explaining firm performance through unique resources",
  theory_type: "framework"
})
```

## Relationships

### 1. Paper → Theory
**Relationship**: `(Paper)-[:USES_THEORY]->(Theory)`
**Properties**:
- `role` (string): "primary", "supporting", "challenging", "extending"
- `section` (string): Where theory is mentioned ("introduction", "literature_review", "discussion")
- `usage_context` (string): How theory is used (brief description)

**Purpose**: 
- Find all papers using a specific theory
- Track theory usage over time
- Identify primary vs supporting theories

**Example Query**:
```cypher
// Find all papers using Resource-Based View
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.year, t.name
ORDER BY p.year
```

### 2. Theory → Theory
**Relationship**: `(Theory)-[:RELATED_TO]->(Theory)`
**Properties**:
- `relationship_type` (string): "complementary", "competing", "extending", "challenging"
- `strength` (float): Relationship strength (0.0-1.0)

**Purpose**:
- Understand theory relationships
- Find complementary theories
- Identify theoretical debates

**Example Query**:
```cypher
// Theories related to RBV
MATCH (t1:Theory {name: "Resource-Based View"})-[:RELATED_TO]->(t2:Theory)
RETURN t2.name, t2.relationship_type
```

### 3. Theory → Theory (Extension)
**Relationship**: `(Theory)-[:EXTENDS]->(Theory)`
**Properties**:
- `extension_type` (string): "theoretical", "empirical", "boundary"
- `year` (integer): When extension was proposed

**Purpose**:
- Track theory development
- Find theory extensions
- Understand theory evolution

**Example Query**:
```cypher
// Theories extending RBV
MATCH (t1:Theory {name: "Resource-Based View"})<-[:EXTENDS]-(t2:Theory)
RETURN t2.name, t2.extension_type
```

## Extraction Strategy

### Where to Look for Theories
1. **Introduction Section**: Theories often introduced here
2. **Literature Review**: Comprehensive theory discussion
3. **Theoretical Framework Section**: Explicit theory presentation
4. **Discussion Section**: Theory application and extension
5. **Abstract**: Main theories mentioned

### What to Extract
1. **Theory Names**: Exact names as they appear (e.g., "Resource-Based View", "RBV")
2. **Theory Role**: Primary theory vs supporting theory
3. **Usage Context**: How theory is used in the paper
4. **Theory Relationships**: If paper mentions relationships between theories

## Common Theories in Strategic Management

### Core Theories
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

### Related Concepts
- Absorptive Capacity
- Organizational Ambidexterity
- Strategic Fit
- Competitive Advantage
- Organizational Identity

## Extraction Prompt Design

### Key Requirements
1. **Exact Names**: Extract theory names exactly as written
2. **Context**: Understand how theory is used
3. **Role**: Identify primary vs supporting theories
4. **Relationships**: Note if theories are related

### Prompt Structure
- Focus on Introduction + Literature Review sections
- Look for theory names, citations, and usage context
- Classify theory role (primary/supporting)
- Extract theory descriptions if provided

