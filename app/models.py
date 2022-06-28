from typing import List
from pydantic import BaseModel
from typing import Optional, Union, List
from datetime import datetime


class User(BaseModel):
    first_name: str
    last_name: Union[str, None]
    user_id: int
    username: Union[str, None]
    state: str
    group: str
    favorite_groups: Union[List[str], None]


#! Модели для представления расписания студентов


class Lesson(BaseModel):
    number: int
    subject: str
    room: str
    teacher: str


class Weekday(BaseModel):
    even: List[Lesson]
    odd: List[Lesson]


class Day(BaseModel):
    date_html: str
    lessons: List[Lesson]
    html: str


class Schedule(BaseModel):
    group: str
    last_updated: datetime
    monday: Weekday
    tuesday: Weekday
    wednesday: Weekday
    thursday: Weekday
    friday: Weekday
    saturday: Weekday
