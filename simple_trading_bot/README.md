# 🧠 Simple Crypto Trading Bot

A basic Python bot that simulates crypto trades using Binance Futures Testnet.  
**For educational purposes only. Not financial advice.**

---

## 📦 Requirements

- Python 3.10+ recommended  
- Install required libraries:
  ```bash
  pip install python-binance==1.0.15
  pip install colorama

## ⚙️ Setup
- Add your Binance Futures Testnet API credentials in simple_trading_bot.py:
API_KEY = "<YOUR_TESTNET_API_KEY>"
API_SECRET = "<YOUR_TESTNET_API_SECRET>"



## 🚀 Usage
Run the bot via command line:
python simple_trading_bot.py <side> <order_type> <quantity> <symbol> [price] [stop_price]


## 💡 Examples
- Market order:
python simple_trading_bot.py buy MARKET 0.001 BTCUSDT
- Limit order:
python simple_trading_bot.py sell LIMIT 0.001 BTCUSDT 45000
- Stop-Limit order:
python simple_trading_bot.py buy STOP_LIMIT 0.001 BTCUSDT 46000 45500


✅ The bot will ask for confirmation before placing any order.


## 📄 Logs
All executed trades and errors are logged in trade_history.log (auto-generated in the same folder).

## 📁 Folder Structure
SimpleTradingBot/
├── simple_trading_bot.py
├── trade_history.log  # auto-generated
└── README.md



## 👤 Author
Anish Wadatkar
ECE AI/ML @ DESPU | Python Developer | Open-source Contributor

## ⚠️ Disclaimer
This bot is for educational/demo purposes only.
It is not intended for real financial trading or investment advice.

