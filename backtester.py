"""
Backtesting script for detector.py

Use data.py to log markets into a csv file
Use the csv to backtest the algorithm

"""

import numpy as np
import pandas as pd

# Edit these two parameters for your backtest
file = "KXAFCONGAME-26JAN14NGRMAR-TIE.csv"
duration = 30  # calibration duration in seconds

df = pd.read_csv(file)
row = 0

# Fetches the market at the next timestamp
def fetch_market():
    global row
    parameters = df.iloc[row]
    row += 1

    print(row)

    return parameters

# Calibrate parameter thresholds of the bot
# EX: a "large" delta_vol differs by market, so you need to define what is "large"
def calibrate():
    delta_vols = []
    delta_prices = []
    delta_spreads = []

    # Collects parameter values over duration (assuming time interval is 1 second)
    for i in range(duration):
        curr_market = fetch_market()

        delta_vols.append(curr_market['delta_vol'])
        delta_prices.append(curr_market['delta_price'])
        delta_spreads.append(curr_market['delta_spread'])

    # Convert lists into np arrays for analysis
    delta_vols = np.array(delta_vols)
    delta_prices = np.array(delta_prices)
    delta_spreads = np.array(delta_spreads)

    # Computes percentiles of parameters to determine how much change is "large" or "small"
    # Modify percentiles to determine conservativeness of bot
    # default values ensure bot works in extreme markets (such as when vol = 0 for long times)
    thresholds = {
        "vol_low": max(1, int(np.percentile(delta_vols, 25))),
        "vol_high": max(5, int(np.percentile(delta_vols, 75))),

        "spread_low": min(-2, int(np.percentile(delta_spreads, 25))),
        "spread_high": max(2, int(np.percentile(delta_spreads, 75))),

        "price_high": max(2, int(np.percentile(delta_prices, 95))),
    }

    return thresholds

# Runs the main spike detector algorithm till end_hour:end_minute
def detect():
    alpha = 1 # evidence that move is a fake spike
    beta = 2 # evidence that move is a real repricing
    decay = 0.9 # old evidence loses 10% weight each jump

    # Bayesian confidence that the current market move is a “fake spike”
    mu = alpha / (alpha + beta)

    print("Calibrating model...")
    # Calibrate model first
    thresholds = calibrate()
    print(thresholds)
    print("Calibration success!")

    print("Trading commencing...")

    # Alpha/beta updates, run until end of csv
    for i in range(len(df) - duration):
        # compares current market to market 10 seconds ago
        curr_market = fetch_market()

        alpha = max(1.0, alpha * 0.99)  # Very slow decay of evidence over time
        beta = max(2.0, beta * 0.99)

        # If the YES price moved up by at least “jump” threshold,
        # classify whether the move looks like a fake spike (alpha) or a real repricing (beta)
        if curr_market['delta_price'] >= thresholds['price_high']:
            # Deprioritize old evidence
            alpha = max(1.0, alpha * decay)
            beta  = max(2.0, beta * decay)

            # Low volume on a jump suggests a hype spike -> alpha++
            if curr_market['delta_vol'] <= thresholds['vol_low']:
                alpha += 1
            # High volume on a jump suggests broad participation -> beta++
            elif curr_market['delta_vol'] >= thresholds["vol_high"]:
                beta += 1
            # Spread widening during the jump suggests makers pulled liquidity -> alpha++
            if curr_market['delta_spread'] >= thresholds['spread_high']:
                alpha += 1
            # Spread tightening during the jump suggests healthy liquidity -> beta++
            elif curr_market['delta_spread'] <= thresholds['spread_low']:
                beta += 1

            print("JUMP",
                  "Δp", curr_market["delta_price"],
                  "Δv", curr_market["delta_vol"],
                  "Δspr", curr_market["delta_spread"],
                  "alpha", alpha, "beta", beta)

            mu = alpha / (alpha + beta)
            print("mu", mu)

        if mu > 0.7:
            # Check if the price is starting to drop. If so, bet
            if curr_market['delta_price'] < 0:
                print("fake spike predicted, and spike stalled. buy no shares to bet against it!")
                date = curr_market['ts']
                print(date)

                # Reset alpha and beta values
                alpha = 1
                beta = 2

                mu = alpha / (alpha + beta)

                # spike cooldown, skip 15 lines in csv
                global row
                row += 15

def main():
    detect()

    print('Program ended.')

if __name__ == "__main__":
    main()