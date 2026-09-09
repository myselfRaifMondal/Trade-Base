import streamlit as st
from db import init_db, ensure_user
from trade import place_trade
from portfolio import calculate_portfolio, get_trade_history_df, get_equity_curve, get_leaderboard
import plotly.express as px

init_db()

st.title("Ascendra Wealth Trade Base")

DEFAULT_USER = "Ad0rable"

user = st.sidebar.text_input("Trader name", DEFAULT_USER).strip()
if not user:
    st.sidebar.warning("Enter a trader name to start trading.")
    st.info("Pick a trader name in the sidebar to get started.")
    st.stop()

# Register the active trader so they show up on the leaderboard, which reads
# from the users table. Idempotent, so this is safe on every rerun.
ensure_user(user)

menu = ['Trade', 'Portfolio', "Leaderboard"]
page = st.sidebar.selectbox("Go to", menu)


if page == "Trade":
    st.subheader("Trade Execution")
    symbol = st.text_input("Stock Symbol", "AAPL")
    action = st.radio("Action", ["BUY", "SELL"])
    quantity = st.number_input("Quantity", min_value=1, step=1)
    if st.button("Place Trade"):
        success, msg = place_trade(user, symbol, action, quantity)
        if success:
            st.success(msg)
        else:
            st.error(msg)
if page == "Portfolio":    
    st.divider()
    st.header("Portfolio Overview")

    holdings, prices, realized, unrealized = calculate_portfolio(user)
    st.subheader("Holdings:")
    for sym, qty in holdings.items():
        if qty > 0:
            st.write(f"{sym}: {qty} shares @ ${round(prices[sym], 2)}")

    st.metric("Realized P&L", f"${round(realized, 2)}")
    st.metric("unrealized P&L", f"${round(unrealized, 2)}")
if page == "Leaderboard":
    st.divider()
    st.header("Leaderboard (Realized P&L)")

    lb_df = get_leaderboard()
    st.dataframe(lb_df, use_container_width=True)

st.divider()
st.header("Trade History")
history_df = get_trade_history_df(user)
st.dataframe(history_df, use_container_width=True)

st.divider()
st.header("Realized P&L Over Time")

equity_df = get_equity_curve(user)
if not equity_df.empty:
    fig = px.line(equity_df, x="Timestamp", y="Realized_PnL", title="Equity Curve")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No P&L data yet. Make some trades!")


