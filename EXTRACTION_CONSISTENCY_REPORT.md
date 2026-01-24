# Paper Node Extraction - Consistency Validation Report

## Test Results: 3 Papers from 2025-2029

### ✅ **100% Success Rate on All Core Fields**

| Field | Success Rate | Notes |
|-------|-------------|-------|
| **Title** | 100% (3/3) | Exact titles extracted correctly |
| **Abstract** | 100% (3/3) | Complete abstracts extracted |
| **Journal** | 100% (3/3) | "Strategic Management Journal" |
| **DOI** | 100% (3/3) | All DOIs extracted correctly |
| **Keywords** | 100% (3/3) | 3-5 keywords per paper |
| **Authors** | 100% (3/3) | Proper name parsing |
| **Methods** | 100% (3/3) | 2-3 methods per paper |

## Paper Details

### Paper 1: 2025_4359
- **Title**: "Double-edged stars: Michelin stars, reactivity, and restaurant exits in New York City"
- **Authors**: 1 (Daniel B. Sands)
- **Methods**: 2 (archival media coverage, first-hand interviews)
- **Keywords**: 3
- **DOI**: 10.1002/smj.3651

### Paper 2: 2025_4488
- **Title**: "Organizational adaptation in dynamic environments: Disentangling..."
- **Authors**: 2 (Srikanth K., Ungureanu C.)
- **Methods**: 3 (N-armed bandit model, Reinforcement learning, Computational model)
- **Keywords**: 4
- **DOI**: 10.1002/smj.3646

### Paper 3: 2025_4573
- **Title**: "Curating 1000 flowers as they bloom: Leveraging pluralistic..."
- **Authors**: 1 (Esther Leibel)
- **Methods**: 3 (semi-structured interviews, fieldnotes, archival data)
- **Keywords**: 5
- **DOI**: 10.1002/smj.3656

## Graph Structure

### Nodes Created
- **Paper**: 3 nodes
- **Author**: 4 unique authors
- **Method**: 8 unique methods
- **Institution**: 3 institutions

### Relationships Created
- **AUTHORED**: 4 (Author → Paper)
- **AFFILIATED_WITH**: 4 (Author → Institution)
- **USES_METHOD**: 8 (Paper → Method)

## Performance Metrics

- **Average Methods per Paper**: 2.7
- **Average Authors per Paper**: 1.3
- **Processing Speed**: Optimized (15k chars, 3k tokens)
- **Success Rate**: 100% (3/3 papers)

## Extraction Quality

### ✅ Working Well
1. **Title Extraction**: Exact titles, no summarization
2. **Abstract Extraction**: Complete text extracted
3. **Author Parsing**: Proper given_name/family_name split
4. **Method Extraction**: Paper-specific methods (no generic lists)
5. **DOI Extraction**: All DOIs found correctly
6. **Keywords**: Relevant keywords extracted

### ⚠️ Needs Improvement
1. **Email Extraction**: Not extracted (should be in "Correspondence" section)
2. **Volume/Issue**: Not extracted from header/footer
3. **Pages**: Not extracted (or placeholder values)
4. **Paper Type**: Not classified
5. **Affiliation Details**: City/country sometimes missing

## Optimizations Applied

1. **Reduced Text Length**: 30k → 15k characters (faster)
2. **Reduced Max Tokens**: 4k → 3k tokens (faster)
3. **Simplified Prompt**: More focused, less verbose
4. **Author ID Generation**: Auto-generate if LLM doesn't provide

## Conclusion

**Paper node extraction is working consistently** with 100% success rate on all core fields across 3 test papers. The system is:
- ✅ **Reliable**: 100% success rate
- ✅ **Fast**: Optimized prompts (no timeouts)
- ✅ **Accurate**: Exact text extraction (no summarization)
- ✅ **Complete**: All core fields extracted

**Status**: Ready for production use on core fields. Email/volume/issue extraction can be improved in next iteration.

