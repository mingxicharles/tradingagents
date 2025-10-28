# OpenRouter 使用指南 / OpenRouter Usage Guide

OpenRouter 允许你使用多个 LLM 提供商（OpenAI, Anthropic, Google, Meta等）通过一个统一的 API。

OpenRouter allows you to use multiple LLM providers (OpenAI, Anthropic, Google, Meta, etc.) through a unified API.

---

## 快速开始 / Quick Start

### 方法 1: 命令行 / Method 1: Command Line

```bash
python run.py AAPL --horizon 1w \
  --openrouter-key "sk-or-v1-your-key" \
  --openrouter-model "anthropic/claude-3-opus"
```

### 方法 2: 环境变量 / Method 2: Environment Variables

```bash
# 设置环境变量 / Set environment variables
export OPENROUTER_API_KEY="sk-or-v1-your-key"
export OPENROUTER_MODEL="anthropic/claude-3-opus"

# 运行 / Run
python run.py AAPL --horizon 1w
```

### 方法 3: Python 代码 / Method 3: Python Code

```python
from tradingagents.config_api import set_openrouter_api_key
from tradingagents.run import execute
from tradingagents.models import ResearchRequest
import asyncio

# 配置 OpenRouter / Configure OpenRouter
set_openrouter_api_key(
    api_key="sk-or-v1-your-key",
    model="anthropic/claude-3-opus"
)

# 运行分析 / Run analysis
request = ResearchRequest(
    symbol="AAPL",
    horizon="1w",
    market_context="general"
)

result = asyncio.run(execute(request, use_real_data=True))
print(result["decision"].recommendation)
```

### 方法 4: .env 文件 / Method 4: .env File

创建 `.env` 文件：
```bash
USE_OPENROUTER=true
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=anthropic/claude-3-opus

# 可选 / Optional
OPENROUTER_REFERER=https://github.com/yourusername/tradingagents
OPENROUTER_APP_TITLE=TradingAgents
```

然后直接运行：
```bash
python run.py AAPL --horizon 1w
```

---

## 推荐模型 / Recommended Models

### 1. **Claude 3 Opus** (最强，最贵 / Most Powerful, Most Expensive)
```bash
--openrouter-model "anthropic/claude-3-opus"
```
- **优点 / Pros:** 最强的推理能力，最好的角色分工，高质量分析
- **缺点 / Cons:** 最贵 (~$15/$75 per 1M tokens)
- **适用 / Best For:** 生产环境，高质量决策

### 2. **Claude 3.5 Sonnet** (推荐 / Recommended)
```bash
--openrouter-model "anthropic/claude-3.5-sonnet"
```
- **优点 / Pros:** 接近 Opus 的质量，但便宜得多
- **缺点 / Cons:** 略慢
- **适用 / Best For:** 平衡性能和成本，日常使用

### 3. **GPT-4** (OpenAI)
```bash
--openrouter-model "openai/gpt-4"
```
- **优点 / Pros:** 优秀的推理，广泛测试
- **缺点 / Cons:** 较贵
- **适用 / Best For:** 需要 OpenAI 特性的场景

### 4. **GPT-4 Turbo**
```bash
--openrouter-model "openai/gpt-4-turbo"
```
- **优点 / Pros:** 更快，更便宜
- **缺点 / Cons:** 推理能力略弱于 GPT-4
- **适用 / Best For:** 大量API调用

### 5. **GPT-3.5 Turbo** (经济实惠 / Budget-Friendly)
```bash
--openrouter-model "openai/gpt-3.5-turbo"
```
- **优点 / Pros:** 非常便宜，快速
- **缺点 / Cons:** 推理能力较弱，角色分工可能不清晰
- **适用 / Best For:** 开发测试，大量数据收集

### 6. **Llama 2 70B** (开源 / Open Source)
```bash
--openrouter-model "meta-llama/llama-2-70b-chat"
```
- **优点 / Pros:** 开源，便宜
- **缺点 / Cons:** 性能不如商业模型
- **适用 / Best For:** 预算有限

