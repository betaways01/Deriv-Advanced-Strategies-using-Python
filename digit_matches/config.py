# digit_matches/config.py

# Strategy options: 'least_seen', 'most_frequent', 'pattern', 'breakout'
ACTIVE_STRATEGY = 'least_seen'

# Fire 3 staggered trades if True
USE_COVERAGE_TRADING = True

# Demo account safety switch (blocks trades if not demo)
REQUIRE_DEMO_ACCOUNT = True

# Stake settings
STAKE_AMOUNT = 300
STAKING_MODE = "dynamic"  # Options: 'constant', 'dynamic'
RISK_PERCENTAGE = 0.02  # 2% of balance for dynamic staking
MIN_STAKE = 10  # Minimum stake in USD
MAX_STAKE = 500  # Maximum stake in USD

# Tick symbol (Volatility 10 1s)
TICK_SYMBOL = '1HZ10V'

# Coverage delay in ticks
COVERAGE_DEPTH = 3