from market import *
import numpy as np
import time

# Input market ticker here
ticker = "KXWTAMATCH-26JAN13MARBON-MAR"

# Calibrate parameter thresholds of the bot
# EX: a "large" delta_vol differs by market, so you need to define what is "large"
def calibrate():
    duration = 1 * 60 # calibration duration

    delta_vols = []
    delta_prices = []

    prev_market = fetch_market(ticker)
    init_time = time.time()

    # Collects parameter values over time period
    while time.time() < duration + init_time:
        time.sleep(1)
        curr_market = fetch_market(ticker, prev_market)

        delta_vols.append(curr_market['delta_vol'])
        delta_prices.append(curr_market['delta_price'])

        prev_market = curr_market

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

    print("Calibrating model...")
    # Calibrate model first
    thresholds = calibrate()
    print(thresholds)
    print("Calibration success!")


    print("Trading commencing...")

    # Alpha/beta updates
    prev_market = fetch_market(ticker)
    while True:
        time.sleep(1)
        curr_market = fetch_market(ticker, prev_market)

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

        # Bayesian confidence that the current market move is a “fake spike”
        mu = alpha / (alpha + beta)

        print(mu)
        if mu > 0.6:
            print("spike predicted. buy now!")


        prev_market = curr_market


if __name__ == '__main__':
    main()