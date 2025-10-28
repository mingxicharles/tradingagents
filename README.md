## Trading Agents LangGraph MVP

Runnable multi-agent trading research pipeline built with LangGraph. The system supervises three research agents (news, technical, fundamental) powered by Qwen models that can run either locally (via HuggingFace transformers) or through any OpenAI-compatible API. A dedicated orchestrator node coordinates fan-out, policy enforcement, optional debate, failure handling, and signal generation.

**Ideal for training**: Local model support enables easy fine-tuning and offline policy learning.

### Features
- LangGraph `StateGraph` with an explicit orchestrator (supervisor) node managing routing, retries, debates, and termination.
- Parallel agent fan-out using async gathers with evidence-required policy; missing evidence auto-downgrades proposals to neutral.
- Optional single-round debate when agent actions conflict, producing a debate transcript.
- Final `DecisionDTO` persisted to `signals/*.json`, designed as the fixed RL contract.
- **Local model support**: Run Qwen models locally using HuggingFace transformers (ideal for training/fine-tuning).
- Provider-agnostic API integration via environment-driven client (OpenRouter, OpenAI, etc.).
- Small CLI (`run.py`) to trigger the entire pipeline end-to-end.

### Quick Start
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure environment**
   - Using OpenAI (default when `OPENAI_API_KEY` is present):
     ```bash
     export OPENAI_API_KEY="sk-..."
     export OPENAI_MODEL="gpt-4o-mini"  # optional override
     ```
   - Using OpenRouter or another compatible provider:
     ```bash
     export OPENROUTER_API_KEY="sk-or-..."  # or OPENAI_API_KEY for other providers
     export OPENAI_MODEL="qwen/Qwen2.5-72B-Instruct"  # optional override
     export OPENROUTER_REFERER="https://yourapp.example.com"  # optional but recommended by OpenRouter
     export OPENROUTER_APP_TITLE="Trading Agents MVP"
     ```
3. **Run the pipeline**
   ```bash
   python run.py AAPL --horizon 1w --context "Post-earnings consolidation"
   ```

The CLI prints the orchestrated recommendation and writes the signal contract to `signals/<symbol>_<timestamp>.json`.

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
