"""
formatter.py – HTML til Telegram
2 beskeder dagligt: middag (13:30) og aften (22:00)
"""

from datetime import datetime
from config import PORTFOLIO, MAG7, INDICES


# ── Helpers ──────────────────────────────────────────────────

def _arrow(pct: float) -> str:
    if pct > 3:    return "🚀"
    if pct > 1:    return "📈"
    if pct > 0.2:  return "🟢"
    if pct > -0.2: return "➡️"
    if pct > -1:   return "🔴"
    if pct > -3:   return "📉"
    return "💥"

def _sign(pct: float) -> str:
    return f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"

def _price(p: float, cur: str = "USD") -> str:
    s = "€" if cur == "EUR" else ("£" if cur == "GBP" else "$")
    return f"{s}{p:,.2f}"

def _esc(t: str) -> str:
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _cap(t: str, n: int = 75) -> str:
    t = _esc(t)
    return t[:n] + "…" if len(t) > n else t

def _link(title: str, url: str) -> str:
    return f'<a href="{url}">{_cap(title, 80)}</a>'

def _vol_label(r: float) -> str:
    if r > 2.5: return "🔥 Meget høj"
    if r > 1.4: return "⬆️ Høj"
    if r < 0.5: return "⬇️ Lav"
    return "➡️ Normal"

def _fmt_vol(v: int) -> str:
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.0f}K"
    return str(v)

def _analyst_emoji(rec: str) -> str:
    r = (rec or "").lower().replace(" ","").replace("_","")
    return {"strongbuy":"💚","buy":"🟢","hold":"🟡","sell":"🔴","strongsell":"💔"}.get(r, "❓")

def _analyst_label(rec: str) -> str:
    r = (rec or "").lower().replace(" ","").replace("_","")
    return {"strongbuy":"Stærkt køb","buy":"Køb","hold":"Hold",
            "sell":"Sælg","strongsell":"Stærkt sælg"}.get(r, "")

def _div(title: str) -> str:
    return f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n<b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

def _sent_icon(s: str) -> str:
    return {"positive":"🟢","negative":"🔴","neutral":"➡️"}.get(s, "")

def _news_block(items: list, n: int = 3) -> list:
    out = []
    for item in (items or [])[:n]:
        if not item.get("link"): continue
        icon = _sent_icon(item.get("sentiment",""))
        out.append(f"  {icon} {_link(item['title'], item['link'])}")
        s = (item.get("summary") or "").strip()
        if s and len(s) > 25:
            out.append(f"    <i>↳ {_cap(s, 140)}</i>")
        out.append("")
    return out


# ── Stock block ──────────────────────────────────────────────

