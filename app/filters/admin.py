"""app/filters/admin.py

Фильтр для проверки админских прав пользователя.
"""

from typing import Any, Dict, Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.properties import MONGODB_URI
from app.utils.db_worker import DBWorker


class IsAdminFilter(BaseFilter):
    """Фильтр для проверки, является ли пользователь администратором."""

    def __init__(self, is_admin: bool = True):
        """Инициализация фильтра.

        Args:
            is_admin (bool): если True, проверяет, что пользователь - админ,
                            если False, проверяет, что пользователь - не админ
        """
        self.is_admin = is_admin

    async def __call__(self, update: Union[Message, CallbackQuery]) -> bool:
        """Проверка фильтра.

        Args:
            update: объект сообщения или callback запроса

        Returns:
            bool: результат проверки
        """
        db = DBWorker(MONGODB_URI)
        settings = db.settings()

        user_id = update.from_user.id
        is_user_admin = user_id in settings.admins

        return is_user_admin == self.is_admin
