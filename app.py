# School Diary Robot by xhable
# v6, added a parser for university schedule (BSTU)
# Now you must put your bot's token into config vars. (they're getting here by os.environ())

#from site_parser import get_state, set_state, get_group, set_group
from site_parser import api_get_groups, api_get_schedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.webhook import get_new_configured_app
from prettytable import PrettyTable
from telebot import types as teletypes
from flask import Flask, request
from pymongo import MongoClient
from transliterate import translit
from aiohttp import web
from concurrent.futures import ProcessPoolExecutor

import asyncio
import aiohttp
import telebot
import datetime
import wdays
import os
import re
import requests
import ast
import time


password = os.environ.get('password')
API_URL = 'https://bgtu-parser.herokuapp.com/'
MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI, retryWrites=False) 
db = client.heroku_38n7vrr9
schedule_db = db.schedule
groups_db = db.groups
users = db.users

# aiogram init
token = os.environ['token']
bot = Bot(token=token, parse_mode='MarkdownV2')
dp = Dispatcher(bot)

# webhook settings
WEBHOOK_HOST = 'https://dnevnikxhb.herokuapp.com'
WEBHOOK_PATH = f"/{token}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = os.getenv('PORT')


#bot = teleawait bot.TeleBot(token, 'Markdown')

UPDATE_TIME = int(os.environ.get('UPDATE_TIME'))

building_1 = 'https://telegra.ph/file/49ec8634ab340fa384787.png'
building_2 = 'https://telegra.ph/file/7d04458ac4230fd12f064.png'
building_3 = 'https://telegra.ph/file/6b801965b5771830b67f0.png'
building_4 = 'https://telegra.ph/file/f79c20324a0ba6cd88711.png'

server = Flask(__name__)
no = '-'
index = [i for i in range(1, 6)]

time_list = ['8:00-9:35', '9:45-11:20', '11:30-13:05', '13:20-14:55', '15:05-16:40']

ADMINS = [124361528, 436335947]

table = PrettyTable(border=False)
table.border = False
table.field_names = ['№', 'Пара', 'Кабинет']

table_r = PrettyTable()

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

def ru_en(text):
    """Функция транслитерации с русского на английский."""            
    return translit(text, 'ru', reversed=True)

def en_ru(text):
    """Функция транслитерации с английского на русский."""
    return translit(text, 'ru', reversed=False)

def get_schedule(group, weekday, weeknum):
    """Функция получения расписания от API."""
    if schedule_db.find_one({'group': group}) is None or time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
        if schedule_db.find_one({'group': group}) is None:
            schedule = api_get_schedule(group, weekday, weeknum)
            schedule_db.insert_one(schedule)
            return schedule[weekday][f'{weeknum}']

        elif time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
            schedule = api_get_schedule(group, weekday, weeknum)
            if schedule != None:
                schedule_db.update_one({'group': group}, {'$set': schedule})
                return schedule[weekday][f'{weeknum}']
            else:
                schedule_db.find_one({'group': group})[weekday][f'{weeknum}']
    else:
        return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']

def get_groups(faculty='Факультет информационных технологий', year='20', force_update=False):
    """Функция получения расписания от API."""
    if groups_db.find_one({"faculty": faculty}) is None:
        group_list = api_get_groups(faculty, year)
        print(group_list)
        groups_db.insert_one({'faculty': faculty, 'year': year, 'groups': group_list, 'last_updated': time.time()})
        return group_list['groups']
    else:
        if force_update == True:
            group_list = api_get_groups(faculty, year)
            if group_list != None:
                groups_db.update_one({'faculty': f'faculty_{faculty}', 'year': year}, {'$set': {'groups': group_list, 'last_updated': time.time()}})
                return group_list['groups']
            else:
                return groups_db.find_one({'faculty': faculty, 'year': year})['groups']
        else:
            return groups_db.find_one({'faculty': faculty, 'year': year})['groups']
    #if schedule_db.find_one({'group': group}) is None or time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
    #    schedule = api_get_groups(faculty, year, force_update)
    #else:
    #    return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']

def get_faculties():
    """Возвращает список факультетов из БД."""
    faculties = []
    for item in groups_db.find({}):
        faculties.append(item['faculty'])
    return faculties    


