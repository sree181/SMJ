# Graph RAG Implementation Plan

## Overview

This document outlines the complete implementation plan for adding Graph RAG (Graph Retrieval-Augmented Generation) capabilities to the Research Intelligence System, enabling comprehensive question-answering using both semantic similarity and graph relationships.

---

## Implementation Approach

### Phase 1: Embedding Generation ✅

**Script**: `generate_all_embeddings.py`

**What it does:**
- Generates vector embeddings for all entity types:
  - **Papers**: `title + abstract` (384-dim vectors)
  - **Theories**: `name + description`
  - **Phenomena**: `phenomenon_name + description + context`
  - **Methods**: `name + type + sample_size + time_period`
  - **Research Questions**: `question` text

**Model**: `all-MiniLM-L6-v2` (SentenceTransformer)
- 384 dimensions
- Fast inference
- Good semantic similarity

**Storage**: 
- Embeddings stored as `embedding` property on each node
- Metadata: `embedding_model`, `embedding_dim`, `embedding_updated_at`

**Batch Processing**: 
- Processes entities in batches of 100
- Efficient for large datasets

---

### Phase 2: Vector Index Creation ✅

**Script**: `setup_graphrag_system.py`

**What it does:**
1. **Checks Neo4j version** (requires 5.x+ for native vector indexes)
2. **Creates vector indexes** for each entity type:
   - `paper_embedding_index`
   - `theory_embedding_index`
   - `phenomenon_embedding_index`
   - `method_embedding_index`
   - `research_question_embedding_index`
3. **Verifies embeddings** are present
4. **Tests vector search** functionality

**Fallback**: If vector indexes aren't supported, embeddings are still stored as properties and can be used with similarity computation.

---

### Phase 3: Graph RAG Query System ✅

**Script**: `graphrag_query_system.py`

**Class**: `GraphRAGQuerySystem`

**Hybrid Search Architecture:**

```
User Query
    ↓
[1] Generate Query Embedding (384-dim vector)
    ↓
[2] Vector Search (Semantic Similarity)
    ├─ Papers (top_k by similarity)
    ├─ Theories (top_k by similarity)
    ├─ Phenomena (top_k by similarity)
    └─ Methods (top_k by similarity)
    ↓
[3] Graph Traversal (Relationship-Based)
    └─ Find papers connected via shared entities
    ↓
[4] Entity Matching (Exact Matches)
    ├─ Extract keywords from query
    ├─ Match theories by name
    └─ Match phenomena by name
    ↓
[5] Context Assembly
    ├─ Combine vector results
    ├─ Add graph-connected papers
    ├─ Include relationship paths
    └─ Build comprehensive context string
    ↓
[6] LLM Generation
    └─ Generate answer with rich context
```

**Key Methods:**

1. **`query(question, top_k, similarity_threshold)`**
   - Main entry point
   - Returns comprehensive context dictionary

2. **`_vector_search_papers()`**
   - Computes cosine similarity between query and all paper embeddings
   - Returns top_k most similar papers

3. **`_graph_traversal()`**
   - Finds papers connected via shared entities (theories, phenomena, methods)
   - Uses connection strength for ranking

4. **`_entity_matching()`**
   - Extracts keywords from query
   - Finds exact matches in theory/phenomenon names
   - Returns papers using those entities

5. **`_build_context()`**
   - Assembles all retrieved information into structured context
   - Formats for LLM consumption

6. **`generate_answer()`**
   - Uses OpenAI GPT-4 to generate comprehensive answer
   - Falls back to summary if LLM unavailable

---

## Integration with Existing System

### Current `/api/query` Endpoint

**Current behavior:**
- Basic keyword matching
- Simple graph queries
- Limited context retrieval

**Enhanced behavior (with Graph RAG):**
- Semantic similarity search
- Graph path traversal
- Rich relationship context
- Better answer quality

### Integration Options

**Option 1: Enhance Existing Endpoint**
```python
# In api_server.py
from graphrag_query_system import GraphRAGQuerySystem

graphrag = GraphRAGQuerySystem()

@app.post("/api/query")
async def process_query(request: QueryRequest):
    # Use Graph RAG if embeddings available
    if use_graphrag:
        result = graphrag.query(request.query)
        answer = graphrag.generate_answer(result)
    else:
        # Fallback to existing method
        answer = llm_client.generate_answer(...)
```

**Option 2: New Endpoint**
```python
@app.post("/api/query/graphrag")
async def process_graphrag_query(request: QueryRequest):
    result = graphrag.query(request.query)
    answer = graphrag.generate_answer(result)
    return QueryResponse(answer=answer, ...)
```

---

## Execution Flow

### Step 1: Generate Embeddings

```bash
cd "Strategic Management Journal"
source ../smj/bin/activate
python generate_all_embeddings.py
```

