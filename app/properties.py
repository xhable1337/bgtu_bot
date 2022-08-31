"""app/properties.py

    Этот модуль хранит в себе константы и некоторые системные функции.
"""

from datetime import datetime
from json import load

################################
# settings.json load
################################
with open('app/settings.json', 'r', encoding='UTF8') as file:
    data = load(file)


################################
# Constants
################################

# Совпадает ли чет/нечет с календарем
ODD_WEEK_CALENDAR = True

# ANCHOR: переместить URI БД к настройкам
# URI для подключения к базе данных MongoDB
# pylint: disable=line-too-long
MONGODB_URI = data['mongodb_uri']

# Токен бота в Telegram
# bot_token = '1147506878:AAGi4Uo6IIGm55TNgG9IIcYIfRZak-HFxN4'
BOT_TOKEN = data['bot_token']

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
