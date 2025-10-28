#!/bin/bash
# Wrapper script to run the pipeline with your API key automatically

# Set your API key here (replace with your actual key)
export OPENAI_API_KEY="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"

# Optional: Set model (default is gpt-4o-mini)
# export OPENAI_MODEL="gpt-4"

echo "Starting trading agents pipeline..."
echo ""

# Run the pipeline with all arguments passed through
python3 run.py "$@"



