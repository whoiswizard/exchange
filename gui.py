# gui.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QPushButton, QComboBox, QVBoxLayout, QGridLayout,
    QMessageBox, QGroupBox, QHBoxLayout, QScrollArea
)
from PySide6.QtCore import QTimer, Qt

from calculator import Calculator
from tracker import get_ticker_24hr
from time_utils import get_current_time, get_time_until_open, is_exchange_active, CITIES_TIMEZONES

class CalculatorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор та Трекінг Біржових Даних")
        self.calculator = Calculator()
        self.init_ui()
        self.init_timers()

    def init_ui(self):
        # Основний макет
        main_layout = QVBoxLayout()

        # Калькулятор
        calc_group = QGroupBox("Калькулятор Прибутку та збитку")
        calc_layout = QGridLayout()

        investment_label = QLabel("Сума інвестицій:")
        self.investment_input = QLineEdit()
        self.investment_input.setPlaceholderText("Введіть суму інвестицій")

        entry_price_label = QLabel("Ціна входу:")
        self.entry_price_input = QLineEdit()
        self.entry_price_input.setPlaceholderText("Введіть ціну входу")

        take_profit_label = QLabel("Take Profit:")
        self.take_profit_input = QLineEdit()
        self.take_profit_input.setPlaceholderText("Введіть ціль по прибутку")

        stop_loss_label = QLabel("Stop Loss:")
        self.stop_loss_input = QLineEdit()
        self.stop_loss_input.setPlaceholderText("Введіть стоп-лосс")

        leverage_label = QLabel("Кредитне плече:")
        self.leverage_input = QLineEdit()
        self.leverage_input.setPlaceholderText("Введіть кредитне плече")

        position_type_label = QLabel("Тип позиції:")
        self.position_type_combo = QComboBox()
        self.position_type_combo.addItems(["Long", "Short"])

        self.calculate_button = QPushButton("Розрахувати")
        self.calculate_button.clicked.connect(self.calculate)

        self.profit_label = QLabel("Прибуток: ")
        self.loss_label = QLabel("Збиток: ")
        self.liquidation_label = QLabel("Ціна ліквідації: ")

        # Додавання елементів до калькулятора
        calc_layout.addWidget(investment_label, 0, 0)
        calc_layout.addWidget(self.investment_input, 0, 1)

        calc_layout.addWidget(entry_price_label, 1, 0)
        calc_layout.addWidget(self.entry_price_input, 1, 1)

        calc_layout.addWidget(take_profit_label, 2, 0)
        calc_layout.addWidget(self.take_profit_input, 2, 1)

        calc_layout.addWidget(stop_loss_label, 3, 0)
        calc_layout.addWidget(self.stop_loss_input, 3, 1)

        calc_layout.addWidget(leverage_label, 4, 0)
        calc_layout.addWidget(self.leverage_input, 4, 1)

        calc_layout.addWidget(position_type_label, 5, 0)
        calc_layout.addWidget(self.position_type_combo, 5, 1)

        calc_layout.addWidget(self.calculate_button, 6, 0, 1, 2)

        calc_layout.addWidget(self.profit_label, 7, 0, 1, 2)
        calc_layout.addWidget(self.loss_label, 8, 0, 1, 2)
        calc_layout.addWidget(self.liquidation_label, 9, 0, 1, 2)

        calc_group.setLayout(calc_layout)
        main_layout.addWidget(calc_group)

        # Трекінг цін
        price_group = QGroupBox("Трекінг Цін")
        price_layout = QVBoxLayout()

        # --- ЗМІНА ПОЧАТОК: Додаємо кнопку оновлення ---
        # Горизонтальний макет для кнопки, щоб розмістити її праворуч
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch() # Додаємо розтягувач, щоб кнопка була справа
        self.refresh_button = QPushButton("Оновити ціни")
        self.refresh_button.clicked.connect(self.update_prices)
        top_bar_layout.addWidget(self.refresh_button)
        price_layout.addLayout(top_bar_layout) # Додаємо цей макет зверху
        # --- ЗМІНА КІНЕЦЬ ---

        # Використовуємо ScrollArea для можливого додавання більше монет
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_content)

        # Початкові монети, додано SOLUSDT, BNBUSDT, LINKUSDT, OPUSDT
        self.tracked_coins = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ETH",
            "SOLUSDT": "SOL",
            "BNBUSDT": "BNB",
            "LINKUSDT": "LINK",
            "OPUSDT": "OP"
        }

        self.coin_labels = {}
        for symbol, name in self.tracked_coins.items():
            label = QLabel(f"{name}: Завантаження... | Change: Завантаження...% | Change: Завантаження... USD | Volume: Завантаження... B USD")
            label.setStyleSheet("font-size: 12px;")
            self.scroll_layout.addWidget(label)
            self.coin_labels[symbol] = label

        price_layout.addWidget(self.scroll_area)
        price_group.setLayout(price_layout)
        main_layout.addWidget(price_group)

        # Додавання нових монет
        add_coin_layout = QHBoxLayout()
        self.new_coin_input = QLineEdit()
        self.new_coin_input.setPlaceholderText("Введіть символ монети, наприклад, 'BNBUSDT'")
        self.add_coin_button = QPushButton("Додати монету")
        self.add_coin_button.clicked.connect(self.add_coin)
        add_coin_layout.addWidget(self.new_coin_input)
        add_coin_layout.addWidget(self.add_coin_button)
        # Додаємо поле вводу нової монети до price_layout, а не price_group
        price_layout.addLayout(add_coin_layout)


        # Час у містах та відкриття бірж
        time_group = QGroupBox("Час та Відкриття Бірж")
        time_layout = QGridLayout()

        self.time_labels = {}
        self.countdown_labels = {}
        self.status_labels = {}

        for i, city in enumerate(CITIES_TIMEZONES.keys()):
            city_label = QLabel(city + ":")
            time_label = QLabel("Завантаження...")
            countdown_label = QLabel("Час до відкриття: Завантаження...")
            status_label = QLabel("Статус: Завантаження...")

            self.time_labels[city] = time_label
            self.countdown_labels[city] = countdown_label
            self.status_labels[city] = status_label

            # Зменшення відступів між колонками
            time_layout.addWidget(city_label, i, 0, alignment=Qt.AlignLeft)
            time_layout.addWidget(time_label, i, 1, alignment=Qt.AlignLeft)
            time_layout.addWidget(countdown_label, i, 2, alignment=Qt.AlignLeft)
            time_layout.addWidget(status_label, i, 3, alignment=Qt.AlignLeft)

        time_group.setLayout(time_layout)
        main_layout.addWidget(time_group)

        self.setLayout(main_layout)
        self.resize(480, 800)

    def init_timers(self):
        # --- ЗМІНА ПОЧАТОК: Видаляємо таймер оновлення цін ---
        # Таймер для оновлення цін більше не потрібен, оскільки є кнопка
        # self.price_timer = QTimer()
        # self.price_timer.timeout.connect(self.update_prices)
        # self.price_timer.start(30000) # оновлюємо дані з апі бінансу раз в 30 секунд
        self.update_prices() # Залишаємо початкове оновлення, щоб дані завантажились при старті
        # --- ЗМІНА КІНЕЦЬ ---

        # Таймер для оновлення часу (1 секунда)
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_times)
        self.time_timer.start(1000) # 1000 мс = 1 секунда
        self.update_times() # Початкове оновлення

    def format_volume(self, volume_usd):
        """
        Форматує обсяг торгів у доларах США до мільярдів (B) або мільйонів (M).
        :param volume_usd: Обсяг торгів у доларах США
        :return: Форматований рядок
        """
        if volume_usd >= 1_000_000_000:
            return f"{volume_usd / 1_000_000_000:.2f} B USD"
        elif volume_usd >= 1_000_000:
            return f"{volume_usd / 1_000_000:.2f} M USD"
        else:
            return f"{volume_usd:,.2f} USD"

    def format_change_usd(self, price_change_percent, price):
        """
        Обчислює та форматує зміну ціни у доларах США.
        :param price_change_percent: Відсоток зміни ціни
        :param price: Поточна ціна монети
        :return: Форматований рядок
        """
        change_amount = price * (price_change_percent / 100)
        return f"{change_amount:.2f} USD"

    def update_prices(self):
        for symbol, label in self.coin_labels.items():
            data = get_ticker_24hr(symbol)
            if data:
                price = float(data['lastPrice'])
                price_change_percent = float(data['priceChangePercent'])
                volume = float(data['volume'])
                volume_usd = price * volume
                change_usd = self.format_change_usd(price_change_percent, price)
                formatted_volume = self.format_volume(volume_usd)
                name = symbol[:-4] # Видаляємо 'USDT'
                # Форматування з комами для кращої читабельності
                label.setText(
                    f"{name}: ${price:,.2f} | Change: {price_change_percent:.2f}% | Change: ${change_usd} | Volume: {formatted_volume}"
                )
            else:
                name = symbol[:-4]
                label.setText(
                    f"{name}: Немає даних | Change: Немає даних% | Change: Немає даних | Volume: Немає даних"
                )

    def update_times(self):
        exchange_status = {}
        for city in CITIES_TIMEZONES.keys():
            current_time = get_current_time(city)
            active = is_exchange_active(city)
            if active:
                time_until_open = "Currently trading"
                status = "Active"
            else:
                time_until_open = get_time_until_open(city)
                status = "Passive"

            exchange_status[city] = {
                "current_time": current_time,
                "time_until_open": time_until_open,
                "status": status
            }

        # Сортування бірж: Active першими
        sorted_exchanges = sorted(
            exchange_status.items(),
            key=lambda item: not (item[1]["status"] == "Active")
        )

        for i, (city, info) in enumerate(sorted_exchanges):
            self.time_labels[city].setText(info["current_time"])
            if info["status"] == "Active":
                self.countdown_labels[city].setText(f"Час до відкриття: {info['time_until_open']}")
            else:
                self.countdown_labels[city].setText(f"Час до відкриття: {info['time_until_open']}")
            self.status_labels[city].setText(f"Статус: {info['status']}")

    def calculate(self):
        try:
            investment_amount = float(self.investment_input.text())
            entry_price = float(self.entry_price_input.text())
            take_profit = float(self.take_profit_input.text())
            stop_loss = float(self.stop_loss_input.text())
            leverage = float(self.leverage_input.text())
            position_type = self.position_type_combo.currentText()

            results = self.calculator.calculate(
                investment_amount,
                entry_price,
                take_profit,
                stop_loss,
                leverage,
                position_type
            )

            self.profit_label.setText(f"Прибуток: {results['profit']:.2f} USD")
            self.loss_label.setText(f"Збиток: {results['loss']:.2f} USD")
            self.liquidation_label.setText(f"Ціна ліквідації: {results['liquidation_price']:.2f} USD")

        except ValueError as e:
            QMessageBox.critical(self, "Помилка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Сталася помилка: {str(e)}")

    def add_coin(self):
        symbol = self.new_coin_input.text().strip().upper()
        if not symbol.endswith("USDT"):
            QMessageBox.warning(self, "Попередження", "Символ монети повинен закінчуватися на 'USDT'. Наприклад, 'BNBUSDT'")
            return
        if symbol in self.tracked_coins:
            QMessageBox.information(self, "Інформація", f"Монета {symbol} вже відстежується.")
            return

        name = symbol[:-4] # Видаляємо 'USDT'
        label = QLabel(f"{name}: Завантаження... | Change: Завантаження...% | Change: Завантаження... USD | Volume: Завантаження... B USD")
        label.setStyleSheet("font-size: 12px;")
        self.scroll_layout.addWidget(label)
        self.coin_labels[symbol] = label
        self.tracked_coins[symbol] = name
        self.new_coin_input.clear()
        self.update_prices()