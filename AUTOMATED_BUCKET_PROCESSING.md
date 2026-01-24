# Automated Multi-Bucket Processing

## Overview

The `process_all_buckets.py` script automatically processes all 5-year buckets sequentially, with resume capability and progress tracking.

## Features

✅ **Automatic Discovery**: Finds all year bucket directories (e.g., 2015-2019, 2020-2024)  
✅ **Sequential Processing**: Processes buckets one at a time to avoid resource conflicts  
✅ **Resume Support**: Skips already processed papers within each bucket  
✅ **Progress Tracking**: Saves intermediate results after each bucket  
✅ **Skip Completed**: Automatically skips buckets that appear fully processed  
✅ **Error Handling**: Continues to next bucket even if one fails  
✅ **Comprehensive Logging**: Detailed logs for monitoring and debugging  

## Usage

### Basic Usage

Process all buckets from current directory:
```bash
python process_all_buckets.py
```

### With Custom Workers

Process with more workers (faster but uses more resources):
```bash
python process_all_buckets.py --workers 10
```

### Start from Specific Bucket

If you want to skip earlier buckets and start from a specific one:
```bash
python process_all_buckets.py --start-from 2020-2024
```

### Process All (Including Completed)

Force processing of all buckets, even if they appear completed:
```bash
python process_all_buckets.py --no-skip-completed
```

### Using Shell Script

For convenience, use the shell script:
```bash
./start_all_buckets.sh
```

## How It Works

1. **Discovery Phase**:
   - Scans base directory for year bucket folders
   - Counts PDFs in each bucket
   - Sorts buckets chronologically

2. **Processing Phase**:
   - For each bucket:
     - Initializes pipeline with resume enabled
     - Processes all papers in the bucket
     - Saves progress after completion
     - Logs results

3. **Completion**:
   - Generates summary of all buckets
   - Saves final results to `bucket_processing_results.json`

## Output Files

- **`process_all_buckets.log`**: Detailed processing log
- **`bucket_processing_results.json`**: Results for each bucket (updated after each bucket)
- **`high_performance_progress.json`**: Combined progress across all buckets

## Example Output

```
================================================================================
AUTOMATED MULTI-BUCKET PROCESSING
================================================================================
Base path: /path/to/Strategic Management Journal
Workers per bucket: 5
Start from: first bucket
================================================================================
Found 3 buckets:
  - 2015-2019: 275 papers
  - 2020-2024: 158 papers
  - 2025-2029: 10 papers

================================================================================
BUCKET 1/3: 2015-2019
================================================================================
Processing bucket: 2015-2019
Total papers: 275
...
✓ Bucket 2015-2019 completed: 275 processed, 0 failed

================================================================================
BUCKET 2/3: 2020-2024
================================================================================
...
```

## Integration with Current Pipeline

The script uses the same `HighPerformancePipeline` class, so:
- ✅ Same resume logic (uses `high_performance_progress.json`)
- ✅ Same extraction methods (GPT-4 with OLLAMA fallback)
- ✅ Same normalization (embedding-based)
- ✅ Same ingestion (Neo4j with batching)

## Monitoring

### Check Current Status

```bash
# View recent log entries
tail -f process_all_buckets.log

# Check which bucket is currently processing
grep "BUCKET.*:" process_all_buckets.log | tail -1

# Check progress
grep "Completed\|Failed" process_all_buckets.log | tail -10
```

### Check Results

```bash
# View results JSON
cat bucket_processing_results.json | jq '.[] | {bucket: .bucket, status: .status, processed: .processed}'
```

## Resume Behavior

- **Within Bucket**: If a bucket is interrupted, restarting will skip already processed papers
- **Between Buckets**: If script is interrupted, restarting will skip completed buckets (if `--no-skip-completed` is not used)

## Error Handling

- If a bucket fails, the script logs the error and continues to the next bucket
- Failed buckets are marked in results with `"status": "failed"`
- You can manually retry failed buckets using the main pipeline script

## Performance

With 5 workers per bucket:
- **Expected throughput**: ~200-300 papers/hour
- **Per bucket time**: Depends on bucket size
  - 275 papers: ~1-1.5 hours
  - 158 papers: ~30-45 minutes
  - 10 papers: ~2-3 minutes

## Next Steps

Once the current 2015-2019 bucket completes, you can:

1. **Manual Start**: Run `python process_all_buckets.py` to process remaining buckets
2. **Automatic**: The script will automatically discover and process all remaining buckets
3. **Selective**: Use `--start-from` to process specific buckets only
