import websocket
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve API_TOKEN and APP_ID from the environment
API_TOKEN = os.getenv('API_TOKEN')
APP_ID = os.getenv('APP_ID')

def on_open(ws):
    print("Connected. Authorizing...")
    ws.send(json.dumps({"authorize": API_TOKEN}))

def on_message(ws, msg):
    print("Message received:", msg)

ws = websocket.WebSocketApp(
    f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}",
    on_open=on_open,
    on_message=on_message
)

ws.run_forever()
