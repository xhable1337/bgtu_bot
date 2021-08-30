# School Diary Robot by xhable
# v6, added a parser for university schedule (BSTU)
# Now you must put your bot's token into config vars. (they're getting here by os.environ())

#from site_parser import get_state, set_state, get_group, set_group
from site_parser import api_get_groups, api_get_schedule
from keyboards import kbm, kbb, kbbb, kb_cancel_building, kb_notifications, kb_notifications_days, days_keyboard, kb_admin, kb_admin_back
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.webhook import get_new_configured_app
from prettytable import PrettyTable
from flask import Flask, request
from pymongo import MongoClient
from transliterate import translit
from aiohttp import web
from concurrent.futures import ProcessPoolExecutor
from math import ceil

import asyncio
import aiohttp
import datetime
import wdays
import os
import re
import requests
import ast
import time


password = os.environ.get('password')
API_URL = os.environ.get('PARSER_URL')
MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI, retryWrites=False) 
db = client.heroku_38n7vrr9
schedule_db = db.schedule
groups_db = db.groups
users = db.users
scheduled_msg = db.scheduled_messages


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


#bot = telebot.TeleBot(token, 'Markdown')

UPDATE_TIME = int(os.environ.get('UPDATE_TIME'))

building_1 = 'https://telegra.ph/file/49ec8634ab340fa384787.png'
building_2 = 'https://telegra.ph/file/7d04458ac4230fd12f064.png'
building_3 = 'https://telegra.ph/file/6b801965b5771830b67f0.png'
building_4 = 'https://telegra.ph/file/f79c20324a0ba6cd88711.png'

server = Flask(__name__)
no = '-'
index = [i for i in range(1, 6)]

rings_list = ['8:00-9:35', '9:45-11:20', '11:30-13:05', '13:20-14:55', '15:05-16:40']

ADMINS = [124361528, 436335947, 465503110]

table = PrettyTable(border=False)
table.border = False
table.field_names = ['№', 'Пара', 'Кабинет']

table_r = PrettyTable()

last_msgid = 0

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

def get_weekname():
    """Функция получения чётности/нечётности недели."""
    if datetime.datetime.today().isocalendar()[1] % 2 == 0:
        weekname = 'нечётная'
    else:
        weekname = 'чётная'
    return weekname

def get_schedule(group, weekday, weeknum):
    """Функция получения расписания от API."""
    if schedule_db.find_one({'group': group}) is None or time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
        if schedule_db.find_one({'group': group}) is None:
            schedule = api_get_schedule(group)
            schedule_db.insert_one(schedule)
            return schedule[weekday][f'{weeknum}']

        elif time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
            schedule = api_get_schedule(group)
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
        return group_list
    else:
        if force_update == True:
            group_list = api_get_groups(faculty, year)
            if group_list != None:
                groups_db.update_one({'faculty': faculty, 'year': year}, {'$set': {'groups': group_list, 'last_updated': time.time()}})
                return group_list
            else:
                return groups_db.find_one({'faculty': faculty, 'year': year})['groups']
        else:
            return groups_db.find_one({'faculty': faculty, 'year': year})['groups']
    #if schedule_db.find_one({'group': group}) is None or time.time() - schedule_db.find_one({'group': group})['last_updated'] > UPDATE_TIME:
    #    schedule = api_get_groups(faculty, year, force_update)
    #else:
    #    return schedule_db.find_one({'group': group})[weekday][f'{weeknum}']

def get_years():
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

def get_faculties():
    """Возвращает список факультетов из БД."""
    faculties = []
    for item in groups_db.find({}):
        faculties.append(item['faculty'])
    return faculties    

@dp.message_handler(commands=['force_update'])
async def force_update_schedule(m):
    if m.from_user.id in ADMINS:
        groups_text = '⚙ Запущено обновление групп...\n\n'
        faculties = get_faculties()

        dt = datetime.datetime.now()
        year = int(dt.strftime('%y'))


        for _ in range(4):
            for faculty in faculties:
                groups_text += f'{faculty}: \n'
                groups = get_groups(faculty=faculty, year=str(year), force_update=True)
                for group in groups:
                    groups_text += f'{group}\n'
                groups_text += '\n'
            year -= 1

        groups_text += '\nХотите ли вы обновить расписание всех групп? (может занять много времени)'
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton(text='✔ Да', callback_data='force-update-yes'),
            types.InlineKeyboardButton(text='❌ Нет', callback_data='force-update-no')
        )
        
        await bot.send_message(m.chat.id, text=groups_text, reply_markup=keyboard, parse_mode='HTML')

@dp.message_handler(commands=['force_update_groups'])
async def force_update_groups(m: types.Message):
    args = m.get_args


