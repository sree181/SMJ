# Author-Theory and Author-Phenomenon Connections - Implementation ✅

## Overview

Successfully implemented relationships between:
1. **Author → Theory**: Which theories authors use in their research
2. **Author → Phenomenon**: Which phenomena authors study

---

## 1. Author-Theory Relationships

### Relationship Structure

**Relationship**: `(Author)-[:USES_THEORY]->(Theory)`

**Properties**:
- `paper_id`: Which paper establishes this connection
- `role`: Theory role in that paper (primary, supporting, challenging, extending)
- `section`: Where theory appears (introduction, literature_review, discussion)
- `first_used_year`: Year when author first used this theory (if new relationship)
- `paper_count`: Number of papers where this author uses this theory

### How It Works

When a paper uses a theory:
1. Paper-Theory relationship is created: `(Paper)-[:USES_THEORY]->(Theory)`
2. **NEW**: All authors of that paper are linked to the theory: `(Author)-[:USES_THEORY]->(Theory)`
3. If author already has relationship with theory, `paper_count` is incremented
4. If new relationship, `first_used_year` is set to paper's publication year

### Code Location

**File**: `redesigned_methodology_extractor.py`
**Method**: `ingest_paper_with_methods()`
**Lines**: After Paper-Theory relationship creation (around line 1795)

```cypher
MATCH (p:Paper {paper_id: $paper_id})<-[:AUTHORED]-(a:Author)
MATCH (t:Theory {name: $theory_name})
MERGE (a)-[r:USES_THEORY {
    paper_id: $paper_id,
    role: $role,
    section: $section
}]->(t)
ON CREATE SET r.first_used_year = $publication_year,
              r.paper_count = 1
ON MATCH SET r.paper_count = r.paper_count + 1
```

---

## 2. Author-Phenomenon Relationships

### Relationship Structure

**Relationship**: `(Author)-[:STUDIES_PHENOMENON]->(Phenomenon)`

**Properties**:
- `paper_id`: Which paper establishes this connection
- `section`: Where phenomenon appears
- `context`: How phenomenon is studied
- `first_studied_year`: Year when author first studied this phenomenon (if new relationship)
- `paper_count`: Number of papers where this author studies this phenomenon

### How It Works

When a paper studies a phenomenon:
1. Paper-Phenomenon relationship is created: `(Paper)-[:STUDIES_PHENOMENON]->(Phenomenon)`
2. **NEW**: All authors of that paper are linked to the phenomenon: `(Author)-[:STUDIES_PHENOMENON]->(Phenomenon)`
3. If author already has relationship with phenomenon, `paper_count` is incremented
4. If new relationship, `first_studied_year` is set to paper's publication year

### Code Location

**File**: `redesigned_methodology_extractor.py`
**Method**: `ingest_paper_with_methods()`
**Lines**: After Paper-Phenomenon relationship creation (around line 2045)

```cypher
MATCH (p:Paper {paper_id: $paper_id})<-[:AUTHORED]-(a:Author)
MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
MERGE (a)-[r:STUDIES_PHENOMENON {
    paper_id: $paper_id,
    section: $section,
    context: $context
}]->(ph)
ON CREATE SET r.first_studied_year = $publication_year,
              r.paper_count = 1
ON MATCH SET r.paper_count = r.paper_count + 1
```

---

## 3. Example Queries

### Find Authors Using a Specific Theory

```cypher
MATCH (a:Author)-[r:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN a.full_name, r.role, r.paper_count, r.first_used_year
ORDER BY r.paper_count DESC
```

**Use Case**: Find all authors who use Resource-Based View and how many papers they've written using it.

### Find Authors Studying a Specific Phenomenon

```cypher
MATCH (a:Author)-[r:STUDIES_PHENOMENON]->(ph:Phenomenon {phenomenon_name: "Economic nationalism in court rulings"})
RETURN a.full_name, r.paper_count, r.first_studied_year
ORDER BY r.paper_count DESC
```

**Use Case**: Find all authors who study economic nationalism and their research history.

### Find Theories Used by an Author

