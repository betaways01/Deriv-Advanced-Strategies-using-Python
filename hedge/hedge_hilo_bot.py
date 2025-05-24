# hedge_hilo_bot.py
import websocket
import json
import os
import time
from dotenv import load_dotenv

# === Load .env ===
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
APP_ID = os.getenv("APP_ID")

# === Parameters ===
SYMBOL = "R_100"  # 1s not needed for Higher/Lower
STAKE = 1.0
BARRIER_OFFSET = 0.2
TRADE_INTERVAL = 15  # seconds between trades

# === State ===
last_trade_time = 0

# === WebSocket Logic ===
def on_open(ws):
    print("🔌 Connected. Authorizing...")
    ws.send(json.dumps({"authorize": API_TOKEN}))

def on_message(ws, message):
    global last_trade_time
    data = json.loads(message)

    if data.get("msg_type") == "authorize":
        print("✅ Authorized.")
        print(f"📉 Subscribing to ticks for {SYMBOL}")
        ws.send(json.dumps({"ticks": SYMBOL, "subscribe": 1}))

    elif data.get("msg_type") == "tick":
        now = time.time()
        if now - last_trade_time < TRADE_INTERVAL:
            return

        quote = float(data["tick"]["quote"])
        place_hedge_trades(ws, quote)
        last_trade_time = now

    elif data.get("msg_type") == "error":
        print("❌ ERROR:", data["error"].get("message", "Unknown error"))

def place_hedge_trades(ws, spot):
    print(f"🎯 Spot: {spot:.5f} | Placing hedge trades")

    # Higher contract
    higher = {
        "buy": 1,
        "price": STAKE,
        "parameters": {
            "amount": STAKE,
            "basis": "stake",
            "contract_type": "CALL",
            "currency": "USD",
            "duration": 1,
            "duration_unit": "t",
            "symbol": SYMBOL,
            "barrier": f"+{BARRIER_OFFSET:.1f}"
        }
    }

    # Lower contract
    lower = {
        "buy": 1,
        "price": STAKE,
        "parameters": {
            "amount": STAKE,
            "basis": "stake",
            "contract_type": "PUT",
            "currency": "USD",
            "duration": 1,
            "duration_unit": "t",
            "symbol": SYMBOL,
            "barrier": f"-{BARRIER_OFFSET:.1f}"
        }
    }

    ws.send(json.dumps(higher))
    ws.send(json.dumps(lower))
    print("🚀 Trades sent: HIGHER + LOWER")

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws, *_):
    print("🔒 Connection closed.")

def run():
    ws = websocket.WebSocketApp(
        f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    run()
