# tracker.py

import requests

def get_ticker_24hr(symbol: str) -> dict:
    """
    Отримує 24-годинні статистичні дані криптовалюти з Binance.
    :param symbol: Торгова пара, наприклад, 'BTCUSDT'
    :return: Словник з даними або None у випадку помилки
    """
    try:
        response = requests.get('https://api.binance.com/api/v3/ticker/24hr', params={'symbol': symbol})
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Помилка при отриманні даних для {symbol}: {e}")
        return None