@dp.message_handler(commands=["admin"])
async def admin_menu(m: types.Message):
    if m.from_user.id in ADMINS:
        await bot.send_message(
            chat_id=m.chat.id,
            text=f'Добро пожаловать в админ-панель, {m.from_user.first_name}.\n'
            'Выберите пункт в меню для дальнейших действий:',
            reply_markup=kb_admin,
            parse_mode='HTML'
        )

@dp.message_handler(commands=["start"])
async def start_handler(m: types.Message):
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

        await bot.send_message(
            m.chat.id, 
            f'Привет, {m.from_user.first_name}!\n'
            '*Для начала работы с ботом выбери свою группу (впоследствии выбор можно изменить):*',
            reply_markup=kb_faculty, 
            parse_mode='Markdown')
    else:
        user = users.find_one({'user_id': m.from_user.id})
        if user.get('favorite_groups') == None:
            users.update_one(
                {'user_id': m.from_user.id}, 
                {'$set': {'favorite_groups': []}})
        elif user.get('first_name') != m.from_user.first_name:
            users.update_one(
                {'user_id': m.from_user.id},
                {'$set': {'first_name': m.from_user.first_name}})
        elif user.get('last_name') != m.from_user.last_name:
            users.update_one(
                {'user_id': m.from_user.id},
                {'$set': {'last_name': m.from_user.last_name}})
        elif user.get('username') != m.from_user.username:
            users.update_one(
                {'user_id': m.from_user.id}, 
                {'$set': {'username': m.from_user.username}})
        group = get_group(m.from_user.id)
        await bot.send_message(
            m.chat.id, 
            f'Привет, {m.from_user.first_name}!\n'
            f'*Твоя группа: {group}.*\n'
            f'*Сейчас идёт {get_weekname()} неделя.*\n'
            'Вот главное меню:', 
            reply_markup=kbm, 
            parse_mode='Markdown')
        set_state(m.from_user.id, 'default')

@dp.message_handler(commands=['whatis'])
async def whatis(m: types.Message):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        key = raw_text.split(' ', maxsplit=1)[1]
        try:
            value = globals()[f'{key}']
            await bot.send_message(m.chat.id, f'Сейчас `{key}` == `{value}`', parse_mode='Markdown')
        except KeyError:
            await bot.send_message(m.chat.id, f'Переменная `{key}` не найдена!', parse_mode='Markdown')

@dp.message_handler(commands=['users_reset'])
async def users_reset(m: types.Message):
    if m.chat.id in ADMINS:
        for user in users.find():
            user_id = user['user_id']
            state = 'default'
            group = 'О-20-ИВТ-1-по-Б'
            set_state(user_id, state)
            set_group(user_id, group)
        await bot.send_message(
            m.chat.id, 
            f'Параметры пользователей сброшены!\n\n'
            'Состояние = {state}\nГруппа = {group}')

@dp.message_handler(commands=['users'])
async def users_handler(m: types.Message):
    if m.chat.id in ADMINS:
        text = '*Список пользователей бота:*\n\n'
        for user in users.find():
            first_name = user['first_name']
            last_name = user['last_name']
            user_id = user['user_id']
            group = user['group']
            str(first_name).replace('_', '\\_')
            str(last_name).replace('_', '\\_')

            if last_name != None or last_name != "None":
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
async def broadcast(m: types.Message):
    if m.chat.id in ADMINS:
        if m.text != '/broadcast':
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
        elif m.text == '/broadcast':
            pass

@dp.message_handler(commands=['exec'])
async def execute(m: types.Message):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        cmd = raw_text.split(' ', maxsplit=1)[1]
        try:
            exec(cmd)
            await bot.send_message(m.chat.id, f'{cmd} - успешно выполнено!')
        except Exception as e:
            await bot.send_message(m.chat.id, f'Произошла ошибка!\n\n`{e}`')


