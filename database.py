# database.py

import sqlite3

DATABASE_NAME = 'coins.db'

def init_db():
    """Ініціалізує базу даних та створює таблицю, якщо її не існує."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                symbol TEXT PRIMARY KEY NOT NULL
            )
        ''')
        conn.commit()

def add_default_coins(default_symbols):
    """Додає початковий набір монет, якщо база даних порожня."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coins")
        if cursor.fetchone()[0] == 0:
            for symbol in default_symbols:
                cursor.execute("INSERT OR IGNORE INTO coins (symbol) VALUES (?)", (symbol,))
            conn.commit()

def get_coins():
    """Отримує всі символи монет з бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT symbol FROM coins ORDER BY symbol")
        # Повертаємо список рядків, а не кортежів
        return [row[0] for row in cursor.fetchall()]

def add_coin(symbol):
    """Додає нову монету до бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO coins (symbol) VALUES (?)", (symbol,))
        conn.commit()

def remove_coin(symbol):
    """Видаляє монету з бази даних."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM coins WHERE symbol = ?", (symbol,))
        conn.commit()