# Metadata Extraction Optimization

## Problem

**Every paper was experiencing OLLAMA timeouts** during metadata extraction:
- 5 retries × 300s timeout = up to 25 minutes per paper just for metadata
- Processing time: ~29 minutes per paper
- This was blocking the entire batch process

## Root Causes

1. **Too much text**: 15,000 characters sent to LLM
2. **Complex prompt**: Very detailed instructions requiring extensive processing
3. **Long timeout**: 300 seconds (5 minutes) per attempt
4. **Too many retries**: 5 retries meant 25+ minutes of waiting

## Optimizations Implemented ✅

### 1. Reduced Text Length
- **Before**: 15,000 characters
- **After**: 5,000 characters
- **Impact**: 3x less text = much faster processing

### 2. Simplified Prompt
- **Before**: Detailed instructions for all fields (title, authors with affiliations, email, etc.)
- **After**: Focus on essential fields only (title, abstract, authors as list, DOI, keywords)
- **Impact**: Faster LLM processing, less complexity

### 3. Reduced Max Tokens
- **Before**: 3,000 tokens
- **After**: 1,500 tokens
- **Impact**: Faster response generation

### 4. Shorter Timeout
- **Before**: 300 seconds (5 minutes)
- **After**: 120 seconds (2 minutes) for metadata extraction
- **Impact**: Faster failure detection, less waiting

### 5. Fewer Retries
- **Before**: 5 retries
- **After**: 3 retries for metadata extraction
- **Impact**: Faster fallback to rule-based extraction

### 6. Enhanced Fallback
- **Before**: Empty metadata dict when LLM fails
- **After**: Rule-based extraction from filename and first page
- **Impact**: Papers still get ingested with basic metadata

## Expected Performance Improvement

**Before:**
- Metadata extraction: 5 retries × 300s = up to 25 minutes
- Total per paper: ~29 minutes

**After:**
- Metadata extraction: 3 retries × 120s = up to 6 minutes (worst case)
- With fallback: ~30 seconds if LLM fails
- Total per paper: ~5-10 minutes (estimated)

**Improvement: 3-6x faster!**

## What Happens Now

1. **Try LLM extraction** (optimized - 5k chars, simple prompt, 120s timeout, 3 retries)
2. **If fails** → Use fallback metadata extraction (rule-based, ~30 seconds)
3. **Continue with other extractions** (theories, methods, findings, etc.)
4. **Ingest paper** with whatever metadata we have

## Result

- ✅ **No more 25-minute waits** for metadata
- ✅ **Papers still get ingested** even if LLM fails
- ✅ **Faster overall processing** (3-6x improvement)
- ✅ **Better reliability** (fallback ensures papers aren't lost)

---

## Monitoring

Watch for these in the logs:

**Good signs:**
- ✅ Metadata extraction completes in < 2 minutes
- ✅ "✓ Metadata extracted" appears quickly
- ✅ No timeout warnings

**If still timing out:**
- ⚠️ May need to reduce text further (3k chars)
- ⚠️ May need to use fallback by default
- ⚠️ May need faster OLLAMA model for metadata

---

## Next Steps

The batch process will automatically use these optimizations. Monitor the logs to see the improvement!

