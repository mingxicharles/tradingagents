# Agent 角色分工问题诊断与解决方案

## 问题诊断

### 原始问题
三个 agents（technical, fundamental, news）分析的内容都差不多，没有各司其职。

### 根本原因分析

#### 1. **System Prompt 太弱** ❌
```python
# 原来的 system prompt
"You are a technical analyst. Synthesize price action..."
```
- 太简短，LLM 容易忽略
- 没有明确说"不要做什么"
- 没有强调专业边界

#### 2. **User Prompt 完全相同** ❌
```python
# 所有agents收到的user prompt完全一样！
"Based on the REAL MARKET DATA above, produce a JSON..."
```
- 没有角色特定的指令
- 没有告诉agent应该专注于什么领域
- 没有明确边界

#### 3. **数据分配是对的，但缺少强调** ⚠️
```python
# 数据分配（正确）：
technical: [get_stock_price_data, get_technical_indicators]
fundamental: [get_company_info, get_stock_price_data]
news: [get_recent_news, get_stock_price_data]
```
但是 prompt 没有说"**只用你获取的数据**"。

---

## 解决方案

### Level 1: 增强 System Prompts

**修改文件：** `tradingagents/config.py`

#### Technical Analyst
```python
"You are a TECHNICAL ANALYST specializing in price action and indicators.\n\n"
"YOUR EXCLUSIVE FOCUS:\n"
"- Price trends, support/resistance levels\n"
"- Technical indicators (RSI, MACD, Bollinger Bands, moving averages)\n"
"- Volume patterns and momentum\n"
"- Chart patterns and breakouts\n\n"
"YOU MUST NOT analyze:\n"
"- News headlines or sentiment - that's news analyst's job\n"
"- Company fundamentals (earnings, revenue, P/E) - that's fundamental analyst's job\n\n"
"Base your recommendation ONLY on technical signals and price action."
```

#### Fundamental Analyst
```python
"You are a FUNDAMENTAL ANALYST specializing in company valuation and financials.\n\n"
"YOUR EXCLUSIVE FOCUS:\n"
"- Valuation metrics (P/E ratio, market cap, P/B ratio)\n"
"- Financial health (revenue, earnings, profit margins, debt)\n"
"- Business fundamentals and competitive position\n"
"- Long-term growth prospects\n\n"
"YOU MUST NOT analyze:\n"
"- Technical indicators (RSI, MACD, moving averages) - that's technical analyst's job\n"
"- Recent news or sentiment - that's news analyst's job\n\n"
"Base your recommendation ONLY on fundamental business metrics and valuation."
```

#### News Analyst
```python
"You are a NEWS AND SENTIMENT ANALYST specializing in market-moving events.\n\n"
"YOUR EXCLUSIVE FOCUS:\n"
"- Recent news headlines and their market impact\n"
"- Regulatory announcements and policy changes\n"
"- Sentiment shifts from news events\n"
"- Macro economic news\n\n"
"YOU MUST NOT analyze:\n"
"- Technical indicators (RSI, MACD, moving averages) - that's technical analyst's job\n"
"- Financial ratios (P/E, revenue, margins) - that's fundamental analyst's job\n\n"
"Base your recommendation ONLY on news sentiment and event analysis."
```

**关键改进：**
- ✅ 明确"YOUR EXCLUSIVE FOCUS"
- ✅ 明确"YOU MUST NOT analyze"
- ✅ 强调"ONLY"

---

### Level 2: 角色特定的 User Prompts

**修改文件：** `tradingagents/agents/data_agent.py`

#### 新增方法：`_get_role_specific_instructions()`

```python
def _get_role_specific_instructions(self) -> str:
    """Get instructions specific to this agent's role"""
    if self.name == "technical":
        return textwrap.dedent("""
        YOUR ANALYSIS SCOPE (Technical Analyst):
        ==========================================
        ANALYZE ONLY:
        - Price action: trends, support/resistance, breakouts
        - Technical indicators: RSI, MACD, Bollinger Bands, Moving Averages
        - Volume patterns and momentum signals
        - Chart patterns and technical setups
        
        IGNORE:
        - News headlines or sentiment (not your domain)
        - Company fundamentals like P/E, revenue, earnings (not your domain)
        
        Your evidence MUST cite specific technical data:
        - Example: "RSI at 65.3 shows momentum but not overbought"
        - Example: "Price broke $175 resistance with 2x normal volume"
        """).strip()
```

**每个 agent 现在收到不同的指令！**

---

### Level 3: 在 base.py 中也添加角色区分

**修改文件：** `tradingagents/agents/base.py`

```python
def _get_role_specific_instructions(self) -> str:
    if self.name == "technical":
        return "YOUR ROLE: Technical Analyst\nFOCUS: Price action, RSI, MACD, volume\nAVOID: News, P/E ratio"
    elif self.name == "fundamental":
        return "YOUR ROLE: Fundamental Analyst\nFOCUS: P/E, revenue, margins\nAVOID: RSI, MACD, news"
    elif self.name == "news":
        return "YOUR ROLE: News Analyst\nFOCUS: Headlines, events, sentiment\nAVOID: RSI, P/E ratio"
```

---

## 测试验证

### 运行角色分工测试
```bash
python test_agent_roles.py
```