@dp.message_handler(commands=["start"])
async def start_handler(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        users.insert_one({
            'first_name': m.from_user.first_name,
            'last_name': m.from_user.last_name,
            'user_id': m.from_user.id,
            'username': m.from_user.username,
            'state': 'default',
            'group': 'О-20-ИВТ-1-по-Б'
        })

        faculty_list = get_faculties()
        kb_faculty = types.InlineKeyboardMarkup()
        for faculty in faculty_list:
            kb_faculty.row(types.InlineKeyboardButton(text=faculty, callback_data=ru_en('f_' + faculty)))

        await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Для начала работы с ботом выбери свою группу \\(впоследствии выбор можно изменить\\):*', reply_markup=kb_faculty, parse_mode='Markdown')
    else:
        user = users.find_one({'user_id': m.from_user.id})
        if user.get('favorite_groups') == None:
            users.update_one({'user_id': m.from_user.id}, {'$set': {'favorite_groups': []}})
        elif user.get('first_name') != m.from_user.first_name:
            users.update_one({'first_name': m.from_user.first_name}, {'$set': {'first_name': m.from_user.first_name}})
        elif user.get('last_name') != m.from_user.last_name:
            users.update_one({'last_name': m.from_user.last_name}, {'$set': {'last_name': m.from_user.last_name}})
        elif user.get('username') != m.from_user.username:
            users.update_one({'username': m.from_user.username}, {'$set': {'username': m.from_user.username}})
        group = get_group(m.from_user.id)
        await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Выбранная группа: {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        set_state(m.from_user.id, 'default')

@dp.message_handler(commands=['whatis'])
async def whatis(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        key = raw_text.split(' ', maxsplit=1)[1]
        try:
            value = globals()[f'{key}']
            await bot.send_message(m.chat.id, f'Сейчас `{key}` == `{value}`', parse_mode='Markdown')
        except KeyError:
            await bot.send_message(m.chat.id, f'Переменная `{key}` не найдена!', parse_mode='Markdown')

@dp.message_handler(commands=['users_reset'])
async def users_reset(m):
    if m.chat.id in ADMINS:
        for user in users.find():
            user_id = user['user_id']
            state = 'default'
            group = 'О-20-ИВТ-1-по-Б'
            set_state(user_id, state)
            set_group(user_id, group)
        await bot.send_message(m.chat.id, f'Параметры пользователей сброшены!\n\nСостояние = {state}\nГруппа = {group}')

@dp.message_handler(commands=['users'])
async def users_handler(m):
    if m.chat.id in ADMINS:
        text = '*Список пользователей бота:*\n\n'
        for user in users.find():
            first_name = user['first_name']
            last_name = user['last_name']
            user_id = user['user_id']
            group = user['group']
            first_name.replace('_', '\\_')
            last_name.replace('_', '\\_')
            if last_name != None:
                
                text += f'[{first_name} {last_name}](tg://user?id={user_id}) ◼ *Группа {group}*\n'
            else:
                text += f'[{first_name}](tg://user?id={user_id}) ◼ *Группа {group}*\n'

        count = users.count_documents({})
        text = f"Всего пользователей: {count}\n\n" + text
        
        if len(text) > 4096:
            for x in range(0, len(text), 4096):
                await bot.send_message(m.chat.id, text[x:x+4096], parse_mode='Markdown')
        else:
            await bot.send_message(m.chat.id, text, parse_mode='Markdown')

@dp.message_handler(commands=['broadcast'])
async def broadcast(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        group = raw_text.split(' ', maxsplit=2)[1]
        text = raw_text.split(' ', maxsplit=2)[2]
        i = 0
        if group == 'all':
            text = f'🔔 *Сообщение для всех групп!*\n' + text
            for user in users.find():
                if i == 25:
                    time.sleep(1)
                user_id = user['user_id']
                try:
                    await bot.send_message(user_id, text, parse_mode='Markdown')
                    i += 1
                except:
                    pass
                #except bot.apihelper.ApiTelegramException:
                #    pass
        elif group == 'test':
            text = f'🔔 *Тестовое сообщение!*\n' + text
            await bot.send_message(m.chat.id, text, parse_mode='Markdown')
        else:
            text = f'🔔 *Сообщение для группы {group}!*\n' + text
            for user in users.find({'group': group}):
                if i == 25:
                    time.sleep(1)
                user_id = user['user_id']
                try:
                    await bot.send_message(user_id, text, parse_mode='Markdown')
                    i += 1
                except:
                    pass
                #except Exceptions.TelegramAPIError:
                #    pass

@dp.message_handler(commands=['exec'])
async def execute(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        cmd = raw_text.split(' ', maxsplit=1)[1]
        try:
            exec(cmd)
            await bot.send_message(m.chat.id, f'{cmd} - успешно выполнено!')
        except Exception as e:
            await bot.send_message(m.chat.id, f'Произошла ошибка!\n\n`{e}`')

# Блок создания клавиатур для бота
kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(text='📅 Расписание по дням', callback_data='days'))
kbm.row(types.InlineKeyboardButton(text='⚡️ Сегодня', callback_data='today'), types.InlineKeyboardButton(text='⚡️ Завтра', callback_data='tomorrow'))
kbm.row(types.InlineKeyboardButton(text='🔔 Расписание пар', callback_data='rings'))
kbm.row(types.InlineKeyboardButton(text='🏠 Найти корпус по аудитории', callback_data='building'))
kbm.row(types.InlineKeyboardButton(text='🔂 Сменить факультет/группу', callback_data='change_faculty'))
kbm.row(types.InlineKeyboardButton(text='⭐ Избранные группы', callback_data='favorite_groups'))

kb_r = types.InlineKeyboardMarkup()
kb_r.row(types.InlineKeyboardButton(text='Понедельник', callback_data='r_monday'))
kb_r.row(types.InlineKeyboardButton(text='Остальные дни', callback_data='r_others'))
kb_r.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))



kbb = types.InlineKeyboardMarkup()
kbb.row(types.InlineKeyboardButton(text='↩️ Назад', callback_data='days'))

kbbb = types.InlineKeyboardMarkup()
kbbb.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))

