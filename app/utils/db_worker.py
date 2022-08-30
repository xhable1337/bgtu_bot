"""db_worker.py

    Этот модуль осуществляет всю работу, связанную с базой данных MongoDB.
    Поля класса DBUser написаны на property и имеют удобный синтаксис получения
    и изменения значений.

    Для работы с модулем, нужно его импортировать и создать инстанс класса DBWorker:

    ```
    from db_worker import DBWorker

    db = DBWorker('my_host')
    ```
"""

from datetime import datetime
from time import time
from typing import Union, List

from pymongo import MongoClient
from loguru import logger

from app.models import Lesson, Schedule, User, Settings
from app.properties import MONGODB_URI


class DBInterface:
    """Интерфейс для работы с базой данных.
    """

    # pylint: disable=too-few-public-methods
    # Это класс-интерфейс, он не требует дополнительных методов.

    def __new__(cls, host: str = MONGODB_URI):
        if not hasattr(cls, 'instance'):
            logger.debug('DBInterface created')
            cls._db_uri = host
            cls.instance = super(DBInterface, cls).__new__(cls)
        return cls.instance

    def __init__(self, host: str = MONGODB_URI, db_name: str = 'bgtu_bot'):
        # Подключение к СУБД
        self._db_uri = host
        client = MongoClient(self._db_uri)

        # Подключение к БД
        database = client.get_database(db_name)

        # Подключение к коллекциям БД
        self._users = database.users
        self._schedule = database.schedule
        self._groups = database.groups
        self._settings = database.settings
        self._scheduled_msg = database.scheduled_messages
        self._teachers = database.teachers


