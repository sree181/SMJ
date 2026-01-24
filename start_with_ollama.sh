#!/bin/bash
# Start high-performance pipeline with OLLAMA fallback

cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate

# Set OLLAMA as fallback
export USE_OLLAMA=true

# Default arguments
DIRECTORY="${1:-2025-2029}"
WORKERS="${2:-5}"

echo "🚀 Starting High-Performance Pipeline with OLLAMA"
echo "   Directory: $DIRECTORY"
echo "   Workers: $WORKERS"
echo "   Using OLLAMA (GPT-4 quota exceeded)"
echo ""

python high_performance_pipeline.py "$DIRECTORY" --workers "$WORKERS"
