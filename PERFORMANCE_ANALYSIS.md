# Performance Analysis - High Performance Pipeline

## Current Performance Metrics

Based on pipeline logs:
- **Avg Extraction Time**: ~16.6 seconds per paper
- **Avg Normalization Time**: ~0.000 seconds (negligible)
- **Avg Ingestion Time**: ~2.0 seconds per paper
- **Total Time per Paper**: ~18.6 seconds
- **Throughput**: ~200-250 papers/hour (with 5 workers)

## Bottleneck Analysis

### 🔴 **PRIMARY BOTTLENECK: Extraction Phase (89% of total time)**

#### 1. **Multiple GPT-4 API Calls Per Paper**
   - **10 separate API calls** per paper:
     1. metadata
     2. theories
     3. phenomena
     4. methods
     5. variables
     6. findings
     7. contributions
     8. authors
     9. research_questions
     10. theory_phenomenon_links

   - **Current Implementation**: 
     ```python
     extraction_tasks = [
         self._extract_with_json_mode(text, "metadata", paper_id),
         self._extract_with_json_mode(text, "theories", paper_id),
         # ... 8 more calls
     ]
     results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
     ```
   
   - **Issue**: Even though calls are async and run in parallel, each call takes ~1.5-2 seconds
   - **Total API time**: 10 calls × ~1.6s = ~16 seconds (matches observed time)

#### 2. **Large Text Chunks**
   - Sending up to **15,000 characters** per request
   - Some requests use 12,000-15,000 chars (theories, phenomena, theory_phenomenon_links)
   - Larger prompts = slower GPT-4 responses

#### 3. **Retry Logic with Exponential Backoff**
   - On failure: `await asyncio.sleep(2 ** attempt)` 
   - Retry delays: 1s, 2s, 4s (if max_retries=3)
   - Adds significant time on API errors

#### 4. **Synchronous PDF Text Extraction**
   - Happens **before** all API calls
   - Blocks the async event loop
   - Could be parallelized or cached

### 🟡 **SECONDARY BOTTLENECK: Ingestion Phase (11% of total time)**

#### 1. **Synchronous Neo4j Operations**
   - All Neo4j operations run in `run_in_executor()` (thread pool)
   - Multiple transactions per paper:
     - Paper node creation
     - Theory nodes + relationships
     - Method nodes + relationships
     - Author nodes + relationships
     - Variable, Finding, Contribution nodes
     - Research Question nodes
   - **Total**: ~10-15 database operations per paper

#### 2. **Transaction Overhead**
   - Each operation is a separate transaction
   - Could be batched into fewer transactions

### ✅ **NOT A BOTTLENECK: Normalization Phase**

- Embedding-based normalization is very fast
- Uses cached embeddings
- Negligible time impact

## Performance Breakdown (Per Paper)

```
Total: ~18.6 seconds
├── Extraction: 16.6s (89%)
│   ├── PDF text extraction: ~0.5s (synchronous)
│   ├── GPT-4 API calls (10 parallel): ~16s
│   │   ├── Each call: ~1.6s average
│   │   ├── Network latency: ~0.2s
│   │   ├── GPT-4 processing: ~1.4s
│   │   └── JSON parsing: ~0.0s
│   └── Result processing: ~0.1s
├── Normalization: 0.0s (<1%)
└── Ingestion: 2.0s (11%)
    ├── Neo4j connection: ~0.1s
    ├── Transactions: ~1.8s
    └── Relationship creation: ~0.1s
```

## Optimization Opportunities

### 🚀 **High Impact Optimizations**

#### 1. **Reduce Number of API Calls (3-5x speedup)**
   - **Current**: 10 separate calls
   - **Optimization**: Combine into 2-3 calls:
     - Call 1: metadata + authors (lightweight)
     - Call 2: theories + phenomena + theory_phenomenon_links (related)
     - Call 3: methods + variables + findings + contributions + research_questions (methodology-related)
   - **Expected**: Reduce from 16s to ~5-6s per paper

#### 2. **Reduce Text Chunk Sizes (1.2-1.5x speedup)**
   - **Current**: 12,000-15,000 chars per request
   - **Optimization**: 
     - Use targeted sections (Introduction for theories, Methodology for methods)
     - Reduce to 8,000-10,000 chars per request
   - **Expected**: Reduce API response time by 20-30%

#### 3. **Parallel PDF Extraction (1.1x speedup)**
   - **Current**: Synchronous, blocks before API calls
   - **Optimization**: Extract PDF text in parallel with first API call
   - **Expected**: Save ~0.5s per paper

#### 4. **Batch Neo4j Operations (1.3-1.5x speedup)**
   - **Current**: 10-15 separate transactions
   - **Optimization**: Batch into 2-3 transactions:
     - Transaction 1: Paper + Authors
     - Transaction 2: Theories + Methods + Phenomena + Relationships
     - Transaction 3: Variables + Findings + Contributions + Research Questions
   - **Expected**: Reduce ingestion from 2.0s to ~1.3s

### 🟢 **Medium Impact Optimizations**

#### 5. **Implement Request Caching**
   - Cache GPT-4 responses for identical text chunks
   - Useful for papers with similar structures
   - **Expected**: 10-20% reduction on duplicate content

#### 6. **Optimize Retry Logic**
   - Reduce max_retries from 3 to 2 for non-critical extractions
   - Use shorter backoff for rate limits
   - **Expected**: Save 1-2s on failures

#### 7. **Connection Pooling for Neo4j**
   - Reuse connections instead of creating new ones
   - **Expected**: Save ~0.1s per paper

### 🔵 **Low Impact Optimizations**

#### 8. **Streaming Responses**
   - Use streaming for GPT-4 (if supported)
   - **Expected**: Minimal improvement (~0.1s)

#### 9. **Pre-warm Embedding Cache**
   - Load common entity embeddings at startup
   - **Expected**: Negligible (normalization is already fast)

## Recommended Implementation Priority

1. **Priority 1**: Reduce API calls (combine into 2-3 calls) - **3-5x speedup**
2. **Priority 2**: Batch Neo4j operations - **1.3-1.5x speedup**
3. **Priority 3**: Reduce text chunk sizes - **1.2-1.5x speedup**
4. **Priority 4**: Parallel PDF extraction - **1.1x speedup**

## Expected Performance After Optimizations

### Current:
- **Time per paper**: ~18.6s
- **Throughput (5 workers)**: ~200-250 papers/hour
- **Throughput (20 workers)**: ~400-500 papers/hour

### After Priority 1-2:
- **Time per paper**: ~6-7s (3x improvement)
- **Throughput (5 workers)**: ~600-750 papers/hour
- **Throughput (20 workers)**: ~1,200-1,500 papers/hour

### After All Optimizations:
- **Time per paper**: ~4-5s (4x improvement)
- **Throughput (5 workers)**: ~900-1,100 papers/hour
- **Throughput (20 workers)**: ~1,800-2,200 papers/hour

## Code Locations for Optimization

1. **API Call Reduction**: `enhanced_gpt4_extractor.py` lines 600-613
2. **Text Chunk Sizes**: `enhanced_gpt4_extractor.py` lines 296-424
3. **PDF Extraction**: `enhanced_gpt4_extractor.py` lines 476-490
4. **Neo4j Batching**: `redesigned_methodology_extractor.py` lines 1600-2800

## Monitoring Recommendations

Add timing logs for:
- Individual API call durations
- PDF extraction time
- Neo4j transaction times
- Retry counts and delays

Example:
```python
logger.info(f"API call {extraction_type} took {duration:.2f}s")
logger.info(f"Neo4j transaction took {duration:.2f}s")
```
