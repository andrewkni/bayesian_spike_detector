from market import *
import time

# Input market ticker here
ticker = "KXNBAGAME-26JAN13SASOKC-SAS"

def main():
    alpha = 2 # evidence that move is a fake spike
    beta = 8 # evidence that move is a real repricing

    prev_market = fetch_market(ticker)

    while True:
        time.sleep(5)
        curr_market = fetch_market(ticker)

        delta_vol = curr_market['volume'] - prev_market['volume'] # change in volume
        delta_spread = curr_market['yes_spread'] - prev_market['yes_spread'] # change in spread
        pct_price = (
                (float(curr_market['last_price_dollars']) - float(prev_market['last_price_dollars']))
                / float(prev_market['last_price_dollars'])) # pct change in price

        prev_market = curr_market


if __name__ == '__main__':
    main()