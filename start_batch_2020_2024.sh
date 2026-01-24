#!/bin/bash
# Start batch processing for 2020-2024 with proper logging

cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate

# Kill any existing batch processes
pkill -f batch_process_complete_extraction 2>/dev/null
sleep 2

# Start new batch process with logging
nohup python batch_process_complete_extraction.py "2020-2024" > batch_extraction_output.log 2>&1 &

echo "✅ Batch processing started!"
echo "📊 Monitor with: tail -f batch_extraction_output.log"
echo "📊 Or use: python monitor_batch_status.py"
echo "📊 Process ID: $!"

