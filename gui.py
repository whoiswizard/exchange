# gui.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QPushButton, QComboBox, QVBoxLayout, QGridLayout,
    QMessageBox, QGroupBox, QHBoxLayout, QScrollArea, QCheckBox
)
from PySide6.QtCore import QTimer, Qt
from datetime import datetime
import pytz

from calculator import Calculator
from tracker import get_ticker_24hr
from time_utils import get_current_time, get_time_until_open, is_exchange_active, CITIES_TIMEZONES
from database import init_db, get_coins, add_default_coins, add_coin as db_add_coin, remove_coin as db_remove_coin

class CalculatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        
        init_db()
        default_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        add_default_coins(default_coins)

        self.setWindowTitle("Калькулятор та Трекінг Біржових Даних")
        self.calculator = Calculator()
        self.coin_widgets = {}
        
        self.init_ui()
        self.init_timers()
        
        self.refresh_coin_display()

    def init_ui(self):
        main_layout = QVBoxLayout()
        calc_group = QGroupBox("Калькулятор Прибутку та збитку"); calc_layout = QGridLayout(); investment_label = QLabel("Сума інвестицій:"); self.investment_input = QLineEdit(); self.investment_input.setPlaceholderText("Введіть суму інвестицій"); entry_price_label = QLabel("Ціна входу:"); self.entry_price_input = QLineEdit(); self.entry_price_input.setPlaceholderText("Введіть ціну входу"); take_profit_label = QLabel("Take Profit:"); self.take_profit_input = QLineEdit(); self.take_profit_input.setPlaceholderText("Введіть ціль по прибутку"); stop_loss_label = QLabel("Stop Loss:"); self.stop_loss_input = QLineEdit(); self.stop_loss_input.setPlaceholderText("Введіть стоп-лосс"); leverage_label = QLabel("Кредитне плече:"); self.leverage_input = QLineEdit(); self.leverage_input.setPlaceholderText("Введіть кредитне плече"); position_type_label = QLabel("Тип позиції:"); self.position_type_combo = QComboBox(); self.position_type_combo.addItems(["Long", "Short"]); self.calculate_button = QPushButton("Розрахувати"); self.calculate_button.clicked.connect(self.calculate); self.profit_label = QLabel("Прибуток: "); self.loss_label = QLabel("Збиток: "); self.liquidation_label = QLabel("Ціна ліквідації: "); calc_layout.addWidget(investment_label, 0, 0); calc_layout.addWidget(self.investment_input, 0, 1); calc_layout.addWidget(entry_price_label, 1, 0); calc_layout.addWidget(self.entry_price_input, 1, 1); calc_layout.addWidget(take_profit_label, 2, 0); calc_layout.addWidget(self.take_profit_input, 2, 1); calc_layout.addWidget(stop_loss_label, 3, 0); calc_layout.addWidget(self.stop_loss_input, 3, 1); calc_layout.addWidget(leverage_label, 4, 0); calc_layout.addWidget(self.leverage_input, 4, 1); calc_layout.addWidget(position_type_label, 5, 0); calc_layout.addWidget(self.position_type_combo, 5, 1); calc_layout.addWidget(self.calculate_button, 6, 0, 1, 2); calc_layout.addWidget(self.profit_label, 7, 0, 1, 2); calc_layout.addWidget(self.loss_label, 8, 0, 1, 2); calc_layout.addWidget(self.liquidation_label, 9, 0, 1, 2); calc_group.setLayout(calc_layout); main_layout.addWidget(calc_group)

        price_group = QGroupBox("Трекінг Цін")
        price_layout = QVBoxLayout()

        top_bar_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Оновити ціни")
        self.refresh_button.clicked.connect(self.update_prices)
        self.delete_button = QPushButton("Видалити обрані")
        self.delete_button.clicked.connect(self.delete_selected_coins)
        
        top_bar_layout.addWidget(self.refresh_button)
        top_bar_layout.addWidget(self.delete_button)
        top_bar_layout.addStretch()
        price_layout.addLayout(top_bar_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Початкове створення scroll_content, яке буде замінено в refresh_coin_display
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        price_layout.addWidget(self.scroll_area)
        
        add_coin_layout = QHBoxLayout()
        self.new_coin_input = QLineEdit()
        self.new_coin_input.setPlaceholderText("Введіть символ монети, наприклад, 'BNBUSDT'")
        self.add_coin_button = QPushButton("Додати монету")
        self.add_coin_button.clicked.connect(self.add_coin)
        add_coin_layout.addWidget(self.new_coin_input)
        add_coin_layout.addWidget(self.add_coin_button)
        price_layout.addLayout(add_coin_layout)

        price_group.setLayout(price_layout)
        main_layout.addWidget(price_group)

        time_group = QGroupBox("Час та Відкриття Бірж"); time_layout = QGridLayout(); self.time_labels = {}; self.countdown_labels = {}; self.status_labels = {};
        for i, city in enumerate(CITIES_TIMEZONES.keys()): city_label = QLabel(city + ":"); time_label = QLabel("Завантаження..."); countdown_label = QLabel("Час до відкриття: Завантаження..."); status_label = QLabel("Статус: Завантаження..."); self.time_labels[city] = time_label; self.countdown_labels[city] = countdown_label; self.status_labels[city] = status_label; time_layout.addWidget(city_label, i, 0, alignment=Qt.AlignLeft); time_layout.addWidget(time_label, i, 1, alignment=Qt.AlignLeft); time_layout.addWidget(countdown_label, i, 2, alignment=Qt.AlignLeft); time_layout.addWidget(status_label, i, 3, alignment=Qt.AlignLeft)
        time_group.setLayout(time_layout); main_layout.addWidget(time_group)
        self.setLayout(main_layout); self.resize(480, 800)

    def init_timers(self):
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_times)
        self.time_timer.start(1000)
        self.update_times()

    def refresh_coin_display(self):
        # --- РАДИКАЛЬНЕ ВИПРАВЛЕННЯ: Повна заміна вмісту ScrollArea ---
        
        # 1. Створюємо новий віджет-контейнер і новий лейаут
        new_scroll_content = QWidget()
        new_scroll_layout = QVBoxLayout(new_scroll_content)
        new_scroll_layout.setContentsMargins(5, 5, 5, 5)

        # Очищуємо старий словник віджетів
        self.coin_widgets.clear()
        
        # 2. Отримуємо актуальний список монет з БД
        symbols = get_coins()
        
        # 3. Наповнюємо новий лейаут новими віджетами
        for symbol in symbols:
            row_layout = QHBoxLayout()
            checkbox = QCheckBox()
            label = QLabel(f"{symbol[:-4]}: Завантаження...")
            label.setStyleSheet("font-size: 12px;")

            row_layout.addWidget(checkbox)
            row_layout.addWidget(label)
            row_layout.addStretch()

            new_scroll_layout.addLayout(row_layout)
            self.coin_widgets[symbol] = {'checkbox': checkbox, 'label': label, 'layout': row_layout}
        
        new_scroll_layout.addStretch() # Додаємо розтягувач в кінець, щоб рядки були зверху

        # 4. Встановлюємо новий віджет як вміст для QScrollArea
        # Старий віджет автоматично видаляється
        self.scroll_area.setWidget(new_scroll_content)
        
        # 5. Оновлюємо посилання на ключові елементи
        self.scroll_content = new_scroll_content
        self.scroll_layout = new_scroll_layout

        # 6. Оновлюємо ціни для новостворених лейблів
        self.update_prices()

    def update_prices(self):
        for symbol, widgets in self.coin_widgets.items():
            label = widgets['label']
            data = get_ticker_24hr(symbol)
            if data:
                price = float(data['lastPrice'])
                price_change_percent = float(data['priceChangePercent'])
                volume = float(data['volume']); volume_usd = price * volume; change_usd = self.format_change_usd(price_change_percent, price); formatted_volume = self.format_volume(volume_usd); name = symbol[:-4]
                label.setText(f"{name}: ${price:,.2f} | Change: {price_change_percent:.2f}% | Change: ${change_usd} | Volume: {formatted_volume}")
            else:
                label.setText(f"{symbol[:-4]}: Немає даних")

    def delete_selected_coins(self):
        coins_to_delete = []
        for symbol, widgets in self.coin_widgets.items():
            if widgets['checkbox'].isChecked():
                coins_to_delete.append(symbol)

        if not coins_to_delete:
            QMessageBox.information(self, "Інформація", "Будь ласка, оберіть монети для видалення.")
            return

        reply = QMessageBox.question(self, "Підтвердження", 
                                     f"Ви впевнені, що хочете видалити {len(coins_to_delete)} монет(и)?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            for symbol in coins_to_delete:
                db_remove_coin(symbol)
            self.refresh_coin_display()
    
    def add_coin(self):
        symbol = self.new_coin_input.text().strip().upper()
        if not symbol:
            return
        if not symbol.endswith("USDT"):
            QMessageBox.warning(self, "Попередження", "Символ монети повинен закінчуватися на 'USDT'.")
            return
        
        if symbol in get_coins():
            QMessageBox.information(self, "Інформація", f"Монета {symbol} вже відстежується.")
            return

        db_add_coin(symbol)
        self.new_coin_input.clear()
        self.refresh_coin_display()
    
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
    def format_volume(self, volume_usd):
        if volume_usd >= 1_000_000_000: return f"{volume_usd / 1_000_000_000:.2f} B USD"
        elif volume_usd >= 1_000_000: return f"{volume_usd / 1_000_000:.2f} M USD"
        else: return f"{volume_usd:,.2f} USD"
    def format_change_usd(self, price_change_percent, price):
        return f"{price * (price_change_percent / 100):.2f} USD"