# simple_trading_bot.py
import sys
import time
import logging
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# ------------------------------
# CONFIG: ENTER YOUR TESTNET KEYS HERE
# ------------------------------
API_KEY = "<YOUR_TESTNET_API_KEY>"
API_SECRET = "<YOUR_TESTNET_API_SECRET>"
BASE_URL = "https://testnet.binancefuture.com"

# ------------------------------
# LOGGING
# ------------------------------
logging.basicConfig(
    filename='trade_history.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------------------
# BASIC BOT CLASS
# ------------------------------
class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        self.client = Client(api_key, api_secret, testnet=testnet)
        if testnet:
            self.client.FUTURES_URL = BASE_URL

    # ------------------------------
    # VALIDATE INPUT
    # ------------------------------
    def validate_order(self, side, order_type, quantity, symbol, price=None, stop_price=None):
        valid_sides = ["buy", "sell"]
        valid_types = ["MARKET", "LIMIT", "STOP_LIMIT"]

        if side.lower() not in valid_sides:
            raise ValueError("Invalid side. Use 'buy' or 'sell'.")
        if order_type.upper() not in valid_types:
            raise ValueError("Invalid order type. Use MARKET, LIMIT, or STOP_LIMIT.")

        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError()
        except:
            raise ValueError("Invalid quantity. Must be a number > 0.")

        if not symbol.upper().endswith("USDT"):
            raise ValueError("Symbol must end with USDT (e.g., BTCUSDT).")

        if order_type.upper() in ["LIMIT", "STOP_LIMIT"] and price is None:
            raise ValueError(f"{order_type} order requires a price.")
        if order_type.upper() == "STOP_LIMIT" and stop_price is None:
            raise ValueError("STOP_LIMIT order requires a stop price.")

        return side.upper(), order_type.upper(), quantity, symbol.upper(), price, stop_price

    # ------------------------------
    # PLACE ORDER
    # ------------------------------
    def place_order(self, side, order_type, quantity, symbol, price=None, stop_price=None):
        try:
            # Confirmation prompt
            print(Fore.YELLOW + f"\nYou are about to place the following order:")
            print(Fore.CYAN + f"Side: {side}, Type: {order_type}, Quantity: {quantity}, Symbol: {symbol}, Price: {price}, Stop: {stop_price}")
            confirm = input(Fore.YELLOW + "Confirm? (y/n): ").strip().lower()
            if confirm != 'y':
                print(Fore.MAGENTA + "Order cancelled by user.")
                return

            if order_type == "MARKET":
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )

            elif order_type == "LIMIT":
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    price=str(price)
                )

            elif order_type == "STOP_LIMIT":
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                    type=ORDER_TYPE_STOP,
                    stopPrice=str(stop_price),
                    price=str(price),
                    quantity=quantity,
                    timeInForce=TIME_IN_FORCE_GTC
                )

            # Success message
            print(Fore.GREEN + "\n=== ORDER EXECUTED SUCCESSFULLY ===")
            print(Fore.CYAN + f"Order ID: {order['orderId']}")
            print(Fore.CYAN + f"Symbol: {order['symbol']}")
            print(Fore.CYAN + f"Side: {order['side']}")
            print(Fore.CYAN + f"Type: {order['type']}")
            print(Fore.CYAN + f"Price: {order.get('price')}")
            print(Fore.CYAN + f"Quantity: {order['origQty']}")
            print(Fore.GREEN + "====================================\n")

            logging.info(f"ORDER: {order}")

        except BinanceAPIException as e:
            print(Fore.RED + f"Binance API Error: {e.message}")
            logging.error(f"Binance API Error: {e.message}")
        except Exception as e:
            print(Fore.RED + f"Error: {str(e)}")
            logging.error(f"Error: {str(e)}")

# ------------------------------
# MAIN PROGRAM (CLI)
# ------------------------------
def main():
    if len(sys.argv) < 5:
        print(Fore.YELLOW + "\nUsage:")
        print("python simple_trading_bot.py <side> <order_type> <quantity> <symbol> [price] [stop_price]")
        print("\nExamples:")
        print("python simple_trading_bot.py buy MARKET 0.001 BTCUSDT")
        print("python simple_trading_bot.py sell LIMIT 0.001 BTCUSDT 45000")
        print("python simple_trading_bot.py buy STOP_LIMIT 0.001 BTCUSDT 46000 45500\n")
        return

    side = sys.argv[1]
    order_type = sys.argv[2]
    quantity = sys.argv[3]
    symbol = sys.argv[4]
    price = sys.argv[5] if len(sys.argv) > 5 else None
    stop_price = sys.argv[6] if len(sys.argv) > 6 else None

    bot = BasicBot(API_KEY, API_SECRET, testnet=True)
    try:
        side, order_type, quantity, symbol, price, stop_price = bot.validate_order(
            side, order_type, quantity, symbol, price, stop_price
        )
        bot.place_order(side, order_type, quantity, symbol, price, stop_price)
    except Exception as e:
        print(Fore.RED + f"Input Error: {str(e)}")
        logging.error(f"Input Error: {str(e)}")

if __name__ == "__main__":
    main()
