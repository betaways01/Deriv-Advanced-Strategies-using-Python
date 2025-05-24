# HEDGE/trader.py
import json
import time

from config import STAKE_AMOUNT, TICK_SYMBOL, REQUIRE_DEMO_ACCOUNT

class Trader:
    def __init__(self, ws):
        self.ws = ws
        self.last_trade_time = 0
        self.account_type = None

    def set_account_type(self, msg):
        """Set account type based on authorization response."""
        loginid = msg.get("authorize", {}).get("loginid", "")
        self.account_type = "demo" if loginid.startswith("VRTC") else "real"
        print(f"🔐 Account type detected: {self.account_type.upper()}")

    def can_trade(self):
        """Check if trading is allowed (demo account required)."""
        if REQUIRE_DEMO_ACCOUNT and self.account_type != "demo":
            print("❌ Trade blocked: Not a demo account")
            return False
        return True

    def place_differs_trade(self, digit, stake):
        """Place a Differs trade with the specified digit and stake."""
        if not self.can_trade():
            return False
        trade_payload = {
            "buy": 1,
            "price": stake,
            "parameters": {
                "amount": stake,
                "basis": "stake",
                "contract_type": "DIGITDIFF",
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": TICK_SYMBOL,
                "barrier": str(digit)
            }
        }
        print(f"🚀 Placing trade: DIFFERS {digit} with stake ${stake:.2f}")
        self.ws.send(json.dumps(trade_payload))
        return True

    def place_matches_trade(self, digit, stake):
        """Place a Matches trade with the specified digit and stake."""
        if not self.can_trade():
            return False
        trade_payload = {
            "buy": 1,
            "price": stake,
            "parameters": {
                "amount": stake,
                "basis": "stake",
                "contract_type": "DIGITMATCH",
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": TICK_SYMBOL,
                "barrier": str(digit)
            }
        }
        print(f"🚀 Placing trade: MATCHES {digit} with stake ${stake:.2f}")
        self.ws.send(json.dumps(trade_payload))
        return True