**Expected output:**
- Papers: ~591 embeddings
- Theories: ~X embeddings
- Phenomena: ~X embeddings
- Methods: ~X embeddings
- Research Questions: ~X embeddings

**Time estimate**: 10-30 minutes (depending on dataset size)

---

### Step 2: Setup Vector Indexes

```bash
python setup_graphrag_system.py
```

**Expected output:**
- Vector indexes created (if Neo4j 5.x+)
- Verification of embeddings
- Test of vector search

**Time estimate**: 1-2 minutes

---

### Step 3: Test Graph RAG System

```bash
python graphrag_query_system.py
```

**Expected output:**
- Test query executed
- Papers, theories, phenomena found
- Context preview

---

### Complete Setup (All Steps)

```bash
python setup_complete_graphrag.py
```

**Orchestrates all three steps in sequence**

---

## Benefits of Graph RAG

### 1. Semantic Understanding
- Finds papers by meaning, not just keywords
- Example: "resource allocation" finds papers about "resource-based view"

### 2. Relationship Awareness
- Discovers connected papers via shared theories/phenomena
- Example: Papers using same theory are connected

### 3. Comprehensive Context
- Combines multiple retrieval methods
- Provides rich context for LLM generation

### 4. Better Answers
- LLM receives more relevant information
- Answers cite specific papers and relationships

---

## Example Queries

### Query 1: "What theories explain competitive advantage?"
**Vector Search**: Finds papers with similar semantic content
**Graph Traversal**: Finds papers connected via "competitive advantage" phenomena
**Entity Matching**: Finds papers using "Resource-Based View", "Dynamic Capabilities"
**Result**: Comprehensive answer citing multiple theories and papers

### Query 2: "How do firms allocate resources?"
**Vector Search**: Finds papers about resource allocation
**Graph Traversal**: Finds papers studying related phenomena
**Entity Matching**: Matches "resource allocation" as phenomenon
**Result**: Answer explaining resource allocation patterns across theories

### Query 3: "What methods are used to study innovation?"
**Vector Search**: Finds papers about innovation methods
**Graph Traversal**: Finds papers using similar methods
**Entity Matching**: Matches "innovation" as phenomenon
**Result**: Answer listing methods and their applications

---

## Performance Considerations

### Embedding Generation
- **Batch size**: 100 entities per batch
- **Model**: Fast inference (~100ms per batch)
- **Total time**: Scales linearly with dataset size

### Vector Search
- **Without index**: O(n) similarity computation
- **With index**: O(log n) approximate search
- **Threshold**: 0.3 similarity (adjustable)

### Graph Traversal
- **Depth**: 1-hop (papers → entities → papers)
- **Limit**: Top 10 connected papers
- **Performance**: Fast with proper indexes

---

## Monitoring & Tuning

### Similarity Threshold
- **Default**: 0.3
- **Too low**: Too many irrelevant results
- **Too high**: Too few results
- **Tune**: Based on query results quality

### Top-K Values
- **Papers**: 10 (default)
- **Theories**: 5 (default)
- **Phenomena**: 5 (default)
- **Adjust**: Based on context size limits

### Context Size
- **Current**: ~2000 tokens
- **Limit**: Adjust based on LLM token limits
- **Strategy**: Prioritize high-similarity results

---

## Future Enhancements

1. **Multi-hop Traversal**: 2-3 hop graph paths
2. **Temporal Filtering**: Filter by publication year
3. **Author Network**: Include author connections
4. **Citation Network**: Include citation relationships
5. **Confidence Scores**: Rank results by confidence
6. **Query Expansion**: Expand queries with synonyms
7. **Caching**: Cache frequent queries
8. **Streaming**: Stream results as they're found

---

## Troubleshooting

### No Embeddings Found
- **Check**: Run `generate_all_embeddings.py` first
- **Verify**: Check Neo4j for `embedding` properties

### Vector Index Not Created
- **Check**: Neo4j version (requires 5.x+)
- **Fallback**: Embeddings still work without indexes

### Low Similarity Scores
- **Adjust**: Lower similarity threshold
- **Check**: Embedding quality (model choice)

### Slow Queries
- **Optimize**: Create vector indexes
- **Limit**: Reduce top_k values
- **Cache**: Cache frequent queries

---

## Summary

The Graph RAG implementation provides:

✅ **Semantic Search**: Find papers by meaning
✅ **Graph Traversal**: Discover connected papers
✅ **Entity Matching**: Exact entity matches
✅ **Rich Context**: Comprehensive information for LLM
✅ **Better Answers**: Higher quality responses

**Next Steps:**
1. Run `setup_complete_graphrag.py`
2. Integrate with `/api/query` endpoint
3. Test with comprehensive questions
4. Monitor and tune parameters
