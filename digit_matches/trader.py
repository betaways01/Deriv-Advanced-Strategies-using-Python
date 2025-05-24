# digit_matches/trader.py
import json
import time
import csv
import os
from collections import Counter, deque
from colorama import init, Fore, Style
from tabulate import tabulate

init(autoreset=True)

from config import STAKE_AMOUNT, TICK_SYMBOL, REQUIRE_DEMO_ACCOUNT, STAKING_MODE, RISK_PERCENTAGE, MIN_STAKE, MAX_STAKE

class Trader:
    def __init__(self, ws):
        self.ws = ws
        self.last_trade_time = 0
        self.pending_trades = []
        self.account_type = None
        self.balance = 0
        self.current_stake = STAKE_AMOUNT
        self.consecutive_losses = 0
        self.max_consecutive_losses = 5
        self.stop_loss_pause = 300  # 5 minutes
        self.stop_loss_time = 0
        self.trade_log = "trade_log.csv"
        self.trade_count = 0
        self.total_wins = 0
        self.total_profit = 0
        self.digit_frequencies = Counter()
        self.strategy_contributions = {'pattern': 0, 'most_frequent': 0, 'least_seen': 0, 'breakout': 0}
        self.recent_trades = deque(maxlen=5)  # Last 5 trades
        self.all_trades = []  # All trades
        if not os.path.exists(self.trade_log):
            with open(self.trade_log, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Digit", "Stake", "Outcome", "Profit"])

    def set_account_type(self, msg):
        loginid = msg.get("authorize", {}).get("loginid", "")
        self.account_type = "demo" if loginid and loginid.startswith("VRTC") else "real"
        try:
            self.ws.send(json.dumps({"balance": 1, "subscribe": 1}))
            self.ws.send(json.dumps({"ticks": TICK_SYMBOL, "subscribe": 1}))
        except Exception as e:
            print(f"{Fore.RED}❌ Subscription failed: {e}{Style.RESET_ALL}")

    def update_balance(self, balance_data):
        new_balance = balance_data.get("balance", {}).get("balance", 0)
        if abs(new_balance - self.balance) > 0.01:
            self.balance = new_balance

    def can_trade(self):
        if REQUIRE_DEMO_ACCOUNT and self.account_type != "demo":
            return False
        if time.time() < self.stop_loss_time:
            return False
        return True

    def calculate_stake(self):
        if STAKING_MODE == "constant":
            return STAKE_AMOUNT
        elif STAKING_MODE == "dynamic":
            if self.balance <= 0:
                return STAKE_AMOUNT
            stake = max(MIN_STAKE, min(MAX_STAKE, self.balance * RISK_PERCENTAGE))
            return round(stake, 2)
        return STAKE_AMOUNT

    def place_match_trade(self, digit, strategies_voted=None):
        if not self.can_trade():
            return
        self.current_stake = self.calculate_stake()
        trade_payload = {
            "buy": 1,
            "price": self.current_stake,
            "parameters": {
                "amount": self.current_stake,
                "basis": "stake",
                "contract_type": "DIGITMATCH",
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": TICK_SYMBOL,
                "barrier": str(digit)
            }
        }
        try:
            self.ws.send(json.dumps(trade_payload))
            self.last_trade_time = time.time()
            self.trade_count += 1
            self.log_trade(digit, self.current_stake, "pending", 0, strategies_voted)
            if self.trade_count % 100 == 0:
                self.analyze_performance()
        except Exception as e:
            print(f"{Fore.RED}❌ Trade failed: {e}{Style.RESET_ALL}")

    def place_multiple_match_trades(self, digits):
        if not self.can_trade():
            return
        for digit in digits:
            self.place_match_trade(digit)

    def fire_coverage_trades(self, digit, delay_ticks, strategies_voted=None):
        for delay in delay_ticks:
            self.pending_trades.append({"digit": digit, "delay": delay, "strategies_voted": strategies_voted})

    def tick(self):
        for trade in self.pending_trades[:]:
            trade["delay"] -= 1
            if trade["delay"] <= 0:
                self.place_match_trade(trade["digit"], trade.get("strategies_voted"))
                self.pending_trades.remove(trade)

    def log_trade(self, digit, stake, outcome, profit, strategies_voted=None):
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.trade_log, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, digit, stake, outcome, profit])
            self.digit_frequencies[digit] += 1
            # Color the outcome for display
            if outcome == "win":
                colored_outcome = f"{Fore.GREEN}{outcome}{Style.RESET_ALL}"
            elif outcome == "loss":
                colored_outcome = f"{Fore.RED}{outcome}{Style.RESET_ALL}"
            else:
                colored_outcome = f"{Fore.YELLOW}{outcome}{Style.RESET_ALL}"
            trade_entry = [timestamp, digit, stake, colored_outcome, profit]
            self.recent_trades.append(trade_entry)
            self.all_trades.append(trade_entry)
            if outcome == "win":
                self.total_wins += 1
                self.total_profit += profit
                if strategies_voted:
                    for strat in strategies_voted:
                        self.strategy_contributions[strat] += 1
                self.consecutive_losses = 0
            elif outcome == "loss":
                self.consecutive_losses += 1
                self.total_profit += profit
                if self.consecutive_losses >= self.max_consecutive_losses:
                    self.stop_loss_time = time.time() + self.stop_loss_pause
        except Exception as e:
            print(f"{Fore.RED}❌ Logging failed: {e}{Style.RESET_ALL}")

    def analyze_performance(self):
        self.display_status()

    def display_status(self, current_digit=None, strategies_voted=None, strategy_votes=None):
        os.system("cls" if os.name == "nt" else "clear")
        win_rate = self.total_wins / self.trade_count if self.trade_count > 0 else 0
        status = "Active" if self.can_trade() else f"Paused ({int(self.stop_loss_time - time.time())}s left)"
        status_color = f"{Fore.GREEN}{status}{Style.RESET_ALL}" if self.can_trade() else f"{Fore.RED}{status}{Style.RESET_ALL}"
        status_table = [
            ["Balance", f"{self.balance:.2f} USD"],
            ["Current Trade", f"Digit {current_digit}" if current_digit else "None"],
            ["Stake", f"{self.current_stake:.2f} USD"],
            ["Win Rate", f"{win_rate:.2%}"],
            ["Total P/L", f"{self.total_profit:.2f} USD"],
            ["Status", status_color]
        ]
        print(f"{Fore.BLUE}{Style.BRIGHT}=== Trading Status ==={Style.RESET_ALL}")
        print(tabulate(status_table, headers=["Metric", "Value"], tablefmt="fancy_grid"))

        if strategy_votes and strategies_voted:
            consensus_table = [[strat, f"Digit {vote[0]} (Weight: {vote[1]:.2f})"] for vote, strat in zip(strategy_votes, strategies_voted)]
            print(f"\n{Fore.BLUE}{Style.BRIGHT}=== Strategy Consensus ==={Style.RESET_ALL}")
            print(tabulate(consensus_table, headers=["Strategy", "Vote"], tablefmt="fancy_grid"))
            print(f"{Fore.YELLOW}Consensus Digit: {current_digit}{Style.RESET_ALL}")

        print(f"\n{Fore.BLUE}{Style.BRIGHT}=== Recent Trades (Last 5) ==={Style.RESET_ALL}")
        print(tabulate(self.recent_trades, headers=["Timestamp", "Digit", "Stake", "Outcome", "Profit"], tablefmt="fancy_grid"))

        print(f"\n{Fore.BLUE}{Style.BRIGHT}=== All Trades (Last 10) ==={Style.RESET_ALL}")
        start_idx = max(0, len(self.all_trades) - 10)
        recent_all_trades = self.all_trades[start_idx:]
        print(tabulate(recent_all_trades, headers=["Timestamp", "Digit", "Stake", "Outcome", "Profit"], tablefmt="fancy_grid"))

        if self.trade_count % 100 == 0 and self.trade_count > 0:
            print(f"\n{Fore.BLUE}{Style.BRIGHT}=== Performance Summary ==={Style.RESET_ALL}")
            print(f"{Fore.BLUE}Digit Frequencies: {dict(self.digit_frequencies)}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Strategy Contributions: {dict(self.strategy_contributions)}{Style.RESET_ALL}")