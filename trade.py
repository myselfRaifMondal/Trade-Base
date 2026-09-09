import logging
import sqlite3
from datetime import datetime 
import yfinance as yf   

logger = logging.getLogger(__name__)


def _fetch_price_with_reason(symbol):
    """Return (price, error_reason). On success error_reason is None."""
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="1d")
        if hist.empty or "Close" not in hist or hist["Close"].empty:
            reason = f"no price data returned for {symbol} (unknown or delisted symbol?)"
            logger.warning("Price lookup failed: %s", reason)
            return None, reason
        return hist["Close"].iloc[-1], None
    except Exception as exc:
        logger.warning("Price lookup failed for %s: %s", symbol, exc, exc_info=True)
        return None, f"{type(exc).__name__}: {exc}"


def fetch_price(symbol):
    price, _ = _fetch_price_with_reason(symbol)
    return price


def place_trade(username, symbol, action, quantity):
    price, reason = _fetch_price_with_reason(symbol.upper())
    if price is None:
        return False, f"Failed to fetch price: {reason}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)", (username, symbol.upper(), action.upper(), quantity, price, timestamp))
    conn.commit()
    conn.close()
    return True, f"{action.title()} {quantity} shares of {symbol.upper()} at ${round(price, 2)}"
