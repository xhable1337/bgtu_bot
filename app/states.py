"""app/states.py

Состояния пользователя для встроенной FSM aiogram.

Здесь описаны все состояния, через которые проходит пользователь во время
многошаговых диалогов. Состояние «по умолчанию» (главное меню) в aiogram
представлено отсутствием активного состояния (`None`), поэтому отдельного
состояния для него не требуется.
"""

from aiogram.fsm.state import State, StatesGroup


class FindClass(StatesGroup):
    """Поиск аудитории: пользователь вводит номер аудитории."""

    choosing_number = State()


class AddFavorite(StatesGroup):
    """Добавление группы в избранное: выбор факультета → года → группы."""

    choosing_group = State()


class AddNotification(StatesGroup):
    """Добавление/изменение уведомления: пользователь вводит время.

    День недели хранится в данных состояния (`FSMContext`) под ключом `weekday`.
    """

    choosing_time = State()
