#!/bin/bash
# Convenience script to start processing all buckets
# This will run after the current bucket (2015-2019) completes

cd "$(dirname "$0")"
source ../smj/bin/activate

# Unset OLLAMA to use GPT-4
unset USE_OLLAMA

# Run the automated bucket processor
# It will automatically discover and process all remaining buckets
python process_all_buckets.py --workers 5 2>&1 | tee process_all_buckets.log

echo ""
echo "✓ All buckets processing complete!"
echo "Check process_all_buckets.log for details"
