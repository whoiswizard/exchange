# database.py

import sqlite3

DATABASE_NAME = 'coins.db'

def init_db():
    """Ініціалізує БД та створює таблицю з новою колонкою."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        # --- ЗМІНА: Додаємо колонку coingecko_id ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                symbol TEXT PRIMARY KEY NOT NULL,
                coingecko_id TEXT 
            )
        ''')
        conn.commit()

def add_default_coins(default_coins_map):
    """Додає початковий набір монет з їх ID, якщо база даних порожня."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coins")
        if cursor.fetchone()[0] == 0:
            for symbol, cg_id in default_coins_map.items():
                cursor.execute("INSERT OR IGNORE INTO coins (symbol, coingecko_id) VALUES (?, ?)", (symbol, cg_id))
            conn.commit()

def get_coins():
    """Отримує всі монети з їх ID з бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, coingecko_id FROM coins ORDER BY symbol")
        # Повертаємо список словників для зручності
        return [{'symbol': row[0], 'coingecko_id': row[1]} for row in cursor.fetchall()]

def add_coin(symbol: str, coingecko_id: str | None):
    """Додає нову монету з її ID до бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO coins (symbol, coingecko_id) VALUES (?, ?)", (symbol, coingecko_id))
        conn.commit()

def remove_coin(symbol):
    """Видаляє монету з бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coins WHERE symbol = ?", (symbol,))
        conn.commit()