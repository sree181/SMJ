#!/bin/bash
# Quick start script for high-performance pipeline

cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate

# Update Neo4j config
python update_neo4j_config.py

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set"
    echo "   Please set it in your .env file or export it:"
    echo "   export OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Default arguments
DIRECTORY="${1:-2025-2029}"
WORKERS="${2:-20}"

echo "🚀 Starting High-Performance Pipeline"
echo "   Directory: $DIRECTORY"
echo "   Workers: $WORKERS"
echo ""

python high_performance_pipeline.py "$DIRECTORY" --workers "$WORKERS"