### 7. **Google PaLM 2**
```bash
--openrouter-model "google/palm-2-chat-bison"
```
- **优点 / Pros:** Google 生态，特定任务优秀
- **缺点 / Cons:** 可用性可能有限
- **适用 / Best For:** Google 平台集成

---

## 价格对比 / Price Comparison

| 模型 / Model | Input ($/1M tokens) | Output ($/1M tokens) | 质量 / Quality |
|--------------|---------------------|----------------------|----------------|
| Claude 3 Opus | $15 | $75 | ⭐⭐⭐⭐⭐ |
| Claude 3.5 Sonnet | $3 | $15 | ⭐⭐⭐⭐⭐ |
| GPT-4 | $30 | $60 | ⭐⭐⭐⭐⭐ |
| GPT-4 Turbo | $10 | $30 | ⭐⭐⭐⭐ |
| GPT-3.5 Turbo | $0.50 | $1.50 | ⭐⭐⭐ |
| Llama 2 70B | $0.64 | $0.80 | ⭐⭐⭐ |

---

## 获取 OpenRouter API Key

1. 访问 [OpenRouter 官网](https://openrouter.ai/)
2. 注册账号
3. 前往 [API Keys](https://openrouter.ai/keys) 页面
4. 创建新的 API key
5. 复制 key（格式：`sk-or-v1-...`）

---

## 完整示例 / Complete Examples

### 示例 1: 使用 Claude 3.5 Sonnet 分析 AAPL

```bash
python run.py AAPL --horizon 1w \
  --openrouter-key "sk-or-v1-your-key" \
  --openrouter-model "anthropic/claude-3.5-sonnet"
```

**预期输出：**
```
✓ Using OpenRouter
  Model: anthropic/claude-3.5-sonnet
✓ Analyzing AAPL with real market data

Resolved LLM provider: openrouter
Using base URL: https://openrouter.ai/api/v1
Model: anthropic/claude-3.5-sonnet

Decision: BUY (confidence 0.85)
...
```

### 示例 2: 测试多个模型对比

```bash
# 测试 GPT-3.5 Turbo (便宜)
python run.py AAPL --openrouter-key "sk-or-v1-key" \
  --openrouter-model "openai/gpt-3.5-turbo"

# 测试 Claude 3.5 Sonnet (推荐)
python run.py AAPL --openrouter-key "sk-or-v1-key" \
  --openrouter-model "anthropic/claude-3.5-sonnet"

# 对比结果
```

### 示例 3: Python 脚本批量测试

```python
import asyncio
import os
from tradingagents.run import execute
from tradingagents.models import ResearchRequest

# 配置 OpenRouter
os.environ["USE_OPENROUTER"] = "true"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-your-key"

# 测试不同模型
models = [
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
]

symbols = ["AAPL", "MSFT", "GOOGL"]

async def test_model(model, symbol):
    os.environ["OPENROUTER_MODEL"] = model
    request = ResearchRequest(symbol=symbol, horizon="1w")
    result = await execute(request, use_real_data=True)
    return {
        "model": model,
        "symbol": symbol,
        "recommendation": result["decision"].recommendation,
        "confidence": result["decision"].confidence,
    }

async def main():
    tasks = []
    for model in models:
        for symbol in symbols:
            tasks.append(test_model(model, symbol))
    
    results = await asyncio.gather(*tasks)
    
    # 分析结果
    for result in results:
        print(f"{result['model']:30s} | {result['symbol']:5s} | "
              f"{result['recommendation']:4s} | {result['confidence']:.2f}")

asyncio.run(main())
```

---

## 高级配置 / Advanced Configuration

### 设置 Referer 和 Title（可选）

OpenRouter 使用这些信息来追踪 API 使用：

```bash
export OPENROUTER_REFERER="https://github.com/yourusername/tradingagents"
export OPENROUTER_APP_TITLE="TradingAgents"
```

或在代码中：
```python
import os
os.environ["OPENROUTER_REFERER"] = "https://github.com/yourusername/tradingagents"
os.environ["OPENROUTER_APP_TITLE"] = "TradingAgents"
```

### 检查当前配置

```python
from tradingagents.config_api import print_api_status

print_api_status()
```

**输出：**
```
============================================================
API Configuration Status
============================================================
Mode: OpenRouter API
Model: anthropic/claude-3.5-sonnet
API Key: ...abc123
============================================================
```

---

## 故障排除 / Troubleshooting

### 错误 1: "OPENROUTER_API_KEY environment variable not set"

**解决方案：**
```bash
# 方法 1: 命令行参数
python run.py AAPL --openrouter-key "sk-or-v1-your-key"

# 方法 2: 环境变量
export OPENROUTER_API_KEY="sk-or-v1-your-key"
python run.py AAPL
```

### 错误 2: "Invalid API key"

**检查：**
- API key 格式正确（以 `sk-or-v1-` 开头）
- 在 OpenRouter 网站上验证 key 有效
- 确保有足够的余额

### 错误 3: 模型不可用

**解决方案：**
```bash
# 查看 OpenRouter 支持的模型列表
# https://openrouter.ai/docs#models

# 使用可用的模型
python run.py AAPL --openrouter-model "openai/gpt-3.5-turbo"
```

### 错误 4: Rate limit exceeded

**解决方案：**
- 降低请求频率
- 升级 OpenRouter 账户
- 使用不同的模型

---

## 成本估算 / Cost Estimation

### 单次分析成本

假设使用 Claude 3.5 Sonnet：
- Input: ~3000 tokens (系统提示 + 数据 + 指令)
- Output: ~800 tokens (分析结果)
- 每个 agent: 3 个

**总成本：**
```
Input:  3 agents × 3000 tokens × $3/1M = $0.027
Output: 3 agents × 800 tokens × $15/1M = $0.036
Total per analysis: ~$0.063
```

### 批量收集成本（100个样本）

```
Claude 3.5 Sonnet: 100 × $0.063 = $6.30
GPT-3.5 Turbo:     100 × $0.008 = $0.80
GPT-4 Turbo:       100 × $0.120 = $12.00
```

**建议 / Recommendation:**
- **开发测试:** GPT-3.5 Turbo
- **数据收集:** Claude 3.5 Sonnet
- **生产环境:** Claude 3 Opus or GPT-4

---

## 与其他 API 对比 / Comparison with Other APIs

| 特性 / Feature | OpenRouter | OpenAI Direct | Local Model |
|----------------|------------|---------------|-------------|
| 多模型选择 | ✅ 20+ | ❌ OpenAI only | ✅ 任何模型 |
| 统一 API | ✅ | ❌ | ❌ |
| 价格 | 竞争力 | 标准 | 免费 |
| 速度 | 中等 | 快 | 取决于硬件 |
| 设置复杂度 | 简单 | 简单 | 复杂 |
| 隐私 | 云端 | 云端 | 本地 |

---

## 最佳实践 / Best Practices

### 1. **选择合适的模型**
- 开发/测试: GPT-3.5 Turbo
- 生产: Claude 3.5 Sonnet or GPT-4
- 预算紧张: Llama 2 70B

### 2. **监控成本**
```python
# 记录每次调用的 token 使用
import logging
logging.basicConfig(level=logging.INFO)
```

### 3. **缓存结果**
```python
# 避免重复分析同一 symbol
cache = {}
if symbol in cache:
    return cache[symbol]
```

### 4. **错误处理**
```python
try:
    result = await execute(request)
except RuntimeError as e:
    # 切换到备用模型
    os.environ["OPENROUTER_MODEL"] = "openai/gpt-3.5-turbo"
    result = await execute(request)
```

---

## 总结 / Summary

**OpenRouter 的优势：**
- ✅ 一个 API key 访问多个模型
- ✅ 统一的接口
- ✅ 竞争力的价格
- ✅ 简单的集成

**推荐配置：**
```bash
# 日常使用 / Daily Use
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# 预算有限 / Budget Limited
OPENROUTER_MODEL=openai/gpt-3.5-turbo

# 最高质量 / Highest Quality
OPENROUTER_MODEL=anthropic/claude-3-opus
```

**快速测试：**
```bash
python run.py AAPL --horizon 1w \
  --openrouter-key "your-key" \
  --openrouter-model "anthropic/claude-3.5-sonnet"
```

祝你使用愉快！🚀

Happy trading! 🚀

