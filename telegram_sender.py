"""
telegram_sender.py
Sender beskeder til Telegram via HTML.
Hvis HTML fejler automatisk pga. ugyldige tegn, sendes plain text som fallback.
"""

import requests
import re
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def _strip_html(text: str) -> str:
    """Fjerner alle HTML-tags og laver plain text."""
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text


def _send_chunk(chunk: str, parse_mode: str = "HTML") -> tuple[bool, str]:
    """Sender én chunk. Returnerer (success, error_description)."""
    if TELEGRAM_TOKEN == "DIN_BOT_TOKEN_HER":
        print("[INFO] Telegram ikke konfigureret — printer til terminal:\n")
        print(chunk)
        return True, ""

    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     chunk,
        "parse_mode":               parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.ok:
            return True, ""
        desc = r.json().get("description", r.text[:200])
        return False, desc
    except Exception as e:
        return False, str(e)


def send_message(text: str) -> bool:
    """
    Sender besked til Telegram.
    1. Forsøger HTML
    2. Hvis HTML fejler pga. parse-fejl → sender plain text automatisk
    """
    chunks  = [text[i:i+4000] for i in range(0, len(text), 4000)]
    success = True

    for chunk in chunks:
        ok, err = _send_chunk(chunk, parse_mode="HTML")

        if not ok:
            # HTML parse fejl — strip tags og send plain text
            if "parse" in err.lower() or "tag" in err.lower() or "entities" in err.lower():
                print(f"[WARN] HTML fejl, sender plain text: {err[:80]}")
                plain    = _strip_html(chunk)
                ok2, e2  = _send_chunk(plain, parse_mode="")
                if not ok2:
                    print(f"[ERROR] Plain text fejlede også: {e2[:100]}")
                    success = False
            else:
                print(f"[ERROR] Telegram: {err[:100]}")
                success = False

    return success


def test_connection() -> bool:
    return send_message("✅ <b>StockBot er online!</b> Forbindelsen virker. 🚀")
