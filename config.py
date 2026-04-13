# ============================================================
#  STOCKBOT CONFIG - Rediger kun denne fil
# ============================================================

# --- Din portefølje ---
PORTFOLIO = {
    "AktieDepot": [
        {"ticker": "MSTR",  "name": "Strategy A"},
        {"ticker": "PNG.V", "name": "Kraken Robotics"},
    ],
    "Aktiesparekonto": [
        {"ticker": "MSTR",    "name": "Strategy A"},
        {"ticker": "AMZN",    "name": "Amazon"},
        {"ticker": "MSFT",    "name": "Microsoft"},
        {"ticker": "IREN",    "name": "Iren"},
    ],
}

ALL_TICKERS = list({t["ticker"] for group in PORTFOLIO.values() for t in group})

# --- MAG7 ---
MAG7 = [
    {"ticker": "AAPL",  "name": "Apple"},
    {"ticker": "MSFT",  "name": "Microsoft"},
    {"ticker": "GOOGL", "name": "Alphabet"},
    {"ticker": "AMZN",  "name": "Amazon"},
    {"ticker": "META",  "name": "Meta"},
    {"ticker": "NVDA",  "name": "Nvidia"},
    {"ticker": "TSLA",  "name": "Tesla"},
]

# --- Globale indeks ---
INDICES = {
    "🇺🇸 USA": [
        {"ticker": "^IXIC", "name": "NASDAQ"},
        {"ticker": "^GSPC", "name": "S&P 500"},
        {"ticker": "^DJI",  "name": "Dow Jones"},
        {"ticker": "QQQ",   "name": "QQQ ETF"},
    ],
    "🇪🇺 Europa": [
        {"ticker": "^STOXX50E", "name": "Euro Stoxx 50"},
        {"ticker": "^GDAXI",    "name": "DAX (DE)"},
        {"ticker": "^FTSE",     "name": "FTSE 100 (UK)"},
        {"ticker": "^OMXC25",   "name": "OMX C25 (DK)"},
    ],
    "🌏 Asien": [
        {"ticker": "^N225",     "name": "Nikkei 225 (JP)"},
        {"ticker": "^HSI",      "name": "Hang Seng (HK)"},
        {"ticker": "000001.SS", "name": "Shanghai (CN)"},
    ],
    "🌎 Øvrige": [
        {"ticker": "^BVSP",   "name": "Bovespa (BR)"},
        {"ticker": "GC=F",    "name": "Guld"},
        {"ticker": "CL=F",    "name": "Olie (WTI)"},
        {"ticker": "BTC-USD", "name": "Bitcoin"},
    ],
}

ALL_INDEX_TICKERS = [t for group in INDICES.values() for t in group]

# --- Telegram ---
TELEGRAM_TOKEN   = "8498629867:AAGjp1odBcDBZZs8bwco6S06TXg4J0L7qV0"
TELEGRAM_CHAT_ID = "7020024369"

# ─────────────────────────────────────────────────────────────
#  TIDSPUNKTER — 2 daglige beskeder (gratis PythonAnywhere)
#
#  Kl. 13:30 dansk tid = 12:30 UTC  (før US åbner kl. 15:30)
#  Kl. 22:00 dansk tid = 21:00 UTC  (efter US lukker kl. 22:00)
#
#  I PythonAnywhere skal du bruge UTC-tiderne:
#  Task 1: python3 /home/DITBRUGERNAVN/stockbot/bot.py midday  → 12:30 UTC
#  Task 2: python3 /home/DITBRUGERNAVN/stockbot/bot.py evening → 21:00 UTC
#  Søndag:  python3 /home/DITBRUGERNAVN/stockbot/bot.py midday → kører søndagsoversigt
# ─────────────────────────────────────────────────────────────
SCHEDULE_MIDDAY  = "13:30"   # Dansk tid — kombineret morgen+middag besked
SCHEDULE_EVENING = "22:00"   # Dansk tid — aftensopsummering

# ─────────────────────────────────────────────────────────────
#  RSS FEEDS
# ─────────────────────────────────────────────────────────────

TRUMP_FEEDS = [
    "https://feeds.reuters.com/reuters/politicsNews",
    "https://www.cnbc.com/id/10000113/device/rss/rss.html",
    "https://feeds.bloomberg.com/politics/news.rss",
    "https://moxie.foxbusiness.com/google-manager/feeds/latest.xml",
]

MACRO_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
]

MARKET_MOVING_FEEDS = [
    "https://www.benzinga.com/feed",
    "https://www.investors.com/feed/",
]

TRUMP_KEYWORDS = [
    "trump", "white house", "tariff", "tariffs", "executive order",
    "president", "administration", "trade war", "sanctions", "truth social",
    "mar-a-lago", "maga", "trade deal", "import tax"
]

CEO_KEYWORDS = [
    "ceo", "chief executive", "chairman", "board", "fired", "resigns",
    "appointed", "steps down", "raises guidance", "cuts guidance",
    "beats earnings", "misses earnings", "buyback", "dividend"
]
