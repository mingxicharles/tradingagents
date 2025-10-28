# 🚀 真实数据功能快速开始

## 一分钟上手

### 1. 安装依赖

```bash
cd tradingagents_test

# Windows
setup_real_data.bat

# Linux/Mac
pip install yfinance pandas
```

### 2. 测试数据工具

```bash
python test_real_data.py
```

选择 `1` 测试数据工具，会显示：
- ✅ 真实的 AAPL 股价数据
- ✅ 计算的技术指标（RSI, MACD等）
- ✅ 公司财务信息
- ✅ 最新新闻

### 3. 运行分析

```bash
# 使用真实数据（默认）
python run.py AAPL --horizon 1w

# Windows 快捷方式
run_local.bat AAPL --horizon 1w
```

**预期输出：**
```
✓ 使用真实市场数据分析 AAPL

Decision: BUY (confidence 0.82)
Rationale:
technical: Current RSI 65.3 shows bullish momentum, price $179.50 above SMA20 $175.20
...

Evidence by agent:
  - technical: RSI at 65.3 indicates bullish momentum without overbought; Price broke $175 resistance; Volume 25% above average
  - fundamental: P/E ratio 28.5 below sector average; Revenue growth 8% YoY; Operating margin 25.3%
  - news: 3 positive analyst upgrades this week; New product launch shows strong demand
```

---

## 📊 功能对比

| 操作 | 使用真实数据 | 不使用真实数据 |
|------|------------|--------------|
| 命令 | `python run.py AAPL` | `python run.py AAPL --no-real-data` |
| 数据来源 | yfinance API | LLM 知识 |
| 证据准确性 | ✅ 高 | ❌ 低（可能编造） |
| 引用具体数字 | ✅ 是 | ❌ 模糊 |
| 适用场景 | RL训练/真实交易 | 测试/原型 |

---

## 🧪 对比测试

运行对比测试查看差异：

```bash
python test_real_data.py
# 选择 3: 对比真实 vs 编造数据
```

**真实数据证据示例：**
```
"RSI currently at 65.3, indicating bullish momentum"
"Price broke above $175 resistance level"
"Volume increased 25% compared to 20-day average"
```

**编造数据证据示例：**
```
"RSI shows bullish momentum"
"Price action indicates strength"
"Volume trending higher"
```

明显区别：真实数据有**具体数字**！

---

## 🎯 RL 训练工作流

### 步骤 1: 收集真实数据样本

```bash
# 使用真实数据运行多次
for symbol in AAPL MSFT GOOGL TSLA NVDA
do
    python run.py $symbol --horizon 1w
    sleep 3
done

# 查看生成的信号
ls signals/
```

### 步骤 2: 标注回报

```python
# 读取信号文件
import json
import yfinance as yf
from datetime import timedelta

with open("signals/aapl_20241028T120000Z.json") as f:
    decision = json.load(f)

# 获取未来回报
symbol = decision["symbol"]
decision_time = decision["generated_at"]
# ... 计算实际回报
```

### 步骤 3: 训练模型

有真实数据支撑的训练样本 → 更可靠的 RL 训练！

---

## ⚙️ 配置选项

### 在代码中控制

```python
from tradingagents.run import execute
from tradingagents.models import ResearchRequest

# 创建请求
request = ResearchRequest(
    symbol="AAPL",
    horizon="1w",
    market_context="Post-earnings"
)

# 选择模式
result = await execute(request, use_real_data=True)  # 真实数据
# 或
result = await execute(request, use_real_data=False)  # 编造数据
```

### 环境变量

```bash
# 设置本地模型
export USE_LOCAL_MODEL="true"
export LOCAL_MODEL="Qwen/Qwen2.5-7B-Instruct"

# 运行
python run.py AAPL --horizon 1w
```

---

## 📚 工具详解

### Technical Agent 使用的工具

1. **get_stock_price_data(symbol)**
   - 90天历史价格
   - 价格变化统计
   - 移动平均线

2. **get_technical_indicators(symbol)**
   - RSI, MACD, 布林带
   - 交易信号

### Fundamental Agent 使用的工具

1. **get_company_info(symbol)**
   - 公司信息
   - 估值指标
   - 财务数据

2. **get_stock_price_data(symbol)**
   - 价格验证

### News Agent 使用的工具

1. **get_recent_news(symbol)**
   - 最新新闻标题
   - 来源和时间

2. **get_stock_price_data(symbol)**
   - 价格对新闻的反应

---

## ✅ 验证安装

```bash
# 测试数据获取
python -c "from tradingagents.dataflows.yfinance_tools import get_stock_price_data; print(get_stock_price_data('AAPL')[:200])"

# 完整测试
python test_real_data.py
```

---

## 🎉 现在你拥有

- ✅ **简洁的架构**（mingxicharles）
- ✅ **真实的数据**（yfinance）
- ✅ **本地模型支持**（Qwen）
- ✅ **灵活的开关**（可选数据源）

完美的 RL 研究配置！开始训练吧！🚀

---

## 💡 下一步

1. ✅ 安装依赖
2. ✅ 测试数据
3. ✅ 运行分析
4. 🎯 收集训练数据
5. 🧠 开始 RL 训练

需要帮助？查看 `REAL_DATA_GUIDE_CN.md` 获取详细文档！

