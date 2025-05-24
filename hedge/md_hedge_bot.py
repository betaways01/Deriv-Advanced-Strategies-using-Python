# HEDGE/md_hedge_bot.py
import websocket
import json
import os
from dotenv import load_dotenv
from collections import deque
import time

from config import TICK_SYMBOL, STAKE_AMOUNT, REQUIRE_DEMO_ACCOUNT
from trader import Trader
from md_hedge import MatchDifferHedgeStrategy

# === Load environment ===
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
APP_ID = os.getenv("APP_ID")

# === Globals ===
tick_buffer = deque(maxlen=100)
trader = None
strategy = None
last_trade_time = 0
MIN_SECONDS_BETWEEN_TRADES = 3  # 5 ticks, assuming 1 second per tick

# === WebSocket Handlers ===
def on_open(ws):
    print("🔌 Connected. Authorizing...")
    ws.send(json.dumps({"authorize": API_TOKEN}))

def on_message(ws, message):
    global trader, strategy, last_trade_time
    data = json.loads(message)

    if data.get("msg_type") == "authorize":
        print("✅ Authorized.")
        trader.set_account_type(data)
        ws.send(json.dumps({"ticks": TICK_SYMBOL, "subscribe": 1}))

    elif data.get("msg_type") == "tick":
        digit = int(str(data["tick"]["quote"])[-1])
        tick_buffer.append(digit)
        print(f"📈 Received tick: Last digit = {digit}")
        
        if len(tick_buffer) < 10:
            print(f"⏳ Waiting for more ticks (have {len(tick_buffer)}/10).")
            return

        # Execute strategy
        if strategy.execute(tick_buffer):
            last_trade_time = time.time()

    elif data.get("msg_type") == "error":
        print("❌ ERROR:", data["error"]["message"])

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws, *_):
    print("🔒 Connection closed.")

def run():
    global trader, strategy
    ws = websocket.WebSocketApp(
        f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    trader = Trader(ws)
    strategy = MatchDifferHedgeStrategy(trader)
    ws.run_forever()

if __name__ == "__main__":
    run()