**测试内容：**
1. 运行一次分析（如 AAPL）
2. 分析每个 agent 的 evidence 和 thesis
3. 统计关键词：
   - Technical 关键词：RSI, MACD, moving average, volume, breakout
   - Fundamental 关键词：P/E, revenue, earnings, margin, valuation
   - News 关键词：news, headline, announcement, sentiment

**预期结果：**
```
AGENT ANALYSIS:

TECHNICAL AGENT:
  Evidence:
    1. RSI at 65.3 shows momentum but not overbought
    2. Price broke $175 resistance with 2x normal volume
  
  Keyword Analysis:
    Technical keywords: 5    ✓
    Fundamental keywords: 0  ✓
    News keywords: 0         ✓

FUNDAMENTAL AGENT:
  Evidence:
    1. P/E ratio of 28 is reasonable for growth profile
    2. Revenue grew 15% YoY with improving margins
  
  Keyword Analysis:
    Technical keywords: 0    ✓
    Fundamental keywords: 6  ✓
    News keywords: 0         ✓

NEWS AGENT:
  Evidence:
    1. Recent product launch received positive media coverage
    2. No major negative headlines in past week
  
  Keyword Analysis:
    Technical keywords: 0    ✓
    Fundamental keywords: 0  ✓
    News keywords: 4         ✓

✓ All agents appear to be focused on their respective domains!
```

---

## 如果问题仍然存在

### 可能的原因

#### 1. **LLM 模型太弱**
- GPT-3.5 可能不够强，无法严格遵循角色边界
- **解决方案**：升级到 GPT-4 或更强的模型

#### 2. **数据本身重叠**
- 所有 agents 都获取 `get_stock_price_data`
- Price data 本身包含价格信息，可能被所有人引用
- **解决方案**：
  ```python
  # 让fundamental和news agent不获取price data
  if config.name == "fundamental":
      data_tools = [get_company_info]  # 只获取公司信息
  elif config.name == "news":
      data_tools = [get_recent_news]   # 只获取新闻
  ```

#### 3. **yfinance 数据质量**
- `get_company_info()` 可能没有返回足够的基本面数据
- `get_recent_news()` 可能新闻太少
- **解决方案**：检查数据质量
  ```python
  from tradingagents.dataflows.yfinance_tools import *
  print(get_company_info("AAPL"))
  print(get_recent_news("AAPL"))
  ```

#### 4. **Temperature 设置**
- Temperature 太低可能导致所有agents给出类似回答
- **解决方案**：增加 temperature
  ```python
  # In llm.py or agents code
  temperature = 0.8  # 增加多样性
  ```

---

## 进一步的增强方案

### Option 1: 硬性过滤数据
在数据工具中过滤输出：

```python
def get_technical_indicators(symbol, days_back=90):
    """Only return technical data, no fundamentals"""
    # ... calculate indicators ...
    
    # 只返回技术指标，不包含价格的基本信息
    return f"""
    Technical Indicators for {symbol}:
    - RSI: {rsi}
    - MACD: {macd}
    - Bollinger Bands: {bb}
    
    NOTE: This is technical data only. 
    Do NOT mention P/E ratio, earnings, or news.
    """
```

### Option 2: 后处理验证
在 orchestrator 中验证 agent 输出：

```python
def _validate_agent_output(self, agent_name, proposal):
    """Validate that agent stayed in their domain"""
    evidence_text = " ".join(proposal.evidence).lower()
    
    if agent_name == "technical":
        if any(word in evidence_text for word in ["p/e", "earnings", "news"]):
            # Re-prompt the agent or penalize
            proposal.conviction *= 0.8  # Reduce confidence
```

### Option 3: 更强的 prompt engineering
使用 few-shot examples：

```python
system_prompt = """
You are a TECHNICAL ANALYST.

Example of GOOD technical analysis:
- "RSI at 65 indicates upward momentum without overbought conditions"
- "Price broke $175 resistance with volume 2x above average"

Example of BAD technical analysis (NOT your job):
- "P/E ratio suggests stock is undervalued" ← This is fundamental analyst's job
- "Recent news about product launch is positive" ← This is news analyst's job

Your evidence must ONLY use technical indicators and price action.
"""
```

---

## 总结

### 改进清单

- ✅ **增强 System Prompts** - 明确"做什么"和"不做什么"
- ✅ **添加角色特定指令** - 每个 agent 收到不同的 user prompt
- ✅ **在 base.py 中也添加** - 确保非数据感知 agent 也有角色区分
- ✅ **创建测试脚本** - `test_agent_roles.py` 验证分工

### 诊断流程

1. 运行 `python test_agent_roles.py`
2. 查看每个 agent 的 evidence 关键词统计
3. 如果仍有重叠：
   - 检查数据工具输出（`get_company_info`, `get_technical_indicators`）
   - 考虑升级 LLM 模型
   - 考虑移除 price data 的重叠
   - 增加 temperature

### 预期效果

**Technical Agent:**
```
Evidence:
- RSI: 65.32 indicates momentum
- MACD crossover suggests bullish trend
- Volume spike 2.3x confirms breakout
```

**Fundamental Agent:**
```
Evidence:
- P/E ratio of 28 vs industry 35 shows value
- Revenue growth 15% YoY exceeds expectations
- Operating margin expanded to 28%
```

**News Agent:**
```
Evidence:
- Product launch announcement received positively
- No regulatory concerns flagged
- Analyst upgrades following earnings
```

**完全不同的分析角度！** 🎯


