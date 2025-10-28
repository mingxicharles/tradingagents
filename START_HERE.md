# 🚀 START HERE - Quick Start Guide

## The Simplest Way to Run (Choose One)

### Method 1: Use the wrapper script ⭐ (RECOMMENDED)

Just run:
```bash
./run_with_key.sh AAPL --horizon 1w
```

That's it! No need to set environment variables.

---

### Method 2: Set API key once, then run normally

**In your terminal, run these commands:**

```bash
# 1. Navigate to the project
cd /Users/charleswang/Downloads/USC/Courses/CS566/tradingagents

# 2. Set your API key (copy-paste this, then add your key)
export OPENAI_API_KEY="sk-your-key-here"

# 3. Verify it's set
echo $OPENAI_API_KEY

# 4. Run the pipeline
python3 run.py AAPL --horizon 1w
```

---

### Method 3: Inline API key (one-time use)

```bash
OPENAI_API_KEY="sk-your-key-here" python3 run.py AAPL
```

---

## Quick Test

To verify everything works:

```bash
# Run the test suite
python3 test_runner.py

# Or just check if API works
OPENAI_API_KEY="sk-your-key" python3 -c "import asyncio; from tradingagents.llm import build_client; print(asyncio.run(build_client().complete([{'role':'user','content':'hi'}])))"
```

---

## What You'll See When It Works

```
Building API client: gpt-4o-mini
Decision: BUY (confidence 0.75)
Rationale:
technical: AAPL shows strong momentum...
news: Recent developments suggest...
fundamental: Strong financial position...
Evidence by agent:
  - technical: ...
  - news: ...
  - fundamental: ...
Signal written to signals/aapl_20251028T123456Z.json
```

---

## Common Error Messages

### ❌ "OPENAI_API_KEY not set"
**Fix**: Use Method 1 (wrapper script) or Method 2 (export variable)

### ❌ "Module not found"
**Fix**: 
```bash
pip install -r requirements.txt
```

### ❌ "No such file or directory"
**Fix**: Make sure you're in the right directory:
```bash
cd /Users/charleswang/Downloads/USC/Courses/CS566/tradingagents
```

---

## 📝 Important Notes

1. **Your API key is exposed** - Go to https://platform.openai.com/api-keys and delete the exposed key
2. The API key in the scripts is just an example - replace with your actual key
3. Each new terminal window needs the key set again (unless you add it to your shell profile)

---

## Still Having Issues?

1. Run: `./debug.sh` to see what's wrong
2. Check: `TROUBLESHOOTING.md` for detailed solutions
3. Run: `python3 test_runner.py` to test step-by-step

---

## Files in This Project

- `run.py` - Main entry point
- `run_with_key.sh` - Easy wrapper script (no setup needed)
- `test_runner.py` - Test your setup
- `debug.sh` - Debug script
- `setup_env.sh` - Environment setup
- `USAGE.md` - Detailed usage guide
- `TROUBLESHOOTING.md` - Fix common problems
- `signals/` - Generated trading signals (JSON files)

---

## Example Commands

```bash
# Analyze Apple with 1 week horizon
./run_with_key.sh AAPL --horizon 1w

# Analyze Microsoft with custom context
./run_with_key.sh MSFT --horizon 1d --context "Post-earnings consolidation"

# Analyze Tesla
./run_with_key.sh TSLA --horizon 1w --context "EV market trends"
```

---

**Happy Trading! 📈**



