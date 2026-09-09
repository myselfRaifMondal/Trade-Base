"""Tests for the realized/unrealized P&L maths in :mod:`portfolio`.

``calculate_portfolio`` normally reads trades out of SQLite and prices out of
yfinance. Both are injected here, so these tests touch neither the disk nor the
network.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio import calculate_portfolio  # noqa: E402


def trades(*rows):
    """Build a trades_provider from ``(symbol, action, qty, price)`` rows."""
    stored = [
        (symbol, action, qty, price, f"2024-01-{i + 1:02d} 10:00:00")
        for i, (symbol, action, qty, price) in enumerate(rows)
    ]
    return lambda username: stored


def prices(**mapping):
    """Build a price_lookup from ``SYMBOL=price`` keyword arguments."""
    return lambda symbol: mapping.get(symbol)


def test_buy_then_full_sell_realizes_the_whole_gain():
    holdings, current_prices, realized, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(("AAPL", "BUY", 10, 100.0), ("AAPL", "SELL", 10, 130.0)),
        price_lookup=prices(AAPL=999.0),
    )

    assert realized == pytest.approx(300.0)
    # Position is flat, so there is nothing left to mark to market and no price
    # should have been looked up at all.
    assert holdings["AAPL"] == 0
    assert unrealized == pytest.approx(0.0)
    assert current_prices == {}


def test_buy_then_full_sell_realizes_a_loss():
    _, _, realized, _ = calculate_portfolio(
        "trader",
        trades_provider=trades(("AAPL", "BUY", 5, 200.0), ("AAPL", "SELL", 5, 180.0)),
        price_lookup=prices(AAPL=180.0),
    )

    assert realized == pytest.approx(-100.0)


def test_average_cost_basis_across_two_buys():
    # 10 @ 100 and 10 @ 200 -> average cost 150. Selling 20 @ 160 realizes
    # 20 * (160 - 150) = 200, not FIFO's 20 * 160 - (1000 + 2000) which is the
    # same here, so the discriminating check is the partial sell below plus the
    # residual basis asserted through unrealized P&L.
    holdings, current_prices, realized, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(
            ("MSFT", "BUY", 10, 100.0),
            ("MSFT", "BUY", 10, 200.0),
        ),
        price_lookup=prices(MSFT=175.0),
    )

    assert realized == pytest.approx(0.0)
    assert holdings["MSFT"] == 20
    assert current_prices == {"MSFT": 175.0}
    # (175 - 150) * 20
    assert unrealized == pytest.approx(500.0)


def test_partial_sell_uses_average_cost_and_leaves_the_rest_held():
    holdings, current_prices, realized, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(
            ("MSFT", "BUY", 10, 100.0),
            ("MSFT", "BUY", 10, 200.0),
            ("MSFT", "SELL", 5, 180.0),
        ),
        price_lookup=prices(MSFT=210.0),
    )

    # 5 * (180 - 150)
    assert realized == pytest.approx(150.0)
    assert holdings["MSFT"] == 15
    # Remaining basis is 3000 - 5 * 150 = 2250, i.e. still 150/share.
    assert unrealized == pytest.approx((210.0 - 150.0) * 15)
    assert current_prices == {"MSFT": 210.0}


def test_sell_larger_than_holding_is_ignored():
    holdings, _, realized, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(
            ("TSLA", "BUY", 5, 100.0),
            ("TSLA", "SELL", 50, 500.0),
        ),
        price_lookup=prices(TSLA=100.0),
    )

    # The oversized sell must not book a phantom profit or move the position.
    assert realized == pytest.approx(0.0)
    assert holdings["TSLA"] == 5
    assert unrealized == pytest.approx(0.0)


def test_sell_with_no_position_at_all_is_ignored():
    holdings, current_prices, realized, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(("NVDA", "SELL", 1, 900.0)),
        price_lookup=prices(NVDA=900.0),
    )

    assert realized == pytest.approx(0.0)
    assert holdings["NVDA"] == 0
    assert unrealized == pytest.approx(0.0)
    assert current_prices == {}


def test_realized_pnl_is_summed_across_symbols():
    _, _, realized, _ = calculate_portfolio(
        "trader",
        trades_provider=trades(
            ("AAPL", "BUY", 10, 100.0),
            ("TSLA", "BUY", 10, 50.0),
            ("AAPL", "SELL", 10, 110.0),
            ("TSLA", "SELL", 10, 40.0),
        ),
        price_lookup=prices(),
    )

    # +100 on AAPL, -100 on TSLA.
    assert realized == pytest.approx(0.0)


def test_unknown_price_does_not_book_a_fake_total_loss():
    holdings, current_prices, _, unrealized = calculate_portfolio(
        "trader",
        trades_provider=trades(("DELISTED", "BUY", 10, 100.0)),
        price_lookup=lambda symbol: None,
    )

    assert holdings["DELISTED"] == 10
    assert current_prices == {"DELISTED": 0.0}
    assert unrealized == pytest.approx(0.0)


def test_defaults_fall_back_to_the_sqlite_and_yfinance_helpers(monkeypatch):
    """Existing call sites pass only a username; the defaults must still wire up."""
    import portfolio

    monkeypatch.setattr(
        portfolio,
        "get_user_trades",
        lambda username: [("AAPL", "BUY", 2, 10.0, "2024-01-01 10:00:00")],
    )
    monkeypatch.setattr(portfolio, "fetch_current_price", lambda symbol: 15.0)

    holdings, current_prices, realized, unrealized = portfolio.calculate_portfolio("trader")

    assert holdings["AAPL"] == 2
    assert current_prices == {"AAPL": 15.0}
    assert realized == pytest.approx(0.0)
    assert unrealized == pytest.approx(10.0)
