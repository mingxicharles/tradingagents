# 真实数据集成指南

## 🎉 新功能：真实市场数据获取

现在 mingxicharles 版本支持从 yfinance 获取真实市场数据！

### ✨ 改进内容

| 功能 | 之前 | 现在 |
|------|------|------|
| **数据来源** | LLM 幻想/编造 | yfinance 真实数据 |
| **技术指标** | LLM 猜测 | 实时计算（RSI, MACD等） |
| **公司信息** | LLM 记忆 | 最新财务数据 |
| **新闻** | 无 | 实时新闻标题 |
| **准确性** | ❌ 低 | ✅ 高 |

---

## 🚀 快速开始

### 步骤 1: 安装新依赖

```bash
cd tradingagents_test
pip install yfinance pandas
```

或重新安装所有依赖：

```bash
pip install -r requirements.txt
```

### 步骤 2: 运行（默认使用真实数据）

```bash
# 使用真实数据（推荐）
python run.py AAPL --horizon 1w

# 或使用本地 Qwen 模型
export USE_LOCAL_MODEL="true"
export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"
python run.py AAPL --horizon 1w
```

**输出示例：**
```
✓ 使用真实市场数据分析 AAPL

Decision: BUY (confidence 0.82)
Rationale:
technical: AAPL shows bullish momentum with RSI at 65.3, price above SMA20 ($178.50 vs $175.20)
news: Recent iPhone launch saw strong pre-orders, positive analyst sentiment
fundamental: Strong financials with P/E of 28.5, revenue growth of 8% YoY

Evidence by agent:
  - technical: Current price $179.50 broke above resistance at $175; RSI at 65.3 indicates bullish momentum; Volume 25% above average
  - news: Apple announces new product line expansion; 5 recent positive articles from major outlets
  - fundamental: Market cap $2.8T, P/E ratio 28.5 below sector average 30.2; Operating margin 25.3%

Signal written to signals/aapl_20241028T120000Z.json
```

---

## 📊 数据工具详解

### Technical Agent 获取的数据

```python
# 自动调用两个工具：
1. get_stock_price_data(symbol)
   - 90天历史价格（OHLCV）
   - 价格变化百分比（1日、5日、30日）
   - 成交量统计
   - 移动平均线（SMA20, SMA50）

2. get_technical_indicators(symbol)
   - RSI（相对强弱指标）
   - MACD（移动平均收敛发散）
   - 布林带（Bollinger Bands）
   - 综合交易信号
```

**真实数据示例：**
```
=== AAPL 技术指标 ===

移动平均线:
  - SMA10: $178.50 (上方)
  - SMA20: $175.20 (上方)
  - SMA50: $172.30 (上方)

RSI (相对强弱指标):
  - 当前值: 65.30
  - 解读: 中性区

MACD:
  - MACD线: 1.25
  - 信号线: 0.85
  - 柱状图: 0.40 (看涨)

综合信号:
  ✓ 短期均线向上排列 (看涨)
  ✓ MACD看涨交叉
```

### Fundamental Agent 获取的数据

```python
# 自动调用两个工具：
1. get_company_info(symbol)
   - 公司基本信息
   - 估值指标（P/E, P/B, 市值）
   - 财务数据（收入、利润率）
   - 分析师建议

2. get_stock_price_data(symbol)
   - 价格趋势验证
```

### News Agent 获取的数据

```python
# 自动调用两个工具：
1. get_recent_news(symbol, max_news=5)
   - 最近5条新闻
   - 新闻来源和时间
   - 标题摘要

2. get_stock_price_data(symbol)
   - 价格对新闻的反应
```

---

## 🔧 高级配置

### 选项1：禁用真实数据（回退到原始模式）

```bash
# 如果数据获取失败或想测试 LLM 原始能力
python run.py AAPL --horizon 1w --no-real-data
```

**输出：**
```
⚠ 仅使用 LLM 知识分析 AAPL（无真实数据）
```

### 选项2：在代码中控制

```python
from tradingagents.run import execute
from tradingagents.models import ResearchRequest

request = ResearchRequest(
    symbol="AAPL",
    horizon="1w",
    market_context="Post-earnings"
)

# 使用真实数据
result = await execute(request, use_real_data=True)

# 或不使用真实数据
result = await execute(request, use_real_data=False)
```

### 选项3：自定义数据工具

编辑 `tradingagents/agents/__init__.py`：

```python
# 为特定 agent 添加更多数据工具
if config.name == "technical":
    data_tools = [
        get_stock_price_data,
        get_technical_indicators,
        your_custom_tool,  # 添加自定义工具
    ]
```

---

## 📝 RL 训练建议

### 收集高质量训练数据

