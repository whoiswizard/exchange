# tracker.py

import requests

def get_ticker_24hr(symbol: str) -> dict | None:
    # ... (Ця функція не змінюється) ...
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr', params={'symbol': symbol})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Помилка при отриманні даних з Binance для {symbol}: {e}")
        return None

def get_market_cap(coingecko_id: str | None) -> float | None:
    # ... (Ця функція не змінюється) ...
    if not coingecko_id:
        return None
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('market_data', {}).get('market_cap', {}).get('usd')
    except requests.RequestException as e:
        print(f"Помилка при отриманні даних з CoinGecko для {coingecko_id}: {e}")
        return None

def get_extended_coin_data(symbol: str, coingecko_id: str | None) -> dict | None:
    """Отримує розширені дані. Тепер coingecko_id передається як аргумент."""
    binance_data = get_ticker_24hr(symbol)
    if not binance_data:
        return None

    # Отримуємо капіталізацію, використовуючи переданий ID
    market_cap = get_market_cap(coingecko_id)
    binance_data['marketCap'] = market_cap
    
    return binance_data