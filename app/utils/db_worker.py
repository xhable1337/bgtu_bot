from datetime import datetime
from time import time
from typing import Union, List

from pymongo import MongoClient

from app.models import Schedule, User
from app.properties import MONGODB_URI


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
        self._teachers = database.teachers


class DBUser(DBInterface):
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
    
    @property
    def notification_time(self) -> dict[str, str]:
        return self._notification_time

    @notification_time.setter
    def notification_time(self, new_notification_time: dict[str, str]):
        self._favorite_groups = new_notification_time
        self._users.update_one(
            {'user_id': self.user_id},
            {'$set': {'notification_time': new_notification_time}}
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
    
    def add_user(self, user: User, replace: bool = True):
        """Функция добавления пользователя в базу данных.

        Аргументы:
            user (User): объект пользователя
            replace (bool): заменять ли имеющийся объект пользователя
        """
        db_user = self.user(user.user_id)
        if db_user:
            if replace:
                return self._users.replace_one({'user_id': user.user_id}, user.json())
        else:
            return self._users.insert_one(user.json())
        

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
    
    
    def add_schedule(self, schedule: Schedule, replace: bool = True):
        """Функция добавления расписания в базу данных.

        Аргументы:
            schedule (Schedule): объект расписания
            replace (bool): заменять ли имеющееся расписание
        """
        if self._schedule.find_one({'group': schedule.group}):
            if replace:
                return self._schedule.replace_one({'group': schedule.group}, schedule.json())
        else:
            return self._schedule.insert_one(schedule.json())


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
                return self._groups.replace_one({'faculty': faculty, 'year': year}, document)
        else:
            return self._groups.insert_one(document)
    
    
    def add_teacher(self, teacher: dict, replace: bool = True):
        """Функция добавления преподавателя в базу данных.

        Аргументы:
            teacher (dict): документ (object-like) преподавателя
            replace (bool): заменять ли имеющиеся объекты преподавателей

        TODO: Переделать под модели pydantic
        """
        name = teacher.get('name')
        if self._teachers.find_one({'name': name}):
            return self._teachers.replace_one({'name': name}, teacher)
        else:
            return self._teachers.insert_one(teacher)


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
        year = int(dt.strftime('%Y'))

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

    @staticmethod
    def faculties() -> list[str]:
        """Функция получения факультетов.
        
        Возвращает:
            list[int]: список факультетов
        """
        # REVIEW: не работает с базой данных
        faculties = [
            'Факультет информационных технологий',
            'Факультет энергетики и электроники',
            'Факультет отраслевой и цифровой экономики',
            'Учебно-научный технологический институт',
            'Механико-технологический факультет',
            'Учебно-научный институт транспорта'
        ]

        return faculties
