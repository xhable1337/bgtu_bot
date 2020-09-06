r"""Парсер сайта БГТУ и базы данных бота, который позволяет получать различную информацию.

Возможности:

• `get_schedule(group, weekday, weeknum)` - получить список с расписанием для заданной группы, дня недели и номера недели.

• `get_groups(faculty, year, force_update)` - получить список групп по заданным факультету и году.

• `get_state(user_id)` - получить состояние по `user_id`.

• `set_state(user_id, state)` - установить состояние `state` по `user_id`.

• `get_group(user_id)` - получить группу по `user_id`.

• `set_group(user_id, group)` - установить группу `group` по `user_id`.
"""


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from prettytable import PrettyTable
from pymongo import MongoClient
import time 
import re
import datetime
import os

#CHROME_BIN = os.environ['GOOGLE_CHROME_SHIM']
#CHROMEDRIVER_PATH = 'chromedriver'
#
#chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument('--headless')
#chrome_options.add_argument('--disable-infobars')
#chrome_options.add_argument('--disable-dev-shm-usage')
#chrome_options.add_argument('--disable-browser-side-navigation')
#chrome_options.add_argument('--disable-gpu')
#chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36")
#chrome_options.binary_location = CHROME_BIN
#PHANTOMJS_PATH = os.environ['PROFILE_PATH']

MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI, retryWrites=False) 
db = client.heroku_38n7vrr9
#users = db.users
schedule_db = db.schedule
groups_db = db.groups
users = db.users

def get_state(user_id):
    """Позволяет просмотреть state по user_id."""
    return users.find_one({'user_id': user_id})['state']

def set_state(user_id, state):
    """Позволяет изменить state по user_id."""
    users.update_one({'user_id': user_id}, {'$set': {'state': state}})

def get_group(user_id):
    """Позволяет просмотреть номер группы по user_id."""
    return users.find_one({'user_id': user_id})['group']

def set_group(user_id, group):
    """Позволяет изменить номер группы по user_id."""
    users.update_one({'user_id': user_id}, {'$set': {'group': group}})

def get_groups(faculty='Факультет информационных технологий', year='20', force_update=False):
    """Получает список групп по заданному факультету с сайта БГТУ, помещает в базу данных и выводит как результат функции.

    На входе:

    • `faculty` [str] - полное название факультета.

    • `year` [str] - год поступления группы.

    • `force_update` [bool] - принудительно обновить список групп в базе.

    На выходе:
    
    • `list` всех групп данного факультета и года поступления.
    """
    if groups_db.find_one() is None:
        year = str(year)
        #driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
        driver = webdriver.PhantomJS()
        #driver = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
        #driver = webdriver.Chrome(executable_path='chromedriver.exe')
        url = 'https://www.tu-bryansk.ru/education/schedule/'
        driver.get(url)
        select_faculty = Select(driver.find_element_by_xpath('//*[@id="faculty"]'))
        select_faculty.select_by_value(faculty)
        time.sleep(0.5)
        select_group = Select(driver.find_element_by_xpath('//*[@id="group"]'))
        options = select_group.options
        options_by_year = []

        for option in options:
                options[options.index(option)] = option.text

        for option in options:
            if option.startswith(f'О-{year}') and option.endswith('Б'):
                options_by_year.append(option)

        groups_db.insert_one({'faculty': faculty, 'year': year, 'groups': options_by_year, 'last_updated': time.time()})

        #driver.quit()

        return options_by_year
    else:
        if force_update == True:
            year = str(year)
            #driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
            driver = webdriver.PhantomJS()
            #driver = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
            #driver = webdriver.Chrome(executable_path='chromedriver.exe')
            url = 'https://www.tu-bryansk.ru/education/schedule/'
            driver.get(url)
            select_faculty = Select(driver.find_element_by_xpath('//*[@id="faculty"]'))
            select_faculty.select_by_value(faculty)
            time.sleep(0.5)
            select_group = Select(driver.find_element_by_xpath('//*[@id="group"]'))
            options = select_group.options
            options_by_year = []

            for option in options:
                    options[options.index(option)] = option.text

            for option in options:
                if option.startswith(f'О-{year}'):
                    options_by_year.append(option)

            groups_db.update_one({'faculty': faculty, 'year': year}, {'$set': {'groups': options_by_year, 'last_updated': time.time()}})

            #driver.quit()

            return options_by_year
        else:
            return groups_db.find_one({'faculty': faculty, 'year': year})['groups']


