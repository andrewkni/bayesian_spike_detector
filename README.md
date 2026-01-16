# Kalshi Bayesian Spike Detector

Python bot + backtester to detect fake YES spikes on Kalshi using a simple Bayesian alpha/beta model.  
When a spike looks fake and stalls, it can buy NO and sell NO on reversal (with spread/fees check + stop-loss + timeout).

## Files

- api_info.py - API creds + request signing
- market.py - Fetch market + compute yes_spread, delta_vol, delta_spread, delta_price.
- bet.py - Place orders + log to trade_log.txt (BUY = limit IOC, SELL = market reduce-only).
- data.py - Log tickers to CSV at ~1Hz for backtesting.
- backtester.py - Run detector on CSV data (prints jumps + fake spike signals).
- detector.py - Live detector/trader.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup
Edit api_info.py:

- key_id = "<your_api_id>"
- key_b64 = "<your_api_secret>"

## Usage
Log markets to CSV
```
python data.py
```

Backtest
```
python backtester.py
```

Live trade
```
python detector.py
```

## Strategy

- Calibrate per-market thresholds from recent deltas (price/volume/spread).
- Track Bayesian fake-spike confidence `mu = alpha / (alpha + beta)`:
  - Low/zero volume + widening spread on a big YES jump increases `alpha` (fake spike)
  - High volume + tightening spread increases `beta` (real repricing)
- Enter when `mu > 0.7` and the spike stalls (`delta_price <= 0`):
  - Buy 1 NO (IOC limit at `no_ask`) only if spread/profit checks pass.
- Exit when NO recovers toward the pre-spike level:
  - Stop-loss if NO moves against you by `stop_loss` cents
  - Optional timeout
  - Sell NO using a market order (reduce-only)

## Good luck!
Tip: Look for markets with recurring patterns of fake spikes. CBA games are one example...

cba_game_sample.csv contains sample data for backtesting. The market ticker of the sample game is "KXCBAGAME-26JAN15NINSHA-NIN".
