from market import *
from datetime import datetime
import numpy as np
import time

# Input market ticker here
ticker = "KXAFCONGAME-26JAN14SENEGY-SEN"

# Calibrate parameter thresholds of the bot
# EX: a "large" delta_vol differs by market, so you need to define what is "large"
def calibrate():
    duration = 1 * 60 # calibration duration

    delta_vols = []
    delta_prices = []

    # Store the last 10 markets (stores up to 10 seconds ago)
    history = []
    prev_market = fetch_market(ticker)
    for i in range(10):
        time.sleep(1)
        curr_market = fetch_market(ticker, prev_market)
        history.append(curr_market)
        prev_market = curr_market

    init_time = time.time()

    # Collects parameter values over time period
    while time.time() < duration + init_time:
        time.sleep(1)

        # computes delta vol, price, etc. from curr to market 10 seconds ago
        curr_market = fetch_market(ticker, history[0])

        delta_vols.append(curr_market['delta_vol'])
        delta_prices.append(curr_market['delta_price'])

        history.pop(0)
        history.append(curr_market)

    # Convert lists into np arrays for analysis
    delta_vols = np.array(delta_vols)
    delta_prices = np.array(delta_prices)

    # Computes percentiles of parameters to determine how much change is "large" or "small"
    # Modify percentiles to determine conservativeness of bot
    # default values ensure bot works in extreme markets (such as when vol = 0 for long times)
    thresholds = {
        "vol_low": max(1, int(np.percentile(delta_vols, 25))),
        "vol_high": max(5, int(np.percentile(delta_vols, 75))),

        "price_high": max(2, int(np.percentile(delta_prices, 95))),
    }

    return thresholds

def main():
    alpha = 1 # evidence that move is a fake spike
    beta = 2 # evidence that move is a real repricing

    # Bayesian confidence that the current market move is a “fake spike”
    mu = alpha / (alpha + beta)

    print("Calibrating model...")
    # Calibrate model first
    thresholds = calibrate()
    print(thresholds)
    print("Calibration success!")

    # Store the last 10 markets (stores up to 10 seconds ago)
    history = []
    prev_market = fetch_market(ticker)
    for i in range(10):
        time.sleep(1)
        curr_market = fetch_market(ticker, prev_market)
        history.append(curr_market)
        prev_market = curr_market

    print("Trading commencing...")

    # Alpha/beta updates
    while True:
        time.sleep(1)

        # compares current market to market 10 seconds ago
        curr_market = fetch_market(ticker, history[0])

        # If the YES price moved up by at least “jump” threshold,
        # classify whether the move looks like a fake spike (alpha) or a real repricing (beta)
        if curr_market['delta_price'] >= thresholds['price_high']:
            # Low volume on a jump suggests a hype spike -> alpha++
            if curr_market['delta_vol'] <= thresholds['vol_low']:
                alpha += 1
            # High volume on a jump suggests broad participation -> beta++
            elif curr_market['delta_vol'] >= thresholds["vol_high"]:
                beta += 1
            # Spread widening during the jump suggests makers pulled liquidity -> alpha++
            if curr_market['delta_spread'] >= 2:
                alpha += 1
            # Spread tightening during the jump suggests healthy liquidity -> beta++
            elif curr_market['delta_spread'] <= -2:
                beta += 1

            print("JUMP",
                  "Δp", curr_market["delta_price"],
                  "Δv", curr_market["delta_vol"],
                  "Δspr", curr_market["delta_spread"],
                  "alpha", alpha, "beta", beta)

            mu = alpha / (alpha + beta)
            print("mu", mu)

        if mu > 0.6:
            print("spike predicted. buy now!")
            date = datetime.fromtimestamp(time.time())
            print(date)

            # Reset alpha and beta values
            alpha = 1
            beta = 2

            # spike cooldown
            time.sleep(10)


        history.pop(0)
        history.append(curr_market)


if __name__ == '__main__':
    main()