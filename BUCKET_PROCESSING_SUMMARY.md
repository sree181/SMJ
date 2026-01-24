# Multi-Bucket Processing Summary

## Available Buckets

| Bucket | Papers | Status |
|--------|--------|--------|
| 1985-1989 | 10 | Pending |
| 1990-1994 | 90 | Pending |
| 1995-1999 | 118 | Pending |
| 2000-2004 | 134 | Pending |
| 2005-2009 | 109 | Pending |
| 2010-2014 | 150 | Pending |
| 2015-2019 | 275 | **Currently Processing** |
| 2020-2024 | 158 | Partially Done (133/158) |
| 2025-2029 | 10 | Pending |

**Total Papers**: 1,054 papers across 9 buckets

## Scripts Created

### 1. `process_all_buckets.py`
Main Python script that:
- Automatically discovers all buckets
- Processes them sequentially
- Handles resume for each bucket
- Saves progress after each bucket
- Generates comprehensive reports

### 2. `start_all_buckets.sh`
Convenience shell script that:
- Activates virtual environment
- Sets up environment variables
- Runs the Python script
- Logs output to file

## Usage

### Option 1: Run After Current Bucket Completes

Once 2015-2019 finishes, run:
```bash
cd "Strategic Management Journal"
./start_all_buckets.sh
```

Or directly:
```bash
source ../smj/bin/activate
python process_all_buckets.py --workers 5
```

### Option 2: Start from Specific Bucket

If you want to skip 2015-2019 and start from 2020-2024:
```bash
python process_all_buckets.py --start-from 2020-2024 --workers 5
```

### Option 3: Process All Including Completed

Force reprocess all buckets:
```bash
python process_all_buckets.py --no-skip-completed --workers 5
```

## Features

✅ **Automatic Discovery**: Finds all year buckets  
✅ **Sequential Processing**: One bucket at a time  
✅ **Resume Support**: Skips already processed papers  
✅ **Progress Tracking**: Saves after each bucket  
✅ **Error Recovery**: Continues even if one bucket fails  
✅ **Comprehensive Logging**: Detailed logs for monitoring  

## Expected Timeline

With 5 workers per bucket (assuming ~200 papers/hour):

| Bucket | Papers | Estimated Time |
|--------|--------|----------------|
| 2015-2019 | 275 | ~1.5 hours (in progress) |
| 2020-2024 | 25 remaining | ~10 minutes |
| 2010-2014 | 150 | ~45 minutes |
| 2000-2004 | 134 | ~40 minutes |
| 1995-1999 | 118 | ~35 minutes |
| 2005-2009 | 109 | ~30 minutes |
| 1990-1994 | 90 | ~25 minutes |
| 1985-1989 | 10 | ~3 minutes |
| 2025-2029 | 10 | ~3 minutes |

**Total Estimated Time**: ~4-5 hours for all remaining buckets

## Monitoring

### Check Current Status
```bash
# View recent activity
tail -f process_all_buckets.log

# Check which bucket is processing
grep "BUCKET.*:" process_all_buckets.log | tail -1

# View results
cat bucket_processing_results.json | jq '.'
```

### Check Individual Bucket Progress
```bash
# Check progress file
cat high_performance_progress.json | jq '.processed_papers | length'

# Count papers for specific bucket
cat high_performance_progress.json | jq -r '.processed_papers[]' | grep "^2015" | wc -l
```

## Output Files

- **`process_all_buckets.log`**: Main processing log
- **`bucket_processing_results.json`**: Results for each bucket (updated incrementally)
- **`high_performance_progress.json`**: Combined progress (shared across all buckets)
- **`high_performance_stats.json`**: Final statistics

## Resume Behavior

- **Within Bucket**: If interrupted, restarting will skip already processed papers
- **Between Buckets**: If script is interrupted, restarting will continue from next incomplete bucket
- **Progress File**: Single shared progress file tracks all buckets

## Next Steps

1. **Wait for 2015-2019 to complete** (currently running)
2. **Run the script**: `./start_all_buckets.sh` or `python process_all_buckets.py`
3. **Monitor progress**: Check logs and results files
4. **Review results**: Check `bucket_processing_results.json` for summary

The script will automatically:
- Process 2015-2019 (if not complete)
- Continue with 2020-2024 (remaining 25 papers)
- Process all other buckets in chronological order
- Skip any buckets that appear fully completed
