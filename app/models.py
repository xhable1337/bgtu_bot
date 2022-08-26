"""app/models.py

    Этот модуль создаёт модели, используемые в коде.
"""

from datetime import datetime
from typing import Union, List

from pydantic import BaseModel

# pylint: disable=too-few-public-methods
# В моделях не нужны методы


class User(BaseModel):
    """Модель пользователя бота.

    #### Поля модели

    - `first_name` (str): имя в Telegram
    - `last_name` (str | None): фамилия в Telegram
    - `user_id` (int): ID в Telegram
    - `username` (str | None): юзернейм в Telegram
    - `state` (str): состояние пользователя
    - `group` (str): текущая группа пользователя
    - `favorite_groups` (list[str] | None): список избранных групп
    """
    first_name: str
    last_name: Union[str, None]
    user_id: int
    username: Union[str, None]
    state: str
    group: str
    favorite_groups: Union[List[str], None]


#! Модели для представления расписания студентов


class Lesson(BaseModel):
    """Модель пары.

    #### Поля модели

    - `number` (int): номер пары
    - `subject` (int): предмет
    - `room` (str): аудитория
    - `teacher` (str): преподаватель (-ли)
    """
    number: int
    subject: str
    room: str
    teacher: str


class Weekday(BaseModel):
    """Модель дня недели.

    #### Поля модели

    - `even` (List[Lesson]): нечётная неделя
    - `odd` (List[Lesson]): чётная неделя
    """
    even: List[Lesson]
    odd: List[Lesson]


class Schedule(BaseModel):
    """Модель расписания.

    #### Поля модели

    - `group` (str): группа
    - `last_updated` (datetime): дата и время обновления
    - `monday` (Weekday): расписание на понедельник
    - `tuesday` (Weekday): расписание на вторник
    - `wednesday` (Weekday): расписание на среду
    - `thursday` (Weekday): расписание на четверг
    - `friday` (Weekday): расписание на пятницу
    - `saturday` (Weekday): расписание на субботу
    """
    group: str
    last_updated: datetime
    monday: Weekday
    tuesday: Weekday
    wednesday: Weekday
    thursday: Weekday
    friday: Weekday
    saturday: Weekday


class Settings(BaseModel):
    """Модель настроек бота.

    #### Поля модели

    - `maintenance` (bool): состояние техработ
    - `admins` (list[int]): список ID админов бота
    """
    maintenance: bool
    admins: List[int]
