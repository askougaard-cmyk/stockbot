"""
data_fetcher.py – kursdata, MA50/200, analytiker, nyheder og dagens aktie
"""

import yfinance as yf
import feedparser
import requests
import re
from datetime import datetime, timedelta
from config import (ALL_TICKERS, MAG7, ALL_INDEX_TICKERS, PORTFOLIO,
                    MACRO_FEEDS, TRUMP_FEEDS, TRUMP_KEYWORDS,
                    CEO_KEYWORDS, MARKET_MOVING_FEEDS)

# ── Sentiment analyse ────────────────────────────────────────

POS = ["surge","jump","beat","beats","rise","rises","gain","profit","growth","record",
       "strong","upgrade","buy","bull","rally","soar","boost","exceed","outperform",
       "raise","raises","positive","optimistic","recovery","rebound","breakthrough"]
NEG = ["fall","drop","miss","misses","decline","loss","cut","cuts","downgrade","sell",
       "bear","crash","warn","warning","risk","concern","tariff","recession","layoff",
       "fine","penalty","investigation","lawsuit","disappoint","weak","slowdown","below"]

def _sentiment(title: str, summary: str = "") -> str:
    text = (title + " " + summary).lower()
    p = sum(1 for w in POS if w in text)
    n = sum(1 for w in NEG if w in text)
    if p > n: return "positive"
    if n > p: return "negative"
    return "neutral"

def _clean(text: str, max_len: int = 250) -> str:
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_len] + "…" if len(text) > max_len else text


# ── Kursdata ─────────────────────────────────────────────────

def get_quote(ticker: str) -> dict | None:
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="220d")
        if hist is None or len(hist) < 2:
            return None
        hist = hist.dropna(subset=["Close"])
        if len(hist) < 2:
            return None

        prev_close = float(hist["Close"].iloc[-2])
        curr_close = float(hist["Close"].iloc[-1])
        change_pct = ((curr_close - prev_close) / prev_close) * 100

        vol_today = float(hist["Volume"].iloc[-1]) if "Volume" in hist else 0
        vol_avg   = float(hist["Volume"].tail(10).mean()) if "Volume" in hist else 0
        vol_ratio = (vol_today / vol_avg) if vol_avg > 0 else 1.0

        ma50  = float(hist["Close"].tail(50).mean())  if len(hist) >= 50  else None
        ma200 = float(hist["Close"].tail(200).mean()) if len(hist) >= 200 else None

        currency = "USD"; w52_high = w52_low = mkt_cap = None
        pe_ratio = forward_pe = eps = eps_forward = None
        target_high = target_low = target_mean = analyst_rec = analyst_count = None
        name = ticker; sector = industry = ""
        try:
            info          = t.info
            currency      = info.get("currency", "USD") or "USD"
            w52_high      = info.get("fiftyTwoWeekHigh")
            w52_low       = info.get("fiftyTwoWeekLow")
            mkt_cap       = info.get("marketCap")
            name          = info.get("shortName") or info.get("longName") or ticker
            pe_ratio      = info.get("trailingPE")
            forward_pe    = info.get("forwardPE")
            eps           = info.get("trailingEps")
            eps_forward   = info.get("epsForward")
            target_high   = info.get("targetHighPrice")
            target_low    = info.get("targetLowPrice")
            target_mean   = info.get("targetMeanPrice")
            analyst_rec   = info.get("recommendationKey", "")
            analyst_count = info.get("numberOfAnalystOpinions")
            sector        = info.get("sector", "")
            industry      = info.get("industry", "")
        except Exception:
            pass

        premarket_price = premarket_change = None
        try:
            pm = t.history(period="1d", interval="1m", prepost=True)
            if pm is not None and not pm.empty:
                last_pm          = float(pm["Close"].iloc[-1])
                premarket_change = ((last_pm - curr_close) / curr_close) * 100
                premarket_price  = round(last_pm, 2)
        except Exception:
            pass

        earnings_date = None
        try:
            cal = t.calendar
            if isinstance(cal, dict):
                ed = cal.get("Earnings Date")
                if ed and len(ed) > 0:
                    earnings_date = str(ed[0].date()) if hasattr(ed[0], "date") else str(ed[0])
            elif cal is not None and hasattr(cal, "columns") and len(cal.columns) > 0:
                earnings_date = str(cal.columns[0].date())
        except Exception:
            pass

        return {
            "ticker": ticker, "name": name,
            "price": round(curr_close, 2), "prev_close": round(prev_close, 2),
            "change_pct": round(change_pct, 2), "currency": currency,
            "volume": int(vol_today), "volume_avg": int(vol_avg),
            "volume_ratio": round(vol_ratio, 2),
            "ma50": round(ma50, 2) if ma50 else None,
            "ma200": round(ma200, 2) if ma200 else None,
            "earnings_date": earnings_date,
            "52w_high": float(w52_high) if w52_high else None,
            "52w_low":  float(w52_low)  if w52_low  else None,
            "market_cap": mkt_cap,
            "pe_ratio":    round(pe_ratio, 1)    if pe_ratio    else None,
            "forward_pe":  round(forward_pe, 1)  if forward_pe  else None,
            "eps":         round(eps, 2)          if eps         else None,
            "eps_forward": round(eps_forward, 2) if eps_forward else None,
            "target_high": round(target_high, 2) if target_high else None,
            "target_low":  round(target_low, 2)  if target_low  else None,
            "target_mean": round(target_mean, 2) if target_mean else None,
            "analyst_rec": analyst_rec, "analyst_count": analyst_count,
            "sector": sector, "industry": industry,
            "premarket_price":  premarket_price,
            "premarket_change": round(premarket_change, 2) if premarket_change is not None else None,
        }
    except Exception as e:
        print(f"[WARN] get_quote({ticker}): {e}")
        return None