# Хэндлер для текста
@dp.message_handler(content_types=["text", "sticker", "photo", "audio", "video", "voice", "video_note", "document", "animation"])
async def anymess(m: types.Message):
    if users.find_one({'user_id': m.from_user.id}) == None:
        await bot.send_message(m.chat.id, 'Для начала работы с ботом выполните команду /start')
    elif users.find_one({'user_id': m.from_user.id}) != None and get_state(m.from_user.id) == 'default':
        group = get_group(m.from_user.id)
        await bot.send_message(
            m.chat.id, 
            text=f'Привет, {m.from_user.first_name}!\n'
            f'<b>Твоя группа: {group}.</b>\n'
            f'<b>Сейчас идёт {get_weekname()} неделя.</b>\n'
            'Вот главное меню:', 
            reply_markup=kbm,
            parse_mode='HTML')
    elif get_state(m.from_user.id) == 'find_class':
        if re.match(r'(\b[1-9][1-9]\b|\b[1-9]\b)', m.text):
            await bot.send_photo(
                m.chat.id, 
                photo=building_1, 
                caption=f'Аудитория {m.text} находится в корпусе №1 <i>(Институтская, 16)</i>.', 
                parse_mode='HTML')
            await bot.send_location(
                m.chat.id, 
                latitude=53.305077, 
                longitude=34.305080)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(
                m.chat.id, 
                f'Привет, {m.from_user.first_name}!\n'
                f'<b>Твоя группа: {group}.</b>\n'
                f'<b>Сейчас идёт {get_weekname()} неделя.</b>\n'
                'Вот главное меню:', 
                reply_markup=kbm, 
                parse_mode='HTML')
        elif re.match(r'\b[1-9][0-9][0-9]\b', m.text):
            await bot.send_photo(
                m.chat.id, 
                photo=building_2, 
                caption=f'Аудитория {m.text} находится в корпусе №2 <i>(бульвар 50 лет Октября, 7)</i>.', 
                parse_mode='HTML')
            await bot.send_location(
                m.chat.id, 
                latitude=53.304442, 
                longitude=34.303849)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(
                m.chat.id, 
                f'Привет, {m.from_user.first_name}!\n'
                f'<b>Твоя группа: {group}.</b>\n'
                f'<b>Сейчас идёт {get_weekname()} неделя.</b>\n'
                'Вот главное меню:', 
                reply_markup=kbm, 
                parse_mode='HTML')
        elif re.match(r'(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)', m.text):
            await bot.send_photo(
                m.chat.id, 
                photo=building_3, 
                caption=f'Аудитория {m.text} находится в корпусе №3 <i>(Харьковская, 8)</i>.', 
                parse_mode='HTML')
            await bot.send_location(
                m.chat.id, 
                latitude=53.304991, 
                longitude=34.306688)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(
                m.chat.id, 
                f'Привет, {m.from_user.first_name}!\n'
                f'<b>Твоя группа: {group}.</b>\n'
                f'<b>Сейчас идёт {get_weekname()} неделя.</b>\n'
                f'Вот главное меню:', 
                reply_markup=kbm, 
                parse_mode='HTML')
        elif re.match(r'\bБ\d{3}\b', m.text):
            await bot.send_photo(
                m.chat.id, 
                photo=building_4, 
                caption=f'Аудитория {m.text} находится в корпусе №4 <i>(Харьковская, 10Б)</i>.', 
                parse_mode='HTML')
            await bot.send_location(
                m.chat.id, 
                latitude=53.303513, 
                longitude=34.305085)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            await bot.send_message(
                m.chat.id, 
                f'Привет, {m.from_user.first_name}!\n'
                f'<b>Твоя группа: {group}.</b>\n'
                f'<b>Сейчас идёт {get_weekname()} неделя.</b>\n'
                'Вот главное меню:', 
                reply_markup=kbm, 
                parse_mode='HTML')
        else:
            await bot.send_message(
                m.chat.id, 
                'Данный номер аудитории некорректен. Повторите попытку или отмените действие:', 
                reply_markup=kb_cancel_building,
                parse_mode='HTML')
    elif get_state(m.from_user.id).startswith('add_notification_'):
        if re.match(r'^2[0-3]:[0-5][0-9]$|^[0]{1,2}:[0-5][0-9]$|^1[0-9]:[0-5][0-9]$|^0?[1-9]:[0-5][0-9]$', m.text):
            if re.match(r'\b[0-9]:[0-5][0-9]\b', m.text):
                notification_time = f"0{m.text}"
            else:
                notification_time = str(m.text)

            weekday = get_state(m.from_user.id).split('_')[2]
            
            user_time_dict = users.find_one({'user_id': m.from_user.id}).get('notification_time')
            if user_time_dict is None or user_time_dict == {}:
                user_time_dict = {
                    "monday": "",
                    "tuesday": "",
                    "wednesday": "",
                    "thursday": "",
                    "friday": "",
                    "saturday": "",
                    "sunday": ""
                }
            
            # Удаляем прошлое напоминание на этот день (edit notification)
            # БЕРЕТ ТОЛЬКО ОЛД НОТИФИКЕЙШН
            try:
                old_notification_time = users.find_one({"user_id": m.from_user.id}).get('notification_time')[weekday]
                scheduled_ = scheduled_msg.find_one({"id": 1})[weekday]
                user_list = list(scheduled_msg.find_one({"id": 1})[weekday][old_notification_time])
                user_list.pop(user_list.index(m.from_user.id))
                scheduled_[old_notification_time] = user_list
                print(f'!! scheduled_ == {scheduled_}')
                scheduled_msg_dict = {weekday: scheduled_}
                #scheduled_msg_dict = {weekday: {old_notification_time: user_list}}
                scheduled_msg.update_one({'id': 1}, {"$set": scheduled_msg_dict})
                user_time_dict[weekday] = ''
                users.update_one({'user_id': m.from_user.id}, {"$set": {"notification_time": user_time_dict}})
                user_time_dict = users.find_one({'user_id': m.from_user.id})['notification_time']
            except:
                pass
            
            user_time_dict[weekday] = notification_time
            users.update_one({'user_id': m.from_user.id}, {"$set": {"notification_time": user_time_dict}})

            notification_list = scheduled_msg.find_one({'id': 1})[weekday].get(notification_time)
            if notification_list == None:
                scheduled_ = scheduled_msg.find_one({"id": 1})[weekday]
                user_list = []
                user_list.append(m.from_user.id)
                scheduled_[notification_time] = user_list
                scheduled_msg_dict = {weekday: scheduled_}
                scheduled_msg.update_one({'id': 1}, {"$set": scheduled_msg_dict})
            else:
                scheduled_ = scheduled_msg.find_one({"id": 1})[weekday]
                user_list = list(scheduled_[notification_time])
                user_list.append(m.from_user.id)
                scheduled_[notification_time] = user_list
                scheduled_msg_dict = {weekday: scheduled_}
                scheduled_msg.update_one({'id': 1}, {"$set": scheduled_msg_dict})

            await bot.send_message(m.chat.id, f'Уведомление на {m.text} установлено!', reply_markup=kbbb, parse_mode='HTML')
            set_state(m.chat.id, 'default')
        else:
            await bot.send_message(m.chat.id, 'Вы ввели некорректное время. Повторите попытку или отмените действие:', reply_markup=kb_cancel_building, parse_mode='HTML')

