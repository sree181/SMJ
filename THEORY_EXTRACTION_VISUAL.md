# Theory Extraction - Visual Guide

## 📋 What Gets Extracted

### From Paper Text (First 20,000 chars)
- Introduction section
- Literature Review section
- Theory mentions and discussions

### Extracted Information
1. **Theory Name**: Exact name as written
2. **Theory Type**: framework, concept, model, perspective
3. **Domain**: strategic_management, organizational_behavior, etc.
4. **Role**: primary, supporting, challenging, extending
5. **Section**: introduction, literature_review, discussion
6. **Usage Context**: How theory is used
7. **Description**: Brief description if provided

## 🎯 Prompt Design

```
Extract theories and theoretical frameworks from this Strategic Management Journal paper.

RULES: Extract EXACT theory names as they appear. Do NOT summarize or rewrite.

Paper text (first 20,000 chars - Introduction + Literature Review):
[Paper text here]

TASK: Extract all theories, frameworks, and theoretical perspectives mentioned.

Look for:
1. Theory Names: Exact names (e.g., "Resource-Based View", "RBV")
2. Theory Role: primary, supporting, challenging, extending
3. Usage Context: How theory is used
4. Section: Where theory appears

Common theories in Strategic Management:
- Resource-Based View (RBV)
- Dynamic Capabilities
- Agency Theory
- [etc...]

Return JSON:
{
  "theories": [
    {
      "theory_name": "exact theory name",
      "theory_type": "framework",
      "domain": "strategic_management",
      "role": "primary",
      "section": "literature_review",
      "usage_context": "how theory is used",
      "description": "brief description"
    }
  ]
}
```

## 📊 Graph Structure

### Nodes Created

```
┌─────────────────────────────────┐
│         Theory Node             │
├─────────────────────────────────┤
│ name: "Resource-Based View"     │
│ domain: "strategic_management"   │
│ theory_type: "framework"        │
│ description: "..."              │
└─────────────────────────────────┘
```

### Relationships Created

```
┌──────────┐                    ┌──────────┐
│  Paper   │                    │  Theory  │
│          │                    │          │
│ 2025_4359 │──[:USES_THEORY]──>│   RBV    │
│          │                    │          │
└──────────┘                    └──────────┘
     │
     │ Properties:
     │ - role: "primary"
     │ - section: "literature_review"
     │ - usage_context: "..."
     │
```

## 🔄 Complete Extraction Flow

```
┌─────────────────────────────────────────┐
│  1. Extract PDF Text                    │
│     (First 20,000 characters)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Send to LLM                          │
│     (OLLAMA llama3.1:8b)                 │
│     Prompt: Theory extraction            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Parse JSON Response                  │
│     Extract theories array               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Validate Theories                    │
│     - Check theory_name not empty        │
│     - Set defaults for missing fields    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Create Neo4j Nodes                   │
│     MERGE (t:Theory {name: $name})       │
│     SET t.domain, t.theory_type, etc.    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. Create Relationships                 │
│     MERGE (p:Paper)-[:USES_THEORY]->(t) │
│     SET r.role, r.section, etc.         │
└─────────────────────────────────────────┘
```

## 📈 Example Extraction Result

### Input Paper Text:
```
Introduction
This paper builds on Resource-Based View (RBV) to explain firm performance.
We also draw on Agency Theory to understand governance mechanisms.
Our theoretical framework extends RBV by incorporating dynamic capabilities.
```

### Extracted Theories:
```json
[
  {
    "theory_name": "Resource-Based View",
    "theory_type": "framework",
    "domain": "strategic_management",
    "role": "primary",
    "section": "introduction",
    "usage_context": "Main theoretical framework to explain firm performance"
  },
  {
    "theory_name": "Agency Theory",
    "theory_type": "framework",
    "domain": "strategic_management",
    "role": "supporting",
    "section": "introduction",
    "usage_context": "Used to understand governance mechanisms"
  },
  {
    "theory_name": "Dynamic Capabilities",
    "theory_type": "framework",
    "domain": "strategic_management",
    "role": "extending",
    "section": "introduction",
    "usage_context": "Extended RBV by incorporating dynamic capabilities"
  }
]
```

### Neo4j Graph Created:
```
(Paper {paper_id: "2025_4359"})
  -[:USES_THEORY {role: "primary"}]->(Theory {name: "Resource-Based View"})
  -[:USES_THEORY {role: "supporting"}]->(Theory {name: "Agency Theory"})
  -[:USES_THEORY {role: "extending"}]->(Theory {name: "Dynamic Capabilities"})
```

## 🔍 Query Examples

### 1. Find Papers Using a Theory
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.year
ORDER BY p.year
```

### 2. Count Theory Usage
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
RETURN t.name, count(p) as usage_count
ORDER BY usage_count DESC
```

### 3. Primary vs Supporting Theories
```cypher
MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
RETURN t.name, r.role, count(p) as count
ORDER BY t.name, r.role
```

## ✅ Test Results

**Paper**: `2025_4359`
**Theories Extracted**: 7
- Value-Based Strategy (primary)
- Value-Based View (VBV) (primary)
- Status Quo Configuration (supporting)
- Reactivity (supporting)
- Resource-Based View (RBV) (challenging)
- Institutional Theory (supporting)
- Upper Echelons Theory (supporting)

**Status**: ✅ Working correctly

