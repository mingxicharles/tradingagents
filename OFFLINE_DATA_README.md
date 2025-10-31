# 离线数据集使用指南 (Offline Dataset Guide)

## 概述

为了解决 Yahoo Finance 不稳定问题，我们创建了一个离线数据集系统。系统可以：
1. 生成合成/历史数据用于测试
2. 使用离线数据集运行交易代理
3. 作为 baseline 进行回测

## 快速开始

### 1. 生成离线数据

```bash
cd tradingagents_test
conda activate tradingagents
python generate_offline_data.py
```

这会生成：
- `dataflows/data_cache/offline_trading_data.parquet` - 完整的离线数据集
- `dataflows/data_cache/offline_trading_data_sample.csv` - CSV 样本（用于检查）

生成的数据包含：
- **Symbols**: AAPL, MSFT, AMZN
- **Date Range**: 2024-01-01 到 2024-12-31
- **数据字段**:
  - OHLCV 价格数据
  - 技术指标 (SMA, EMA, RSI, MACD, Bollinger Bands)
  - 基本面数据 (P/E, Market Cap, Revenue, EPS)
  - 新闻数据 (新闻计数、情感、标题)

### 2. 使用离线数据运行代理

```bash
# 使用离线数据集（而不是 yfinance）
python -m tradingagents.run AAPL --offline-data --date 2024-1-15

# 使用特定日期
python -m tradingagents.run MSFT --offline-data --date 2024-3-20

# 不指定日期（使用数据集中的最新日期）
python -m tradingagents.run AMZN --offline-data
```

### 3. 对比：在线 vs 离线

```bash
# 在线数据（yfinance，可能不稳定）
python -m tradingagents.run AAPL --date 2024-1-15

# 离线数据（稳定，用于测试）
python -m tradingagents.run AAPL --offline-data --date 2024-1-15
```

## 数据集结构

### 价格数据 (OHLCV)
- `Open`, `High`, `Low`, `Close`, `Volume`
- 基于随机游走生成，包含趋势和波动

### 技术指标
- `SMA_10`, `SMA_20`, `SMA_50` - 简单移动平均
- `EMA_12`, `EMA_26` - 指数移动平均
- `RSI` - 相对强弱指数 (14期)
- `MACD`, `MACD_Signal`, `MACD_Hist` - MACD 指标
- `BB_Upper`, `BB_Middle`, `BB_Lower` - 布林带

### 基本面数据
- `PE_Ratio` - 市盈率
- `Market_Cap` - 市值
- `Revenue` - 营收
- `EPS` - 每股收益

### 新闻数据
- `news_count` - 新闻数量
- `sentiment` - 情感 (positive/neutral/negative)
- `title` - 新闻标题
- `source` - 新闻来源

## 自定义生成

编辑 `generate_offline_data.py` 可以自定义：

```python
# 修改股票列表
UNIVERSE = ["AAPL", "MSFT", "GOOGL", "NVDA"]

# 修改日期范围
START = "2023-01-01"
END = "2024-12-31"

# 修改基础价格
base_prices = {"AAPL": 180.0, "MSFT": 380.0, ...}
```

## Baseline 设置

### 创建 Baseline

1. **生成数据集**：
   ```bash
   python generate_offline_data.py
   ```

2. **运行多个测试日期**：
   ```bash
   python -m tradingagents.run AAPL --offline-data --date 2024-1-15
   python -m tradingagents.run AAPL --offline-data --date 2024-2-15
   python -m tradingagents.run AAPL --offline-data --date 2024-3-15
   ```

3. **收集结果**：
   - 所有决策保存在 `signals/` 目录
   - 可以分析决策的准确性、置信度等

### 评估 Baseline

- **决策一致性**：相同输入应该产生相似输出
- **数据准确性**：离线数据应该与实际市场数据特征一致
- **代理行为**：各代理应该基于离线数据给出合理建议

## 故障排除

### 问题：找不到离线数据文件
```
FileNotFoundError: Offline data file not found
```

**解决**：
```bash
python generate_offline_data.py
```

### 问题：日期不在数据集中
如果指定日期不在数据集范围内，系统会使用最近的可用日期。

### 问题：Symbol 不在数据集中
确保 symbol 在 `UNIVERSE` 列表中：
- 当前支持：AAPL, MSFT, AMZN
- 添加更多：编辑 `generate_offline_data.py` 中的 `UNIVERSE`

## 与原始代码的区别

### 数据源切换

**原始代码** (yfinance)：
```python
from ..dataflows.yfinance_tools import get_stock_price_data
```

**离线版本**：
```python
from ..dataflows.local_data import get_stock_price_data_local
```

### Agent 构建

使用 `--offline-data` 标志会自动切换数据源：
- `build_agents(..., use_offline_data=True)` 使用本地数据函数
- 所有数据工具保持相同的接口，只是数据源不同

## 下一步

1. **扩展数据集**：添加更多股票、更长时间范围
2. **改进生成**：使用真实历史数据（如果有）
3. **基准测试**：建立性能基准用于 RL 训练
4. **回测框架**：自动化运行多个日期并评估结果