def _stock_block(q: dict, news: list = None, skip_news_msg: str = "") -> list:
    out = []
    t   = q["ticker"]
    cur = q.get("currency","USD")

    out.append(f"{_arrow(q['change_pct'])} <b>{_cap(q['name'],28)}</b> (<code>{t}</code>)")

    pm_str = ""
    if q.get("premarket_change") is not None:
        now   = datetime.now().hour
        icon  = "🌙" if (now >= 22 or now < 9) else "🌤"
        label = "After" if now >= 16 else "Pre"
        pm_str = f"   {icon} {label}: {_sign(q['premarket_change'])}"
    out.append(f"  💰 <b>{_price(q['price'],cur)}</b>  {_sign(q['change_pct'])}{pm_str}")

    if q.get("volume") and q.get("volume_ratio") and q["volume"] > 0:
        out.append(f"  📊 Vol: {_fmt_vol(q['volume'])}  {_vol_label(q['volume_ratio'])}")

    hi = q.get("52w_high"); lo = q.get("52w_low")
    if hi and lo and hi > 0:
        pct_hi = ((q["price"] - hi) / hi) * 100
        out.append(f"  📏 52u: {_price(lo,cur)} → {_price(hi,cur)}  <i>({_sign(pct_hi)} fra high)</i>")

    ma50 = q.get("ma50"); ma200 = q.get("ma200")
    if ma50 or ma200:
        parts = []
        if ma50:
            d = ((q["price"]-ma50)/ma50)*100
            parts.append(f"MA50: {_price(ma50,cur)} {'⬆️' if d>0 else '⬇️'} {_sign(d)}")
        if ma200:
            d = ((q["price"]-ma200)/ma200)*100
            parts.append(f"MA200: {_price(ma200,cur)} {'⬆️' if d>0 else '⬇️'} {_sign(d)}")
        out.append(f"  📈 {' │ '.join(parts)}")

    pe_p = []
    if q.get("pe_ratio"):   pe_p.append(f"P/E: {q['pe_ratio']}")
    if q.get("forward_pe"): pe_p.append(f"Fwd P/E: {q['forward_pe']}")
    if q.get("eps"):        pe_p.append(f"EPS: ${q['eps']}")
    if pe_p: out.append(f"  💹 {' │ '.join(pe_p)}")

    if q.get("target_mean"):
        upside = ((q["target_mean"] - q["price"]) / q["price"]) * 100
        cnt    = f" ({q['analyst_count']} analytikere)" if q.get("analyst_count") else ""
        al     = _analyst_label(q.get("analyst_rec",""))
        ae     = _analyst_emoji(q.get("analyst_rec",""))
        out.append(f"  🎯 Kursmål: <b>{_price(q['target_mean'],cur)}</b> ({_sign(upside)}){cnt}")
        if q.get("target_low") and q.get("target_high"):
            out.append(f"  📐 Range: {_price(q['target_low'],cur)} – {_price(q['target_high'],cur)}")
        if al:
            out.append(f"  {ae} Anbefaling: <b>{al}</b>")

    if q.get("earnings_date"):
        try:
            days = (datetime.strptime(q["earnings_date"],"%Y-%m-%d") - datetime.now()).days
            cd   = f" (om {days} dage)" if days >= 0 else ""
        except Exception:
            cd = ""
        out.append(f"  📅 Earnings: {q['earnings_date']}{cd}")

    if skip_news_msg:
        out.append(f"  📰 <i>{_esc(skip_news_msg)}</i>")
    elif news:
        out.append("")
        out += _news_block(news, 3)
    else:
        out.append("")

    return out


# ── Sektioner ────────────────────────────────────────────────

def format_portfolio_section(quotes: dict, news: dict) -> str:
    out  = [_div("📊 DIN PORTEFØLJE")]
    seen = set()
    for group, stocks in PORTFOLIO.items():
        out.append(f"\n🗂 <b>{_esc(group)}</b>")
        for s in stocks:
            t = s["ticker"]
            if t in seen: continue
            seen.add(t)
            q = quotes.get(t)
            if not q:
                out.append(f"  <code>{t}</code> — data utilgængelig\n")
                continue
            out += _stock_block(q, news.get(t, []))
    return "\n".join(out)


def format_mag7_section(quotes: dict, news: dict) -> str:
    portfolio_tickers = {s["ticker"] for g in PORTFOLIO.values() for s in g}
    out = [_div("💎 MAG7")]
    for s in MAG7:
        t = s["ticker"]
        q = quotes.get(t)
        if not q: continue
        if t in portfolio_tickers:
            out += _stock_block(q, news=None,
                                skip_news_msg="Se nyheder i din portefølje ovenfor 👆")
        else:
            out += _stock_block(q, news.get(t, []))
    return "\n".join(out)


def format_indices_section(quotes: dict) -> str:
    out = [_div("🌍 GLOBALE INDEKS")]
    for region, tickers in INDICES.items():
        out.append(f"\n<b>{region}</b>")
        for idx in tickers:
            q = quotes.get(idx["ticker"])
            if not q: continue
            pm = ""
            if q.get("premarket_change") is not None:
                now  = datetime.now().hour
                icon = "🌙" if (now >= 22 or now < 9) else "🌤"
                pm   = f"  {icon} {_sign(q['premarket_change'])}"
            out.append(
                f"{_arrow(q['change_pct'])} <b>{idx['name']}</b>  "
                f"{_price(q['price'],q.get('currency','USD'))}  {_sign(q['change_pct'])}{pm}"
            )
    out.append("")
    return "\n".join(out)


def format_daily_recap(recap_text: str) -> str:
    if not recap_text: return ""
    return recap_text + "\n"


