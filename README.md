[![](https://imgur.com/rY41C9X)](https://imgur.com/rY41C9X)
[![](https://imgur.com/IKdRsdQ)](https://imgur.com/IKdRsdQ)
[![](https://imgur.com/aGgBg6q)](https://imgur.com/aGgBg6q)
# 📈 Trade Base

Welcome to your personal, private stock market simulation playground — a **streamlit-based virtual trading terminal** made just for *you*.

💡 Think of it as your own Zerodha, Robinhood, or Upstox — but without any logins, risk, or angry customer support reps.

---
## ⚠️ Disclaimer

This app is for educational and entertainment purposes only.
It does not execute real trades, and no actual money is involved.

## ⚙️ Features

### 🔁 Paper Trading (Buy/Sell)
- Simulate buying and selling real stocks using **virtual currency**
- Trades are stored locally using SQLite
- No real money is involved, but it *feels* real

### 📊 Live Portfolio & Real-Time P&L
- View current holdings with average buy price
- Auto-calculates **unrealized and realized P&L** based on live stock prices via Yahoo Finance

### 🔒 Close Open Positions "FUTURE UPDATE"
- One-click exit from your holdings
- Trade logs updated automatically

### 🧠 Solo Mode "COMMUNITY VERSION COMING SOON"
- No login/signup headaches
- All trades are stored under a single default user (`"raif"` or `"default"`)

---

## 🏗️ Tech Stack

| Tool            | Role                        |
|-----------------|-----------------------------|
| `Streamlit`     | UI for trading + dashboard  |
| `SQLite`        | Stores all trades locally   |
| `yfinance`      | Live price data from Yahoo  |
| `Python 3.9+`   | The brain behind the app    |

---

## 🚀 Getting Started

### 1. Clone this repo

```bash
git clone https://github.com/your-username/virtual-paper-trading-app.git
cd virtual-paper-trading-app
```

### 2. Set up your virtual environment
```bash
python -m venv env
source env/bin/activate  # Mac/Linux
env\Scripts\activate.bat # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit app
```bash
streamlit run app.py
```

## File Structure

```
.
├── app.py              # Main streamlit app file
├── trade.py            # Trading logic (buy/sell)
├── portfolio.py        # Portfolio & P&L logic
├── users.db            # SQLite DB to store trades
├── requirements.txt    # Python dependencies
└── README.md           # This very file
```

## Upcoming Features

- 💵 Virtual cash balance & fund management
- 📝 Trade journaling / notes per trade
- 🧪 Strategy backtesting module
- 📈 Candlestick charts for each trade
- 🧠 Trade suggestions based on AI
- 🧑‍🧑‍🧒‍🧒 Community Version

