#!/usr/bin/env python3
"""
Pick the most impactful single news per day for AAPL (macro or micro).

Env:
  export FINNHUB_API_KEY="..."
  # optional for macro pool (free tier ~30d history):
  export NEWSAPI_API_KEY="..."

Usage:
  python aapl_top_news.py --start 2024-10-10 --end 2024-12-10 \
    --out aapl_top_news.csv --market-tz America/New_York --pause 1.1

Notes:
- Company pool: Finnhub company-news (window widened ±1 day, then filter by market tz day).
- Macro pool: NewsAPI everything with macro keywords (if within window & quota).
- One row per day: date,symbol,news
"""

import os, time, re, argparse, requests
import pandas as pd
from datetime import date, timedelta

SYMBOL = "AAPL"

MACRO_KEYWORDS = [
    # rates/central bank
    "fed", "fomc", "rate cut", "rate hike", "interest rate", "dot plot",
    "ecb", "boe", "boj",
    # inflation & labor
    "cpi", "ppi", "core inflation", "inflation cooling", "jobs report", "nonfarm payrolls",
    # growth & gdp
    "gdp", "retail sales", "ism", "pmis",
    # policy/trade/geopolitics
    "tariff", "trade war", "sanction", "export controls", "geopolitical",
    # liquidity/financial stability
    "qt", "qe", "bank failure", "credit crunch",
]

# Micro (company) high-impact keywords
MICRO_KEYWORDS = [
    "earnings", "results", "eps", "revenue", "guidance", "beat", "miss",
    "buyback", "repurchase", "dividend", "split",
    "downgrade", "upgrade", "price target",
    "acquire", "acquisition", "merger", "m&a",
    "sec", "lawsuit", "investigation",
    "product launch", "chip", "ai", "partnership", "contract",
]

REPUTABLE_SOURCES = {"reuters", "bloomberg", "wsj", "financial times", "ap", "associated press"}

def _to_day_tz(epoch_sec: int, tz: str) -> str:
    if not epoch_sec:
        return ""
    try:
        return pd.to_datetime(epoch_sec, unit="s", utc=True).tz_convert(tz).strftime("%Y-%m-%d")
    except Exception:
        return pd.to_datetime(epoch_sec, unit="s", utc=True).strftime("%Y-%m-%d")

def _within_newsapi_window(d: date) -> bool:
    cutoff = (pd.Timestamp.utcnow() - pd.Timedelta(days=30)).date()
    return d >= cutoff

def fetch_company_pool_finnhub(sym: str, day: date, key: str, market_tz: str, session: requests.Session):
    """Finnhub company news widened ±1 day; then filter back to 'day' in market tz."""
    base = "https://finnhub.io/api/v1/company-news"
    _from = (pd.Timestamp(day) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    _to   = (pd.Timestamp(day) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    r = session.get(base, params={"symbol": sym, "from": _from, "to": _to, "token": key}, timeout=20)
    try:
        data = r.json()
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    # normalize + filter to exact day in market tz
    out = []
    dstr = day.strftime("%Y-%m-%d")
    for a in data:
        ts = int(a.get("datetime") or 0)
        if _to_day_tz(ts, market_tz) != dstr:
            continue
        out.append({
            "title": (a.get("headline") or "").strip(),
            "description": (a.get("summary") or "").strip(),
            "source": (a.get("source") or "").strip(),
            "publishedAt": None,  # finnhub gives epoch; we use ts for scoring if needed
            "epoch": ts,
            "kind": "micro",
            "url": a.get("url") or "",
        })
    return out

def fetch_macro_pool_newsapi(day: date, key: str, session: requests.Session):
    """NewsAPI macro pool (if within ~30d). Query big macro keywords in one OR-joined string."""
    if not _within_newsapi_window(day):
        return []
    base = "https://newsapi.org/v2/everything"
    q = " OR ".join(MACRO_KEYWORDS)
    params = {
        "q": q,
        "from": f"{day}T00:00:00Z",
        "to":   f"{day}T23:59:59Z",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": key,
    }
    r = session.get(base, params=params, timeout=20)
    try:
        data = r.json()
    except Exception:
        return []
    if r.status_code != 200 or data.get("status") != "ok":
        return []
    out = []
    for a in data.get("articles", []) or []:
        out.append({
            "title": (a.get("title") or "").strip(),
            "description": (a.get("description") or a.get("content") or "").strip(),
            "source": ((a.get("source") or {}) or {}).get("name", ""),
            "publishedAt": a.get("publishedAt"),
            "epoch": None,
            "kind": "macro",
            "url": a.get("url") or "",
        })
    return out

def has_number(text: str) -> bool:
    return bool(re.search(r"\\b\\d+(\\.\\d+)?%|\\$\\s?\\d+", text))

def impact_score(item: dict) -> float:
    """Blend macro/micro category weight + keyword strength + source authority + numbers."""
    title = (item.get("title") or "")
    desc  = (item.get("description") or "")
    text  = f"{title} {desc}".lower()

    # category base
    cat = item.get("kind")
    base = 1.0
    if cat == "micro":
        base = 1.6  # company-specific usually more directly impactful for the stock
    elif cat == "macro":
        base = 1.3  # macro can dominate on certain days

    # keyword weights
    micro_hits = sum(k in text for k in MICRO_KEYWORDS)
    macro_hits = sum(k in text for k in [k.lower() for k in MACRO_KEYWORDS])
    kw = micro_hits * 0.7 + macro_hits * 0.6

    # numbers / concreteness
    nums = 0.6 if has_number(title + " " + desc) else 0.0

    # source authority
    src = (item.get("source") or "").lower()
    src_w = 0.3 if src in REPUTABLE_SOURCES else 0.0

    # small bonus if title explicitly mentions ticker or company name tokens
    ticker_bonus = 0.3 if "aapl" in text or "apple" in text else 0.0

    return base + kw + nums + src_w + ticker_bonus

def pick_top_for_day(company_pool: list, macro_pool: list) -> str:
    pool = company_pool + macro_pool
    if not pool:
        return ""
    best = max(pool, key=impact_score)
    title = best.get("title","").strip()
    desc  = best.get("description","").strip()
    src   = best.get("source","").strip()
    when  = best.get("publishedAt") or (pd.to_datetime(best.get("epoch"), unit="s", utc=True).isoformat() if best.get("epoch") else "")
    txt = "; ".join([p for p in [title, desc] if p])
    meta = ", ".join([p for p in [src, when] if p])
    return f"{txt} ({meta})" if meta else txt

def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", default="aapl_top_news.csv")
    ap.add_argument("--market-tz", default="America/New_York")
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    news_key    = os.environ.get("NEWSAPI_API_KEY")  # optional

    if not finnhub_key:
        raise SystemExit("FINNHUB_API_KEY is required for historical company news.")

    sess = requests.Session()
    rows = []
    for d in daterange(start, end):
        if args.verbose:
            print(f"=== {d} ===")
        company = fetch_company_pool_finnhub(SYMBOL, d, finnhub_key, args.market_tz, sess)
        macro = fetch_macro_pool_newsapi(d, news_key, sess) if news_key else []
        top = pick_top_for_day(company, macro)
        rows.append({"date": d.isoformat(), "symbol": SYMBOL, "news": top})
        time.sleep(args.pause)

    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)
    print("Wrote:", args.out)
    nonempty = (out["news"].str.len() > 0).sum()
    print(f"Non-empty days: {nonempty}/{len(out)}")

if __name__ == "__main__":
    main()
