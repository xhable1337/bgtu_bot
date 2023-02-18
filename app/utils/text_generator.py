"""text_generator.py

    Этот модуль генерирует текст расписания пар и звонков.
"""
from typing import List

from prettytable import PrettyTable

from app.models import Lesson

wd_numbers = {
    'monday': 1,
    'tuesday': 2,
    'wednesday': 3,
    'thursday': 4,
    'friday': 5,
    'saturday': 6,
    'sunday': 7
}

wd_translate = {
    'monday': 'понедельник',
    'tuesday': 'вторник',
    'wednesday': 'среда',
    'thursday': 'четверг',
    'friday': 'пятница',
    'saturday': 'суббота',
    'sunday': 'воскресенье'
}

wd_name = {
    1: ('понедельник', 'monday'),
    2: ('вторник', 'tuesday'),
    3: ('среда', 'wednesday'),
    4: ('четверг', 'thursday'),
    5: ('пятница', 'friday'),
    6: ('суббота', 'saturday'),
    7: ('воскресенье', 'sunday'),
    8: ('понедельник', 'monday')
}

# Список звонков
rings_list = ['8:00-9:35', '9:45-11:20', '11:30-13:05',
              '13:20-14:55', '15:05-16:40', '16:50-18:25', '18:40-20:15', '20:25-22:00']


def schedule_text(
        schedule_type: str, isoweekday: int, group: str,
        weektype: str, schedule: List[Lesson]) -> str:
    """Функция генерации текста с расписанием.

    Аргументы:
        schedule_type (str): тип расписания (today/tomorrow/other)
        isoweekday (int): день недели по ISO календарю
        group (str): группа
        weekname (str): тип недели (even/odd | чёт/нечет)
        schedule (List[Lesson]): расписание на данный день

    Возвращает:
        str: текст с расписанием
    """
    # Определение типа расписания
    schedule_types = {
        'today': 'Сегодня',
        'tomorrow': 'Завтра',
        'other': 'Расписание'
    }
    schedule_type = schedule_types[schedule_type]

    # Если выбрано воскресенье, пар нет => завершаем функцию
    if isoweekday == 7:
        return (
            f'<b><u>Выбрана группа {group}</u></b>\n'
            f'<b>{schedule_type}:</b> воскресенье\n\n'
            f'Удачных выходных!'
        )

    # Текст расписания
    schedule_txt = ''

    # Определение типа недели (чёт/нечет)
    weektypes = {
        'even': 'чётная',
        'odd': 'нечётная'
    }
    weektype = weektypes[weektype]

    # Заполнение текста списком пар
    for lesson in schedule:
        if lesson.subject != '-':
            teacher_text = f'<b>Преподаватели:</b> {lesson.teacher}'

            if ',' in lesson.teacher:
                teacher_text = f'<b>Преподаватели:</b> {lesson.teacher}'
            else:
                teacher_text = f'<b>Преподаватель:</b> {lesson.teacher}'

            time = rings_list[lesson.number-1]
            lesson_type = lesson.subject.split(" ")[0]
            lesson_subject = lesson.subject.split(" ", maxsplit=1)[1]

            schedule_txt += (
                f'<u>Пара №{lesson.number} <i>({time})</i></u>\n'
                f'<code>{lesson_type}</code> <b>{lesson_subject}</b>\n'
                f'<b>Аудитория:</b> <code>{lesson.room}</code>\n'
                f'{teacher_text}\n\n'
            )

    text = (
        f'<b><u>Выбрана группа {group}</u></b>\n'
        f'<b>{schedule_type}:</b> {wd_name[isoweekday][0]}\n'
        f'<b>Неделя:</b> {weektype}\n\n'
        f'{schedule_txt}\n'
        '<code>[Л]</code> - <b>лекция</b>\n'
        '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
        '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
    )

    return text


def rings_table() -> str:
    """Функция генерации текста расписания звонков.

    Возвращает:
        str: таблица с расписанием звонков
    """
    table = PrettyTable()
    table.add_column(fieldname="№", column=[i for i in range(1, 8)])
    table.add_column(fieldname="Время", column=rings_list)
    text = f'Расписание пар\n\n<code>{table}</code>'
    return text