def format_stock_of_day(sotd: dict) -> str:
    if not sotd: return ""
    out  = [_div("⭐ DAGENS AKTIE — Værd at holde øje med")]
    cur  = sotd.get("currency","USD")
    rec  = _analyst_label(sotd.get("analyst_rec",""))
    ae   = _analyst_emoji(sotd.get("analyst_rec",""))
    reasons = " · ".join(sotd.get("reasons",[]))

    out.append(f"<b>{_cap(sotd['name'],30)}</b> (<code>{sotd['ticker']}</code>)")
    out.append(f"  💡 <i>Hvorfor: {_esc(reasons)}</i>")
    out.append(f"  {_arrow(sotd['change_pct'])} Kurs: <b>{_price(sotd['price'],cur)}</b>  {_sign(sotd['change_pct'])}")

    if sotd.get("volume_ratio") and sotd["volume_ratio"] > 1:
        out.append(f"  📊 Vol: {_fmt_vol(sotd['volume'])}  {_vol_label(sotd['volume_ratio'])}")

    ma50 = sotd.get("ma50"); ma200 = sotd.get("ma200")
    if ma50 or ma200:
        parts = []
        if ma50:
            d = ((sotd["price"]-ma50)/ma50)*100
            parts.append(f"MA50: {_sign(d)}")
        if ma200:
            d = ((sotd["price"]-ma200)/ma200)*100
            parts.append(f"MA200: {_sign(d)}")
        out.append(f"  📈 {' │ '.join(parts)}")

    if sotd.get("target_mean"):
        upside = ((sotd["target_mean"] - sotd["price"]) / sotd["price"]) * 100
        out.append(f"  🎯 Analytikermål: {_price(sotd['target_mean'],cur)} ({_sign(upside)})")
    if rec:
        out.append(f"  {ae} Anbefaling: {rec}")
    if sotd.get("sector"):
        out.append(f"  🏭 {sotd['sector']}")

    out.append(f"\n  ⚠️ <i>Ikke en anbefaling — lav altid din egen research!</i>")
    out.append("")
    return "\n".join(out)


def format_macro_section(indicators: dict, macro_news: list) -> str:
    out = [_div("📉 MAKROØKONOMI")]
    labels = {
        "cpi_yoy":      "🧾 CPI (inflation)",
        "core_cpi":     "🧾 Core CPI",
        "unemployment": "👷 Arbejdsløshed",
        "fed_rate":     "🏦 Fed Funds Rate",
    }
    for key, label in labels.items():
        ind = indicators.get(key)
        if not ind: continue
        s     = "+" if ind["change"] >= 0 else ""
        emoji = "🔺" if ind["change"] > 0 else ("🔻" if ind["change"] < 0 else "➡️")
        out.append(f"{emoji} {label}: <b>{ind['value']}%</b>  ({s}{ind['change']}% — {ind['date']})")

    cpi = indicators.get("cpi_yoy"); unemp = indicators.get("unemployment")
    analysis = []
    if cpi:
        if cpi["value"] > 3.5:   analysis.append("🔥 Høj inflation → Fed holder renten → pres på vækstaktier")
        elif cpi["value"] < 2.5: analysis.append("❄️ Lav inflation → Mulige rentenedsættelser → positivt for aktier")
        else:                     analysis.append("✅ Inflation tæt på Feds mål (2-3%)")
    if unemp and abs(unemp["change"]) > 0.1:
        if unemp["change"] > 0: analysis.append("⚠️ Stigende ledighed → svagere forbrugsvækst")
        else:                    analysis.append("💪 Faldende ledighed → stærkt arbejdsmarked")
    if analysis:
        out.append("\n📖 <b>Hvad betyder det?</b>")
        for a in analysis: out.append(f"  {a}")

    if macro_news:
        out.append("\n📰 <b>Makronyheder:</b>")
        out += _news_block(macro_news, 4)
    out.append("")
    return "\n".join(out)


def format_trump_section(items: list) -> str:
    if not items: return ""
    out = [_div("🇺🇸 TRUMP & POLITIK")]
    out += _news_block(items, 5)
    out.append("")
    return "\n".join(out)


def format_market_news_section(items: list) -> str:
    if not items: return ""
    out = [_div("⚡ MARKEDSBEVÆGENDE NYHEDER")]
    out += _news_block(items, 5)
    out.append("")
    return "\n".join(out)


def format_ceo_section(items: list) -> str:
    if not items: return ""
    out = [_div("🎙 CEO & LEDELSE")]
    out += _news_block(items, 4)
    out.append("")
    return "\n".join(out)