# Хэндлер обработки действий кнопок
@dp.callback_query_handler()
async def button_func(call: types.CallbackQuery):
    if call.data == 'days':
        await bot.answer_callback_query(call.id)
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            weekname = '[Н] - нечётная'
            buttons = ['[Н]', 'Ч']
        else:
            weekname = '[Ч] - чётная'
            buttons = ['Н', '[Ч]']

        kb_dn = days_keyboard(buttons)

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Выберите неделю и день (сейчас идёт {weekname}):\n',
            reply_markup=kb_dn,
            parse_mode='HTML'
        )
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

        schedule_txt = ''

        for lesson in schedule:
            if lesson[1] != '-':
                #print(f'{lesson[0]}) {lesson[1]}')
                schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'
            #table.add_row(lesson)
        
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'<b>Выбрана группа {group}</b>\n'
            f'<b>Расписание:</b> {wdays.translate(weekday)}\n'
            f'<b>Неделя:</b> {weekname}\n\n'
            f'{schedule_txt}\n'
            '<code>[Л]</code> - <b>лекция</b>\n'
            '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
            '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>',
            reply_markup=kbb, parse_mode='HTML')
    elif call.data == 'today':
        await bot.answer_callback_query(call.id)
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday()
        if isoweekday == 7:
            text = f'<b>Выбрана группа {group}</b>\nСегодня: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        else:
            group = get_group(call.from_user.id)
            isoweekday = datetime.datetime.today().isoweekday()
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                weeknum = '1'
                weekname = 'нечётная'
            else:
                weeknum = '2'
                weekname = 'чётная'

            schedule = get_schedule(group, weekday, weeknum)
            schedule_txt = ''

            for lesson in schedule:
                if lesson[1] != '-':
                    schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'
            
            text = (
                f'<b>Выбрана группа {group}</b>\n'
                f'<b>Сегодня:</b> {wdays.names(isoweekday)[0]}\n'
                f'<b>Неделя:</b> {weekname}\n\n'
                f'{schedule_txt}\n'
                '<code>[Л]</code> - <b>лекция</b>\n'
                '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
                '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
            )

        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text, reply_markup=kbbb, parse_mode='HTML')
    elif call.data == 'rings':
        await bot.answer_callback_query(call.id)
        table_r.clear()
        table_r.add_column(fieldname="№", column=index)
        table_r.add_column(fieldname="Время", column=rings_list)
        text = f'Расписание пар\n\n```{table_r}```'
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomorrow':
        await bot.answer_callback_query(call.id)
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday() + 1
        if isoweekday == 6:
            text = f'<b>Выбрана группа {group}</b>\nЗавтра: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        elif isoweekday == 8:
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                weeknum = '1'
                weekname = 'нечётная'
            else:
                weeknum = '2'
                weekname = 'чётная'

            schedule = get_schedule(group, weekday, weeknum)

            schedule_txt = ''
            for lesson in schedule:
                if lesson[1] != '-':
                    schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'
            
            text = (
                f'<b>Выбрана группа {group}</b>\n'
                f'<b>Завтра:</b> {wdays.names(isoweekday)[0]}\n'
                f'<b>Неделя:</b> {weekname}\n\n'
                f'{schedule_txt}\n'
                '<code>[Л]</code> - <b>лекция</b>\n'
                '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
                '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
            )
        else:
            weekday = wdays.names(isoweekday)[1]

            if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                weeknum = '1'
                weekname = 'нечётная'
            else:
                weeknum = '2'
                weekname = 'чётная'

            schedule = get_schedule(group, weekday, weeknum)

            schedule_txt = ''
            #print(f'369. schedule = {schedule}')
            for lesson in schedule:
                if lesson[1] != '-':
                    schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'                
                #print(f'371. lesson = {lesson}')
                #table.add_row(lesson)
            
            text = (
                f'<b>Выбрана группа {group}</b>\n'
                f'<b>Завтра:</b> {wdays.names(isoweekday)[0]}\n'
                f'<b>Неделя:</b> {weekname}\n\n'
                f'{schedule_txt}\n'
                '<code>[Л]</code> - <b>лекция</b>\n'
                '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
                '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
            )
            
        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='HTML')

    elif call.data == 'tomain':
        await bot.answer_callback_query(call.id, text='Возврат в главное меню...')
        await bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id,
            text=f'Привет, {call.from_user.first_name}!\n'
            f'*Твоя группа: {get_group(call.from_user.id)}.*\n'
            f'*Сейчас идёт {get_weekname()} неделя.*\n'
            'Вот главное меню:',
            reply_markup=kbm, 
            parse_mode='Markdown'
        )

    elif call.data == 'building':
        await bot.answer_callback_query(call.id)
        set_state(call.from_user.id, 'find_class')
        await bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text='Отправьте номер аудитории:', 
            reply_markup=kb_cancel_building, 
            parse_mode='Markdown'
        )

    elif call.data == 'cancel_find_class':
        await bot.answer_callback_query(call.id)
        set_state(call.from_user.id, 'default')
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Привет, {call.from_user.first_name}!\n'
            f'*Твоя группа: {get_group(call.from_user.id)}.*\n'
            f'*Сейчас идёт {get_weekname()} неделя.*\n'
            'Вот главное меню:',
            reply_markup=kbm, 
            parse_mode='Markdown'
        )

    # Выбор факультета
    elif call.data == 'change_faculty':
        await bot.answer_callback_query(call.id)
        faculty_list = get_faculties()
        kb_faculty = types.InlineKeyboardMarkup()

        for faculty in faculty_list:
            callback_faculty = str('f_' + faculty).replace(' ', '_')
            kb_faculty.row(types.InlineKeyboardButton(text=faculty, callback_data=ru_en(callback_faculty)))

        kb_faculty.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Выберите факультет:', # Выберите год поступления:
            reply_markup=kb_faculty, 
            parse_mode='Markdown'
        )

    # Выбор года поступления
    elif str(call.data).startswith('f_'):
        await bot.answer_callback_query(call.id)

        faculty = str(call.data[2:])

        years_list = get_years()
        kb_years = types.InlineKeyboardMarkup()

        for year in years_list:
            callback_year = f'y_{year}_{faculty}'
            kb_years.row(types.InlineKeyboardButton(text='20' + str(year), callback_data=callback_year))

        kb_years.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Выберите год поступления:',
            reply_markup=kb_years, 
            parse_mode='Markdown'
        )

    # Выбор группы
    elif str(call.data).startswith('y_'):
        await bot.answer_callback_query(call.id)
        year = call.data.split('_')[1]

        cb_faculty = str(call.data[5:])
        cb_faculty = en_ru(cb_faculty).capitalize()
        faculty = cb_faculty.replace('_', ' ')
        
        if 'економики' in faculty:
            faculty = 'Факультет отраслевой и цифровой экономики'
        elif 'електроники' in faculty:
            faculty = 'Факультет энергетики и электроники'
            
        group_list = get_groups(faculty=faculty, year=year)
        kb_group = types.InlineKeyboardMarkup()

        for group in group_list:
            kb_group.row(types.InlineKeyboardButton(text=group, callback_data=group))

        kb_group.row(
            types.InlineKeyboardButton(
                text='🚫 Отмена', 
                callback_data='cancel_find_class'
            )
        )

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Выберите группу:',
            reply_markup=kb_group, parse_mode='Markdown'
        )


    elif call.data == 'change_group':
        await bot.answer_callback_query(call.id)
        group_list = get_groups()
        kb_group = types.InlineKeyboardMarkup()

        for group in group_list:
            kb_group.row(types.InlineKeyboardButton(text=group, callback_data=group))

        kb_group.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Выберите группу:',
            reply_markup=kb_group, 
            parse_mode='Markdown'
        )

    elif call.data == 'favorite_groups':
        await bot.answer_callback_query(call.id)
        kb_favorite = types.InlineKeyboardMarkup()
        user = users.find_one({'user_id': call.from_user.id})
        i = 0
        if user.get('favorite_groups') is not None:
            for group in user.get('favorite_groups'):
                kb_favorite.row(
                    types.InlineKeyboardButton(text=group, callback_data=group),
                    types.InlineKeyboardButton(text='❌', callback_data=f'{group}__del'))
                i += 1
            space_left = 5 - i
            for i in range(space_left):
                kb_favorite.row(types.InlineKeyboardButton(text='➕ Добавить', callback_data='add_favorite'))
        else:
            users.update_one(
                {"user_id": call.from_user.id}, 
                {"$set": {"favorite_groups": []}})
            for i in range(5):
                kb_favorite.row(types.InlineKeyboardButton(text='➕ Добавить', callback_data='add_favorite'))
        kb_favorite.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Твой список избранных групп:',
            reply_markup=kb_favorite
        )
        
    elif str(call.data).startswith('О-20'):
        await bot.answer_callback_query(call.id)
        if str(call.data).endswith('__del'):
            user = users.find_one({'user_id': call.from_user.id})
            favorite_groups = user.get('favorite_groups')
            group = str(call.data).split('__')[0]
            favorite_groups.pop(favorite_groups.index(group))
            users.update_one(
                {'user_id': call.from_user.id}, 
                {'$set': {'favorite_groups': favorite_groups}})
            
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Группа {group} удалена из избранных\\!\n'
                f'*Твоя группа: {get_group(call.from_user.id)}.*\n'
                f'*Сейчас идёт {get_weekname()} неделя.*\n'
                'Вот главное меню:',
                reply_markup=kbm,
                parse_mode='Markdown'
            )
            set_state(call.from_user.id, 'default')
        else:
            if get_state(call.from_user.id) == 'default':
                group = str(call.data)
                set_group(call.from_user.id, group)
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f'Привет, {call.from_user.first_name}\\!\n'
                                            f'*Твоя группа: {get_group(call.from_user.id)}.*\n'
                                            f'*Сейчас идёт {get_weekname()} неделя.*\n'
                                            'Вот главное меню:',
                                            reply_markup=kbm, parse_mode='Markdown')
                
            elif get_state(call.from_user.id) == 'add_favorite':
                user = users.find_one({'user_id': call.from_user.id})
                favorite_groups = user.get('favorite_groups')
                favorite_groups.append(call.data)
                users.update_one({'user_id': call.from_user.id}, {'$set': {'favorite_groups': favorite_groups}})
                await bot.edit_message_text(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f'Группа {call.data} добавлена в избранные\\!\n'
                                            f'*Твоя группа: {get_group(call.from_user.id)}.*\n'
                                            f'*Сейчас идёт {get_weekname()} неделя.*\n'
                                            'Вот главное меню:',
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

        kb_faculty.row(types.InlineKeyboardButton(text='🚫 Отмена', 
                                                  callback_data='cancel_find_class'))
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=f'Выберите факультет:',
                                    reply_markup=kb_faculty, parse_mode='Markdown')
        
    elif call.data == 'notifications':
        await bot.answer_callback_query(call.id)
        notification_time = users.find_one({"user_id": call.from_user.id}).get('notification_time')
        print(f"not. time ({call.from_user.id}) == {notification_time}")
        if notification_time is None or notification_time == {}:
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=f'Уведомления с расписанием отсутствуют\\.\n'
                                        'Выберите день недели для установки времени автоматической отправки расписания:',
                                        reply_markup=kb_notifications_days, parse_mode='MarkdownV2')
        else:
            text = 'Дни недели, по которым вы получаете уведомления с расписанием: \n\n'
            notification_time = users.find_one({"user_id": call.from_user.id}).get('notification_time')
            for day in notification_time:
                if notification_time[day] != "":
                    day_ru = wdays.translate(day)
                    text += f'{day_ru.capitalize()}: {notification_time[day]}\n'
            text += '\nХотите изменить время, добавить или удалить напоминания\\? Выберите день:'
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=text,
                                        reply_markup=kb_notifications_days)

    elif str(call.data).startswith('notify_'):
        weekday = str(call.data).split('_')[1]
        notification_time = users.find_one({"user_id": call.from_user.id}).get('notification_time')

        if notification_time is None or notification_time == {} or notification_time.get(weekday) is None or notification_time.get(weekday) == "":
            set_state(call.from_user.id, f'add_notification_{weekday}')
            text = (f'Добавление напоминания \\({wdays.translate(weekday)}\\)\n\n'
                    'Введите время, в которое вы хотите получать расписание:\n'
                    '————————————————————\n'
                    'Если введённое время в диапазоне от 00:00 до 12:59, то бот отправит расписание на сегодня\\.\n'
                    'Если же введённое время в диапазоне от 13:00 до 23:59, то расписание на завтра\\.')
            reply_markup = kb_cancel_building
        else:
            text = f'Изменение напоминания \\({wdays.translate(weekday)}\\):'
            kb_notifications = types.InlineKeyboardMarkup()
            kb_notifications.row(types.InlineKeyboardButton(text='❌ Удалить', callback_data=f'del_notification_{weekday}'))
            kb_notifications.row(types.InlineKeyboardButton(text='✍ Изменить', callback_data=f'edit_notification_{weekday}'))
            kb_notifications.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))
            reply_markup = kb_notifications

        await bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=reply_markup)

    elif str(call.data).startswith('del_notification_'):
        await bot.answer_callback_query(call.id)
        weekday = str(call.data).split('_')[2]
        notification_time = users.find_one({"user_id": call.from_user.id}).get('notification_time')[weekday]

        user_list = list(scheduled_msg.find_one({"id": 1})[weekday][notification_time])
        user_list.pop(user_list.index(call.from_user.id))
        scheduled_msg_dict = {weekday: {notification_time: user_list}}
        print(f'user_list == {user_list}')
        scheduled_msg.update_one({'id': 1}, {"$set": scheduled_msg_dict})

        user_time_dict = dict(users.find_one({"user_id": call.from_user.id})['notification_time'])
        user_time_dict[weekday] = ''
        users.update_one({'user_id': call.from_user.id}, {"$set": {"notification_time": user_time_dict}})

        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=f'Уведомление \\({wdays.translate(weekday)}\\) выключено\\.',
                                    reply_markup=kbbb)

    elif str(call.data).startswith('edit_notification_'):
        await bot.answer_callback_query(call.id)
        weekday = str(call.data).split('_')[2]
        notification_time = users.find_one({"user_id": call.from_user.id}).get('notification_time')[weekday]
        
        text = (f'Сейчас вы получаете расписание \\({wdays.translate(weekday)}\\) в {notification_time}\\.\n'
                'Введите время, в которое вы хотите получать расписание:\n'
                '————————————————————\n'
                'Если введённое время в диапазоне от 00:00 до 12:59, то бот отправит расписание на сегодня\\.\n'
                'Если же введённое время в диапазоне от 13:00 до 23:59, то расписание на завтра\\.')

        set_state(call.from_user.id, f'add_notification_{weekday}')
        await bot.edit_message_text(chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=kb_cancel_building, parse_mode='MarkdownV2')
    
    elif str(call.data).startswith('force-update-'):
        choice = str(call.data).split('-')[2]
        text = ''
        if choice == 'no':
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text='Хорошо, не обновляем расписание.')
        else:
            text = '⚙ Запущено обновление расписания...\n\n'
            faculties = get_faculties()
            for faculty in faculties:
                text += f'{faculty}: \n'
                groups = get_groups(faculty)
                for group in groups:
                    get_schedule(group, 'monday', '1')
                    text += f'✔ {group}\n'
                    await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=text,
                                        parse_mode='HTML')
            text += '\nРасписание обновлено успешно!'
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=call.message.message_id,
                                        text=text,
                                        parse_mode='HTML')
    
    elif str(call.data) == 'user_list':
        count = users.count_documents({})
        text = f'<u>Список пользователей бота (всего {count}):</u>\n\n'
        block_count = 0
        await bot.answer_callback_query(call.id, "Ожидайте загрузки из базы...")
        for user in users.find():
            first_name = user['first_name']
            last_name = user['last_name']
            user_id = user['user_id']
            group = user['group']
            if last_name != None or last_name != "None":
                if len(text + f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a> ◼ <b>Группа {group}</b>\n') <= 4096:
                    text += f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a> ◼ <b>Группа {group}</b>\n'
                else:
                    if block_count == 0:
                        await bot.edit_message_text(
                            text=text,
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            parse_mode='HTML'
                        )
                    else:
                        last_msg = await bot.send_message(call.message.chat.id, text, parse_mode='HTML')
                        globals()['last_msgid'] = last_msg.message_id
                        text = f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a> ◼ <b>Группа {group}</b>\n'
            else:
                if len(text + f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n') <= 4096:
                    text += f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n'
                else:
                    if block_count == 0:
                        await bot.edit_message_text(
                            text=text, 
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            parse_mode='HTML'
                        )
                    else:
                        last_msg = await bot.send_message(call.message.chat.id, text, parse_mode='HTML')
                        globals()['last_msgid'] = last_msg.message_id
                        text = f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n'
            
            block_count += 1
        print("last_msgid: ", globals()['last_msgid'])
        
        if block_count == 0:
            await bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=kb_admin_back
            )
        else:
            await bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=globals()['last_msgid'],
                reply_markup=kb_admin_back
            )

    elif str(call.data) == 'toadmin':
        await bot.edit_message_text(
                text=f'Добро пожаловать в админ-панель, {call.from_user.first_name}.\n'
                'Выберите пункт в меню для дальнейших действий:', 
                chat_id=call.from_user.id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=kb_admin
            )