def get_all_quotes(tickers: list) -> dict:
    return {t: q for t in tickers if (q := get_quote(t)) is not None}


def get_upcoming_earnings(tickers: list, days_ahead: int = 21) -> list:
    upcoming = []; cutoff = datetime.now() + timedelta(days=days_ahead); seen = set()
    for ticker in tickers:
        if ticker in seen: continue
        seen.add(ticker)
        try:
            q = get_quote(ticker)
            if not q or not q.get("earnings_date"): continue
            ed = datetime.strptime(q["earnings_date"], "%Y-%m-%d")
            if datetime.now() <= ed <= cutoff:
                upcoming.append(q)
        except Exception:
            pass
    return sorted(upcoming, key=lambda x: x["earnings_date"])


# ── Dagens aktie ─────────────────────────────────────────────

def get_stock_of_the_day() -> dict | None:
    portfolio_tickers = {s["ticker"] for g in PORTFOLIO.values() for s in g}
    watchlist = [
        "NVDA","AAPL","GOOGL","META","TSLA","AMD","INTC","CRM","ORCL",
        "NFLX","SHOP","PLTR","SNOW","COIN","UBER","SPOT","PYPL",
        "ARM","SMCI","MRVL","AVGO","QCOM","TSM","ASML","ADBE","NOW",
        "PANW","CRWD","ZS","NET","DDOG","MDB","ABNB","DASH","RBLX",
    ]
    candidates_tickers = [t for t in watchlist if t not in portfolio_tickers]
    candidates = []
    for ticker in candidates_tickers:
        q = get_quote(ticker)
        if not q: continue
        score = 0; reasons = []
        abs_chg = abs(q["change_pct"]); vol_r = q.get("volume_ratio", 1)
        if abs_chg > 5:   score += 4; reasons.append(f"stor bevægelse ({q['change_pct']:+.1f}%)")
        elif abs_chg > 2: score += 2; reasons.append(f"markant bevægelse ({q['change_pct']:+.1f}%)")
        if vol_r > 2.5:   score += 3; reasons.append(f"eksplosiv volumen ({vol_r:.1f}x snit)")
        elif vol_r > 1.5: score += 1; reasons.append(f"høj volumen ({vol_r:.1f}x)")
        if q.get("52w_high") and q["price"] >= q["52w_high"] * 0.98:
            score += 2; reasons.append("tæt på 52-ugers high 🔝")
        if q.get("earnings_date"):
            try:
                days = (datetime.strptime(q["earnings_date"], "%Y-%m-%d") - datetime.now()).days
                if 0 <= days <= 3:
                    score += 3; reasons.append(f"earnings om {days} dag(e)! 📅")
            except Exception:
                pass
        rec = (q.get("analyst_rec") or "").lower()
        if "buy" in rec: score += 1; reasons.append("analytikere anbefaler køb")
        if score > 0:
            candidates.append({**q, "score": score, "reasons": reasons})
    if not candidates:
        return None
    return sorted(candidates, key=lambda x: x["score"], reverse=True)[0]


# ── RSS Nyheder ──────────────────────────────────────────────