kb_cancel_building = types.InlineKeyboardMarkup()
kb_cancel_building.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))

#kb_group = types.InlineKeyboardMarkup()
#kb_group.row(types.InlineKeyboardButton(text='1️⃣', callback_data='group_1'), types.InlineKeyboardButton(text='2️⃣', callback_data='group_2'))
#kb_group.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))

# Хэндлер для текста
@dp.message_handler(content_types=["text", "sticker", "photo", "audio", "video", "voice", "video_note", "document", "animation"])
async def anymess(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        await bot.send_message(m.chat.id, 'Для начала работы с ботом выполните команду /start')
    elif users.find_one({'user_id': m.from_user.id}) != None and get_state(m.from_user.id) == 'default':
        group = get_group(m.from_user.id)
        await bot.send_message(m.chat.id, text=f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
    elif get_state(m.from_user.id) == 'find_class':
        if re.match(r'(\b[1-9][1-9]\b|\b[1-9]\b)', m.text):
            await bot.send_photo(m.chat.id, photo=building_1, caption=f'Аудитория {m.text} находится в корпусе №1 _\\(Институтская, 16\\)_.', parse_mode='Markdown')
            await bot.send_location(m.chat.id, latitude=53.305077, longitude=34.305080)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'\b[1-9][0-9][0-9]\b', m.text):
            await bot.send_photo(m.chat.id, photo=building_2, caption=f'Аудитория {m.text} находится в корпусе №2 _\\(бульвар 50 лет Октября, 7\\)_.', parse_mode='Markdown')
            await bot.send_location(m.chat.id, latitude=53.304442, longitude=34.303849)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)', m.text):
            await bot.send_photo(m.chat.id, photo=building_3, caption=f'Аудитория {m.text} находится в корпусе №3 _\\(Харьковская, 8\\)_.', parse_mode='Markdown')
            await bot.send_location(m.chat.id, latitude=53.304991, longitude=34.306688)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'\bБ\d{3}\b', m.text):
            await bot.send_photo(m.chat.id, photo=building_4, caption=f'Аудитория {m.text} находится в корпусе №4 _\\(Харьковская, 10Б\\)_.', parse_mode='Markdown')
            await bot.send_location(m.chat.id, latitude=53.303513, longitude=34.305085)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        else:
            await bot.send_message(m.chat.id, 'Данный номер аудитории некорректен. Повторите попытку или отмените действие:', reply_markup=kb_cancel_building)
    elif get_group(m.from_user.id) != 1 and get_group(m.from_user.id) != 2:
        set_group(m.from_user.id, 1)

