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

# === WebSocket Handlers ===
def on_open(ws):
    print("🔌 Connected. Authorizing...")
    ws.send(json.dumps({"authorize": API_TOKEN}))

def on_message(ws, message):
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

        # Select 4 unique random digits and place trades instantly
        digits_to_trade = random.sample(range(10), 4)
        print(f"🎯 Instant match trades on digits: {digits_to_trade}")
        for d in digits_to_trade:
            trader.place_match_trade(d)

    elif data.get("msg_type") == "error":
        print("❌ ERROR:", data["error"]["message"])

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
