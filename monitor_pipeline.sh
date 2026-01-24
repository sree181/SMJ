#!/bin/bash
# Monitor high-performance pipeline progress

cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"

echo "📊 Pipeline Status Monitor"
echo "=========================="
echo ""

# Check if process is running
if pgrep -f "high_performance_pipeline.py" > /dev/null; then
    echo "✅ Pipeline is running"
    echo ""
    
    # Show recent log entries
    echo "Recent activity:"
    tail -20 high_performance_pipeline.log 2>/dev/null | grep -E "(Processing|Completed|Failed|Worker)" | tail -10
    echo ""
    
    # Check progress file
    if [ -f "high_performance_progress.json" ]; then
        echo "Progress:"
        python3 -c "
import json
with open('high_performance_progress.json') as f:
    data = json.load(f)
    processed = len(data.get('processed_papers', []))
    print(f'  Processed: {processed} papers')
" 2>/dev/null || echo "  (Unable to read progress)"
    fi
else
    echo "❌ Pipeline is not running"
    echo ""
    echo "Last log entries:"
    tail -10 high_performance_pipeline.log 2>/dev/null || echo "  (No log file found)"
fi

echo ""
echo "To view full log: tail -f high_performance_pipeline.log"