# Хэндлер обработки действий кнопок
@dp.callback_query_handler()
async def button_func(call):
    if call.data == 'days':
        await bot.answer_callback_query(call.id)
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            weekname = '[Н] \\- нечётная'
            buttons = ['[Н]', 'Ч']
        else:
            weekname = '[Ч] \\- чётная'
            buttons = ['Н', '[Ч]']

        kb_dn = types.InlineKeyboardMarkup()
        kb_dn.row(
            types.InlineKeyboardButton(text=buttons[0], callback_data='week_1'),
            types.InlineKeyboardButton(text='Пн', callback_data='wday_monday_1'),
            types.InlineKeyboardButton(text='Вт', callback_data='wday_tuesday_1'),
            types.InlineKeyboardButton(text='Ср', callback_data='wday_wednesday_1'),
            types.InlineKeyboardButton(text='Чт', callback_data='wday_thursday_1'),
            types.InlineKeyboardButton(text='Пт', callback_data='wday_friday_1'))
        kb_dn.row(
            types.InlineKeyboardButton(text=buttons[1], callback_data='week_2'),
            types.InlineKeyboardButton(text='Пн', callback_data='wday_monday_2'),
            types.InlineKeyboardButton(text='Вт', callback_data='wday_tuesday_2'),
            types.InlineKeyboardButton(text='Ср', callback_data='wday_wednesday_2'),
            types.InlineKeyboardButton(text='Чт', callback_data='wday_thursday_2'),
            types.InlineKeyboardButton(text='Пт', callback_data='wday_friday_2'))
        kb_dn.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))

        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите неделю и день \\(сейчас идёт {weekname}\\):\n',
        reply_markup=kb_dn)
    elif call.data[:5] == 'wday_':
        await bot.answer_callback_query(call.id)
        table = PrettyTable(border=False)
        table.field_names = ['№', 'Пара', 'Кабинет']
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday()
        weeknum = str(call.data)[-1]
        weekday = call.data[5:-2]
        
        schedule = get_schedule(group, weekday, weeknum)

        if weeknum == '1':
            weekname = 'нечётная'
        elif weeknum == '2':
            weekname = 'чётная'

        for lesson in schedule:
            table.add_row(lesson)
        
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'*Выбрана группа {group}*\nРасписание: {wdays.translate(weekday)}\nНеделя: {weekname}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*',
        reply_markup=kbb, parse_mode='Markdown')
    elif call.data == 'today':
        await bot.answer_callback_query(call.id)
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday()
        if isoweekday == 6 or isoweekday == 7:
            text = f'*Выбрана группа {group}*\nСегодня: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        else:
            table = PrettyTable(border=False)
            table.field_names = ['№', 'Пара', 'Кабинет']
            group = get_group(call.from_user.id)
            isoweekday = datetime.datetime.today().isoweekday()
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                weeknum = '1'
            else:
                weeknum = '2'

            schedule = get_schedule(group, weekday, weeknum)

            for lesson in schedule:
                table.add_row(lesson)
            text = f'*Выбрана группа {group}*\nСегодня: {wdays.names(isoweekday)[0]}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*'

        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text, reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'rings':
        await bot.answer_callback_query(call.id)
        table_r.clear()
        table_r.add_column(fieldname="№", column=index)
        table_r.add_column(fieldname="Время", column=time_list)
        text = f'Расписание пар\n\n```{table_r}```'
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomorrow':
        await bot.answer_callback_query(call.id)
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday() + 1
        if isoweekday == 6 or isoweekday == 7:
            text = f'*Выбрана группа {group}*\nЗавтра: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        elif isoweekday == 8:
            table = PrettyTable(border=False)
            table.field_names = ['№', 'Пара', 'Кабинет']
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 != 0:
                weeknum = '1'
            else:
                weeknum = '2'

            schedule = get_schedule(group, weekday, weeknum)

            for lesson in schedule:
                table.add_row(lesson)
            text = f'*Выбрана группа {group}*\nЗавтра: {wdays.names(isoweekday)[0]}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*'
        else:
            table = PrettyTable(border=False)
            table.field_names = ['№', 'Пара', 'Кабинет']
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                weeknum = '1'
            else:
                weeknum = '2'

            schedule = get_schedule(group, weekday, weeknum)

            print(f'369. schedule = {schedule}')
            for lesson in schedule:
                print(f'371. lesson = {lesson}')
                table.add_row(lesson)
            text = f'*Выбрана группа {group}*\nЗавтра: {wdays.names(isoweekday)[0]}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*'

        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomain':
        await bot.answer_callback_query(call.id, text='Возврат в главное меню...')
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа {get_group(call.from_user.id)}.*\nВот главное меню:',
        reply_markup=kbm, parse_mode='Markdown')
    elif call.data == 'building':
        await bot.answer_callback_query(call.id)
        set_state(call.from_user.id, 'find_class')
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отправьте номер аудитории:', reply_markup=kb_cancel_building, parse_mode='Markdown')
    elif call.data == 'cancel_find_class':
        await bot.answer_callback_query(call.id)
        set_state(call.from_user.id, 'default')
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа {get_group(call.from_user.id)}.*\nВот главное меню:',
        reply_markup=kbm, parse_mode='Markdown')
    elif call.data == 'change_faculty':
        await bot.answer_callback_query(call.id)
        faculty_list = get_faculties()
        kb_faculty = types.InlineKeyboardMarkup()

        for faculty in faculty_list:
            callback_faculty = str('f_' + faculty).replace(' ', '_')
            kb_faculty.row(types.InlineKeyboardButton(text=faculty, callback_data=ru_en(callback_faculty)))

        kb_faculty.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите факультет:',
        reply_markup=kb_faculty, parse_mode='Markdown')
    elif str(call.data).startswith('f_'):
        await bot.answer_callback_query(call.id)
        in_faculty = str(call.data[2:])
        in_faculty = en_ru(in_faculty).capitalize()
        faculty = in_faculty.replace('_', ' ')
        
        if 'економики' in faculty:
            faculty = 'Факультет отраслевой и цифровой экономики'
        elif 'електроники' in faculty:
            faculty = 'Факультет энергетики и электроники'
            
        print(faculty)
        group_list = get_groups(faculty=faculty)
        kb_group = types.InlineKeyboardMarkup()

        for group in group_list:
            kb_group.row(types.InlineKeyboardButton(text=group, callback_data=group))

        kb_group.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите группу:',
        reply_markup=kb_group, parse_mode='Markdown')
    elif call.data == 'change_group':
        await bot.answer_callback_query(call.id)
        group_list = get_groups()
        kb_group = types.InlineKeyboardMarkup()

        for group in group_list:
            kb_group.row(types.InlineKeyboardButton(text=group, callback_data=group))

        kb_group.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите группу:',
        reply_markup=kb_group, parse_mode='Markdown')
    elif call.data == 'favorite_groups':
        await bot.answer_callback_query(call.id)
        kb_favorite = types.InlineKeyboardMarkup()
        user = users.find_one({'user_id': call.from_user.id})
        i = 0
        if user.get('favorite_groups') is not None:
            for group in user.get('favorite_groups'):
                kb_favorite.row(
                    types.InlineKeyboardButton(text=group, callback_data=group),
                    types.InlineKeyboardButton(text='❌', callback_data=f'{group}__del')
                )
                i += 1
            space_left = 5 - i
            for i in range(space_left):
                kb_favorite.row(types.InlineKeyboardButton(text='➕ Добавить', callback_data='add_favorite'))
        else:
            users.update_one({"user_id": call.from_user.id}, {"$set": {"favorite_groups": []}})
            for i in range(5):
                kb_favorite.row(
                    types.InlineKeyboardButton(text='➕ Добавить', callback_data='add_favorite')
                )
        kb_favorite.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Твой список избранных групп:', reply_markup=kb_favorite)
        
    elif str(call.data).startswith('О-20'):
        await bot.answer_callback_query(call.id)
        if str(call.data).endswith('__del'):
            user = users.find_one({'user_id': call.from_user.id})
            favorite_groups = user.get('favorite_groups')
            group = str(call.data).split('__')[0]
            favorite_groups.pop(favorite_groups.index(group))
            users.update_one({'user_id': call.from_user.id}, {'$set': {'favorite_groups': favorite_groups}})
            await bot.edit_message_text(chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Группа {group} удалена из избранных!\n*Сейчас выбрана группа {get_group(call.from_user.id)}.*\nВот главное меню:',
            reply_markup=kbm, parse_mode='Markdown')
            set_state(call.from_user.id, 'default')
        else:
            if get_state(call.from_user.id) == 'default':
                group = str(call.data)
                set_group(call.from_user.id, group)
                await bot.edit_message_text(chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа {get_group(call.from_user.id)}.*\nВот главное меню:',
                reply_markup=kbm, parse_mode='Markdown')
            elif get_state(call.from_user.id) == 'add_favorite':
                user = users.find_one({'user_id': call.from_user.id})
                favorite_groups = user.get('favorite_groups')
                favorite_groups.append(call.data)
                users.update_one({'user_id': call.from_user.id}, {'$set': {'favorite_groups': favorite_groups}})
                await bot.edit_message_text(chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Группа {call.data} добавлена в избранные!\n*Сейчас выбрана группа {get_group(call.from_user.id)}.*\nВот главное меню:',
                reply_markup=kbm, parse_mode='Markdown')
                set_state(call.from_user.id, 'default')
    
    elif call.data == 'add_favorite':
        await bot.answer_callback_query(call.id)
        set_state(call.from_user.id, 'add_favorite')
        faculty_list = get_faculties()
        kb_faculty = types.InlineKeyboardMarkup()

        for faculty in faculty_list:
            callback_faculty = str('f_' + faculty).replace(' ', '_')
            kb_faculty.row(types.InlineKeyboardButton(text=faculty, callback_data=ru_en(callback_faculty)))

        kb_faculty.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите факультет:',
        reply_markup=kb_faculty, parse_mode='Markdown')

