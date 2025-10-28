# API Configuration Guide

## Quick Setup

### Method 1: Interactive Configuration (Recommended)

```bash
python configure_api.py
```

This will guide you through:
1. Choosing between OpenAI API or local model
2. Entering your credentials
3. Optionally saving to `.env` file

---

### Method 2: Command Line

**For OpenAI API:**
```bash
# Option A: Pass API key directly
python run.py AAPL --horizon 1w --api-key "sk-your-key-here"

# Option B: Set environment variable
export OPENAI_API_KEY="sk-your-key-here"
python run.py AAPL --horizon 1w

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"
python run.py AAPL --horizon 1w
```

**For Local Model:**
```bash
python run.py AAPL --horizon 1w --local-model "Qwen/Qwen2.5-7B-Instruct"
```

---

### Method 3: Python Code

```python
from tradingagents.config_api import set_openai_api_key, set_local_model
from tradingagents.run import execute
from tradingagents.models import ResearchRequest

# Option A: Use OpenAI API
set_openai_api_key("sk-your-key-here")

# Option B: Use local model
# set_local_model("Qwen/Qwen2.5-7B-Instruct")

# Run analysis
request = ResearchRequest(
    symbol="AAPL",
    horizon="1w",
    market_context="Post-earnings"
)

result = await execute(request, use_real_data=True)
print(result["decision"].recommendation)
```

---

### Method 4: `.env` File (Persistent)

Create a `.env` file in the project root:

```bash
# For OpenAI API
OPENAI_API_KEY=sk-your-key-here

# OR for local model
USE_LOCAL_MODEL=true
LOCAL_MODEL=Qwen/Qwen2.5-7B-Instruct
```

Then simply run:
```bash
python run.py AAPL --horizon 1w
```

---

## Configuration Examples

### Example 1: OpenAI with Real Data
```bash
export OPENAI_API_KEY="sk-proj-..."
python run.py AAPL --horizon 1w
```

**Output:**
```
✓ Analyzing AAPL with real market data
Decision: BUY (confidence 0.82)
...
```

### Example 2: Local Model with Real Data
```bash
python run.py AAPL --horizon 1w --local-model "Qwen/Qwen2.5-7B-Instruct"
```

**Output:**
```
✓ Using local model: Qwen/Qwen2.5-7B-Instruct
Loading local model: Qwen/Qwen2.5-7B-Instruct
✓ Analyzing AAPL with real market data
...
```

### Example 3: API Key via Command Line
```bash
python run.py MSFT --horizon 1d --api-key "sk-proj-..." --context "Tech sector rotation"
```

---

## Checking Configuration

```python
from tradingagents.config_api import print_api_status

print_api_status()
```

**Output:**
```
============================================================
API Configuration Status
============================================================
Mode: OpenAI API
API Key: ...abc123
============================================================
```

Or run:
```bash
python configure_api.py
# Choose option 3: Check current configuration
```

---

## Troubleshooting

### Error: "API not configured"

**Problem:**
```
❌ Error: API not configured: OpenAI API key not set
```

**Solution:**
```bash
# Quick fix - use command line
python run.py AAPL --api-key "your-key"

# Or configure permanently
python configure_api.py
```

### Error: "Invalid API key"

**Problem:**
```
❌ Error: API key seems invalid (too short)
```

**Solution:**
- Get a valid key from https://platform.openai.com/api-keys
- Make sure you copied the entire key (starts with `sk-proj-` or `sk-`)

### Using Local Model Without GPU

**Problem:** Out of memory

**Solution:**
```bash
# Use smaller model
python run.py AAPL --local-model "Qwen/Qwen2.5-1.5B-Instruct"
```

---

## Priority Order

The system checks for configuration in this order:

1. **Command line arguments** (`--api-key` or `--local-model`)
2. **Environment variables** (`OPENAI_API_KEY`, `USE_LOCAL_MODEL`)
3. **`.env` file** (auto-loaded by python-dotenv)

Later settings override earlier ones.

---

## Security Best Practices

### ✅ DO:
- Use `.env` file and add it to `.gitignore`
- Use environment variables
- Rotate API keys regularly

### ❌ DON'T:
- Commit API keys to git
- Share API keys in public repos
- Hardcode API keys in source code

---

## Full Workflow Example

```bash
# 1. Configure API (one-time setup)
python configure_api.py
# Select option 1, enter your API key, save to .env

# 2. Install data dependencies
pip install yfinance pandas

# 3. Run analysis
python run.py AAPL --horizon 1w

# 4. For RL training (collect many samples)
for symbol in AAPL MSFT GOOGL TSLA NVDA
do
    python run.py $symbol --horizon 1w
    sleep 3
done

# 5. Check generated signals
ls signals/
```

---

## Need Help?

1. Run interactive config: `python configure_api.py`
2. Check status: `python configure_api.py` → option 3
3. Test setup: `python test_real_data.py`

Your API is ready when you see:
```
✓ API key configured
✓ Analyzing AAPL with real market data
```

Happy trading! 🚀

