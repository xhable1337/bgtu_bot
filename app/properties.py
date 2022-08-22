"""app/properties.py

    Этот модуль хранит в себе константы и некоторые системные функции.
"""

from datetime import datetime

################################
# Constants
################################

# Совпадает ли чет/нечет с календарем
ODD_WEEK_CALENDAR = True

# ANCHOR: переместить URI БД к настройкам
# URI для подключения к базе данных MongoDB
# pylint: disable=line-too-long
MONGODB_URI = 'mongodb://localhost:27017'

# Токен бота в Telegram
# bot_token = '1147506878:AAGi4Uo6IIGm55TNgG9IIcYIfRZak-HFxN4'
BOT_TOKEN = '2036333661:AAE9ocZfHf-lkrU9SFi8d0DlnB8ftrx5ioE'

################################
# Functions
################################


def week_is_odd() -> bool:
    """Функция определения нечётной учебной недели.

    Возвращает:
        bool: является ли неделя нечётной
    """
    is_odd = datetime.today().isocalendar()[1] % 2 != 0

    if ODD_WEEK_CALENDAR:
        # Если чет/нечет совпадает с календарем
        return is_odd

    return not is_odd