def _parse_feed(url: str, max_items: int = 8) -> list:
    try:
        feed  = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items * 2]:
            title   = (entry.get("title") or "").strip()
            link    = (entry.get("link")  or "").strip()
            summary = _clean(entry.get("summary") or entry.get("description") or "")
            if not title or not link: continue
            items.append({
                "title":     title,
                "link":      link,
                "summary":   summary,
                "source":    feed.feed.get("title", ""),
                "sentiment": _sentiment(title, summary),
            })
            if len(items) >= max_items: break
        return items
    except Exception as e:
        print(f"[WARN] RSS {url[:50]}: {e}")
        return []


def get_ticker_news(ticker: str, max_items: int = 4) -> list:
    url   = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    items = _parse_feed(url, max_items)
    if not items:
        try:
            t = yf.Ticker(ticker)
            try:    raw = t.get_news(count=max_items)
            except Exception: raw = getattr(t, "news", []) or []
            for n in (raw or [])[:max_items]:
                try:
                    content = n.get("content", {})
                    title   = content.get("title") or n.get("title", "")
                    link    = content.get("canonicalUrl", {}).get("url") or n.get("link") or n.get("url", "")
                    summary = _clean(content.get("summary") or n.get("summary", ""))
                except Exception:
                    title = n.get("title",""); link = n.get("link") or n.get("url",""); summary = ""
                if title and link:
                    items.append({"title": title, "link": link, "summary": summary,
                                  "source": "Yahoo Finance", "sentiment": _sentiment(title, summary)})
        except Exception:
            pass
    return items


def get_portfolio_news() -> dict:
    return {t: items for t in ALL_TICKERS if (items := get_ticker_news(t, 4))}


def get_mag7_news() -> dict:
    return {s["ticker"]: items for s in MAG7 if (items := get_ticker_news(s["ticker"], 4))}


def get_trump_news(max_items: int = 6) -> list:
    """
    Henter Trump/politik nyheder fra flere gratis RSS-kilder.
    Filtrerer på Trump-relaterede nøgleord.
    """
    all_items = []
    for url in TRUMP_FEEDS:
        all_items += _parse_feed(url, 15)

    # Filtrer på Trump-keywords
    filtered = [
        i for i in all_items
        if any(kw in i["title"].lower() or kw in i["summary"].lower()
               for kw in TRUMP_KEYWORDS)
    ]

    # Dedupliker på titel
    seen_titles = set()
    unique = []
    for item in filtered:
        key = item["title"][:50].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)

    return unique[:max_items]


def get_market_moving_news(max_items: int = 6) -> list:
    """
    Nyheder der potentielt bevæger markedet:
    CEO-udtalelser, Fed-taler, earnings surprises, opkøb osv.
    """
    all_items = []
    # CNBC Breaking
    all_items += _parse_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html", 20)
    # Reuters Business
    all_items += _parse_feed("https://feeds.reuters.com/reuters/businessNews", 20)
    # Markedsspecifikke feeds
    for url in MARKET_MOVING_FEEDS:
        all_items += _parse_feed(url, 10)

    keywords = [
        "fed","powell","rate cut","rate hike","fomc","earnings","beat","miss",
        "acquisition","merger","buyout","ipo","bankruptcy","layoffs","guidance",
        "upgrade","downgrade","price target","analyst","revenue","profit",
        "quarterly results","q1","q2","q3","q4","raises","cuts","trump","tariff",
        "market","stocks","rally","selloff","crash","correction"
    ]

    filtered = [
        i for i in all_items
        if any(kw in i["title"].lower() for kw in keywords)
    ]

    # Dedupliker
    seen = set()
    unique = []
    for item in filtered:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:max_items]


def get_ceo_news(max_items: int = 5) -> list:
    all_items = []
    all_items += _parse_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html", 40)
    all_items += _parse_feed("https://feeds.reuters.com/reuters/businessNews", 20)
    filtered = [i for i in all_items
                if any(k in i["title"].lower() for k in CEO_KEYWORDS)]
    seen = set()
    unique = []
    for item in filtered:
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:max_items]


def get_macro_news(max_items: int = 8) -> list:
    all_items = []
    for url in MACRO_FEEDS:
        all_items += _parse_feed(url, 10)
    keywords = ["inflation","cpi","jobs","unemployment","fed","gdp","tariff",
                "recession","payroll","fomc","powell","rate","trade","deficit","economy"]
    filtered = [i for i in all_items if any(kw in i["title"].lower() for kw in keywords)]
    seen = set(); unique = []
    for item in (filtered or all_items):
        key = item["title"][:50].lower()
        if key not in seen:
            seen.add(key); unique.append(item)
    return unique[:max_items]


