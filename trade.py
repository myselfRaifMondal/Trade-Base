import sqlite3
from datetime import datetime 
import yfinance as yf   

def fetch_price(symbol):
    try:
        data = yf.Ticker(symbol)
        hist = data.history(period="1d")
        return hist["Close"][-1]
    except:
        return None 

def place_trade(username, symbol, action, quantity):
    price = fetch_price(symbol.upper())
    if price is None:
        return False, "Failed to fetch price"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?)", (username, symbol.upper(), action.upper(), quantity, price, timestamp))
    conn.commit()
    conn.close()
    return True, f"{action.title()} {quantity} shares of {symbol.upper()} at ${round(price, 2)}"

