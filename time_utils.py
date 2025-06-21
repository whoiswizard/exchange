# time_utils.py

from datetime import datetime, time, timedelta
import pytz

# Визначення часових поясів для міст
CITIES_TIMEZONES = {
    "Нью-Йорк": "America/New_York",
    "Лондон": "Europe/London",
    "Токіо": "Asia/Tokyo"
}

# Визначення часу відкриття та закриття бірж у кожному місті
EXCHANGE_HOURS = {
    "Нью-Йорк": {"open": time(9, 30), "close": time(16, 0)},
    "Лондон": {"open": time(8, 0), "close": time(16, 30)},
    "Токіо": {"open": time(9, 0), "close": time(15, 0)}
}

REFERENCE_CITY = "Лондон"  # Вибір референтного міста для розрахунку часу до відкриття

def get_current_time(city: str) -> str:
    """
    Отримує поточний час у заданому місті.
    :param city: Назва міста
    :return: Форматований час як рядок
    """
    try:
        timezone = pytz.timezone(CITIES_TIMEZONES[city])
        city_time = datetime.now(timezone)
        return city_time.strftime("%H:%M:%S")
    except Exception as e:
        print(f"Помилка при отриманні часу для {city}: {e}")
        return "Немає даних"

def is_exchange_active(city: str) -> bool:
    """
    Визначає, чи біржа у заданому місті зараз відкрита (active) або закрита (passive).
    :param city: Назва міста
    :return: True, якщо біржа відкрита, інакше False
    """
    try:
        timezone = pytz.timezone(CITIES_TIMEZONES[city])
        now = datetime.now(timezone).time()
        open_time = EXCHANGE_HOURS[city]["open"]
        close_time = EXCHANGE_HOURS[city]["close"]
        return open_time <= now <= close_time
    except Exception as e:
        print(f"Помилка при визначенні статусу біржі для {city}: {e}")
        return False

def get_time_until_open(city: str, reference_city: str = REFERENCE_CITY) -> str:
    """
    Розраховує час до наступного відкриття біржі у заданому місті відносно референтного міста.
    :param city: Назва міста, для якого розраховується час до відкриття
    :param reference_city: Назва референтного міста (за замовчуванням Лондон)
    :return: Форматований час до відкриття як рядок
    """
    try:
        ref_timezone = pytz.timezone(CITIES_TIMEZONES[reference_city])
        ref_time = datetime.now(ref_timezone)

        target_timezone = pytz.timezone(CITIES_TIMEZONES[city])
        target_now = datetime.now(target_timezone)

        # Встановлюємо час відкриття на сьогодні
        target_open_today = target_timezone.localize(datetime.combine(target_now.date(), EXCHANGE_HOURS[city]["open"]))

        if target_now >= target_open_today:
            # Якщо вже після відкриття, наступне відкриття завтра
            target_open = target_open_today + timedelta(days=1)
        else:
            target_open = target_open_today

        # Переводимо час відкриття у референтний часовий пояс
        target_open_ref = target_open.astimezone(ref_timezone)

        delta = target_open_ref - ref_time

        if delta.total_seconds() < 0:
            delta += timedelta(days=1)

        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours} год {minutes} хв {seconds} с"
    except Exception as e:
        print(f"Помилка при розрахунку часу до відкриття для {city}: {e}")
        return "Невідомо"