```cypher
MATCH (a:Author {author_id: "smith_john"})-[r:USES_THEORY]->(t:Theory)
RETURN t.name, r.role, r.paper_count, r.first_used_year
ORDER BY r.paper_count DESC
```

**Use Case**: See which theories an author uses most frequently.

### Find Phenomena Studied by an Author

```cypher
MATCH (a:Author {author_id: "smith_john"})-[r:STUDIES_PHENOMENON]->(ph:Phenomenon)
RETURN ph.phenomenon_name, ph.phenomenon_type, r.paper_count, r.first_studied_year
ORDER BY r.paper_count DESC
```

**Use Case**: See which phenomena an author studies most frequently.

### Find Authors Who Use Theory to Explain Phenomenon

```cypher
MATCH (a:Author)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
MATCH (a)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
MATCH (t)-[:EXPLAINS_PHENOMENON]->(ph)
RETURN a.full_name, t.name, ph.phenomenon_name
```

**Use Case**: Find authors who use RBV to explain specific phenomena.

### Most Prolific Authors for a Theory

```cypher
MATCH (a:Author)-[r:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN a.full_name, r.paper_count, r.first_used_year
ORDER BY r.paper_count DESC
LIMIT 10
```

**Use Case**: Find the most prolific authors using a specific theory.

### Theory Evolution by Author

```cypher
MATCH (a:Author {author_id: "smith_john"})-[r:USES_THEORY]->(t:Theory)
RETURN t.name, r.first_used_year, r.paper_count
ORDER BY r.first_used_year
```

**Use Case**: Track how an author's theoretical focus evolves over time.

---

## 4. Relationship Properties Explained

### Author-Theory Relationship Properties

- **`paper_id`**: Links back to the specific paper where this connection was made
- **`role`**: How the theory was used in that paper (primary, supporting, etc.)
- **`section`**: Where in the paper the theory appeared
- **`first_used_year`**: When the author first used this theory (tracks evolution)
- **`paper_count`**: How many papers the author has written using this theory (tracks expertise)

### Author-Phenomenon Relationship Properties

- **`paper_id`**: Links back to the specific paper where this connection was made
- **`section`**: Where in the paper the phenomenon appeared
- **`context`**: How the phenomenon was studied
- **`first_studied_year`**: When the author first studied this phenomenon (tracks evolution)
- **`paper_count`**: How many papers the author has written studying this phenomenon (tracks expertise)

---

## 5. Benefits

### Research Analytics

1. **Author Expertise**: Identify authors' areas of expertise (theories and phenomena)
2. **Collaboration Opportunities**: Find authors working on similar theories/phenomena
3. **Theory Evolution**: Track how authors' theoretical focus changes over time
4. **Phenomenon Specialization**: Identify authors who specialize in specific phenomena

### Query Capabilities

1. **Find Experts**: "Who are the experts on Resource-Based View?"
2. **Find Collaborators**: "Who else studies economic nationalism?"
3. **Track Evolution**: "How has Author X's theoretical focus evolved?"
4. **Identify Gaps**: "Which authors use Theory Y but haven't studied Phenomenon Z?"

---

## 6. Implementation Details

### Automatic Creation

- Relationships are created **automatically** during paper ingestion
- No manual intervention required
- All authors of a paper are linked to all theories and phenomena in that paper

### Incremental Updates

- If author already has relationship with theory/phenomenon:
  - `paper_count` is incremented
  - Existing properties are preserved
- If new relationship:
  - `first_used_year` / `first_studied_year` is set
  - `paper_count` starts at 1

### Performance

- Uses `MERGE` to avoid duplicates
- Uses `ON CREATE` and `ON MATCH` for efficient updates
- Relationships are created in the same transaction as paper ingestion

---

## Summary

✅ **Author-Theory Relationships**: Implemented with role, section, year tracking
✅ **Author-Phenomenon Relationships**: Implemented with context, section, year tracking
✅ **Automatic Creation**: Links created during paper ingestion
✅ **Incremental Updates**: Paper counts and years tracked automatically

**Status**: Complete and ready to use! 🎉

