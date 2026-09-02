"""app/config.py

Конфигурация приложения, загружаемая из переменных окружения и файла `.env`.

Для чтения настроек используется Pydantic Settings. Приоритет значений:

1. переменные окружения;
2. файл `.env` в корне проекта.

Поля конфигурации автоматически валидируются при импорте модуля.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Настройки бота.

    #### Поля модели

    - `bot_token` (str): токен бота в Telegram
    - `mongodb_uri` (str): URI для подключения к базе данных MongoDB
    - `proxy` (str | None): URL прокси-сервера (опционально)
    - `odd_week_calendar` (bool): совпадает ли чётность недели с календарём
    """

    bot_token: str = Field(validation_alias="BOT_TOKEN")
    mongodb_uri: str = Field(validation_alias="MONGODB_URI")
    proxy: str | None = Field(default=None, validation_alias="PROXY_URL")
    odd_week_calendar: bool = Field(
        default=False, validation_alias="ODD_WEEK_CALENDAR"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Config()
