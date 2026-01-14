import requests

def fetch_market(ticker):
    """
    Returns the market data for a ticker.
    Computes the spread and stores it in the market object.

    :param ticker:
    :return: market
    """
    url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

    market_response = requests.get(url)
    market_data = market_response.json()
    market = market_data['market']

    # Calculate additional parameters
    market['yes_spread'] = market['yes_ask'] - market['yes_bid']

    return market


