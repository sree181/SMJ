# Graph Structure Analysis for Agent Queries

## Current Structure Analysis

### ✅ What Works Well:

1. **Direct Entity Access**:
   ```cypher
   MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
   RETURN p.title, p.year
   ```
   ✅ Works: Simple queries about papers using specific theories

2. **Paper-to-Paper Relationships**:
   ```cypher
   MATCH (p1:Paper)-[:USES_SAME_THEORY]->(p2:Paper)
   RETURN p1.title, p2.title
   ```
   ✅ Works: Finding related papers

3. **Author Networks**:
   ```cypher
   MATCH (a:Author)-[:AUTHORED]->(p:Paper)
   RETURN a.full_name, count(p) as paper_count
   ```
   ✅ Works: Author productivity queries

### ❌ Limitations for Complex Agent Queries:

## Complex Query Examples That Fail or Are Slow:

### 1. "What theories are commonly used together?"
**Current**: ❌ **Cannot answer efficiently**
- Would require: `MATCH (p:Paper)-[:USES_THEORY]->(t1), (p)-[:USES_THEORY]->(t2) WHERE t1 <> t2`
- Problem: O(n²) complexity, slow for large datasets
- **Solution**: Pre-compute `OFTEN_USED_WITH` relationships

### 2. "What methods are typically used with Resource-Based View?"
**Current**: ❌ **Cannot answer efficiently**
- Would require: `MATCH (p:Paper)-[:USES_THEORY]->(t), (p)-[:USES_METHOD]->(m) WHERE t.name = "Resource-Based View"`
- Problem: Must compute on-the-fly, slow
- **Solution**: Pre-compute `COMMONLY_USED_WITH` relationships

### 3. "How has methodology evolved over time?"
**Current**: ⚠️ **Partially works, but limited**
- Can find: `MATCH (p:Paper)-[:USES_METHOD]->(m) WHERE p.year >= 2000 RETURN m.name, p.year`
- Problem: No explicit evolution relationships
- **Solution**: Add `EVOLVED_TO` relationships between methods

### 4. "What research questions are similar to this one?"
**Current**: ❌ **Cannot answer**
- No relationships between ResearchQuestion nodes
- **Solution**: Add `SIMILAR_TO` relationships using embeddings

### 5. "What findings support or contradict each other?"
**Current**: ❌ **Cannot answer**
- No relationships between Finding nodes
- **Solution**: Add `SUPPORTS` and `CONTRADICTS` relationships

### 6. "What are the most common theory-method combinations?"
**Current**: ⚠️ **Works but slow**
- Requires aggregation query: `MATCH (p:Paper)-[:USES_THEORY]->(t), (p)-[:USES_METHOD]->(m) WITH t, m, count(p) as freq RETURN t.name, m.name, freq ORDER BY freq DESC`
- Problem: Computed on-the-fly, slow for large datasets
- **Solution**: Pre-compute Pattern nodes

### 7. "What papers address similar research questions?"
**Current**: ❌ **Cannot answer efficiently**
- Would require: `MATCH (p1:Paper)-[:ADDRESSES]->(rq1), (p2:Paper)-[:ADDRESSES]->(rq2) WHERE rq1.question ~ rq2.question`
- Problem: Text similarity is slow, no semantic relationships
- **Solution**: Add `SIMILAR_TO` relationships between ResearchQuestions

### 8. "What are research gaps (theories without methods)?"
**Current**: ⚠️ **Works but complex**
- Requires: `MATCH (t:Theory) WHERE NOT EXISTS { MATCH (p:Paper)-[:USES_THEORY]->(t), (p)-[:USES_METHOD]->(m) }`
- Problem: Complex query, slow
- **Solution**: Pre-compute ResearchGap nodes

---

## Recommended Enhanced Graph Structure

### New Relationship Types:

1. **Entity-to-Entity**:
   - `(Theory)-[:OFTEN_USED_WITH]->(Theory)` - Theory co-occurrence
   - `(Method)-[:OFTEN_USED_WITH]->(Method)` - Method co-occurrence
   - `(Theory)-[:COMMONLY_USED_WITH]->(Method)` - Theory-Method patterns

2. **Semantic**:
   - `(ResearchQuestion)-[:SIMILAR_TO]->(ResearchQuestion)` - Similar questions
   - `(Finding)-[:SUPPORTS]->(Finding)` - Supporting findings
   - `(Finding)-[:CONTRADICTS]->(Finding)` - Contradicting findings

3. **Temporal**:
   - `(Method)-[:EVOLVED_TO]->(Method)` - Method evolution
   - `(Theory)-[:EXTENDED_BY]->(Theory)` - Theory extension

4. **Hierarchical**:
   - `(Theory)-[:SUBTHEORY_OF]->(Theory)` - Theory hierarchy
   - `(Method)-[:SUBTYPE_OF]->(Method)` - Method hierarchy

5. **Aggregation**:
   - `(Pattern)-[:REPRESENTS]->(Theory)` - Common patterns
   - `(Pattern)-[:REPRESENTS]->(Method)` - Common patterns

---

## Agent Query Capabilities

### With Enhanced Structure:

1. ✅ **"What theories are commonly used together?"**
   ```cypher
   MATCH (t1:Theory)-[:OFTEN_USED_WITH]->(t2:Theory)
   RETURN t1.name, t2.name, r.frequency
   ORDER BY r.frequency DESC
   ```

2. ✅ **"What methods are typically used with Resource-Based View?"**
   ```cypher
   MATCH (t:Theory {name: "Resource-Based View"})-[:COMMONLY_USED_WITH]->(m:Method)
   RETURN m.name, r.frequency
   ORDER BY r.frequency DESC
   ```

3. ✅ **"How has methodology evolved over time?"**
   ```cypher
   MATCH (m1:Method)-[:EVOLVED_TO]->(m2:Method)
   RETURN m1.name, m2.name, r.time_gap
   ```

4. ✅ **"What research questions are similar to this one?"**
   ```cypher
   MATCH (rq1:ResearchQuestion {question_id: $id})-[:SIMILAR_TO]->(rq2:ResearchQuestion)
   WHERE r.similarity > 0.75
   RETURN rq2.question, r.similarity
   ```

5. ✅ **"What findings support each other?"**
   ```cypher
   MATCH (f1:Finding)-[:SUPPORTS]->(f2:Finding)
   RETURN f1.finding_text, f2.finding_text
   ```

---

## Summary

### Current Structure:
- ✅ Good for: Simple queries, direct relationships
- ❌ Limited for: Complex queries, entity-to-entity patterns, semantic similarity

### Enhanced Structure Needed:
- ✅ Entity-to-entity relationships
- ✅ Semantic relationships
- ✅ Temporal relationships
- ✅ Aggregation nodes

### Implementation Priority:
1. **High**: Entity-to-entity relationships (enables most complex queries)
2. **Medium**: Semantic relationships (enables similarity queries)
3. **Low**: Hierarchical relationships (nice to have)

