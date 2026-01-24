# Graph RAG Monitoring & Tuning Guide

## Overview

This guide helps you monitor Graph RAG performance and tune parameters for optimal results.

---

## Key Parameters to Tune

### 1. Similarity Threshold (`similarity_threshold`)

**Current Default**: `0.3`

**What it does**: Minimum cosine similarity score for results to be included

**How to tune**:
- **Too low (< 0.2)**: Too many irrelevant results, noisy context
- **Too high (> 0.5)**: Too few results, may miss relevant papers
- **Sweet spot**: 0.3-0.4 for most queries

**Example**:
```python
# More strict (fewer, higher-quality results)
result = graphrag.query("your question", similarity_threshold=0.4)

# More lenient (more results, may include less relevant)
result = graphrag.query("your question", similarity_threshold=0.25)
```

### 2. Top-K Values (`top_k`)

**Current Defaults**:
- Papers: `10`
- Theories: `5`
- Phenomena: `5`
- Methods: `5`

**What it does**: Number of results to return for each entity type

**How to tune**:
- **Smaller (3-5)**: Faster, more focused, may miss relevant results
- **Larger (15-20)**: More comprehensive, slower, may include noise
- **Context limit**: Consider LLM token limits (typically 2000-4000 tokens)

**Example**:
```python
# More comprehensive
result = graphrag.query("your question", top_k=15)

# More focused
result = graphrag.query("your question", top_k=5)
```

---

## Monitoring Metrics

### 1. Query Performance

**Metrics to track**:
- Query response time
- Number of papers retrieved
- Similarity scores distribution
- LLM generation time

**How to monitor**:
```python
import time

start = time.time()
result = graphrag.query("your question")
elapsed = time.time() - start

print(f"Query time: {elapsed:.2f}s")
print(f"Papers found: {len(result['papers'])}")
print(f"Avg similarity: {sum(p['similarity'] for p in result['papers'])/len(result['papers']):.3f}")
```

### 2. Answer Quality

**Metrics to track**:
- Answer length (should be 200-2000 chars typically)
- Number of sources cited
- Relevance of sources
- User feedback (if available)

**How to monitor**:
```python
answer = graphrag.generate_answer(result)
print(f"Answer length: {len(answer)} chars")
print(f"Sources: {len(result['sources'])} papers")
```

### 3. Embedding Coverage

**Check periodically**:
```cypher
// Check embedding coverage
MATCH (p:Paper)
WHERE p.embedding IS NOT NULL
RETURN count(p) as with_embeddings

MATCH (p:Paper)
RETURN count(p) as total

// Should be close to 100%
```

---

## Tuning Strategies

### Strategy 1: Query-Specific Tuning

Different query types may need different parameters:

**Theory Questions** (e.g., "What is resource-based view?"):
```python
result = graphrag.query(
    query,
    top_k=5,              # Fewer papers, more focused
    similarity_threshold=0.35  # Higher threshold for precision
)
```

**Broad Questions** (e.g., "What research exists on strategy?"):
```python
result = graphrag.query(
    query,
    top_k=15,            # More papers for comprehensive coverage
    similarity_threshold=0.25  # Lower threshold to cast wider net
)
```

**Comparison Questions** (e.g., "Compare theory X and Y"):
```python
result = graphrag.query(
    query,
    top_k=10,
    similarity_threshold=0.3,
    # May need to query twice and combine results
)
```

### Strategy 2: Adaptive Thresholds

Adjust based on result quality:

```python
def adaptive_query(query, initial_threshold=0.3):
    result = graphrag.query(query, similarity_threshold=initial_threshold)
    
    # If too few results, lower threshold
    if len(result['papers']) < 3:
        result = graphrag.query(query, similarity_threshold=initial_threshold - 0.1)
    
    # If too many low-quality results, raise threshold
    avg_sim = sum(p['similarity'] for p in result['papers']) / len(result['papers'])
    if avg_sim < 0.25 and len(result['papers']) > 10:
        result = graphrag.query(query, similarity_threshold=initial_threshold + 0.1)
    
    return result
```

### Strategy 3: Result Filtering

Post-process results to improve quality:

```python
def filter_results(result, min_similarity=0.3, max_results=10):
    # Filter by similarity
    filtered_papers = [
        p for p in result['papers'] 
        if p.get('similarity', 0) >= min_similarity
    ][:max_results]
    
    # Sort by similarity
    filtered_papers.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    
    result['papers'] = filtered_papers
    return result
```

---

## Performance Optimization

### 1. Caching

Cache frequent queries:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_hash, top_k, threshold):
    # Query logic here
    pass
```

### 2. Batch Processing

For multiple queries, process in batches:

```python
queries = ["query1", "query2", "query3"]
results = []

for query in queries:
    result = graphrag.query(query)
    results.append(result)
```

### 3. Parallel Processing

For independent queries:

```python
import asyncio

async def process_queries(queries):
    tasks = [graphrag.query_async(q) for q in queries]
    return await asyncio.gather(*tasks)
```

---

## Common Issues & Solutions

### Issue 1: Too Few Results

**Symptoms**: Query returns < 3 papers

**Solutions**:
1. Lower `similarity_threshold` (e.g., 0.25)
2. Increase `top_k` (e.g., 15)
3. Check if embeddings exist for relevant entities
4. Verify query is not too specific

### Issue 2: Too Many Irrelevant Results

**Symptoms**: Many papers with low similarity scores

**Solutions**:
1. Raise `similarity_threshold` (e.g., 0.4)
2. Decrease `top_k` (e.g., 5)
3. Add post-processing filters
4. Improve query specificity

### Issue 3: Slow Queries

**Symptoms**: Query takes > 10 seconds

**Solutions**:
1. Reduce `top_k` values
2. Use vector indexes (verify they exist)
3. Limit graph traversal depth
4. Cache frequent queries

### Issue 4: Poor Answer Quality

**Symptoms**: LLM generates generic or irrelevant answers

**Solutions**:
1. Increase context quality (raise similarity threshold)
2. Include more diverse sources (theories, phenomena, methods)
3. Adjust LLM temperature (lower = more focused)
4. Provide better context formatting

---

## Monitoring Dashboard (Future)

Consider implementing:
- Query performance metrics
- Answer quality scores
- User feedback tracking
- Embedding coverage reports
- Similarity score distributions

---

## Recommended Defaults

For most use cases:

```python
DEFAULT_PARAMS = {
    "top_k": 10,              # Papers
    "similarity_threshold": 0.3,
    "theory_top_k": 5,
    "phenomenon_top_k": 5,
    "method_top_k": 5
}
```

For production:
- Start with defaults
- Monitor performance
- Adjust based on user feedback
- A/B test different parameters

---

## Testing Checklist

After tuning, verify:
- [ ] Query response time < 5 seconds
- [ ] At least 3-5 relevant papers per query
- [ ] Average similarity > 0.3
- [ ] Answer quality is good (manual review)
- [ ] Sources are relevant to query
- [ ] No errors in logs

---

## Next Steps

1. **Baseline**: Test with current defaults
2. **Measure**: Collect performance metrics
3. **Tune**: Adjust parameters based on results
4. **Validate**: Test with diverse queries
5. **Deploy**: Use tuned parameters in production
6. **Monitor**: Continue tracking performance
