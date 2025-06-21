# calculator.py

class Calculator:
    def __init__(self):
        self.maintenance_margin_rate = 0.005  # 0.5% маржа

    def calculate(self, investment_amount, entry_price, take_profit, stop_loss, leverage, position_type):
        if investment_amount <= 0 or entry_price <= 0 or take_profit <= 0 or stop_loss <= 0 or leverage <= 0:
            raise ValueError("Введіть коректні значення.")

        position_size = investment_amount * leverage
        quantity = position_size / entry_price  # Кількість монет

        if position_type == "Long":
            profit = (take_profit - entry_price) * quantity
            loss = (entry_price - stop_loss) * quantity
            liquidation_price = self.calculate_liquidation_price_long(entry_price, leverage)
        elif position_type == "Short":
            profit = (entry_price - take_profit) * quantity
            loss = (stop_loss - entry_price) * quantity
            liquidation_price = self.calculate_liquidation_price_short(entry_price, leverage)
        else:
            raise ValueError("Невірний тип позиції.")

        return {
            "profit": profit,
            "loss": loss,
            "liquidation_price": liquidation_price
        }

    def calculate_liquidation_price_long(self, entry_price, leverage):
        return entry_price * (1 - ((1 / leverage) - self.maintenance_margin_rate))

    def calculate_liquidation_price_short(self, entry_price, leverage):
        return entry_price * (1 + ((1 / leverage) - self.maintenance_margin_rate))