class DBUser(DBInterface):
    """Класс для работы с пользователем в базе данных.
    """

    # pylint: disable=too-many-instance-attributes
    # При инициализации объявляются все необходимые поля.

    def __init__(self, user_id: int):
        super().__init__()
        self._db_obj: dict = self._users.find_one(
            {'user_id': user_id}, {'_id': False})

        if not self._db_obj:
            raise ValueError(f'User {user_id} not found.')

        self.first_name: str = self._db_obj['first_name']
        self.last_name: Union[str, None] = self._db_obj['last_name']
        self.user_id: int = self._db_obj['user_id']
        self.username: Union[str, None] = self._db_obj['username']
        self._state: str = self._db_obj['state']
        self._group: str = self._db_obj['group']
        self._notification_time: dict = self._db_obj.get('notification_time')
        self._favorite_groups: Union[List[str], None] = (
            self._db_obj['favorite_groups']
        )

    def obj(self) -> User:
        """Объект модели User."""
        return User(**{
            'first_name': self.first_name,
            'last_name': self.last_name,
            'user_id': self.user_id,
            'username': self.username,
            'state': self.state,
            'group': self.group,
            'notification_time': self.notification_time,
            'favorite_groups': self.favorite_groups
        })

    @property
    def full_name(self):
        """Полное имя пользователя (fn+ln при наличии ln, либо только fn)."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"

        return self.first_name

    def __str__(self):
        if self.username:
            details = f'[@{self.username}, {self.user_id}]'
        else:
            details = f'[{self.user_id}]'

        group = self.group

        return f"{self.full_name} {details} - {group}"

    @property
    def state(self) -> str:
        """Текущее состояние пользователя."""
        return self._state

    @state.setter
    def state(self, new_state: str):
        self._state = new_state
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'state': new_state}}
        )

    @property
    def group(self) -> str:
        """Текущая группа пользователя."""
        return self._group

    @group.setter
    def group(self, new_group: str):
        self._group = new_group
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'group': new_group}}
        )

    @property
    def favorite_groups(self) -> list[str]:
        """Список избранных групп пользователя."""
        return self._favorite_groups

    @favorite_groups.setter
    def favorite_groups(self, new_fav: list[str]):
        self._favorite_groups = new_fav
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'favorite_groups': new_fav}}
        )

    @property
    def notification_time(self) -> dict[str, str]:
        """Словарь ежедневных уведомлений пользователя"""
        return self._notification_time

    @notification_time.setter
    def notification_time(self, new_notification_time: dict[str, str]):
        self._favorite_groups = new_notification_time
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'notification_time': new_notification_time}}
        )


class DBSettings(DBInterface):
    """Класс для работы с настройками бота в базе данных.
    """

    # pylint: disable=too-many-instance-attributes
    # При инициализации объявляются все необходимые поля.

    def __init__(self):
        super().__init__()
        self._db_obj: dict = self._settings.find_one({}, {'_id': False})

        if not self._db_obj:
            raise ValueError('Settings are not found.')

        self._maintenance: bool = self._db_obj['maintenance']
        self._admins: list[int] = self._db_obj['admins']

    def obj(self) -> Settings:
        """Объект модели User."""
        return Settings(**{
            'maintenance': self._maintenance,
            'admins': self._admins
        })

    @property
    def maintenance(self) -> bool:
        """Состояние техработ."""
        return self._maintenance

    @maintenance.setter
    def maintenance(self, new_maintenance_state: bool):
        self._maintenance = new_maintenance_state
        self._settings.update_one(
            {},
            {'$set': {'maintenance': new_maintenance_state}}
        )

    @property
    def admins(self) -> list[int]:
        """Список админов бота."""
        return self._admins

    @admins.setter
    def admins(self, new_admins_list: list[int]):
        self._admins = new_admins_list
        self._settings.update_one(
            {},
            {'$set': {'admins': new_admins_list}}
        )


class DBWorker(DBInterface):
    """Класс-синглтон для работы с базой данных.
    """
    def __new__(cls, host: str, db_name: str = 'bgtu_bot'):
        if not hasattr(cls, 'instance'):
            cls._db_name = db_name
            cls.instance = super(DBWorker, cls).__new__(cls)
        return cls.instance

    def user(self, user_id: int) -> DBUser:
        """Функция получения объекта пользователя.

        Аргументы:
            user_id (int): ID пользователя в Telegram

        Возвращает:
            DBUser: объект пользователя
        """
        try:
            return DBUser(user_id)
        except ValueError:
            return None

    def add_user(self, user: User, replace: bool = True):
        """Функция добавления пользователя в базу данных.

        Аргументы:
            user (User): объект пользователя
            replace (bool): заменять ли имеющийся объект пользователя
        """
        db_user = self.user(user.user_id)
        if db_user:
            if replace:
                self._users.replace_one({'user_id': user.user_id}, user.dict())
        else:
            self._users.insert_one(user.dict())

    def schedule(
            self, group: str, weekday: str = None,
            weektype: str = None) -> Schedule:
        """Функция получения объекта расписания по группе.

        Аргументы:
            group (str): имя группы
            weekday (str, optional): день недели. Требует weektype.
            weektype (str, optional): тип недели (even/odd). Требует weekday.

        Возвращает:
            Schedule: объект расписания
        """
        db_schedule = self._schedule.find_one(
            {'group': group}, {'_id': False}
        )

        if not db_schedule:
            return None

        if weekday and weektype:
            lessons_list = db_schedule[weekday][weektype]
            return [Lesson(**lessons_list[i]) for i in range(len(lessons_list))]

        return Schedule(**db_schedule)

    def add_schedule(self, schedule: Schedule, replace: bool = True):
        """Функция добавления расписания в базу данных.

        Аргументы:
            schedule (Schedule): объект расписания
            replace (bool): заменять ли имеющееся расписание
        """
        if self._schedule.find_one({'group': schedule.group}):
            if replace:
                self._schedule.replace_one(
                    {'group': schedule.group}, schedule.dict())
        else:
            self._schedule.insert_one(schedule.dict())

    def groups(self, faculty: str, year: str) -> list[str]:
        """Функция получения списка групп по факультету и году поступления.

        Аргументы:
            faculty (str): факультет
            year (str): год поступления

        Возвращает:
            list[str]: список групп
        """
        # REVIEW - нужно полностью перейти на четырёхзначные года
        if len(year) == 2:
            year = datetime.today().strftime("%Y")[:2] + year

        groups = self._groups.find_one(
            {'faculty': faculty, 'year': year}
        )

        return groups['groups']

    def add_groups(self, faculty: str, year: str, groups: list[str], replace: bool = True):
        """Функция добавления групп в базу данных.

        Аргументы:
            faculty (str): факультет списка групп
            year (str): год поступления списка групп
            groups (list[str]): список групп
            replace (bool): заменять ли имеющиеся группы
        """
        # TODO: Переделать под модель из pydantic
        last_updated = time()

        document = {
            'last_updated': last_updated,
            'faculty': faculty,
            'year': year,
            'groups': groups
        }

        if self._groups.find_one({'faculty': faculty, 'year': year}):
            if replace:
                self._groups.replace_one(
                    {'faculty': faculty, 'year': year}, document)
        else:
            self._groups.insert_one(document)

    def add_teacher(self, teacher: dict, replace: bool = True):
        """Функция добавления преподавателя в базу данных.

        Аргументы:
            teacher (dict): документ (object-like) преподавателя
            replace (bool): заменять ли имеющиеся объекты преподавателей

        TODO: Переделать под модели pydantic
        """
        name = teacher.get('name')
        if self._teachers.find_one({'name': name}):
            if replace:
                self._teachers.replace_one({'name': name}, teacher)
        else:
            self._teachers.insert_one(teacher)

    @staticmethod
    def years() -> list[int]:
        """Функция получения актуальных годов поступления.

        Возвращает:
            list[int]: список актуальных годов поступления
        """
        # REVIEW: не работает с базой данных
        years = []
        now = datetime.now()
        day = int(now.strftime('%d'))
        month = int(now.strftime('%m'))
        year = int(now.strftime('%Y'))

        # Добавлять ли следующий год в список
        next_year = True

        if month < 8:
            # ? Учебный год ЕЩЁ не кончился (1-7 месяцы)
            # Добавлять текущий календарный год в список не нужно
            next_year = False
        elif month == 8:
            # ? В конце августа (после ≈27 числа) составляют новое расписание
            # Нужно добавлять текущий календарный год в список при дне >= 27
            next_year = day >= 27
        else:
            # ? Учебный год УЖЕ начался (9-12 месяцы)
            # Нужно добавлять текущий календарный год в список
            next_year = True

        if next_year:
            # Нужно добавить текущий год в список
            for _ in range(4):
                years.append(year)
                year -= 1
        else:
            # Убираем текущий год из списка
            for _ in range(4):
                year -= 1
                years.append(year)

        return years

    @staticmethod
    def faculties() -> list[dict[str, str]]:
        """Функция получения факультетов.

        Возвращает:
            list[int]: список факультетов
        """
        # REVIEW: не работает с базой данных

        faculties_objects = [
            {
                'full': 'Факультет информационных технологий',
                'short': 'ФИТ'
            },
            {
                'full': 'Факультет энергетики и электроники',
                'short': 'ФЭЭ'
            },
            {
                'full': 'Факультет отраслевой и цифровой экономики',
                'short': 'ФОЦЭ'
            },
            {
                'full': 'Учебно-научный технологический институт',
                'short': 'УНТИ'
            },
            {
                'full': 'Механико-технологический факультет',
                'short': 'МТФ'
            },
            {
                'full': 'Учебно-научный институт транспорта',
                'short': 'УНИТ'
            },
        ]

        return faculties_objects

    def settings(self) -> DBSettings:
        """Функция получения настроек бота.

        Возвращает:
            DBSettings: объект настроек бота
        """
        try:
            return DBSettings()
        except ValueError:
            return None
