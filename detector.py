from market import fetch_market
from datetime import datetime
import numpy as np
import time

# Find the last n markets and store it in history [1 second intervals]
def fetch_past_markets(ticker, n):
    history = []
    prev_market = fetch_market(ticker)
    for i in range(n):
        time.sleep(1)
        curr_market = fetch_market(ticker, prev_market)
        history.append(curr_market)
        prev_market = curr_market

    return history

# Calibrate parameter thresholds of the bot
# EX: a "large" delta_vol differs by market, so you need to define what is "large"
def calibrate(ticker):
    duration = 60 # calibration duration in seconds

    delta_vols = []
    delta_prices = []
    delta_spreads = []

    # Store the last 10 markets (stores up to 10 seconds ago)
    history = fetch_past_markets(ticker, 10)

    init_time = time.time()

    # Collects parameter values over time period
    while time.time() < duration + init_time:
        time.sleep(1)

        # computes delta vol, price, etc. from curr to market 10 seconds ago
        curr_market = fetch_market(ticker, history[0])

        delta_vols.append(curr_market['delta_vol'])
        delta_prices.append(curr_market['delta_price'])
        delta_spreads.append(curr_market['delta_spread'])

        history.pop(0)
        history.append(curr_market)

    # Convert lists into np arrays for analysis
    delta_vols = np.array(delta_vols)
    delta_prices = np.array(delta_prices)
    delta_spreads = np.abs(np.array(delta_spreads))

    # Computes percentiles of parameters to determine how much change is "large" or "small"
    # Modify percentiles to determine conservativeness of bot
    # default values ensure bot works in extreme markets (such as when vol = 0 for long times)

    # Compute vol thresholds with all vol that is not 0 (cuz 0 is no evidence)
    delta_vols_nonzero = delta_vols[delta_vols > 0]
    if len(delta_vols_nonzero) == 0:
        vol_low, vol_high = 1, 5
    else:
        vol_low = max(1, int(np.percentile(delta_vols_nonzero, 25)))
        vol_high = max(vol_low + 1, int(np.percentile(delta_vols_nonzero, 75)))

    # Compute spread thresholds with all spread that is not 0 (cuz 0 is no evidence)
    delta_spreads_nonzero = delta_spreads[delta_spreads > 0]
    if len(delta_spreads_nonzero) == 0:
        spread_thresh = 2  # spread thresh is by default 2 if there is no spread activity
    else:
        spread_thresh = int(np.percentile(delta_spreads_nonzero, 80))
        spread_thresh = max(1, spread_thresh)

    # Compute price threshold with all delta price that is not 0
    delta_prices_nonzero = delta_prices[delta_prices > 0]
    if len(delta_prices_nonzero) == 0:
        price_high = 2
    else:
        price_high = max(2, int(np.percentile(delta_prices_nonzero, 99.5)))

    thresholds = {
        "vol_low": vol_low,
        "vol_high": vol_high,

        "spread_thresh": spread_thresh,

        "price_high": price_high,
    }

    return thresholds

# Runs the main spike detector algorithm till end_hour:end_minute
def detect(ticker, end_hour, end_minute):
    alpha = 1 # evidence that move is a fake spike
    beta = 2 # evidence that move is a real repricing
    decay = 0.9 # old evidence loses 10% weight each jump

    # Bayesian confidence that the current market move is a “fake spike”
    mu = alpha / (alpha + beta)

    print("Calibrating model...")
    # Calibrate model first
    thresholds = calibrate(ticker)
    print(thresholds)
    print("Calibration success!")

    # Store the last 10 markets (stores up to 10 seconds ago)
    history = fetch_past_markets(ticker, 10)

    print("Trading commencing...")

    # Alpha/beta updates
    while True:
        time.sleep(1)

        # compares current market to market 10 seconds ago
        curr_market = fetch_market(ticker, history[0])

        alpha = max(1.0, alpha * 0.99)  # Very slow decay of evidence over time
        beta = max(2.0, beta * 0.99)

        if curr_market['delta_price'] >= thresholds['price_high']:
            # Deprioritize old evidence
            alpha = max(1.0, alpha * decay)
            beta  = max(2.0, beta * decay)

            # If the YES price moved up by at least "jump" threshold,
            # classify whether the move looks like a fake spike (alpha) or a real repricing (beta)
            if curr_market["delta_vol"] == 0:
                # only blame "fake spike" if liquidity actually pulls
                if curr_market["delta_spread"] >= thresholds["spread_thresh"]:
                    alpha += 1
                # if spread tightens with no prints, treat it as tiny beta
                elif curr_market["delta_spread"] <= -thresholds["spread_thresh"]:
                    beta += 0.25
                # otherwise no evidence

            # Low volume on a jump suggests a hype spike -> alpha++
            elif curr_market['delta_vol'] <= thresholds['vol_low']:
                alpha += 1
            # High volume on a jump suggests broad participation -> beta++
            elif curr_market['delta_vol'] >= thresholds["vol_high"]:
                beta += 1 + min(3, curr_market["delta_vol"] / thresholds["vol_high"])

            # Spread tightening during the jump suggests healthy liquidity -> beta++
            if curr_market['delta_spread'] <= -thresholds['spread_thresh'] and curr_market['delta_vol'] >= thresholds[
                "vol_high"]:
                beta += 1
            # Spread widening during the jump suggests makers pulled liquidity -> alpha++
            elif curr_market['delta_spread'] >= thresholds['spread_thresh']:
                alpha += 1

            print("JUMP",
                  "ts", curr_market["ts"],
                  "Δp", curr_market["delta_price"],
                  "Δv", curr_market["delta_vol"],
                  "Δspr", curr_market["delta_spread"],
                  "alpha", alpha, "beta", beta)

            mu = alpha / (alpha + beta)
            print("mu", mu)

        if mu > 0.7:
            # Check if the price is starting to drop. If so, bet
            if curr_market['delta_price'] <= 0:
                print("fake spike predicted, and spike stalled. buy no shares to bet against it!")
                date = datetime.fromtimestamp(time.time())
                print(date)

                # Reset alpha and beta values
                alpha = 1
                beta = 2

                mu = alpha / (alpha + beta)

                # spike cooldown
                time.sleep(15)

                # reset history, fetch new past 10 markets
                history = fetch_past_markets(ticker, 10)

        # update history
        history.pop(0)
        history.append(curr_market)

        # End when end time is reached
        if datetime.now().hour == end_hour and datetime.now().minute == end_minute:
            break

def main():
    ticker = input("Input market ticker: ")

    start_hour = int(input("Enter start hour: "))
    start_minute = int(input("Enter start minute: "))

    end_hour = int(input("Enter end hour: "))
    end_minute = int(input("Enter end minute: "))

    # start program at start time (3:25 AM for CBA games)
    print('Waiting for start time...')
    while True:
        if datetime.now().hour == start_hour and datetime.now().minute == start_minute:
            break
        time.sleep(60)

    detect(ticker, end_hour, end_minute)

    print('Program ended.')

if __name__ == "__main__":
    main()