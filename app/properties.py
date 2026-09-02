"""app/properties.py

Этот модуль хранит в себе константы и некоторые системные функции.
"""

from datetime import datetime

from app.config import config

################################
# Constants
################################

# Совпадает ли чет/нечет с календарем
ODD_WEEK_CALENDAR = False

# URI для подключения к базе данных MongoDB
# pylint: disable=line-too-long
MONGODB_URI = config.mongodb_uri

# Токен бота в Telegram
BOT_TOKEN = config.bot_token

# URL прокси-сервера (опционально, например "socks5://user:pass@host:port")
# Если значение не задано — бот запускается без прокси
PROXY_URL: str | None = config.proxy

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
