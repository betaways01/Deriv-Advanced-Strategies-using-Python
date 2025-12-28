# Deriv Advanced Strategies using Python

This repository contains Python-based trading strategies designed for use with **Deriv** markets.
It focuses on **digit match strategies** and **hedging logic**, with modular bots, configurable parameters, and basic testing support.

The codebase is structured to allow experimentation with different strategy variations and execution styles.

---

## Project Structure

```
.
├── digit_matches/
│   ├── config.py
│   ├── match_bot.py
│   ├── match_bot_mid.py
│   ├── match_bot_random.py
│   ├── state.py
│   ├── strategies.py
│   └── trader.py
│
├── hedge/
│   ├── config.py
│   ├── hedge_hilo_bot.py
│   ├── md_hedge.py
│   ├── md_hedge_bot.py
│   └── trader.py
│
├── test/
│   └── setup_test.py
│
├── trade_log.csv
├── requirements.txt
└── .gitignore
```

---

## Overview

### `digit_matches/`

Implements different digit match trading bots and strategy logic, including:

* Core trading execution
* Strategy definitions
* State management
* Configuration handling

### `hedge/`

Contains hedging-based strategies, including:

* High/Low hedge bots
* Market direction hedge logic
* Separate trader modules for execution

### `test/`

Basic setup and testing utilities.

### `trade_log.csv`

Sample or generated trade logs for tracking and analysis.

---

## Setup

1. Clone the repository:

```bash
git clone https://github.com/betaways01/Deriv-Advanced-Strategies-using-Python.git
cd Deriv-Advanced-Strategies-using-Python
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure strategy parameters inside the relevant `config.py` files.

---

## Usage

Each strategy folder contains its own bot and trader logic.
Run the desired bot script directly after configuration, for example:

```bash
python digit_matches/match_bot.py
```

or

```bash
python hedge/hedge_hilo_bot.py
```

---

## Notes

* This project is intended for **educational and experimental purposes**.
* Always test strategies thoroughly before using them with real funds.
* Logs and parameters should be reviewed regularly to manage risk.

---

## License

This project is provided as-is.
Use at your own discretion.
