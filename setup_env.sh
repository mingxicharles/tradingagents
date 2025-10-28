#!/bin/bash
# Trading Agents Environment Setup Script

# Set your OpenAI API key here
export OPENAI_API_KEY="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"

# Optional: Override model (default is gpt-4o-mini with OpenAI API key)
# export OPENAI_MODEL="gpt-4"

# For local model usage (when USE_LOCAL_MODEL=true):
# export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"

echo "✓ Environment configured for OpenAI"
echo "  Model: ${OPENAI_MODEL:-gpt-4o-mini}"
echo "  API Key: ${OPENAI_API_KEY:0:10}... (configured)"
echo ""
echo "Run your pipeline with:"
echo "  python run.py AAPL --horizon 1w"
echo ""
echo "Or source this file: source setup_env.sh"

