# digit_matches/match_bot.py
import websocket
import json
import os
from dotenv import load_dotenv
from collections import deque, Counter
import time
import threading
from colorama import init, Fore, Style

init(autoreset=True)

from config import ACTIVE_STRATEGY, USE_COVERAGE_TRADING, COVERAGE_DEPTH, TICK_SYMBOL
from trader import Trader
import strategies

# === Load environment ===
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
APP_ID = os.getenv("APP_ID")

# === Globals ===
tick_buffer = deque(maxlen=100)
prev_digits = set()
trader = None
used_digit = None
last_match_digit = None
match_hold_ticks = 0
last_trade_time = 0
MIN_SECONDS_BETWEEN_BURSTS = 10
strategy_performance = {'pattern': {'wins': 0, 'total': 0, 'weight': 0.2},
                       'most_frequent': {'wins': 0, 'total': 0, 'weight': 0.4},
                       'least_seen': {'wins': 0, 'total': 0, 'weight': 0.3},
                       'breakout': {'wins': 0, 'total': 0, 'weight': 0.1}}
ws = None
reconnect_delay = 1
max_reconnect_delay = 32
last_balance_log = 0

# === Strategy Consensus ===
def select_digit():
    votes = []
    strategies_voted = []
    strat_1 = strategies.detect_pattern(tick_buffer)
    strat_2 = strategies.most_frequent_digit(tick_buffer)
    strat_3 = strategies.least_seen_digit(tick_buffer)
    strat_4 = strategies.detect_compression_breakout(tick_buffer, prev_digits)
    
    for digit, strat in [(strat_1, 'pattern'), (strat_2, 'most_frequent'), 
                         (strat_3, 'least_seen'), (strat_4, 'breakout')]:
        if digit is not None:
            votes.append((digit, strategy_performance[strat]['weight']))
            strategies_voted.append(strat)
            strategy_performance[strat]['total'] += 1
    
    if not votes:
        return None, None, None
    
    weighted_scores = {}
    for digit, weight in votes:
        weighted_scores[digit] = weighted_scores.get(digit, 0) + weight
    
    consensus = max(weighted_scores, key=weighted_scores.get)
    return consensus, strategies_voted, votes

# === Keep-Alive Ping ===
def keep_alive_ping():
    while ws and ws.sock and ws.sock.connected:
        try:
            ws.send(json.dumps({"ping": 1}))
            time.sleep(30)
        except Exception:
            break

# === WebSocket Handlers ===
def on_open(ws_instance):
    global ws, reconnect_delay
    ws = ws_instance
    print(f"{Fore.CYAN}🔌 Connected. Authorizing...{Style.RESET_ALL}")
    reconnect_delay = 1
    try:
        ws.send(json.dumps({"authorize": API_TOKEN}))
        threading.Thread(target=keep_alive_ping, daemon=True).start()
    except Exception as e:
        print(f"{Fore.RED}❌ Authorization failed: {e}{Style.RESET_ALL}")

def on_message(ws_instance, message):
    global prev_digits, used_digit, last_match_digit, match_hold_ticks, last_trade_time, last_balance_log
    try:
        data = json.loads(message)

        if data.get("msg_type") == "authorize":
            print(f"{Fore.GREEN}✅ Authorized{Style.RESET_ALL}")
            trader.set_account_type(data)

        elif data.get("msg_type") == "balance":
            trader.update_balance(data)
            if time.time() - last_balance_log > 10:
                last_balance_log = time.time()
                trader.display_status()

        elif data.get("msg_type") == "tick":
            digit = int(str(data["tick"]["quote"])[-1])
            tick_buffer.append(digit)
            trader.tick()

            if len(tick_buffer) < 50:
                return

            MAX_HOLD_TICKS = 3 if trader.consecutive_losses > 2 else 5
            if last_match_digit is not None:
                match_hold_ticks += 1
                if match_hold_ticks < MAX_HOLD_TICKS:
                    return
                else:
                    last_match_digit = None
                    match_hold_ticks = 0

            now = time.time()
            if now - last_trade_time < MIN_SECONDS_BETWEEN_BURSTS:
                return

            selected, strategies_voted, votes = select_digit()
            if selected is not None:
                used_digit = selected
                last_match_digit = selected
                last_trade_time = now
                trader.display_status(selected, strategies_voted, votes)
                if USE_COVERAGE_TRADING:
                    trader.fire_coverage_trades(selected, delay_ticks=list(range(COVERAGE_DEPTH)), strategies_voted=strategies_voted)
                else:
                    trader.place_match_trade(selected, strategies_voted)

            prev_digits = set(tick_buffer)

        elif data.get("msg_type") == "buy":
            contract_id = data.get("buy", {}).get("contract_id")
            if contract_id:
                ws.send(json.dumps({"proposal_open_contract": 1, "contract_id": contract_id, "subscribe": 1}))
            else:
                print(f"{Fore.RED}❌ Trade placement failed: No contract ID{Style.RESET_ALL}")
            trader.display_status(used_digit)

        elif data.get("msg_type") == "proposal_open_contract":
            contract = data.get("proposal_open_contract", {})
            if contract.get("is_sold", 0) == 1:
                digit = contract.get("barrier")
                stake = contract.get("buy_price", 0)
                outcome = "win" if contract.get("profit", 0) > 0 else "loss"
                profit = contract.get("profit", 0)
                trader.log_trade(digit, stake, outcome, profit)
                for strat in strategy_performance:
                    if strat in trader.strategy_contributions:
                        strategy_performance[strat]['wins'] += trader.strategy_contributions[strat]
                        trader.strategy_contributions[strat] = 0
                trader.display_status(used_digit)

        elif data.get("msg_type") == "ping":
            pass

        elif data.get("msg_type") == "error":
            print(f"{Fore.RED}❌ API Error: {data['error']['message']}{Style.RESET_ALL}")
            trader.display_status(used_digit)

    except Exception as e:
        print(f"{Fore.RED}❌ Message processing error: {e}{Style.RESET_ALL}")

def on_error(ws_instance, error):
    print(f"{Fore.RED}❌ WebSocket Error: {error}{Style.RESET_ALL}")

def on_close(ws_instance, close_status_code, close_msg):
    global reconnect_delay
    print(f"{Fore.RED}🔒 Connection closed: Code={close_status_code}, Reason={close_msg}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔄 Reconnecting in {reconnect_delay} seconds...{Style.RESET_ALL}")
    time.sleep(reconnect_delay)
    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
    run()

def run():
    global ws, trader
    websocket.enableTrace(False)
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