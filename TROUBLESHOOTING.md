# Troubleshooting Guide

## Quick Diagnostic

Run this to test your setup:
```bash
python3 test_runner.py
```

Or use the debug script:
```bash
./debug.sh
```

## Common Issues and Solutions

### 1. "OPENAI_API_KEY not set" or "API key not found"

**Problem**: The environment variable isn't set in your shell.

**Solutions**:

#### Option A: Use the wrapper script (easiest)
```bash
./run_with_key.sh AAPL --horizon 1w
```

#### Option B: Set it inline for one command
```bash
OPENAI_API_KEY="sk-your-key" python3 run.py AAPL
```

#### Option C: Export it in your terminal
```bash
export OPENAI_API_KEY="sk-your-key"
python3 run.py AAPL
```

#### Option D: Add it to your shell profile (persistent)
```bash
# For bash
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.zshrc
source ~/.zshrc
```

### 2. "Module not found" or ImportError

**Problem**: Dependencies not installed.

**Solution**:
```bash
pip install -r requirements.txt
```

If that doesn't work:
```bash
pip3 install -r requirements.txt
python3 -m pip install -r requirements.txt
```

### 3. "No module named 'tradingagents'"

**Problem**: Not in the right directory or Python path issue.

**Solution**:
```bash
# Make sure you're in the tradingagents directory
cd /path/to/tradingagents

# Verify you can see the files
ls tradingagents/*.py

# Try running again
python3 run.py AAPL
```

### 4. API call fails with authentication error

**Problem**: Invalid API key.

**Solutions**:
- Check your key at https://platform.openai.com/api-keys
- Make sure there are no extra spaces or quotes
- Regenerate a new key if needed

### 5. Rate limit or quota exceeded

**Problem**: Hit OpenAI rate limits.

**Solutions**:
- Wait a few minutes
- Upgrade your OpenAI plan
- Use a cheaper model: `export OPENAI_MODEL="gpt-3.5-turbo"`

### 6. Works in one terminal but not another

**Problem**: Environment variables are per-terminal session.

**Solution**: Export the variable in each new terminal, or add it to your shell profile (see #1, Option D).

## Step-by-Step Setup for New Terminal

```bash
# 1. Navigate to project
cd /Users/charleswang/Downloads/USC/Courses/CS566/tradingagents

# 2. Set API key (replace with your actual key)
export OPENAI_API_KEY="sk-your-actual-key-here"

# 3. Verify it's set
echo $OPENAI_API_KEY

# 4. Run the pipeline
python3 run.py AAPL --horizon 1w

# 5. Check output
ls signals/
```

## Testing Your Setup

**Quick test** (just tests API connection):
```bash
export OPENAI_API_KEY="sk-your-key"
python3 -c "
import asyncio
from tradingagents.llm import build_client
async def test():
    client = build_client()
    result = await client.complete([{'role': 'user', 'content': 'Say hello'}])
    print(f'Success! {result}')
asyncio.run(test())
"
```

**Full test** (tests everything):
```bash
export OPENAI_API_KEY="sk-your-key"
python3 test_runner.py
```

## Still Not Working?

1. Run the debug script: `./debug.sh`
2. Check Python version: `python3 --version` (needs 3.8+)
3. Check if you're in the right directory: `pwd`
4. Try verbose mode:
   ```bash
   export OPENAI_API_KEY="sk-your-key"
   python3 -v run.py AAPL 2>&1 | grep -i error
   ```

## Need Help?

Copy and paste the full error message you're seeing, and I can help debug it!