def get_macro_indicators() -> dict:
    indicators = {}
    urls = {
        "cpi_yoy":      "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL",
        "unemployment": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE",
        "fed_rate":     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS",
        "core_cpi":     "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPILFESL",
    }
    for key, url in urls.items():
        try:
            lines = requests.get(url, timeout=10).text.strip().split("\n")
            last  = lines[-1].split(","); prev = lines[-2].split(",")
            indicators[key] = {
                "date":   last[0], "value": float(last[1]),
                "prev":   float(prev[1]),
                "change": round(float(last[1]) - float(prev[1]), 3),
            }
        except Exception as e:
            print(f"[WARN] Macro {key}: {e}")
    return indicators


def get_daily_recap(portfolio_news: dict, mag7_news: dict,
                    macro_news: list, trump_news: list = None,
                    market_news: list = None) -> str:
    """Daglig recap med sentiment-analyse af alle nyheder."""
    all_news = []
    for items in portfolio_news.values():
        all_news += items
    for items in mag7_news.values():
        all_news += items
    all_news += macro_news
    if trump_news:
        all_news += trump_news
    if market_news:
        all_news += market_news

    pos = [i for i in all_news if i.get("sentiment") == "positive"]
    neg = [i for i in all_news if i.get("sentiment") == "negative"]
    neu = [i for i in all_news if i.get("sentiment") == "neutral"]

    lines = ["📋 <b>DAGENS NYHEDSRECAP</b>\n"]

    if pos:
        lines.append("🟢 <b>Positive signaler:</b>")
        for item in pos[:3]:
            lines.append(f"  • {_clean(item['title'], 90)}")
            if item.get("summary") and len(item["summary"]) > 30:
                lines.append(f"    <i>↳ {_clean(item['summary'], 140)}</i>")
        lines.append("")

    if neg:
        lines.append("🔴 <b>Negative signaler:</b>")
        for item in neg[:3]:
            lines.append(f"  • {_clean(item['title'], 90)}")
            if item.get("summary") and len(item["summary"]) > 30:
                lines.append(f"    <i>↳ {_clean(item['summary'], 140)}</i>")
        lines.append("")

    if neu and len(lines) < 6:
        lines.append("➡️ <b>Øvrige nyheder:</b>")
        for item in neu[:2]:
            lines.append(f"  • {_clean(item['title'], 90)}")

    total = len(pos) + len(neg) + len(neu)
    if total > 0:
        pos_pct = int((len(pos) / total) * 100)
        neg_pct = int((len(neg) / total) * 100)
        if pos_pct > 60:
            lines.append(f"\n💡 <i>Overordnet positiv stemning ({pos_pct}% positive nyheder)</i>")
        elif neg_pct > 60:
            lines.append(f"\n💡 <i>Overordnet negativ stemning ({neg_pct}% negative nyheder)</i>")
        else:
            lines.append(f"\n💡 <i>Blandet nyhedsbillede — {pos_pct}% positive, {neg_pct}% negative</i>")

    return "\n".join(lines)


def get_weekly_summary_data(watchlist_history: list = None) -> dict:
    all_t  = list(set(ALL_TICKERS + [s["ticker"] for s in MAG7]
                      + [i["ticker"] for i in ALL_INDEX_TICKERS]))
    quotes = get_all_quotes(all_t)
    weekly = {}
    for ticker, q in quotes.items():
        try:
            hist = yf.Ticker(ticker).history(period="7d")
            if hist is not None and len(hist) >= 2:
                hist  = hist.dropna(subset=["Close"])
                start = float(hist["Close"].iloc[0]); end = float(hist["Close"].iloc[-1])
                weekly[ticker] = {**q, "week_change_pct": round(((end-start)/start)*100, 2)}
            else:
                weekly[ticker] = {**q, "week_change_pct": None}
        except Exception:
            weekly[ticker] = {**q, "week_change_pct": None}

    p_news  = get_portfolio_news()
    m_news  = get_mag7_news()
    trump   = get_trump_news()
    macro_n = get_macro_news()
    mkt     = get_market_moving_news()

    return {
        "quotes":            weekly,
        "portfolio_news":    p_news,
        "mag7_news":         m_news,
        "macro_news":        macro_n,
        "trump_news":        trump,
        "market_news":       mkt,
        "indicators":        get_macro_indicators(),
        "upcoming_earnings": get_upcoming_earnings(all_t, days_ahead=7),
        "watchlist_history": watchlist_history or [],
        "daily_recap":       get_daily_recap(p_news, m_news, macro_n, trump, mkt),
    }
