# Quick Usage Guide

## ⚠️ IMPORTANT: Your API Key is Exposed

The API key you provided has been exposed in conversation. **Please immediately:**

1. Go to https://platform.openai.com/api-keys
2. Revoke the key: `sk-proj-2sxaX8uj0iol...`
3. Generate a new API key

## Testing Your Setup

Your system is **working correctly**! Here's proof:

```bash
# The pipeline successfully ran and produced:
Decision: BUY (confidence 0.75)
Signal written to signals/aapl_20251028T184224Z.json
```

## Quick Start

### Option 1: Use the setup script
```bash
source setup_env.sh
python run.py AAPL --horizon 1w --context "Post-earnings analysis"
```

### Option 2: Set environment variables manually
```bash
export OPENAI_API_KEY="sk-your-new-key"
python run.py AAPL --horizon 1w
```

### Option 3: Inline (for testing)
```bash
OPENAI_API_KEY="sk-your-key" python run.py MSFT --horizon 1d
```

## What Works

✅ OpenAI API integration  
✅ Multi-agent orchestration (news, technical, fundamental)  
✅ Evidence-based decision making  
✅ Signal generation to JSON  
✅ Retry logic and error handling  
✅ LangGraph routing with conditional debates  

## Common Issues

### Issue: "Module not found"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "API key not found"
**Solution**: Export the environment variable
```bash
export OPENAI_API_KEY="sk-your-key"
```

### Issue: "Rate limit exceeded"
**Solution**: Wait a moment or upgrade your OpenAI plan

### Issue: Want to use a cheaper model
**Solution**: Specify the model explicitly
```bash
export OPENAI_MODEL="gpt-3.5-turbo"  # Cheaper option
python run.py AAPL
```

## Example Output

```json
{
  "symbol": "AAPL",
  "recommendation": "BUY",
  "confidence": 0.75,
  "evidence": {
    "technical": [...],
    "news": [...],
    "fundamental": [...]
  }
}
```

The signal is saved to `signals/<symbol>_<timestamp>.json`

## Using Local Models (No API Costs)

If you want to avoid API costs and have a GPU:

```bash
export USE_LOCAL_MODEL="true"
export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"
python run.py AAPL
```

First run will download the model (~15GB).