async def time_trigger():
    while True:
        print(f'time_trigger(): {time.strftime("%H:%M:%S")}')

        hour = time.strftime("%H")
        #minute = time.strftime("%M")
        fulltime = time.strftime("%H:%M")
        weekday_name = time.strftime('%A').lower()

        if int(hour) < 24 and int(hour) >= 12:
            day = 'tomorrow'
            ru_day = 'Завтра'
        else:
            day = 'today'
            ru_day = 'Сегодня'
        
        timetable = scheduled_msg.find_one({"id": 1})[weekday_name]

        if fulltime in timetable:
            print("time_trigger() [709]. heelllloooooo")
            for user_id in timetable[fulltime]:
                print("time_trigger() [711]. heelllloooooo")
                group = get_group(user_id)
                isoweekday = datetime.datetime.today().isoweekday()
                if day == 'tomorrow':
                    isoweekday += 1
                if isoweekday == 6 or isoweekday == 7:
                    pass
                elif isoweekday == 8:
                    weekday = wdays.names(isoweekday)[1]

                    if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                        weeknum = '1'
                        weeknum = 'нечётная'
                    else:
                        weeknum = '2'
                        weekname = 'чётная'

                    schedule = get_schedule(group, weekday, weeknum)
                    schedule_txt = ''

                    for lesson in schedule:
                        if lesson[1] != '-':
                            schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'

                        #table.add_row(lesson)
                    
                    text = (
                        f'[🔔 Ежедневное уведомление в {fulltime}]\n'
                        f'<b>Выбрана группа {group}</b>\n'
                        f'<b>{ru_day}:</b> {wdays.names(isoweekday)[0]}\n'
                        f'<b>Неделя:</b> {weekname}\n\n'
                        f'{schedule_txt}\n'
                        '<code>[Л]</code> - <b>лекция</b>\n'
                        '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
                        '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
                    )

                    await bot.send_message(user_id, text, reply_markup=kbbb, parse_mode='HTML')
                else:
                    weekday = wdays.names(isoweekday)[1]

                    if datetime.datetime.today().isocalendar()[1] % 2 == 0:
                        weeknum = '1'
                        weeknum = 'нечётная'
                    else:
                        weeknum = '2'
                        weekname = 'чётная'

                    schedule = get_schedule(group, weekday, weeknum)
                    schedule_txt = ''

                    for lesson in schedule:
                        if lesson[1] != '-':
                            schedule_txt += f'Пара №{lesson[0]} <i>({rings_list[lesson[0]-1]})</i>\n<code>{lesson[1].split(" ", maxsplit=1)[0]}</code> <b>{lesson[1].split(" ", maxsplit=1)[1]}</b>\n<b>Аудитория:</b> <code>{lesson[2]}</code>\n\n'
                    
                    text = (
                        f'[🔔 Ежедневное уведомление в {fulltime}]\n'
                        f'<b>Выбрана группа {group}</b>\n'
                        f'<b>{ru_day}:</b> {wdays.names(isoweekday)[0]}\n'
                        f'<b>Неделя:</b> {weekname}\n\n'
                        f'{schedule_txt}\n'
                        '<code>[Л]</code> - <b>лекция</b>\n'
                        '<code>[ПЗ]</code> - <b>практическое занятие</b>\n'
                        '<code>[ЛАБ]</code> - <b>лабораторное занятие</b>'
                    )

                    await bot.send_message(user_id, text, reply_markup=kbbb, parse_mode='HTML')
                await asyncio.sleep(1)
        
        await asyncio.sleep(60)

def startbot():
    while True:
        executor.start_polling(dp, skip_updates=True)
        break

if __name__ == "__main__":
    executor_ = ProcessPoolExecutor(4)
    loop = asyncio.get_event_loop()
    
    time_trigger_ = asyncio.ensure_future(time_trigger())
    print('time_trigger(): initialized')

    startbot_ = asyncio.ensure_future(loop.run_in_executor(executor_, startbot))
    print('startbot(): initialized')