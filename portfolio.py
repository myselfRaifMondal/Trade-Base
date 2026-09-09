import logging
import sqlite3
import yfinance as yf   
from collections import defaultdict
import pandas as pd 

logger = logging.getLogger(__name__)

def get_trade_history_df(username):
    trades = get_user_trades(username)
    df = pd.DataFrame(trades, columns=["Symbol", "Action", "Quantity", "Price", "Timestamp"])
    df["Price"] = df["Price"].round(2)
    return df.sort_values(by="Timestamp", ascending=False)

def get_equity_curve(username):
    trades = get_user_trades(username)
    pnl_data = []
    holdings = defaultdict(int)
    cost_basis = defaultdict(float)
    realized_pnl = 0.0

    for symbol, action, qty, price, ts in sorted(trades, key=lambda x: x[4]):
        if action == "BUY":
            holdings[symbol] += qty
            cost_basis[symbol] += qty * price
        elif action == "SELL":
            if holdings[symbol] >= qty:
                avg_cost = cost_basis[symbol] / holdings[symbol]
                pnl = qty * (price - avg_cost)
                realized_pnl += pnl
                cost_basis[symbol] -= avg_cost * qty
                holdings[symbol] -= qty
        pnl_data.append((ts, realized_pnl))
    return pd.DataFrame(pnl_data, columns=["Timestamp", "Realized_PnL"])

def get_leaderboard():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [u[0] for u in c.fetchall()]
    conn.close()

    data = []
    for user in users:
        _, _, realized, _ = calculate_portfolio(user)
        data.append((user, realized))
    df = pd.DataFrame(data, columns=["User", "Realized_PnL"])
    return df.sort_values(by="Realized_PnL", ascending=False)

def get_user_trades(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT symbol, action, quantity, price, timestamp FROM trades WHERE username=?", (username,))
    trades = c.fetchall()
    conn.close()
    return trades

def fetch_current_price(symbol):
    """Return the latest close price for ``symbol``, or ``None`` when unavailable.

    Isolated from :func:`calculate_portfolio` so the network call can be
    replaced in tests (see the ``price_lookup`` parameter). ``None`` means the
    price is unknown, which callers report as 0.0 while leaving unrealized P&L
    untouched rather than booking a fake 100% loss.
    """
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="1d")
        if hist.empty or "Close" not in hist or hist["Close"].empty:
            logger.warning(
                "No price data returned for %s (unknown or delisted symbol?); "
                "treating current price as 0.0",
                symbol,
            )
            return None
        return hist["Close"].iloc[-1]
    except Exception as exc:
        logger.warning(
            "Failed to fetch current price for %s: %s; treating current price as 0.0",
            symbol,
            exc,
            exc_info=True,
        )
        return None


def calculate_portfolio(username, trades_provider=None, price_lookup=None):
    """Return ``(holdings, current_prices, realized_pnl, unrealized_pnl)``.

    ``trades_provider`` and ``price_lookup`` exist purely for testing: they
    default to :func:`get_user_trades` (SQLite) and :func:`fetch_current_price`
    (yfinance), so existing callers are unaffected.
    """
    trades_provider = trades_provider or get_user_trades
    price_lookup = price_lookup or fetch_current_price

    trades = trades_provider(username)
    holdings = defaultdict(int)
    cost_basis = defaultdict(float)
    realized_pnl = 0.0

    for symbol, action, qty, price, _ in trades:
        if action == "BUY":
            holdings[symbol] += qty
            cost_basis[symbol] += qty * price
        elif action == "SELL":
            if holdings[symbol] >= qty:
                avg_cost = cost_basis[symbol] / holdings[symbol]
                realized_pnl += qty * (price - avg_cost)
                holdings[symbol] -= qty
                cost_basis[symbol] -= qty * avg_cost
    unrealized_pnl = 0.0
    current_prices = {}
    for symbol in holdings:
        if holdings[symbol] == 0:
            continue
        current_price = price_lookup(symbol)
        if current_price is None:
            current_prices[symbol] = 0.0
            continue
        current_prices[symbol] = current_price
        avg_cost = cost_basis[symbol] / holdings[symbol]
        unrealized_pnl += (current_price - avg_cost) * holdings[symbol]
    return holdings, current_prices, realized_pnl, unrealized_pnl
