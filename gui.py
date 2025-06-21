# gui.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QPushButton, QComboBox, QVBoxLayout, QGridLayout,
    QMessageBox, QGroupBox, QHBoxLayout, QScrollArea, QCheckBox, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from datetime import datetime
import pytz

from calculator import Calculator
from tracker import get_extended_coin_data # Імпортуємо оновлену функцію
from time_utils import get_current_time, get_time_until_open, is_exchange_active, CITIES_TIMEZONES
from database import init_db, get_coins, add_default_coins, add_coin as db_add_coin, remove_coin as db_remove_coin
from coingecko_api import CoinGeckoAPI # Імпортуємо наш новий API клієнт

class NumericTableWidgetItem(QTableWidgetItem):
    # ... (Цей клас не змінюється) ...
    def __init__(self, value, precision=2):
        self.numeric_value = float(value)
        text_to_display = f"{self.numeric_value:,.{precision}f}"
        super().__init__(text_to_display)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    def __lt__(self, other):
        return self.numeric_value < other.numeric_value

class CalculatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        
        init_db()
        # Оновлюємо початковий список, тепер це словник
        default_coins = {
            "BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "SOLUSDT": "solana", 
            "BNBUSDT": "binancecoin", "XRPUSDT": "ripple", "DOGEUSDT": "dogecoin",
            "AAVEUSDT": "aave", "LINKUSDT": "chainlink", "SUIUSDT": "sui", "MATICUSDT": "matic-network"
        }
        add_default_coins(default_coins)
        
        self.cg_api = CoinGeckoAPI() # Створюємо екземпляр нашого API клієнта

        self.setWindowTitle("Калькулятор та Трекінг Біржових Даних")
        self.calculator = Calculator()
        self.init_ui()
        self.init_timers()
        self.refresh_coin_display()

    def init_ui(self):
        # ... (Код цієї секції не змінюється) ...
        main_layout = QVBoxLayout()
        calc_group = QGroupBox("Калькулятор Прибутку та збитку"); calc_layout = QGridLayout(); investment_label = QLabel("Сума інвестицій:"); self.investment_input = QLineEdit(); self.investment_input.setPlaceholderText("Введіть суму інвестицій"); entry_price_label = QLabel("Ціна входу:"); self.entry_price_input = QLineEdit(); self.entry_price_input.setPlaceholderText("Введіть ціну входу"); take_profit_label = QLabel("Take Profit:"); self.take_profit_input = QLineEdit(); self.take_profit_input.setPlaceholderText("Введіть ціль по прибутку"); stop_loss_label = QLabel("Stop Loss:"); self.stop_loss_input = QLineEdit(); self.stop_loss_input.setPlaceholderText("Введіть стоп-лосс"); leverage_label = QLabel("Кредитне плече:"); self.leverage_input = QLineEdit(); self.leverage_input.setPlaceholderText("Введіть кредитне плече"); position_type_label = QLabel("Тип позиції:"); self.position_type_combo = QComboBox(); self.position_type_combo.addItems(["Long", "Short"]); self.calculate_button = QPushButton("Розрахувати"); self.calculate_button.clicked.connect(self.calculate); self.profit_label = QLabel("Прибуток: "); self.loss_label = QLabel("Збиток: "); self.liquidation_label = QLabel("Ціна ліквідації: "); calc_layout.addWidget(investment_label, 0, 0); calc_layout.addWidget(self.investment_input, 0, 1); calc_layout.addWidget(entry_price_label, 1, 0); calc_layout.addWidget(self.entry_price_input, 1, 1); calc_layout.addWidget(take_profit_label, 2, 0); calc_layout.addWidget(self.take_profit_input, 2, 1); calc_layout.addWidget(stop_loss_label, 3, 0); calc_layout.addWidget(self.stop_loss_input, 3, 1); calc_layout.addWidget(leverage_label, 4, 0); calc_layout.addWidget(self.leverage_input, 4, 1); calc_layout.addWidget(position_type_label, 5, 0); calc_layout.addWidget(self.position_type_combo, 5, 1); calc_layout.addWidget(self.calculate_button, 6, 0, 1, 2); calc_layout.addWidget(self.profit_label, 7, 0, 1, 2); calc_layout.addWidget(self.loss_label, 8, 0, 1, 2); calc_layout.addWidget(self.liquidation_label, 9, 0, 1, 2); calc_group.setLayout(calc_layout); main_layout.addWidget(calc_group)
        price_group = QGroupBox("Трекінг Цін"); price_layout = QVBoxLayout()
        top_bar_layout = QHBoxLayout(); self.refresh_button = QPushButton("Оновити ціни"); self.refresh_button.clicked.connect(self.update_prices); self.delete_button = QPushButton("Видалити обрані"); self.delete_button.clicked.connect(self.delete_selected_coins); top_bar_layout.addWidget(self.refresh_button); top_bar_layout.addWidget(self.delete_button); top_bar_layout.addStretch(); price_layout.addLayout(top_bar_layout)
        self.coin_table = QTableWidget(); self.column_headers = ["", "Назва", "Ціна, USD", "Зміна, %", "Зміна, USD", "Обсяг (24г), М", "Капіталізація, B"]; self.coin_table.setColumnCount(len(self.column_headers)); self.coin_table.setHorizontalHeaderLabels(self.column_headers); self.coin_table.setSortingEnabled(True); self.coin_table.setSelectionBehavior(QTableWidget.SelectRows); self.coin_table.setEditTriggers(QTableWidget.NoEditTriggers); self.coin_table.verticalHeader().setVisible(False)
        header = self.coin_table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.ResizeToContents); header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for i in range(2, len(self.column_headers)): header.setSectionResizeMode(i, QHeaderView.Stretch)
        price_layout.addWidget(self.coin_table)
        add_coin_layout = QHBoxLayout(); self.new_coin_input = QLineEdit(); self.new_coin_input.setPlaceholderText("Введіть символ монети, наприклад, 'BNBUSDT'"); self.add_coin_button = QPushButton("Додати монету"); self.add_coin_button.clicked.connect(self.add_coin); add_coin_layout.addWidget(self.new_coin_input); add_coin_layout.addWidget(self.add_coin_button); price_layout.addLayout(add_coin_layout)
        price_group.setLayout(price_layout); main_layout.addWidget(price_group)
        time_group = QGroupBox("Час та Відкриття Бірж"); time_layout = QGridLayout(); self.time_labels = {}; self.countdown_labels = {}; self.status_labels = {};
        for i, city in enumerate(CITIES_TIMEZONES.keys()): city_label = QLabel(city + ":"); time_label = QLabel("Завантаження..."); countdown_label = QLabel("Час до відкриття: Завантаження..."); status_label = QLabel("Статус: Завантаження..."); self.time_labels[city] = time_label; self.countdown_labels[city] = countdown_label; self.status_labels[city] = status_label; time_layout.addWidget(city_label, i, 0, alignment=Qt.AlignLeft); time_layout.addWidget(time_label, i, 1, alignment=Qt.AlignLeft); time_layout.addWidget(countdown_label, i, 2, alignment=Qt.AlignLeft); time_layout.addWidget(status_label, i, 3, alignment=Qt.AlignLeft)
        time_group.setLayout(time_layout); main_layout.addWidget(time_group)
        self.setLayout(main_layout); self.resize(800, 800)

    def init_timers(self):
        # ... (Код не змінюється) ...
        self.time_timer = QTimer(); self.time_timer.timeout.connect(self.update_times); self.time_timer.start(1000); self.update_times()
        self.price_update_timer = QTimer(self); self.price_update_timer.timeout.connect(self.update_prices); self.price_update_timer.start(30000)

    def refresh_coin_display(self):
        self.coin_table.setSortingEnabled(False)
        
        # get_coins() тепер повертає список словників
        coins_data = get_coins()
        self.coin_table.setRowCount(len(coins_data))

        for row_index, coin in enumerate(coins_data):
            symbol = coin['symbol']
            coingecko_id = coin['coingecko_id']
            
            checkbox_widget = QWidget(); checkbox_layout = QHBoxLayout(checkbox_widget); checkbox = QCheckBox(); checkbox_layout.addWidget(checkbox); checkbox_layout.setAlignment(Qt.AlignCenter); checkbox_layout.setContentsMargins(0,0,0,0); self.coin_table.setCellWidget(row_index, 0, checkbox_widget)
            
            name_item = QTableWidgetItem(symbol[:-4])
            # Зберігаємо обидва значення для подальшого використання
            name_item.setData(Qt.UserRole, symbol)
            name_item.setData(Qt.UserRole + 1, coingecko_id)
            self.coin_table.setItem(row_index, 1, name_item)

            for col in range(2, len(self.column_headers)):
                 self.coin_table.setItem(row_index, col, QTableWidgetItem("..."))

        self.coin_table.setSortingEnabled(True)
        self.update_prices()

    def update_prices(self):
        for row in range(self.coin_table.rowCount()):
            name_item = self.coin_table.item(row, 1)
            if not name_item: continue
            
            symbol = name_item.data(Qt.UserRole)
            coingecko_id = name_item.data(Qt.UserRole + 1)
            
            data = get_extended_coin_data(symbol, coingecko_id)
            
            if data:
                price = float(data['lastPrice'])
                price_change_percent = float(data['priceChangePercent'])
                price_change_usd = price * (price_change_percent / 100)
                volume_usd = float(data['quoteVolume'])
                market_cap = data.get('marketCap')

                self.coin_table.setItem(row, 2, NumericTableWidgetItem(price, precision=4))
                self.coin_table.setItem(row, 3, NumericTableWidgetItem(price_change_percent, precision=2))
                self.coin_table.setItem(row, 4, NumericTableWidgetItem(price_change_usd, precision=2))
                self.coin_table.setItem(row, 5, NumericTableWidgetItem(volume_usd / 1_000_000, precision=2))
                
                if market_cap:
                    self.coin_table.setItem(row, 6, NumericTableWidgetItem(market_cap / 1_000_000_000, precision=2))
                else:
                    item = QTableWidgetItem("N/A"); item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter); self.coin_table.setItem(row, 6, item)

    def add_coin(self):
        """Повністю перероблений метод для автоматичного пошуку ID."""
        symbol_input = self.new_coin_input.text().strip().upper()
        if not symbol_input: return
        if not symbol_input.endswith("USDT"):
            QMessageBox.warning(self, "Попередження", "Символ монети повинен закінчуватися на 'USDT'.")
            return
        
        # Перевіряємо, чи є вже така монета в БД
        existing_symbols = [c['symbol'] for c in get_coins()]
        if symbol_input in existing_symbols:
            QMessageBox.information(self, "Інформація", f"Монета {symbol_input} вже відстежується.")
            return

        # Показуємо користувачу, що йде пошук
        self.add_coin_button.setText("Пошук ID...")
        self.add_coin_button.setEnabled(False)
        QApplication.processEvents() # Оновлюємо GUI

        base_asset = symbol_input.replace("USDT", "")
        coingecko_id = self.cg_api.find_id_by_symbol(base_asset)

        # Повертаємо кнопку в нормальний стан
        self.add_coin_button.setText("Додати монету")
        self.add_coin_button.setEnabled(True)

        if not coingecko_id:
            QMessageBox.warning(self, "ID не знайдено", 
                                f"Не вдалося автоматично знайти ID для '{base_asset}' на CoinGecko.\n"
                                f"Монета буде додана без даних про капіталізацію.")

        # Додаємо в БД з ID або без нього (None)
        db_add_coin(symbol_input, coingecko_id)
        self.new_coin_input.clear()
        self.refresh_coin_display()
    
    def delete_selected_coins(self):
        # ... (Код не змінюється) ...
        coins_to_delete = [];
        for row in range(self.coin_table.rowCount()):
            checkbox_widget = self.coin_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    symbol = self.coin_table.item(row, 1).data(Qt.UserRole)
                    coins_to_delete.append(symbol)
        if not coins_to_delete:
            QMessageBox.information(self, "Інформація", "Будь ласка, оберіть монети для видалення.")
            return
        reply = QMessageBox.question(self, "Підтвердження", f"Ви впевнені, що хочете видалити {len(coins_to_delete)} монет(и)?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for symbol in coins_to_delete:
                db_remove_coin(symbol)
            self.refresh_coin_display()
    
    # ... (решта методів не змінюється) ...
    def calculate(self):
        try:
            investment_amount = float(self.investment_input.text()); entry_price = float(self.entry_price_input.text()); take_profit = float(self.take_profit_input.text()); stop_loss = float(self.stop_loss_input.text()); leverage = float(self.leverage_input.text()); position_type = self.position_type_combo.currentText()
            results = self.calculator.calculate(investment_amount, entry_price, take_profit, stop_loss, leverage, position_type)
            self.profit_label.setText(f"Прибуток: {results['profit']:.2f} USD"); self.loss_label.setText(f"Збиток: {results['loss']:.2f} USD"); self.liquidation_label.setText(f"Ціна ліквідації: {results['liquidation_price']:.2f} USD")
        except ValueError as e: QMessageBox.critical(self, "Помилка", str(e))
        except Exception as e: QMessageBox.critical(self, "Помилка", f"Сталася помилка: {str(e)}")
    def update_times(self):
        exchange_status = {}; ref_now = datetime.now(pytz.timezone(CITIES_TIMEZONES["Лондон"])); is_weekend = ref_now.weekday() in [5, 6]
        for city in CITIES_TIMEZONES.keys(): current_time = get_current_time(city); time_until_open = get_time_until_open(city); status = "Вихідний" if is_weekend else ("Active" if is_exchange_active(city) else "Passive"); exchange_status[city] = { "current_time": current_time, "time_until_open": time_until_open, "status": status }
        sorted_exchanges = sorted(exchange_status.items(), key=lambda item: (item[1]["status"] != "Active", item[1]["status"] != "Passive", item[1]["status"] != "Вихідний"))
        for city, info in sorted_exchanges: self.time_labels[city].setText(info["current_time"]); self.countdown_labels[city].setText("Зараз торги" if info["status"] == "Active" else f"До відкриття: {info['time_until_open']}"); self.status_labels[city].setText(f"Статус: {info['status']}")

# Потрібно додати імпорт QApplication для processEvents
from PySide6.QtWidgets import QApplication