def format_earnings_section(upcoming: list) -> str:
    if not upcoming: return ""
    out = [_div("📅 KOMMENDE EARNINGS")]
    for e in upcoming:
        try:
            days = (datetime.strptime(e["earnings_date"],"%Y-%m-%d") - datetime.now()).days
            cd   = f"om {days} dag{'e' if days!=1 else ''}"
        except Exception:
            cd = ""
        cur = e.get("currency","USD")
        out.append(f"\n📌 <b>{_esc(e['name'])}</b> (<code>{e['ticker']}</code>)")
        out.append(f"  📆 {e['earnings_date']} ({cd})   💰 {_price(e['price'],cur)}  {_sign(e['change_pct'])}")
        pe_p = []
        if e.get("pe_ratio"):   pe_p.append(f"P/E: {e['pe_ratio']}")
        if e.get("forward_pe"): pe_p.append(f"Fwd P/E: {e['forward_pe']}")
        if e.get("eps_forward"):pe_p.append(f"EPS est: ${e['eps_forward']}")
        if pe_p: out.append(f"  💹 {' │ '.join(pe_p)}")
        if e.get("target_mean"):
            upside = ((e["target_mean"]-e["price"])/e["price"])*100
            out.append(f"  🎯 Analytikermål: {_price(e['target_mean'],cur)} ({_sign(upside)})")
            if e.get("target_low") and e.get("target_high"):
                out.append(f"  📐 Range: {_price(e['target_low'],cur)} – {_price(e['target_high'],cur)}")
        al = _analyst_label(e.get("analyst_rec",""))
        if al: out.append(f"  {_analyst_emoji(e.get('analyst_rec',''))} {al}")
        if e.get("sector"): out.append(f"  🏭 {e['sector']}")
        out.append("  <i>💡 Beat EPS+Rev → +3-8% dagen efter · Miss → -5-15% · Tjek guidance!</i>")
    out.append("")
    return "\n".join(out)


def format_weekly_watchlist(quotes: dict, watchlist_history: list = None) -> str:
    watch = []
    for q in quotes.values():
        if not q or not q.get("52w_high"): continue
        drop = ((q["price"] - q["52w_high"]) / q["52w_high"]) * 100
        if drop < -15:
            watch.append({**q, "drop": round(drop,1)})
    if not watch and not watchlist_history:
        return ""

    out = [_div("🔭 WATCHLIST")]
    if watch:
        watch.sort(key=lambda x: x["drop"])
        for w in watch[:5]:
            cur = w.get("currency","USD")
            out.append(f"👀 <b>{_cap(w['name'],25)}</b> (<code>{w['ticker']}</code>)")
            out.append(f"  {_price(w['price'],cur)}  {w['drop']:.1f}% fra 52u-high")
            if w.get("target_mean"):
                upside = ((w["target_mean"]-w["price"])/w["price"])*100
                out.append(f"  🎯 {_price(w['target_mean'],cur)} ({_sign(upside)})")
            al = _analyst_label(w.get("analyst_rec",""))
            if al: out.append(f"  {_analyst_emoji(w.get('analyst_rec',''))} {al}")
            out.append(f"  💡 <i>Mulig opkøbsmulighed — lav din egen research</i>\n")

    if watchlist_history:
        out.append("\n📋 <b>Ugens dagens-aktier:</b>")
        for item in watchlist_history:
            out.append(f"  • {_esc(item)}")

    return "\n".join(out)


# ── Samlede beskeder ─────────────────────────────────────────

def build_midday_message(data: dict) -> str:
    """
    Kl. 13:30 — Kombineret besked:
    Dagens aktie → Nyhedsrecap → Nyheder (Trump/marked) →
    Din portefølje → MAG7 → Indeks → Makro → Earnings
    """
    dato   = datetime.now().strftime("%A %d. %b %Y")
    header = (
        f"📊 <b>DAGLIG OVERSIGT — {dato}</b>\n"
        f"<i>Kl. 13:30 · US marked åbner om 2 timer (kl. 15:30)</i>\n"
    )
    parts = [
        header,
        format_stock_of_day(data.get("stock_of_day")),
        format_daily_recap(data.get("daily_recap","")),
        format_trump_section(data.get("trump_news",[])),
        format_market_news_section(data.get("market_news",[])),
        format_portfolio_section(data["quotes"], data.get("portfolio_news",{})),
        format_mag7_section(data["quotes"], data.get("mag7_news",{})),
        format_indices_section(data["quotes"]),
        format_macro_section(data.get("indicators",{}), data.get("macro_news",[])),
        format_earnings_section(data.get("upcoming_earnings",[])),
    ]
    return "\n".join(p for p in parts if p)


