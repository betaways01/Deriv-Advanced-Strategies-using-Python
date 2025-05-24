# digit_matches/match_bot_mid.py
import websocket
import json
import os
import random
from dotenv import load_dotenv
from collections import deque
import time

from config import TICK_SYMBOL
from trader import Trader

# === Load environment ===
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
APP_ID = os.getenv("APP_ID")

# === Globals ===
tick_buffer = deque(maxlen=100)
trader = None
run_count = 0
last_selected_digits = []
last_trade_time = 0
MIN_TRADE_INTERVAL = 7  # avoid back-to-back trades

# === WebSocket Handlers ===
def on_open(ws):
    print("🔌 Connected. Authorizing...")
    ws.send(json.dumps({"authorize": API_TOKEN}))

def on_message(ws, message):
    global run_count, last_selected_digits, last_trade_time
    data = json.loads(message)

    if data.get("msg_type") == "authorize":
        print("✅ Authorized.")
        trader.set_account_type(data)
        ws.send(json.dumps({"ticks": TICK_SYMBOL, "subscribe": 1}))

    elif data.get("msg_type") == "tick":
        digit = int(str(data["tick"]["quote"])[-1])
        tick_buffer.append(digit)
        trader.tick()

        if len(tick_buffer) < 50:
            return

        now = time.time()
        if now - last_trade_time < MIN_TRADE_INTERVAL:
            return

        if run_count % 4 < 2:
            digits_to_trade = last_selected_digits
        else:
            digits_to_trade = random.sample(range(4, 10), 5)
            last_selected_digits = digits_to_trade

        print(f"🎯 Instant match trades on digits: {digits_to_trade}")
        trader.place_multiple_match_trades(digits_to_trade)

        run_count += 1
        last_trade_time = now

    elif data.get("msg_type") == "error":
        print("❌ ERROR:", data["error"].get("message", "Unknown error"))

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws, *_):
    print("🔒 Connection closed.")

def run():
    global trader
    ws = websocket.WebSocketApp(
        f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    trader = Trader(ws)
    ws.run_forever()

if __name__ == "__main__":
    run()
