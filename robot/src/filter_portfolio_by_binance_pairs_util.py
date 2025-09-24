import requests

def filter_portfolio_by_binance_pairs(portfolio_coins, quote_assets=("USDT", "BNB")):
    """
    Filters a list of coins, returning only those with at least one valid Binance spot trading pair (e.g., COINUSDT or COINBNB).
    Args:
        portfolio_coins (list[str]): List of coin tickers (e.g., ["ADA", "BTC", ...])
        quote_assets (tuple): Quote assets to check pairs against (default: ("USDT", "BNB"))
    Returns:
        dict: {coin: [valid_pairs]} for coins with at least one valid pair
        list: [coin] for coins with no valid pairs
    """
    url = "https://api.binance.com/api/v3/exchangeInfo"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    all_symbols = set(s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING')

    valid = {}
    missing = []
    for coin in portfolio_coins:
        pairs = [f"{coin}{quote}" for quote in quote_assets]
        found = [pair for pair in pairs if pair in all_symbols]
        if found:
            valid[coin] = found
        else:
            missing.append(coin)
    return valid, missing
