import requests

def fetch_market(ticker, prev_market=None):
    """
    Returns the market data for a ticker.
    Computes the spread.
    Computes the change in volume, spread, and change in price if given a previous market.

    :param ticker:
    :param prev_market:
    :return: market
    """
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

    market_response = requests.get(url)
    market_data = market_response.json()
    market = market_data['market']

    market['yes_spread'] = market['yes_ask'] - market['yes_bid']  # spread

    # Calculate additional parameters if there is a previous market
    if prev_market:
        # change in volume
        market['delta_vol'] = market['volume'] - prev_market['volume']

        # change in spread
        market['delta_spread'] = market['yes_spread'] - prev_market['yes_spread']

        # change in price, convert to cents
        market['delta_price'] = int(round(100*(float(market['yes_bid_dollars']) - float(prev_market['yes_bid_dollars']))))

    return market