## Установка Webhook для быстрого взаимодействия с ботом
#async def on_startup(dp):
#    await bot.delete_webhook()
#    await bot.set_webhook(url=WEBHOOK_URL)



#@server.route('/' + token, methods=['POST'])
#def getMessage():
#    await bot.process_new_updates([teletypes.Update.de_json(request.stream.read().decode("utf-8"))])
#    return "!", 200


#@server.route("/wh")
#def webhook():
#    #await bot.delete_webhook()
#    #await bot.set_webhook(url=WEBHOOK_URL)
#    return "!", 200

async def test_print():
    while 1:
        print("hello world")
        await asyncio.sleep(60)

async def startserver():
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
    web.run_app(app, host='0.0.0.0', port=os.getenv('PORT'))

async def startbot():
    while 1:
        executor.start_polling(dp, skip_updates=True)
        break
    #start_webhook(
    #    dispatcher=dp,
    #    webhook_path=WEBHOOK_PATH,
    #    on_startup=on_startup,
    #    skip_updates=True,
    #    host=WEBAPP_HOST,
    #    port=WEBAPP_PORT,
    #)

if __name__ == "__main__":
    executor_ = ProcessPoolExecutor(4)
    loop = asyncio.get_event_loop()
    print('hello from main')
    
    t_ = asyncio.ensure_future(test_print())
    print('test print')

    startbot_ = asyncio.ensure_future(loop.run_in_executor(executor_, startbot))
    print('startbot worked')
    #loop.run_forever()
    #executor.start_polling(dp, skip_updates=True)
#    executor_ = ProcessPoolExecutor(4)
#    loop = asyncio.get_event_loop()
#    startbot_ = asyncio.ensure_future(startbot())
#    startserver_ = asyncio.ensure_future(startserver())

    #server.run(host="0.0.0.0", port=int(os.environ.get('PORT', '8443')))
    


    #app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
    #app.on_startup.append(on_startup)
    #dp.loop.set_task_factory(dp.get_current())
    #web.run_app(app, host='0.0.0.0', port=os.getenv('PORT'))  # Heroku stores port you have to listen in your app