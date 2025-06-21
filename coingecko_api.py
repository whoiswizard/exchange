# coingecko_api.py

import requests
import time

class CoinGeckoAPI:
    def __init__(self):
        self._coin_list = None
        self._last_fetch_time = 0
        self._cache_duration = 3600 * 24  # Кешувати на 24 години

    def _fetch_coin_list(self):
        """Отримує повний список монет з CoinGecko."""
        print("Fetching full coin list from CoinGecko...")
        try:
            response = requests.get("https://api.coingecko.com/api/v3/coins/list")
            response.raise_for_status()
            self._coin_list = response.json()
            self._last_fetch_time = time.time()
            print("Coin list fetched successfully.")
        except requests.RequestException as e:
            print(f"Failed to fetch coin list from CoinGecko: {e}")
            self._coin_list = []

    def get_coin_list(self):
        """Повертає кешований список монет, оновлюючи його за потреби."""
        current_time = time.time()
        if not self._coin_list or (current_time - self._last_fetch_time > self._cache_duration):
            self._fetch_coin_list()
        return self._coin_list

    def find_id_by_symbol(self, target_symbol: str):
        """Знаходить CoinGecko ID за символом (тікером)."""
        target_symbol = target_symbol.lower()
        coin_list = self.get_coin_list()
        
        # Шукаємо точне співпадіння
        for coin in coin_list:
            if coin.get('symbol') == target_symbol:
                return coin.get('id')
        
        # Якщо точного немає, повертаємо None
        return None