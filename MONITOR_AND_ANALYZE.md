# Monitor and Analyze Pipeline Results

## Current Status

✅ **Pipeline Running**: High-performance pipeline processing 2025-2029 folder (10 papers)
✅ **Using GPT-4**: With embedding normalization and async processing
✅ **Workers**: 5 concurrent workers

## Real-Time Monitoring

### Check Pipeline Status
```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
./monitor_pipeline.sh
```

### View Live Logs
```bash
tail -f high_performance_pipeline.log
```

### Check Progress
```bash
cat high_performance_progress.json | python -m json.tool
```

## After Completion - Detailed Analysis

Once the pipeline completes, run the comprehensive analysis:

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python analyze_results_detailed.py
```

This will provide:
- ✅ Extraction quality metrics
- ✅ Normalization effectiveness
- ✅ Entity extraction counts
- ✅ Error analysis
- ✅ Neo4j ingestion verification
- ✅ Performance comparison vs targets
- ✅ Recommendations

## Expected Results

Based on the objectives:

| Metric | Target | What to Look For |
|--------|--------|------------------|
| Papers/hour | 200+ | Should see high throughput |
| Entity accuracy | ~95% | Check entity counts per paper |
| Normalization coverage | ~98% | Should see high normalization hits |
| False positive rate | ~3% | Check error analysis |
| Success rate | >95% | Most papers should process successfully |

## Quick Status Check

```bash
# Check if still running
ps aux | grep high_performance_pipeline

# Check progress count
python3 -c "
import json
with open('high_performance_progress.json') as f:
    data = json.load(f)
    print(f\"Processed: {len(data.get('processed_papers', []))} papers\")
"

# Check recent activity
tail -20 high_performance_pipeline.log | grep -E "(Processing|Completed)"
```

## Next Steps After Analysis

1. **Review Results**: Check extraction quality and normalization coverage
2. **Verify Neo4j**: Ensure all papers and entities are properly ingested
3. **Scale Up**: If results are good, process larger batches (2020-2024)
4. **Optimize**: Adjust workers or settings based on performance

## Files to Review

- `high_performance_pipeline.log` - Detailed processing log
- `high_performance_progress.json` - Progress tracking
- `high_performance_stats.json` - Final statistics
- `analyze_results_detailed.py` - Comprehensive analysis script
