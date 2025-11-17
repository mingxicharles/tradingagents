## 🚀 Super-Intelligent Trading Agents System

**Production-ready multi-agent trading analysis platform** for secondary market stocks, powered by LangGraph, specialized AI agents, and advanced orchestration. Completely restructured with enterprise-grade configuration, logging, testing, and data abstraction.

### 🎯 Trading Universe
- **Magnificent 7**: AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META
- **Additional 8**: JPM, BRK.B, V, UNH, PG, JNJ, WMT, XOM

### ✨ Key Features

**Phase 1 & 2 Complete:**
- ✅ **Unified Data Abstraction**: Single interface for live (yfinance), offline (parquet), and CSV data
- ✅ **Centralized Configuration**: Type-safe Pydantic-based config with validation
- ✅ **Structured Logging**: Production-ready JSON/colored logging with request tracking
- ✅ **Testing Infrastructure**: pytest framework with fixtures and unit tests
- ✅ **Bug-Free Models**: All missing classes and methods implemented
- ✅ **Clean Architecture**: Consolidated from dual orchestration to single LangGraph pattern

**Core Trading Features:**
- 🤖 **Multi-Agent Analysis**: News, Technical, and Fundamental agents working in parallel
- 🎯 **LangGraph Orchestration**: Sophisticated workflow with debate mechanism
- 📊 **Evidence-Based Decisions**: Policy enforcement requiring evidence for recommendations
- 💬 **Agent Debates**: Automatic conflict resolution through structured debates
- 📈 **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- 🔄 **Flexible LLM Support**: OpenAI, OpenRouter, or local models (Qwen)
- 💾 **Signal Persistence**: JSON signals ready for backtesting/execution

**Production-Ready:**
- ⚙️ Environment-based configuration
- 📝 Comprehensive logging with log levels
- ✅ Unit test coverage
- 🔧 Type-safe validation
- 🎨 Clean code structure
- 📚 Full documentation

### 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. **Run analysis** (examples)
   ```bash
   # Basic analysis
   python -m tradingagents.run AAPL

   # With specific date and horizon
   python -m tradingagents.run MSFT --date 2024-01-15 --horizon 1w

   # With market context
   python -m tradingagents.run NVDA --context "Post-earnings volatility"

   # Enable debug logging
   python -m tradingagents.run GOOGL --log-level DEBUG

   # Use offline data (no API calls)
   python -m tradingagents.run TSLA --offline-data
   ```

4. **View results**
   - Console output with detailed analysis
   - JSON signal saved to `signals/<symbol>_<timestamp>.json`
   - Logs in `logs/` directory (if configured)

### Using Local Models (Recommended for Training)

The pipeline supports running Qwen models locally using HuggingFace transformers, which is ideal for training and fine-tuning.

1. **Install additional dependencies**
   ```bash
   pip install transformers torch accelerate bitsandbytes
   ```

2. **Configure for local model** (choose based on GPU availability):
   
   **For GPU (CUDA) with quantization:**
   ```bash
   export USE_LOCAL_MODEL="true"
   export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"  # or any Qwen model
   ```
   
   **For smaller models on CPU:**
   ```bash
   export USE_LOCAL_MODEL="true"
   export LOCAL_MODEL="Qwen/Qwen2.5-1.5B-Instruct"  # smaller model
   ```

3. **First run downloads the model** (may take several minutes):
   ```bash
   python run.py AAPL --horizon 1w
   ```
   
   The first run will download the model from HuggingFace to `~/.cache/huggingface/`.

**Recommended local models for different hardware:**
- **High-end GPU (24GB+ VRAM)**: `Qwen/Qwen2.5-72B-Instruct` (best quality)
- **Mid-range GPU (12-24GB VRAM)**: `Qwen/Qwen2.5-14B-Instruct`
- **Standard GPU (8-12GB VRAM)**: `Qwen/Qwen2.5-7B-Instruct` (recommended)
- **Low-end GPU or CPU**: `Qwen/Qwen2.5-1.5B-Instruct` (faster but lower quality)

**Benefits of local models:**
- No API costs
- Full control over inference (can customize generation params)
- Easy to fine-tune on your own data
- Privacy (data never leaves your machine)
- Stable performance (no rate limits or API outages)

### Architecture
- `tradingagents/models.py`: Dataclasses defining `ResearchRequest`, `AgentProposal`, `DecisionDTO`, and `DebateTranscript`. `DecisionDTO` acts as the RL integration boundary.
- `tradingagents/llm.py`: Dual-mode LLM client supporting both local HuggingFace models (`LocalLLMClient`) and API providers (`APILLMClient`) with retry support.
- `tradingagents/agents/`: Base classes (`ResearchAgent`) plus JSON-parsing concrete agents (`JsonResearchAgent`) for news, technical, and fundamental research personas.
- `tradingagents/orchestrator.py`: Implements the LangGraph supervisor with explicit routing nodes:
  - `orchestrator`: Fans out to agents in parallel with retry logic
  - `policy_check`: Evaluates whether debate is needed (conditional routing)
  - `debate`: Runs debate rounds when conflicts exist
  - `finalize`: Produces DecisionDTO from weighted proposals
  - `write_signal`: Persists decision to signals/*.json
- `tradingagents/run.py`: Builds the graph, executes it asynchronously, and surfaces a simple CLI.
- `signals/`: Output directory for generated decision contracts (created automatically).

### RL-Ready Interfaces
- `DecisionDTO`: Immutable schema for final decisions, including agent proposals, evidence map, and optional debate transcript.
- `signals/*.json`: Persisted subset of the DTO (recommendation, confidence, evidence) serving as the contract for downstream RL or execution systems.

### Training/Fine-Tuning Preparation

With local models, you can easily fine-tune the agents on your own trading data:

1. **Collect training data**: Run the pipeline on historical symbols and gather `signals/*.json` outputs
2. **Prepare dataset**: Convert signals to HuggingFace dataset format
3. **Fine-tune using transformers**: Use the local model and apply standard training loops
   ```python
   from transformers import TrainingArguments, Trainer
   
   # Load your local model
   from tradingagents.llm import LocalLLMClient
   client = LocalLLMClient("Qwen/Qwen2.5-7B-Instruct")
   
   # Add training loop using your dataset
   ```
4. **Hot-swap models**: Change `LOCAL_MODEL` env var to use your fine-tuned model

The RL-compatible `DecisionDTO` and `signals/*.json` formats provide a fixed contract for reward shaping and training signal generation.

### Extending Toward RL
- Plug reinforcement learners after the `DecisionDTO` stage to evaluate or override signals.
- Add additional agent configurations in `config.py` (weights are already surfaced for value blending).
- Integrate tool-specific observability or reward shaping by consuming `policy_flags` and `errors` tracked in the state.
- Use local models for offline policy learning with your historical trading data.