def get_schedule(group, weekday, weeknum):
    """Получает расписание с сайта БГТУ и помещает в базу данных.

    Если расписание обновлялось более суток назад/не существует в БД - оно автоматически обновится/добавится. 

    На входе: 
    
    • `group` [str] - группа, для которой нужно получить расписание

    • `weekday` [str] - английское название дня недели, для которого нужно получить расписание

    • `weeknum` [int] - тип недели. 1 - нечётная, 2 - чётная.

    На выходе:

    • `list` с расписанием на выбранный день.
    """
    if schedule_db.find_one({'group': group}) is None or time.time() - schedule_db.find_one({'group': group})['last_updated'] > 86400:
        no = '-'
        days = {'Понедельник': 'monday', 'Вторник': 'tuesday', 'Среда': 'wednesday', 'Четверг': 'thursday', 'Пятница': 'friday'}
        lesson_times = {'08:00 - 09:35': 1, '09:45 - 11:20': 2, '11:30 - 13:05': 3, '13:20 - 14:55': 4, '15:05 - 16:40': 5}
        schedule = {
        'group': group,
        'last_updated': time.time(),
        'monday': {'1': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]], '2': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]]},
        'tuesday': {'1': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]], '2': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]]},
        'wednesday': {'1': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]], '2': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]]},
        'thursday': {'1': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]], '2': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]]},
        'friday': {'1': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]], '2': [[1, no, no], [2, no, no], [3, no, no], [4, no, no], [5, no, no]]}
        }
        subject_short = {
            'Физическая культура и спорт': 'Физ-ра',
            'Программирование': 'Програм.',
            'Педагогика и психология': 'Пед. и псих.',
            'Информатика': 'Информат.',
            'Алгебра и геометрия': 'Алг. и геом.',
            'Иностранный язык': 'Ин.яз.',
            'Дискретная математика': 'Дискр.мат.',
            'Эконимическая теория': 'Экон.теория',
            'Экономическая теория': 'Экон.теория',
            'Алгоритмические языки': 'Алг.языки',
            'Языки программирования': 'Языки прогр.',
            'Начертательная геометрия': 'Начерт.геом.'

        }

        #driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
        driver = webdriver.PhantomJS()
        #driver = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)
        #driver = webdriver.Chrome(executable_path='chromedriver.exe')
        url = 'https://www.tu-bryansk.ru/education/schedule/'
        driver.get(url)
        select_group = Select(driver.find_element_by_xpath('//*[@id="group"]'))
        select_group.select_by_value(group)

        time.sleep(0.5)
        td = driver.find_elements_by_tag_name('td')
        iter_index = -1

        for i in td:
            td[td.index(i)] = i.text

        for i in td:
            iter_index += 1
            if i in days:
                it = 0
                day = days[i]
                subject, room = '', ''

            if re.match(r'\b\d\d:\d\d - \d\d:\d\d\b', i):
                it = 0
                index = lesson_times[i] - 1

            if '\n' in i:
                subject_type = i.split('\n')[1]
                subject = i.split('\n')[0]

                if subject in subject_short:
                    subject = subject_short[subject]

                if subject_type == 'практическое занятие':
                    subject = f"[ПЗ] {subject}"
                elif subject_type == 'лекция':
                    subject = f"[Л] {subject}"
                elif subject_type == 'лабораторное занятие':
                    subject = f"[ЛАБ] {subject}"

            if str(i).startswith('ауд. ') or str(i) == 'спортзал':
                room = str(i)
                if str(i).startswith('ауд. '):
                    room = room[5:]

                try:
                    if re.match(r'\b\d\d:\d\d - \d\d:\d\d\b', td[iter_index + 1]) or td[iter_index + 1] in days or i == td[-1]:
                        if it == 0:
                            schedule[day]['1'][index][1], schedule[day]['1'][index][2] = subject, room
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                        else:
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                            it = 0
                    elif td[iter_index + 1] == '':
                        if it == 0:
                            schedule[day]['1'][index][1], schedule[day]['1'][index][2] = subject, room
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                        else:
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                            it = 0
                    else:
                        schedule[day]['1'][index][1], schedule[day]['1'][index][2] = subject, room
                        subject, room = '', ''
                        it += 1
                except IndexError:
                    if i == td[-1]:
                        if it == 0:
                            schedule[day]['1'][index][1], schedule[day]['1'][index][2] = subject, room
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                        else:
                            schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                            subject, room = '', ''
                            it = 0

            if i == '':    
                td[iter_index], td[iter_index + 1], td[iter_index + 2] = no, 'Nobody N. O.', no
                if re.match(r'\b\d\d:\d\d - \d\d:\d\d\b', td[iter_index - 1]):
                    subject, room = no, no
                    schedule[day]['1'][index][1], schedule[day]['1'][index][2] = subject, room
                    subject, room = '', ''
                    it += 1
                elif str(td[iter_index - 1]).startswith('ауд. ') or str(td[iter_index - 1]) == 'спортзал':
                    subject, room = no, no
                    schedule[day]['2'][index][1], schedule[day]['2'][index][2] = subject, room
                    subject, room = '', ''
                    it = 0

        iter_index = 0

        schedule['last_updated'] = time.time()

        if schedule_db.find_one({'group': group}) is None:
            schedule_db.insert_one(schedule)
            return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']

        elif time.time() - schedule_db.find_one({'group': group})['last_updated'] > 86400:
            schedule_db.update_one({'group': group}, {'$set': schedule})
            return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']

        #driver.quit()

    else:
        return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']


# How to use

# 1. Get schedule list by group, weekday and weeknum
# schedule = get_schedule('О-20-ИВТ-1-по-Б', 'friday', 2)

# ---- Packing it in prettytable
# for i in schedule:
#     table.add_row(i)
# print(table)

# 2. Get groups list by faculty name
# print(get_groups())