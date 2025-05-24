# HEDGE/md_hedge.py
import json
import time
from collections import Counter
import random
from config import TICK_SYMBOL, STAKE_AMOUNT, REQUIRE_DEMO_ACCOUNT

class MatchDifferHedgeStrategy:
    def __init__(self, trader):
        self.trader = trader
        self.stake_ratio = 49  # Differs:Matches stake ratio (49:1)
        self.total_stake = STAKE_AMOUNT  # Total stake ($300)
        self.tick_symbol = TICK_SYMBOL  # Volatility 10 (1s)
        self.require_demo_account = REQUIRE_DEMO_ACCOUNT
        self.tick_duration = 1  # Assume 1 second per tick
        self.wait_ticks = 5  # Wait 5 ticks between cycles

    def calculate_stakes(self):
        """Calculate stake sizes for Matches and Differs based on ratio."""
        differs_stake = self.total_stake * (self.stake_ratio / (self.stake_ratio + 1))
        matches_stake = self.total_stake / (self.stake_ratio + 1)
        return differs_stake, matches_stake

    def select_differs_digit(self, buffer):
        """Select a digit for Differs absent from the last 10 ticks."""
        if not buffer:
            print("⚠️ Empty tick buffer, cannot select Differs digit.")
            return None
        recent_ticks = list(buffer)[-10:]  # Last 10 ticks
        all_digits = set(range(10))
        absent_digits = all_digits - set(recent_ticks)
        return random.choice(list(absent_digits)) if absent_digits else random.choice(range(10))

    def select_matches_digit(self, buffer):
        """Select the most recent digit for Matches."""
        if not buffer:
            print("⚠️ Empty tick buffer, cannot select Matches digit.")
            return None
        return list(buffer)[-1] if buffer else None

    def execute(self, buffer):
        """Execute simultaneous Matches and Differs trades, wait 5 ticks."""
        if not self.trader.can_trade():
            print("❌ Trading blocked: Demo account required.")
            return False

        # Check if enough time has passed since last trade
        current_time = time.time()
        if self.trader.last_trade_time and (current_time - self.trader.last_trade_time) < (self.wait_ticks * self.tick_duration):
            print(f"⏳ Waiting {(self.wait_ticks * self.tick_duration) - (current_time - self.trader.last_trade_time):.2f} seconds before next trade cycle.")
            return False

        if not buffer:
            print("⚠️ No tick data available, skipping trades.")
            return False

        # Calculate stakes
        differs_stake, matches_stake = self.calculate_stakes()

        # Select digits
        differs_digit = self.select_differs_digit(buffer)
        matches_digit = self.select_matches_digit(buffer)

        if differs_digit is None or matches_digit is None:
            print("⚠️ Failed to select valid digits for trading.")
            return False

        # Ensure different digits
        if differs_digit == matches_digit:
            all_digits = list(range(10))
            all_digits.remove(matches_digit)
            differs_digit = random.choice(all_digits) if all_digits else None

        if differs_digit is None:
            print("⚠️ Failed to resolve digit conflict.")
            return False

        # Place trades simultaneously
        differs_placed = self.trader.place_differs_trade(differs_digit, differs_stake)
        matches_placed = False
        if differs_placed:
            matches_placed = self.trader.place_matches_trade(matches_digit, matches_stake)
            if matches_placed:
                self.trader.last_trade_time = time.time()
                print(f"✅ Trades placed: DIFFERS {differs_digit} (${differs_stake:.2f}), MATCHES {matches_digit} (${matches_stake:.2f})")
                return True
        return False