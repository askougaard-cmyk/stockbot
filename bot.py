"""
bot.py — kør: python3 bot.py [midday|evening|sunday|test|preview]

2 daglige beskeder (gratis PythonAnywhere):
  Kl. 13:30 — Kombineret oversigt (morgen + pre-market + nyheder)
  Kl. 22:00 — Aftensopsummering (dagens resultat + recap)
  Søndag 13:30 — Ugeoversigt
"""

import schedule, time, logging, sys, json, os
from datetime import datetime
from config import (ALL_TICKERS, MAG7, ALL_INDEX_TICKERS,
                    SCHEDULE_MIDDAY, SCHEDULE_EVENING)
from data_fetcher import (get_all_quotes, get_portfolio_news, get_mag7_news,
                           get_macro_news, get_trump_news, get_ceo_news,
                           get_macro_indicators, get_upcoming_earnings,
                           get_stock_of_the_day, get_weekly_summary_data,
                           get_daily_recap, get_market_moving_news)
from formatter import (build_midday_message, build_evening_message,
                        build_sunday_message)
from telegram_sender import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/stockbot.log"), logging.StreamHandler()]
)
log = logging.getLogger("stockbot")

WATCHLIST_FILE = "data/watchlist_history.json"


def _load_watchlist() -> list:
    try:
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_watchlist(items: list):
    os.makedirs("data", exist_ok=True)
    try:
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(items[-35:], f)
    except Exception as e:
        log.error(f"Watchlist gem fejl: {e}")


def _clear_watchlist():
    try:
        with open(WATCHLIST_FILE, "w") as f:
            json.dump([], f)
    except Exception:
        pass


def is_weekday() -> bool:
    return datetime.now().weekday() < 5   # 0=man … 4=fre

def is_sunday() -> bool:
    return datetime.now().weekday() == 6

def _sign_str(pct):
    return f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"


def collect(heavy=True) -> dict:
    all_t = list(set(ALL_TICKERS + [s["ticker"] for s in MAG7]
                     + [i["ticker"] for i in ALL_INDEX_TICKERS]))
    log.info("Henter kursdata...")
    quotes   = get_all_quotes(all_t)
    log.info("Henter nyheder...")
    p_news   = get_portfolio_news()
    m_news   = get_mag7_news()
    macro_n  = get_macro_news()
    log.info("Henter Trump/politik nyheder...")
    trump    = get_trump_news()
    log.info("Henter markedsbevægende nyheder...")
    mkt_news = get_market_moving_news()
    log.info("Henter CEO-nyheder...")
    ceo      = get_ceo_news()
    log.info("Henter earnings...")
    earn     = get_upcoming_earnings(all_t)
    log.info("Finder dagens aktie...")
    sotd     = get_stock_of_the_day()
    log.info("Laver nyhedsrecap...")
    recap    = get_daily_recap(p_news, m_news, macro_n, trump, mkt_news)
    inds     = {}
    if heavy:
        log.info("Henter makroindikatorer...")
        inds = get_macro_indicators()
    return dict(
        quotes=quotes, portfolio_news=p_news, mag7_news=m_news,
        macro_news=macro_n, trump_news=trump, ceo_news=ceo,
        market_news=mkt_news, upcoming_earnings=earn,
        indicators=inds, stock_of_day=sotd, daily_recap=recap
    )


# ── Jobs ────────────────────────────────────────────────────

def job_midday():
    """Kl. 13:30 — søndag=ugeoversigt, lørdag=ingenting, hverdag=middag"""
    if is_sunday():
        log.info("☀️ Søndag — sender ugeoversigt...")
        try:
            wl   = _load_watchlist()
            data = get_weekly_summary_data(watchlist_history=wl)
            send_message(build_sunday_message(data))
            _clear_watchlist()
            log.info("✅ Søndagsoversigt sendt")
        except Exception as e:
            log.error(e); send_message(f"⚠️ Fejl (søndag): {e}")
        return

    if not is_weekday():
        log.info("💤 Lørdag — ingen besked")
        return

    log.info("📊 Middagsbesked (kl. 13:30)...")
    try:
        data = collect(heavy=True)
        send_message(build_midday_message(data))

        # Gem dagens aktie til ugens watchlist
        sotd = data.get("stock_of_day")
        if sotd:
            dato  = datetime.now().strftime("%d/%m")
            entry = (f"{dato}: {sotd['name']} ({sotd['ticker']}) "
                     f"{_sign_str(sotd['change_pct'])} — "
                     f"{', '.join(sotd.get('reasons', []))}")
            wl = _load_watchlist()
            wl.append(entry)
            _save_watchlist(wl)

        log.info("✅ Middagsbesked sendt")
    except Exception as e:
        log.error(e); send_message(f"⚠️ Fejl (middag): {e}")


def job_evening():
    """Kl. 22:00 — kun hverdage"""
    if not is_weekday():
        log.info("💤 Weekend — ingen aftensbesked")
        return

    log.info("🌙 Aftensbesked (kl. 22:00)...")
    try:
        send_message(build_evening_message(collect(heavy=True)))
        log.info("✅ Aftensbesked sendt")
    except Exception as e:
        log.error(e); send_message(f"⚠️ Fejl (aften): {e}")


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "midday":
        job_midday()
    elif cmd == "evening":
        job_evening()
    elif cmd == "sunday":
        wl   = _load_watchlist()
        data = get_weekly_summary_data(watchlist_history=wl)
        send_message(build_sunday_message(data))
    elif cmd == "test":
        from telegram_sender import test_connection
        test_connection()
    elif cmd == "preview":
        data = collect(heavy=True)
        print(build_midday_message(data))
    else:
        # Kør som scheduler (til Mac/server der kører 24/7)
        schedule.every().day.at(SCHEDULE_MIDDAY).do(job_midday)
        schedule.every().day.at(SCHEDULE_EVENING).do(job_evening)
        log.info(f"⏰ Bot kører — middag: {SCHEDULE_MIDDAY} / aften: {SCHEDULE_EVENING}")
        log.info("💤 Lørdag: ingen beskeder | ☀️ Søndag: ugeoversigt kl. 13:30")
        while True:
            schedule.run_pending()
            time.sleep(30)
