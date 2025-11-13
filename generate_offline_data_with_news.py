#!/usr/bin/env python3
"""
生成包含真实新闻的离线交易数据
结合yfinance的价格数据 + Finnhub/NewsAPI的新闻数据
使用激进的文本清理策略确保无乱码
"""

import os
import time
import re
import argparse
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import unicodedata
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict

# ========================================
# 配置
# ========================================
OUTPUT_DIR = "dataflows/data_cache"

# 新闻关键词
MACRO_KEYWORDS = [
    "fed", "fomc", "rate cut", "rate hike", "interest rate", "dot plot",
    "ecb", "boe", "boj",
    "cpi", "ppi", "core inflation", "inflation cooling", "jobs report", "nonfarm payrolls",
    "gdp", "retail sales", "ism", "pmis",
    "tariff", "trade war", "sanction", "export controls", "geopolitical",
    "qt", "qe", "bank failure", "credit crunch",
]

MICRO_KEYWORDS = [
    "earnings", "results", "eps", "revenue", "guidance", "beat", "miss",
    "buyback", "repurchase", "dividend", "split",
    "downgrade", "upgrade", "price target",
    "acquire", "acquisition", "merger", "m&a",
    "sec", "lawsuit", "investigation",
    "product launch", "chip", "ai", "partnership", "contract",
]

REPUTABLE_SOURCES = {"reuters", "bloomberg", "wsj", "financial times", "ap", "associated press"}


# ========================================
# 辅助函数
# ========================================
def _to_day_tz(epoch_sec: int, tz: str) -> str:
    """将时间戳转换为时区的日期字符串"""
    if not epoch_sec:
        return ""
    try:
        return pd.to_datetime(epoch_sec, unit="s", utc=True).tz_convert(tz).strftime("%Y-%m-%d")
    except Exception:
        return pd.to_datetime(epoch_sec, unit="s", utc=True).strftime("%Y-%m-%d")


def _within_newsapi_window(d: date) -> bool:
    """检查日期是否在NewsAPI的免费窗口内（约30天）"""
    cutoff = (pd.Timestamp.utcnow() - pd.Timedelta(days=30)).date()
    return d >= cutoff


def has_number(text: str) -> bool:
    """检查文本是否包含数字"""
    return bool(re.search(r"\\b\\d+(\\.\\d+)?%|\\$\\s?\\d+", text))