def build_evening_message(data: dict) -> str:
    """
    Kl. 22:00 — Aftensopsummering:
    Dagens vindere/tabere → Recap → Portefølje → MAG7 → Indeks → Makro → Watchlist
    """
    dato   = datetime.now().strftime("%A %d. %b")
    header = f"🌙 <b>AFTENSOPSUMMERING — {dato}</b>\n<i>US markedet er lukket</i>\n"

    portfolio_tickers = {s["ticker"] for g in PORTFOLIO.values() for s in g}
    movers = sorted(
        [q for t, q in data["quotes"].items() if t in portfolio_tickers and q],
        key=lambda x: x["change_pct"], reverse=True
    )
    winner_section = ""
    if len(movers) >= 2:
        b, w = movers[0], movers[-1]
        winner_section = (
            _div("🏆 DAGENS BEVÆGELSER") +
            f"🥇 Bedste:    <b>{_cap(b['name'],25)}</b>  {_sign(b['change_pct'])}\n"
            f"🥴 Dårligste: <b>{_cap(w['name'],25)}</b>  {_sign(w['change_pct'])}\n"
        )

    parts = [
        header,
        winner_section,
        format_daily_recap(data.get("daily_recap","")),
        format_trump_section(data.get("trump_news",[])),
        format_market_news_section(data.get("market_news",[])),
        format_portfolio_section(data["quotes"], data.get("portfolio_news",{})),
        format_mag7_section(data["quotes"], data.get("mag7_news",{})),
        format_indices_section(data["quotes"]),
        format_macro_section(data.get("indicators",{}), data.get("macro_news",[])),
        format_weekly_watchlist(data["quotes"]),
    ]
    return "\n".join(p for p in parts if p)


def build_sunday_message(data: dict) -> str:
    dato   = datetime.now().strftime("%A %d. %b %Y")
    header = f"☀️ <b>SØNDAGSOVERSIGT — {dato}</b>\n<i>Weekend-recap + hvad venter mandag</i>\n"

    quotes            = data.get("quotes",{})
    portfolio_tickers = {s["ticker"] for g in PORTFOLIO.values() for s in g}
    mag7_tickers      = {s["ticker"] for s in MAG7}

    port_week = sorted(
        [q for q in quotes.values() if q and q.get("ticker") in portfolio_tickers
         and q.get("week_change_pct") is not None],
        key=lambda x: x.get("week_change_pct",0), reverse=True
    )
    week_section = ""
    if port_week:
        week_section = _div("📅 UGENS PERFORMANCE (Din portefølje)") + "\n"
        for q in port_week:
            wc = q.get("week_change_pct",0)
            week_section += f"{_arrow(wc)} <b>{_cap(q['name'],25)}</b>  uge: {_sign(wc)}\n"

    mag7_week = sorted(
        [q for q in quotes.values() if q and q.get("ticker") in mag7_tickers
         and q.get("week_change_pct") is not None],
        key=lambda x: x.get("week_change_pct",0), reverse=True
    )
    mag7_section = ""
    if mag7_week:
        mag7_section = _div("💎 MAG7 UGENS PERFORMANCE") + "\n"
        for q in mag7_week:
            wc = q.get("week_change_pct",0)
            mag7_section += f"{_arrow(wc)} <b>{_cap(q['name'],20)}</b>  {_sign(wc)}\n"

    monday = [_div("🔮 HVAD VENTER MANDAG?")]
    upcoming = data.get("upcoming_earnings",[])
    if upcoming:
        monday.append("📅 <b>Earnings denne uge:</b>")
        for e in upcoming[:5]:
            monday.append(f"  • <b>{_esc(e['name'])}</b> — {e['earnings_date']}")
    macro_news = data.get("macro_news",[])
    if macro_news:
        monday.append("\n📰 <b>Hold øje med:</b>")
        monday += _news_block(macro_news, 4)
    monday.append("\n💡 <i>US futures åbner søndag kl. 23:00 dansk tid — første signal for mandagen</i>")

    parts = [
        header, week_section, mag7_section,
        format_daily_recap(data.get("daily_recap","")),
        format_macro_section(data.get("indicators",{}), []),
        format_trump_section(data.get("trump_news",[])),
        "\n".join(monday),
        format_weekly_watchlist(quotes, data.get("watchlist_history",[])),
    ]
    return "\n".join(p for p in parts if p)
