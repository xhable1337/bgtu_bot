from datetime import datetime
from typing import Union, List

from pymongo import MongoClient

from app.models import Schedule

# ANCHOR: переместить URI БД к настройкам
MONGODB_URI = 'mongodb://heroku_38n7vrr9:8pojct20ovk5sgvthiugo3kmpa@dnevnikcluster-shard-00-00.7tatu.mongodb.net:27017,dnevnikcluster-shard-00-01.7tatu.mongodb.net:27017,dnevnikcluster-shard-00-02.7tatu.mongodb.net:27017/heroku_38n7vrr9?ssl=true&replicaSet=atlas-106r53-shard-0&authSource=admin&retryWrites=true&w=majority'


class DBInterface:
    def __new__(cls, host: str = MONGODB_URI):
        if not hasattr(cls, 'instance'):
            print('Interface created')
            cls.instance = super(DBInterface, cls).__new__(cls)
        return cls.instance

    def __init__(self, host: str = MONGODB_URI, db_name: str = 'heroku_38n7vrr9'):
        # Подключение к СУБД
        client = MongoClient(host)

        # Подключение к БД
        database = client.get_database(db_name)

        # Подключение к коллекциям БД
        self._users = database.users
        self._schedule = database.schedule2
        self._groups = database.groups
        self._settings = database.settings
        self._scheduled_msg = database.scheduled_messages


class DBUser(DBInterface):
    def __init__(self, user_id: int):
        super().__init__()
        self._db_obj = self._users.find_one(
            {'user_id': user_id}, {'_id': False})

        if not self._db_obj:
            raise ValueError(f'User {user_id} not found.')

        self.first_name: str = self._db_obj['first_name']
        self.last_name: Union[str, None] = self._db_obj['last_name']
        self.user_id: int = self._db_obj['user_id']
        self.username: Union[str, None] = self._db_obj['username']
        self._state: str = self._db_obj['state']
        self._group: str = self._db_obj['group']
        self._favorite_groups: Union[List[str], None] = (
            self._db_obj['favorite_groups']
        )

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    def __str__(self):
        if self.username:
            details = f'[@{self.username}, {self.user_id}]'
        else:
            details = f'[{self.user_id}]'

        group = self.group

        return f"{self.full_name} {details} - {group}"

    @property
    def state(self):
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
        return self._favorite_groups

    @favorite_groups.setter
    def favorite_groups(self, new_fav: list[str]):
        self._favorite_groups = new_fav
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'favorite_groups': new_fav}}
        )


class DBWorker(DBInterface):
    def __new__(cls, host: str, db_name: str = 'heroku_38n7vrr9'):
        if not hasattr(cls, 'instance'):
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
            return db_schedule[weekday][weektype]

        return Schedule(**db_schedule)

    def groups(self, faculty: str, year: str) -> list[str]:
        """Функция получения списка групп по факультету и году поступления.

        Аргументы:
            faculty (str): факультет
            year (str): год поступления

        Возвращает:
            list[str]: список групп
        """
        groups = self._groups.find_one(
            {'faculty': faculty, 'year': year}
        )

        return groups['groups']

    @staticmethod
    def years() -> list[int]:
        """Функция получения актуальных годов поступления.

        Возвращает:
            list[int]: список актуальных годов поступления
        """
        # REVIEW: не работает с базой данных
        years = []
        dt = datetime.datetime.now()
        month = int(dt.strftime('%m'))
        year = int(dt.strftime('%y'))

        if month <= 5:
            # Учебный год ЕЩЁ не кончился
            for _ in range(4):
                year -= 1
                years.append(year)
        else:
            # Учебный год УЖЕ кончился или УЖЕ начался
            for _ in range(4):
                years.append(year)
                year -= 1

        return years