```python
# create_training_dataset.py
import asyncio
from datetime import datetime, timedelta
from tradingagents.run import execute
from tradingagents.models import ResearchRequest
import yfinance as yf

async def collect_with_labels():
    """收集带标签的训练数据"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    # 收集历史决策
    decisions = []
    
    for symbol in symbols:
        # 过去30天，每周一个决策点
        for days_ago in range(0, 90, 7):
            decision_date = datetime.now() - timedelta(days=days_ago+7)
            
            # 模拟在那个时间点做决策
            request = ResearchRequest(
                symbol=symbol,
                horizon="1w",
                market_context=f"Analysis on {decision_date.date()}"
            )
            
            # 获取决策（基于那个时间点的数据）
            result = await execute(request, use_real_data=True)
            decision = result["decision"]
            
            # 获取未来7天的真实回报
            ticker = yf.Ticker(symbol)
            future_date = decision_date + timedelta(days=7)
            
            hist = ticker.history(
                start=decision_date,
                end=future_date
            )
            
            if len(hist) >= 2:
                actual_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                
                # 计算奖励
                if decision.recommendation == "BUY":
                    reward = actual_return
                elif decision.recommendation == "SELL":
                    reward = -actual_return
                else:
                    reward = 0
                
                decisions.append({
                    "symbol": symbol,
                    "date": decision_date.isoformat(),
                    "recommendation": decision.recommendation,
                    "confidence": decision.confidence,
                    "evidence": decision.evidence,
                    "actual_return": actual_return,
                    "reward": reward
                })
                
                print(f"✓ {symbol} {decision_date.date()}: {decision.recommendation} → {actual_return:+.2%}")
            
            await asyncio.sleep(2)  # 避免API限制
    
    # 保存训练数据
    import json
    with open("training_data.json", "w") as f:
        json.dump(decisions, f, indent=2)
    
    print(f"\n收集了 {len(decisions)} 个训练样本")

if __name__ == "__main__":
    asyncio.run(collect_with_labels())
```

运行：
```bash
python create_training_dataset.py
```

这会生成 `training_data.json`，包含：
- ✅ 真实的市场数据
- ✅ Agent 的决策
- ✅ 实际的市场回报
- ✅ 计算好的奖励

---

## 🔍 数据质量验证

### 检查数据是否真实

```python
# verify_data.py
from tradingagents.dataflows.yfinance_tools import (
    get_stock_price_data,
    get_technical_indicators
)

# 获取数据
price_data = get_stock_price_data("AAPL")
tech_data = get_technical_indicators("AAPL")

print("价格数据：")
print(price_data)
print("\n技术指标：")
print(tech_data)

# 验证数据来自 yfinance
import yfinance as yf
ticker = yf.Ticker("AAPL")
current_price = ticker.history(period="1d")['Close'].iloc[-1]
print(f"\nyfinance 验证: ${current_price:.2f}")
```

---

## 📊 真实数据 vs 编造数据对比

### 实验：比较两种模式

```python
# compare_modes.py
import asyncio
from tradingagents.run import execute
from tradingagents.models import ResearchRequest

async def compare():
    request = ResearchRequest(
        symbol="AAPL",
        horizon="1w",
        market_context="Test comparison"
    )
    
    # 真实数据模式
    result_real = await execute(request, use_real_data=True)
    
    # 编造数据模式
    result_fake = await execute(request, use_real_data=False)
    
    print("=== 真实数据模式 ===")
    print(f"推荐: {result_real['decision'].recommendation}")
    print(f"信心: {result_real['decision'].confidence}")
    print("证据（前3条）:")
    for agent, evidence in list(result_real['decision'].evidence.items())[:3]:
        print(f"  {agent}: {evidence[0] if evidence else 'N/A'}")
    
    print("\n=== 编造数据模式 ===")
    print(f"推荐: {result_fake['decision'].recommendation}")
    print(f"信心: {result_fake['decision'].confidence}")
    print("证据（前3条）:")
    for agent, evidence in list(result_fake['decision'].evidence.items())[:3]:
        print(f"  {agent}: {evidence[0] if evidence else 'N/A'}")

asyncio.run(compare())
```

**预期差异：**
- 真实数据：引用具体数字（如"RSI 65.3"）
- 编造数据：模糊描述（如"RSI显示看涨"）

---

## ⚠️ 注意事项

### 1. API 限制
yfinance 是免费的，但有使用限制：
- 避免短时间内大量请求
- 建议每次请求间隔 2-5 秒

### 2. 数据延迟
- yfinance 数据有轻微延迟（通常 <15分钟）
- 不适合高频交易

### 3. 错误处理
如果数据获取失败，Agent 会收到错误信息：
```
获取 AAPL 数据时出错: [错误详情]
```
Agent 仍会尝试分析，但会标注数据不可靠

---

## 🎯 最佳实践

### 研究用途
```bash
# 1. 先验证数据
python verify_data.py

# 2. 收集多样化样本
python create_training_dataset.py

# 3. 定期更新数据
# (yfinance 会自动获取最新数据)
```

### 生产用途
```bash
# 使用真实数据做决策
python run.py AAPL --horizon 1w

# 保存信号
ls signals/  # 查看生成的决策
```

---

## 🤝 结合优势

现在你拥有：
- ✅ **mingxicharles 的简洁架构**（易于理解和修改）
- ✅ **TauricResearch 的真实数据**（准确可靠）
- ✅ **本地 Qwen 模型支持**（适合训练）
- ✅ **灵活的开关**（可选择是否使用真实数据）

这是最佳的研究配置！🎓

---

## 📚 下一步

1. 安装依赖：`pip install yfinance pandas`
2. 测试：`python run.py AAPL --horizon 1w`
3. 收集数据：运行 `create_training_dataset.py`
4. 开始 RL 训练！

有问题随时问！🚀

