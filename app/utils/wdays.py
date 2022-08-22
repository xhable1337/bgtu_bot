"""app/utils/wdays.py

    Этот модуль занимается работой с днями недель:
    перевод, получение isoweekday, получение названия
    по isoweekday.

"""


def numbers(name: str) -> int:
    """Находит isoweekday для заданного дня недели.

    Аргументы:
        name (str): английское имя дня недели

    Возвращает:
        int: isoweekday этого дня недели
    """
    if name == 'monday':
        num = 1
    elif name == 'tuesday':
        num = 2
    elif name == 'wednesday':
        num = 3
    elif name == 'thursday':
        num = 4
    elif name == 'friday':
        num = 5
    elif name == 'saturday':
        num = 6
    elif name == 'sunday':
        num = 7
    return num


def translate(name: str) -> str:
    """Переводит день недели с английского на русский язык.

    Аргументы:
        name (str): день недели на английском языке

    Возвращает:
        str: день недели на русском языке
    """
    if name == 'monday':
        newname = 'понедельник'
    elif name == 'tuesday':
        newname = 'вторник'
    elif name == 'wednesday':
        newname = 'среда'
    elif name == 'thursday':
        newname = 'четверг'
    elif name == 'friday':
        newname = 'пятница'
    elif name == 'saturday':
        newname = 'суббота'
    elif name == 'sunday':
        newname = 'воскресенье'
    return newname


def names(isoweekday: int) -> tuple[str, str]:
    """Находит русское и английское названия дня недели по isoweekday.

    Аргументы:
        isoweekday (int): номер дня недели (1-7, 8)

    Возвращает:
        tuple[str, str]: кортеж вида ('понедельник', 'monday')
    """
    if isoweekday == 1:
        wdr = 'понедельник'
        wde = 'monday'
    elif isoweekday == 2:
        wdr = 'вторник'
        wde = 'tuesday'
    elif isoweekday == 3:
        wdr = 'среда'
        wde = 'wednesday'
    elif isoweekday == 4:
        wdr = 'четверг'
        wde = 'thursday'
    elif isoweekday == 5:
        wdr = 'пятница'
        wde = 'friday'
    elif isoweekday == 6:
        wdr = 'суббота'
        wde = 'saturday'
    elif isoweekday == 7:
        wdr = 'воскресенье'
        wde = 'sunday'
    elif isoweekday == 8:
        wdr = 'понедельник'
        wde = 'monday'
    return wdr, wde