def clean_text(text: str) -> str:
    """
    激进清理文本中的乱码字符
    使用多种策略确保彻底清除所有编码问题
    """
    if not text or pd.isna(text):
        return text
    
    if not isinstance(text, str):
        return str(text)
    
    # ====== 策略1: 明确的乱码字符替换 ======
    replacements = {
        # 撇号和引号
        '鈥�': "'", '鈥�': "'", '鈥�': '"', '鈥�': '"',
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2032': "'", '\u2033': '"',
        '脗聝': "'", '脗鈥�': '"',
        
        # 破折号
        '鈥�': '-', '鈥�': '-', '鈥�': '-',
        '\u2013': '-', '\u2014': '-', '\u2015': '-',
        
        # 省略号
        '鈥�': '...', '\u2026': '...',
        
        # 空格和不可见字符
        '脗聽': ' ', '\xa0': ' ', '\u00a0': ' ',
        
        # 符号
        '脗漏': '(c)', '脗庐': '(R)', '\u00a9': '(c)', '\u00ae': '(R)',
        '鈧�': 'EUR', '拢': 'GBP', '\u20ac': 'EUR', '\u00a3': 'GBP',
        '鈩�': 'deg', '\u00b0': 'deg',
        
        # 其他常见乱码
        '脙聡': 'a', '脙漏': 'e', '脙墨': 'i', '脙碌': 'o', '脙篓': 'u',
        '\u00e0': 'a', '\u00e8': 'e', '\u00e9': 'e', '\u00ec': 'i', '\u00f2': 'o', '\u00f9': 'u',
        '\u00c0': 'A', '\u00c8': 'E', '\u00c9': 'E', '\u00cc': 'I', '\u00d2': 'O', '\u00d9': 'U',
    }
    
    cleaned = text
    for bad, good in replacements.items():
        cleaned = cleaned.replace(bad, good)
    
    # ====== 策略2: Unicode标准化 ======
    try:
        cleaned = unicodedata.normalize('NFKD', cleaned)
    except Exception:
        pass
    
    # ====== 策略3: 移除问题字符模式 ======
    cleaned = re.sub(r'鈥.', '', cleaned)
    cleaned = re.sub(r'脗.', '', cleaned)
    cleaned = re.sub(r'脙.', '', cleaned)
    cleaned = re.sub(r'卢', '(R)', cleaned)
    cleaned = re.sub(r'漏', '(c)', cleaned)
    
    # ====== 策略4: 保留ASCII + 常见标点 ======
    allowed_chars = set(
        'abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        '0123456789'
        ' .,;:!?()-\'"/$%&+='
        '\n\r\t'
    )
    cleaned = ''.join(c if c in allowed_chars else ' ' for c in cleaned)
    
    # ====== 策略5: 清理多余空格和标点 ======
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\.\.\.+', '...', cleaned)
    cleaned = re.sub(r'--+', '-', cleaned)
    cleaned = re.sub(r'\s+([.,;:!?])', r'\1', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


# ========================================
# 新闻获取
# ========================================
def fetch_company_pool_finnhub(sym: str, day: date, key: str, market_tz: str, session: requests.Session) -> List[Dict]:
    """从Finnhub获取公司新闻"""
    base = "https://finnhub.io/api/v1/company-news"
    _from = (pd.Timestamp(day) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    _to = (pd.Timestamp(day) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        r = session.get(base, params={"symbol": sym, "from": _from, "to": _to, "token": key}, timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  Warning: Finnhub API error for {day}: {e}")
        return []
    
    if not isinstance(data, list):
        return []
    
    # 过滤到准确的日期并清理文本
    out = []
    dstr = day.strftime("%Y-%m-%d")
    for a in data:
        ts = int(a.get("datetime") or 0)
        if _to_day_tz(ts, market_tz) != dstr:
            continue
        out.append({
            "title": clean_text((a.get("headline") or "").strip()),
            "description": clean_text((a.get("summary") or "").strip()),
            "source": clean_text((a.get("source") or "").strip()),
            "publishedAt": None,
            "epoch": ts,
            "kind": "micro",
            "url": a.get("url") or "",
        })
    return out


def fetch_macro_pool_newsapi(day: date, key: str, session: requests.Session) -> List[Dict]:
    """从NewsAPI获取宏观新闻（可选，需要API key）"""
    if not key or not _within_newsapi_window(day):
        return []
    
    base = "https://newsapi.org/v2/everything"
    q = " OR ".join(MACRO_KEYWORDS)
    params = {
        "q": q,
        "from": f"{day}T00:00:00Z",
        "to": f"{day}T23:59:59Z",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": key,
    }
    
    try:
        r = session.get(base, params=params, timeout=20)
        data = r.json()
    except Exception as e:
        print(f"  Warning: NewsAPI error for {day}: {e}")
        return []
    
    if r.status_code != 200 or data.get("status") != "ok":
        return []
    
    out = []
    for a in data.get("articles", []) or []:
        out.append({
            "title": clean_text((a.get("title") or "").strip()),
            "description": clean_text((a.get("description") or a.get("content") or "").strip()),
            "source": clean_text(((a.get("source") or {}) or {}).get("name", "")),
            "publishedAt": a.get("publishedAt"),
            "epoch": None,
            "kind": "macro",
            "url": a.get("url") or "",
        })
    return out


def impact_score(item: dict, symbol: str) -> float:
    """计算新闻影响力得分"""
    title = (item.get("title") or "")
    desc = (item.get("description") or "")
    text = f"{title} {desc}".lower()
    
    # 基础分数
    cat = item.get("kind")
    base = 1.0
    if cat == "micro":
        base = 1.6
    elif cat == "macro":
        base = 1.3
    
    # 关键词权重
    micro_hits = sum(k in text for k in MICRO_KEYWORDS)
    macro_hits = sum(k in text for k in [k.lower() for k in MACRO_KEYWORDS])
    kw = micro_hits * 0.7 + macro_hits * 0.6
    
    # 数字/具体性
    nums = 0.6 if has_number(title + " " + desc) else 0.0
    
    # 来源权威性
    src = (item.get("source") or "").lower()
    src_w = 0.3 if src in REPUTABLE_SOURCES else 0.0
    
    # 提及股票代码
    ticker_bonus = 0.3 if symbol.lower() in text else 0.0
    
    return base + kw + nums + src_w + ticker_bonus


def pick_top_for_day(company_pool: List[Dict], macro_pool: List[Dict], symbol: str) -> str:
    """选择当天最重要的新闻"""
    pool = company_pool + macro_pool
    if not pool:
        return ""
    
    best = max(pool, key=lambda x: impact_score(x, symbol))
    title = best.get("title", "").strip()
    desc = best.get("description", "").strip()
    src = best.get("source", "").strip()
    when = best.get("publishedAt") or (
        pd.to_datetime(best.get("epoch"), unit="s", utc=True).isoformat() 
        if best.get("epoch") else ""
    )
    
    txt = "; ".join([p for p in [title, desc] if p])
    meta = ", ".join([p for p in [src, when] if p])
    return f"{txt} ({meta})" if meta else txt


def daterange(a: date, b: date):
    """生成日期范围"""
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


# ========================================
# 价格数据获取（yfinance）
# ========================================
def fetch_price_data(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    """使用yfinance获取真实价格数据"""
    print(f"  从yfinance获取 {symbol} 的价格数据...")
    
    buffer_start = start_date - timedelta(days=60)
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=buffer_start, end=end_date + timedelta(days=1))
    
    if df.empty:
        raise ValueError(f"无法获取 {symbol} 的数据，请检查股票代码")
    
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df = df.round(2)
    df.index.name = 'Date'
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    close = df['Close']
    
    df['SMA_10'] = close.rolling(10).mean()
    df['SMA_20'] = close.rolling(20).mean()
    df['SMA_50'] = close.rolling(50).mean()
    
    df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
    
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0.0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / (loss.replace(0, 1e-9))
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['BB_Middle'] = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df


def fetch_fundamentals(symbol: str) -> Dict:
    """获取基本面数据"""
    print(f"  获取 {symbol} 的基本面数据...")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'PE_Ratio': info.get('trailingPE', np.nan),
            'Market_Cap': info.get('marketCap', np.nan),
            'Revenue': info.get('totalRevenue', np.nan),
            'EPS': info.get('trailingEps', np.nan),
        }
    except Exception as e:
        print(f"  Warning: 无法获取基本面数据: {e}")
        return {
            'PE_Ratio': np.nan,
            'Market_Cap': np.nan,
            'Revenue': np.nan,
            'EPS': np.nan,
        }


# ========================================
# 主函数
# ========================================
def main():
    parser = argparse.ArgumentParser(description='生成包含真实新闻的离线交易数据（无乱码）')
    parser.add_argument('--symbol', default='AAPL', help='股票代码（默认: AAPL）')
    parser.add_argument('--start', default='2024-11-12', help='开始日期 YYYY-MM-DD')
    parser.add_argument('--end', default=None, help='结束日期 YYYY-MM-DD（默认: 开始日期+2个月）')
    parser.add_argument('--market-tz', default='America/New_York', help='市场时区')
    parser.add_argument('--pause', type=float, default=1.0, help='API请求间隔（秒）')
    parser.add_argument('--output-name', default=None, help='输出文件名（不含扩展名）')
    parser.add_argument('--verbose', action='store_true', help='显示详细输出')
    
    args = parser.parse_args()
    
    # 解析日期
    start_date = date.fromisoformat(args.start)
    if args.end:
        end_date = date.fromisoformat(args.end)
    else:
        end_date = start_date + timedelta(days=60)
    
    symbol = args.symbol.upper()
    
    # 获取API密钥
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    newsapi_key = os.environ.get("NEWSAPI_API_KEY")
    
    if not finnhub_key:
        print("警告: 未设置 FINNHUB_API_KEY，将无法获取新闻数据")
        print("请设置环境变量: export FINNHUB_API_KEY='your_key'")
        print("继续使用价格数据...")
    
    print(f"\n{'='*60}")
    print(f"生成离线交易数据（带新闻，无乱码）")
    print(f"{'='*60}")
    print(f"股票代码: {symbol}")
    print(f"日期范围: {start_date} 到 {end_date}")
    print(f"市场时区: {args.market_tz}")
    if newsapi_key:
        print(f"新闻来源: Finnhub + NewsAPI")
    else:
        print(f"新闻来源: Finnhub")
    print(f"{'='*60}\n")
    
    # 1. 获取价格数据
    print("步骤 1/3: 获取价格数据...")
    price_df = fetch_price_data(symbol, start_date, end_date)
    print(f"  [OK] 获取了 {len(price_df)} 天的数据")
    
    # 2. 计算技术指标
    print("\n步骤 2/3: 计算技术指标...")
    price_df = compute_indicators(price_df)
    print(f"  [OK] 计算完成")
    
    # 3. 获取新闻数据
    print("\n步骤 3/3: 获取新闻数据...")
    
    if finnhub_key:
        sess = requests.Session()
        news_data = []
        
        trading_days = price_df[
            (price_df['Date'] >= start_date) & 
            (price_df['Date'] <= end_date)
        ]['Date'].tolist()
        
        for day in trading_days:
            if args.verbose:
                print(f"  获取 {day} 的新闻...")
            
            company_news = fetch_company_pool_finnhub(symbol, day, finnhub_key, args.market_tz, sess)
            macro_news = fetch_macro_pool_newsapi(day, newsapi_key, sess) if newsapi_key else []
            
            top_news = pick_top_for_day(company_news, macro_news, symbol)
            news_count = len(company_news) + len(macro_news)
            
            news_data.append({
                'Date': day,
                'news': top_news,
                'news_count': news_count
            })
            
            time.sleep(args.pause)
        
        news_df = pd.DataFrame(news_data)
        print(f"  [OK] 获取了 {len(news_df)} 天的新闻")
        
        price_df = price_df.merge(news_df, on='Date', how='left')
        price_df['news'] = price_df['news'].fillna("")
        price_df['news_count'] = price_df['news_count'].fillna(0).astype(int)
        
        non_empty_news = (price_df['news'].str.len() > 0).sum()
        print(f"  [OK] 有新闻的交易日: {non_empty_news}/{len(trading_days)}")
    else:
        price_df['news'] = ""
        price_df['news_count'] = 0
        print("  [WARNING] 跳过新闻获取（未设置API密钥）")
    
    # 4. 添加基本面数据
    print("\n获取基本面数据...")
    fundamentals = fetch_fundamentals(symbol)
    for key, value in fundamentals.items():
        price_df[key] = value
    
    # 5. 添加symbol列
    price_df['symbol'] = symbol
    
    # 6. 只保留目标日期范围的数据
    price_df = price_df[
        (price_df['Date'] >= start_date) & 
        (price_df['Date'] <= end_date)
    ]
    
    # 7. 保存数据
    print(f"\n保存数据...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if args.output_name:
        base_name = args.output_name
    else:
        base_name = f"offline_trading_data_{symbol}_{start_date}_{end_date}"
    
    parquet_path = os.path.join(OUTPUT_DIR, f"{base_name}.parquet")
    price_df.to_parquet(parquet_path, index=False)
    print(f"  [OK] Parquet: {parquet_path}")
    
    csv_path = os.path.join(OUTPUT_DIR, f"{base_name}.csv")
    price_df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"  [OK] CSV: {csv_path}")
    
    # 8. 显示摘要
    print(f"\n{'='*60}")
    print(f"数据生成完成！")
    print(f"{'='*60}")
    print(f"总行数: {len(price_df):,}")
    print(f"列数: {len(price_df.columns)}")
    print(f"日期范围: {price_df['Date'].min()} 到 {price_df['Date'].max()}")
    print(f"\n前5行预览:")
    print(price_df.head())
    print(f"\n数据列:")
    print(price_df.columns.tolist())
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

