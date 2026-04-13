# 📱 StockBot — Komplet Setup Guide

Alt er gratis. Det eneste du behøver er en computer/Raspberry Pi der kører 24/7
(eller en gratis cloud-server — se trin 5).

---

## TRIN 1 — Opret din Telegram Bot (5 min)

1. Åbn Telegram og søg efter **@BotFather**
2. Skriv `/newbot`
3. Giv botten et navn, fx `MinStockBot`
4. Giv den et brugernavn der slutter på `bot`, fx `minstockbot_bot`
5. BotFather svarer med dit **Token** — det ser sådan ud:
   ```
   1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Kopier token'et — du skal bruge det om lidt

**Find dit Chat ID:**
1. Start en samtale med din nye bot (søg den op og skriv "hej")
2. Åbn i browser: `https://api.telegram.org/botDIN_TOKEN/getUpdates`
   (erstat DIN_TOKEN med dit token)
3. Find `"chat":{"id":XXXXXXXXX}` — det tal er dit Chat ID

---

## TRIN 2 — Installer Python-pakker

```bash
# Kræver Python 3.10+
pip install -r requirements.txt
```

---

## TRIN 3 — Sæt dine oplysninger ind i config.py

Åbn `config.py` og rediger disse to linjer:

```python
TELEGRAM_TOKEN  = "1234567890:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TELEGRAM_CHAT_ID = "123456789"
```

---

## TRIN 4 — Test at det virker

```bash
# Test Telegram-forbindelsen
python bot.py test

# Se en preview-besked i terminalen (uden at sende)
python bot.py preview

# Send morgenbesked med det samme
python bot.py morning
```

---

## TRIN 5 — Kør botten 24/7 (vælg én metode)

### Option A: Din egen computer / Raspberry Pi
```bash
# Kør i baggrunden (Linux/Mac)
nohup python bot.py &

# Eller med screen (anbefales)
screen -S stockbot
python bot.py
# Ctrl+A + D for at detache
```

### Option B: Gratis cloud-server (Render.com)

1. Gå til **render.com** og opret gratis konto
2. "New" → "Background Worker"
3. Forbind din GitHub (upload filerne til et privat repo)
4. Start command: `python bot.py`
5. Sæt environment variables i Render:
   - `TELEGRAM_TOKEN` = dit token
   - `TELEGRAM_CHAT_ID` = dit chat id
6. Opdater `config.py` til at læse fra env:
   ```python
   import os
   TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "DIN_BOT_TOKEN_HER")
   TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "DIN_CHAT_ID_HER")
   ```

### Option C: Gratis PythonAnywhere

1. Gå til **pythonanywhere.com** → gratis konto
2. Upload filerne
3. "Tasks" → tilføj 3 scheduled tasks:
   - `python /home/DITBRUGERNAVN/stockbot/bot.py morning` kl. 09:00
   - `python /home/DITBRUGERNAVN/stockbot/bot.py afternoon` kl. 16:00
   - `python /home/DITBRUGERNAVN/stockbot/bot.py evening` kl. 22:00

---

## TRIN 6 — Tilpas din portefølje

Åbn `config.py` og rediger `PORTFOLIO` sektionen:

```python
PORTFOLIO = {
    "AktieDepot": [
        {"ticker": "MSTR",  "name": "Strategy A"},
        {"ticker": "PNG",   "name": "Kraken Robotics"},
    ],
    ...
}
```

**Find den rigtige ticker:**
- Gå til finance.yahoo.com og søg din aktie
- Brug den ticker Yahoo viser (fx `QDVE.DE` for tyske børser, `WEBN.PA` for Paris)

---

## Hvad botten sender

### 🌅 Kl. 09:00 — Før markedet åbner
- Din portefølje med pre-market bevægelser
- MAG7 status
- Indeks (NASDAQ, S&P500, Dow Jones)
- Inflation/jobs data (hvis ny udgivelse)
- Trump nyheder
- Kommende earnings (næste 7 dage)

### 📈 Kl. 16:00 — Markedet er åbent
- Live kurser på alle dine aktier
- MAG7 live
- CEO-udtalelser og breaking news
- Trump nyheder

### 🌙 Kl. 22:00 — Opsummering
- Dagens vinder og taber i din portefølje
- Fuld opsummering
- Ugentlig watchlist (aktier faldet >15% fra 52-ugers high)
- Makroanalyse

---

## Fejlsøgning

| Problem | Løsning |
|---------|---------|
| `ModuleNotFoundError` | Kør `pip install -r requirements.txt` igen |
| Telegram sender ikke | Tjek token og chat_id i config.py |
| "data utilgængelig" på aktie | Tjek at ticker-symbolet er korrekt på Yahoo Finance |
| FRED data virker ikke | Tjek internetforbindelsen — FRED.stlouisfed.org |
| PNG ticker virker ikke | Kraken Robotics er på TSX Venture — prøv `PNG.V` |

---

## Filstruktur

```
stockbot/
├── config.py          ← Rediger kun denne
├── bot.py             ← Kør denne
├── data_fetcher.py    ← Henter data (yfinance + RSS)
├── formatter.py       ← Formaterer Telegram-beskeder
├── telegram_sender.py ← Sender til Telegram
├── requirements.txt
├── logs/
│   └── stockbot.log
└── SETUP.md           ← Denne fil
```

---

## Alt er 100% gratis

| Komponent | Tjeneste | Pris |
|-----------|----------|------|
| Kursdata | Yahoo Finance (yfinance) | Gratis |
| Nyheder | Yahoo Finance RSS | Gratis |
| Makrodata | FRED (Federal Reserve) | Gratis |
| Trump nyheder | RSS tracker | Gratis |
| Telegram bot | Telegram Bot API | Gratis |
| Hosting | PythonAnywhere / Render | Gratis tier |
