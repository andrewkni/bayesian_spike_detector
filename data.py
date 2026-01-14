"""
Market Logger for backtesting

This script logs a list of Kalshi market tickers ~every second and appends
timestamped market parameters to a CSV file for every ticker

"""

from datetime import datetime
from market import fetch_market
from detector import fetch_past_markets
import csv
import time

def log_markets(markets, start_hour, start_minute, end_hour, end_minute):
    # Wait until start time
    print("Waiting until start time...")
    while True:
        now = datetime.now()
        if now.hour == start_hour and now.minute == start_minute:
            break
        time.sleep(30)

    print("Logging beginning!")

    history = {}
    writers = {}
    files = {}

    for ticker in markets:
        # initial snapshot of past 10 markets
        history[ticker] = fetch_past_markets(ticker, 10)

        f = open(f"{ticker}.csv", "a", newline="")
        files[ticker] = f
        w = csv.writer(f)
        writers[ticker] = w

        # write header if file is empty
        if f.tell() == 0:
            w.writerow(["ts", "yes_ask", "yes_bid", "yes_spread", "delta_vol", "delta_spread", "delta_price"])

    while True:
        now = datetime.now()

        # stop condition
        if now.hour == end_hour and now.minute >= end_minute:
            break

        loop_start = time.time()

        for ticker in markets:
            curr = fetch_market(ticker, history[ticker][0])  # compare curr markets to 10 second ago markets
            history[ticker].pop(0)
            history[ticker].append(curr)

            row = [
                now.replace(microsecond=0).isoformat(),
                curr["yes_ask"],
                curr["yes_bid"],
                curr["yes_spread"],
                curr["delta_vol"],
                curr["delta_spread"],
                curr["delta_price"]
            ]

            writers[ticker].writerow(row)
            files[ticker].flush()

            print(f"{ticker} {row}")

        # sleep to maintain stable cadence
        elapsed = time.time() - loop_start
        time.sleep(max(0.0, 1.0 - elapsed))

    for f in files.values():
        f.close()

def main():
    print("Welcome to the market logger program!")

    all_markets = []

    file = ""
    while file != "e":
        file = input("Enter market ticker (input \"e\" to exit): ")
        all_markets.append(file)

    all_markets.remove("e")

    start_hour = int(input("Enter start hour: "))
    start_minute = int(input("Enter start minute: "))

    end_hour = int(input("Enter end hour: "))
    end_minute = int(input("Enter end minute: "))

    log_markets(all_markets, start_hour, start_minute, end_hour, end_minute)

if __name__ == "__main__":
    main()
