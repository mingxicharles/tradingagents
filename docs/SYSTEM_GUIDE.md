# Trading Agents System Guide

**Complete guide to LLM-driven multi-agent trading analysis system**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Workflows](#workflows)
4. [Key Data Models](#key-data-models)
5. [Visual Reference](#visual-reference)
6. [Usage Examples](#usage-examples)

---

## System Overview

### What This System Does

An LLM-powered multi-agent trading analysis platform that:
- Coordinates 3 specialized agents (News, Technical, Fundamental)
- Generates trading recommendations (BUY/SELL/HOLD)
- Supports debate mechanism for conflicting recommendations
- Provides complete trajectory tracking for RL training

### Dual Architecture

**Orchestrator (Production - 90% of traffic)**
- Rule-based LangGraph workflow
- Fast (3-5s), cheap ($0.10/analysis)
- Deterministic and auditable
- Used by: `run.py`

**Controller (Research - 10% of traffic)**
- LLM-driven decision making
- Flexible (7-10s), costlier ($0.40/analysis)
- Adaptive and exploratory
- Used by: `batch_test.py`

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────┐
│              Entry Points                       │
│  run.py (CLI)      batch_test.py (Batch)       │
└─────────────┬───────────────────┬───────────────┘
              │                   │
      ┌───────▼────────┐  ┌──────▼──────┐
      │  Orchestrator  │  │  Controller │
      │  (LangGraph)   │  │ (LLM-Driven)│
      └───────┬────────┘  └──────┬──────┘
              │                   │
              └──────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  News   │    │Technical│    │Fundamental│
    │  Agent  │    │  Agent  │    │   Agent   │
    └────┬────┘    └────┬────┘    └────┬─────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                ┌───────▼────────┐
                │   LLM Client   │
                │ Local + API    │
                └───────┬────────┘
                        │
                ┌───────▼────────┐
                │  Data Sources  │
                │ yfinance + CSV │
                └────────────────┘
```

### Three Specialized Agents

**News Agent**
- Role: Sentiment & event analysis
- Data: News feeds, analyst ratings
- Focus: Catalysts, sentiment shifts, regulatory events

**Technical Agent**
- Role: Price action & indicators
- Data: OHLCV, RSI, MACD, moving averages
- Focus: Chart patterns, momentum, support/resistance

**Fundamental Agent**
- Role: Valuation & financials
- Data: P/E ratio, revenue, margins
- Focus: Business quality, growth metrics, competitive position

---

## Workflows

### Orchestrator Workflow (LangGraph)

```
START
  ↓
┌─────────────────────────────┐
│ 1. Orchestrator Node        │
│    - Optional: LLM selects   │
│      agents (supervisor)     │
│    - Execute agents (parallel)│
│    - Gather proposals        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 2. Policy Check Node        │
│    - Detect conflicts        │
│      (BUY vs SELL)          │
│    - Decide: debate or not   │
└──────────────┬──────────────┘
               ↓
        ┌──────┴──────┐
        │             │
    Conflict      No Conflict
        │             │
        ▼             │
┌──────────────┐      │
│ 3. Debate    │      │
│    - Multi-  │      │
│      round   │      │
│    - Track   │      │
│      changes │      │
└──────┬───────┘      │
       │              │
       └──────┬───────┘
              ↓
┌─────────────────────────────┐
│ 4. Finalize Node            │
│    - Weighted aggregation    │
│    - Calculate confidence    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 5. Write Signal Node        │
│    - Save to JSON file       │
└──────────────┬──────────────┘
               ↓
              END

Duration: 3-5 seconds
Cost: $0.10 per analysis
```

### Controller Workflow (LLM-Driven)

```
START
  ↓
1. Create Plan (LLM decides which agents)
  ↓
2. Fetch Data (controller sees everything)
  ↓
3. Execute Agents (with dynamic prompts)
  ↓
4. Evaluate Results (LLM detects conflicts)
  ↓
5. [Optional] Conduct Debate (LLM moderated)
  ↓
6. Make Final Decision (LLM synthesis)
  ↓
Output: FinalDecision + Trajectory
  ↓
END

Duration: 7-10 seconds
Cost: $0.40 per analysis
```

### Debate Mechanism

```
Initial: News=BUY, Tech=SELL, Fund=HOLD
         (Conflict detected!)
              ↓
┌─────────────────────────────┐
│ Debate Round 1              │
│ - Show opposing arguments    │
│ - Agents revise positions    │
│ - Track changes              │
└──────────────┬──────────────┘
              ↓
  News: BUY (0.85→0.75)  ← reduced conviction
  Tech: SELL→HOLD        ← changed action
  Fund: HOLD (unchanged)
              ↓
       Converged!
       (No more BUY vs SELL)
```

---

## Key Data Models

### Input: AnalysisRequest

```python
AnalysisRequest(
    symbol="AAPL",
    horizon="1d",           # "1d", "1w", "1m"
    market_context="...",   # Optional context
    trade_date="2025-11-13" # Defaults to today
)
```

### Agent Output: AgentProposal

```python
AgentProposal(
    agent="technical",
    action="BUY",           # BUY/SELL/HOLD
    conviction=0.78,        # 0.0-1.0
    thesis="Bullish MACD crossover...",
    evidence=[
        "MACD crossed above signal line",
        "RSI at 62, room for upside",
        "Volume confirms buying interest"
    ],
    caveats=["Near upper Bollinger Band"],
    neutral=False
)
```

### Orchestrator Output: DecisionDTO

```python
DecisionDTO(
    symbol="AAPL",
    horizon="1d",
    recommendation="BUY",
    confidence=0.68,
    rationale="...",
    evidence={
        "news": ["Analyst upgrade", "Revenue beat"],
        "technical": ["MACD bullish", "RSI 62"],
        "fundamental": ["P/E reasonable", "Margins strong"]
    },
    proposals={...},  # All agent proposals
    debate=None       # Or DebateTranscript if debate occurred
)
```

### Controller Output: FinalDecision

```python
FinalDecision(
    symbol="AAPL",
    recommendation="BUY",
    confidence=0.75,
    rationale="Strong consensus...",
    key_factors=[
        "Analyst upgrade with $220 target",
        "MACD bullish crossover",
        "P/E reasonable at 30"
    ],
    risks=[
        "Overbought RSI risk",
        "Premium valuation"
    ],
    agent_weights={
        "technical": 0.40,
        "news": 0.30,
        "fundamental": 0.30
    },
    agent_proposals={...},
    evaluation={...}
)
```

### Conviction Scale

```
0.90-1.00  ████████████████████  Exceptional
0.75-0.89  ████████████████      High
0.60-0.74  ████████████          Moderate
0.45-0.59  ████████              Low
0.20-0.44  ████                  Very Low
0.00-0.19  █                     Minimal
```

---

## Visual Reference

### Orchestrator State Flow

```
Initial State
┌────────────────────┐
│ request: ✓         │
│ proposals: {}      │
│ debate: None       │
│ decision: None     │
└────────────────────┘
         ↓
After Orchestrator
┌────────────────────┐
│ request: ✓         │
│ proposals: {       │
│   news: ✓,         │
│   tech: ✓,         │
│   fund: ✓          │
│ }                  │
│ debate: None       │
│ decision: None     │
└────────────────────┘
         ↓
Final State
┌────────────────────┐
│ request: ✓         │
│ proposals: ✓       │
│ debate: ✓ (if any) │
│ decision: ✓        │
│ signal_path: ✓     │
└────────────────────┘
```

### Timeline Example (Orchestrator)

```
T=0ms     User Request (AAPL, 1d)
T=500ms   Supervisor selects agents (optional LLM)
T=1000ms  Agents start (parallel execution)
          ├─ News Agent     ████████████
          ├─ Tech Agent       ████████████
          └─ Fund Agent         ████████████
T=3000ms  All proposals gathered
T=3010ms  Policy check (conflict detection)
T=3020ms  Finalize (weighted aggregation)
T=3030ms  Write signal (JSON output)
END       Total: 3.03 seconds
```

### Orchestrator vs Controller

```
┌──────────────────┬────────────────┬────────────────┐
│ Aspect           │ Orchestrator   │ Controller     │
├──────────────────┼────────────────┼────────────────┤
│ Workflow         │ Fixed graph    │ LLM decides    │
│ LLM Calls        │ 3-5            │ 7-13           │
│ Duration         │ 3-5s           │ 7-10s          │
│ Cost             │ $0.10          │ $0.40          │
│ Determinism      │ High           │ Low            │
│ Flexibility      │ Low            │ High           │
│ Production Ready │ ✓              │ Research       │
│ Output           │ DecisionDTO    │ FinalDecision  │
│                  │ + Signal JSON  │ + Trajectory   │
└──────────────────┴────────────────┴────────────────┘
```

---

## Usage Examples

### CLI (Orchestrator)

```bash
# Basic usage
python run.py AAPL --horizon 1d

# With specific date
python run.py AAPL --date 2024-11-15

# With context
python run.py AAPL --horizon 1w --context "Post-earnings"

# With local model
python run.py AAPL --local-model "Qwen/Qwen2.5-7B-Instruct"

# With OpenRouter
python run.py AAPL --openrouter-key "sk-or-..." --openrouter-model "openai/gpt-4"
```

### Python API (Orchestrator)

```python
from tradingagents import execute
from tradingagents.models import AnalysisRequest

request = AnalysisRequest(
    symbol="AAPL",
    horizon="1d",
    market_context="Tech sector rotation",
    trade_date="2025-11-13"
)

result = await execute(request, use_real_data=True)
decision = result["decision"]

print(f"Recommendation: {decision.recommendation}")
print(f"Confidence: {decision.confidence}")
print(f"Rationale: {decision.rationale}")
```

### Batch Testing (Controller)

```bash
# Run batch tests on CSV data
python batch_test.py --csv data.csv --max-tests 50

# Filter by symbol
python batch_test.py --csv data.csv --symbol AAPL --verbose

# Quick test
python quick_batch_test.py
```

### Output Files

**Signal Files** (`signals/`)
```json
{
  "symbol": "AAPL",
  "recommendation": "BUY",
  "confidence": 0.68,
  "evidence": {
    "news": ["..."],
    "technical": ["..."],
    "fundamental": ["..."]
  },
  "timestamp": "2025-11-13T14:30:22Z"
}
```

**Trajectory Files** (`trajectories/`) - From Controller
```json
{
  "steps": [
    {
      "step": "plan",
      "timestamp": "...",
      "data": {...}
    },
    {
      "step": "agent_execution",
      "data": {...}
    },
    {
      "step": "final_decision",
      "data": {...}
    }
  ],
  "total_steps": 5
}
```

---

## Configuration

### LLM Providers

**Local Models (HuggingFace)**
```bash
export USE_LOCAL_MODEL="true"
export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

**OpenAI**
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"  # Optional
```

**OpenRouter**
```bash
export OPENROUTER_API_KEY="sk-or-..."
export OPENROUTER_MODEL="openai/gpt-3.5-turbo"
```

### Data Sources

**Live Market Data** (default)
- Uses `yfinance` for real-time data
- Fetches: prices, news, indicators, company info

**Offline Data**
```bash
python run.py AAPL --offline-data
```

**CSV Batch Data**
```bash
python batch_test.py --csv path/to/data.csv
```

---

## Key Design Decisions

### Why Dual Architecture?

**Orchestrator (Rule-Based)**
- Industry standard (used by Uber, LinkedIn, Elastic)
- Production-ready: fast, cheap, deterministic
- Matches LangGraph best practices
- 90% of use cases

**Controller (LLM-Driven)**
- Cutting-edge research approach
- Adaptive to novel situations
- Complete trajectory tracking for RL
- 10% of use cases (exploration, high-value decisions)

### Why Three Agents?

Specialized expertise prevents overlap:
- **News:** Catalysts and sentiment (no technical indicators)
- **Technical:** Price action and indicators (no news/fundamentals)
- **Fundamental:** Valuation and financials (no technicals/news)

Independent analysis → debate if conflicts → higher quality decisions

### Why Debate Mechanism?

Research shows multi-round deliberation improves LLM outputs:
- Agents reconsider positions with peer evidence
- Often leads to convergence (SELL → HOLD)
- Tracked position changes valuable for RL training
- Real debate transcripts show conviction adjustments

---

## Performance & Costs

### Latency

| Component | Orchestrator | Controller |
|-----------|--------------|------------|
| Agent Selection | 500ms (optional) | 800ms (LLM) |
| Agent Execution | 2500ms (parallel) | 2500ms |
| Evaluation | 10ms (rules) | 700ms (LLM) |
| Debate (if needed) | 2000ms | 3000ms |
| Finalization | 10ms | 800ms (LLM) |
| **Total (no debate)** | **3s** | **7s** |
| **Total (with debate)** | **5s** | **10s** |

### Costs (per 1000 analyses/day)

| System | Per Analysis | Daily | Annual |
|--------|--------------|-------|--------|
| **Orchestrator** | $0.10 | $100 | $36,500 |
| **Controller** | $0.40 | $400 | $146,000 |
| **Hybrid (90/10)** | $0.13 | $130 | $47,450 |

*Assumes GPT-4o-mini. Local models: $0 variable cost.*

---

## File Structure

```
tradingagents/
├── tradingagents/          # Main package
│   ├── models.py           # All data structures
│   ├── orchestrator.py     # LangGraph workflow
│   ├── controller.py       # LLM-driven workflow
│   ├── run.py              # CLI entry point
│   ├── llm.py              # LLM clients (Local + API)
│   ├── config.py           # Agent configurations
│   ├── agents/             # Agent implementations
│   │   ├── base.py
│   │   └── simple_agent.py
│   └── dataflows/          # Data sources
│       ├── yfinance_tools.py
│       ├── csv_data_loader.py
│       └── local_data.py
│
├── docs/                   # Documentation
│   ├── SYSTEM_GUIDE.md     # This file
│   ├── ARCHITECTURE_RECOMMENDATIONS.md
│   └── CODEBASE_ANALYSIS.md
│
├── signals/                # Output: Signal JSON files
├── trajectories/           # Output: Trajectory files
├── batch_test_results/     # Output: Test results
│
├── batch_test.py           # Batch testing script
├── requirements.txt        # Dependencies
└── README.md               # Project README
```

---

## Quick Reference

### Common Commands

```bash
# Run analysis
python run.py AAPL

# Batch test
python batch_test.py --csv data.csv

# Generate offline data
python generate_offline_data.py

# Debug data flow
python debug_data_flow.py
```

### Key Imports

```python
# Execute analysis
from tradingagents import execute
from tradingagents.models import AnalysisRequest, DecisionDTO

# Build orchestrator
from tradingagents.orchestrator import TradingOrchestrator
from tradingagents.agents import build_agents

# Build controller
from tradingagents.controller import LLMController

# LLM client
from tradingagents.llm import build_client
```

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
USE_LOCAL_MODEL=true
LOCAL_MODEL=Qwen/Qwen2.5-7B-Instruct

# Optional
OPENAI_MODEL=gpt-4o-mini
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

---

## Troubleshooting

### "API not configured"
Set API key:
```bash
export OPENAI_API_KEY="sk-..."
# OR
python run.py AAPL --api-key "sk-..."
```

### "LLM request failed"
Check:
1. API key is valid
2. Internet connection
3. Rate limits not exceeded
4. Model name is correct

### "No data available"
For offline data:
```bash
python generate_offline_data.py
python run.py AAPL --offline-data
```

### Slow performance
Use local model:
```bash
export USE_LOCAL_MODEL=true
export LOCAL_MODEL="Qwen/Qwen2.5-1.5B-Instruct"  # Smaller = faster
```

---

## Next Steps

1. **Production Deployment:** See `ARCHITECTURE_RECOMMENDATIONS.md`
2. **Bug Fixes Applied:** See `CODEBASE_ANALYSIS.md`
3. **Extend System:** Add new agents in `tradingagents/agents/`
4. **RL Training:** Use trajectory files from controller
5. **Fine-tune Models:** Use signal files as training data

---

**For detailed architecture recommendations and industry best practices, see `ARCHITECTURE_RECOMMENDATIONS.md`**

**For bug fixes and code improvements, see `CODEBASE_ANALYSIS.md`**
