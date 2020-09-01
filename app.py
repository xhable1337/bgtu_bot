# School Diary Robot by xhable
# v3, added university schedule (BSTU)
# Now you must put your bot's token into config vars. (they're getting here by os.environ())

from dbutils import get_state, set_state
from prettytable import PrettyTable
from telebot import types, apihelper
from flask import Flask, request
from pymongo import MongoClient
import telebot
import datetime
import wdays
import os
import re

MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI, retryWrites=False) 
db = client.heroku_38n7vrr9
users = db.users

building_1 = 'https://telegra.ph/file/49ec8634ab340fa384787.png'
building_2 = 'https://telegra.ph/file/7d04458ac4230fd12f064.png'
building_3 = 'https://telegra.ph/file/6b801965b5771830b67f0.png'
building_4 = 'https://telegra.ph/file/f79c20324a0ba6cd88711.png'

server = Flask(__name__)
token = os.environ['token']
no = '-'
index = [1, 2, 3, 4, 5]
wday_monday_1 = ['[ПЗ] Ин.яз.', '[Л] Мат.анализ', '[ПЗ] Мат.анализ', '[ПЗ] Ин.яз.', no, [322, 'А', 'Б204', 322, no]]
wday_monday_2 = ['[Л] Физ-ра', '[Л] Мат.анализ', '[ПЗ] Мат.анализ', '[ПЗ] Ин.яз.', no, ['Б404', 'А', 'Б204', 322, no]]
wday_tuesday_1 = ['[Л] Дискр.мат.', '[ПЗ] Дискр.мат.', '[Л] Програм.', no, no, ['B', 'Б204', 219, no, no]]
wday_tuesday_2 = ['[Л] Информат.', '[ПЗ] Дискр.мат.', '[Л] Програм.', no, no, [219, 'Б204', 219, no, no]]
wday_wednesday_1 = [no, '[Л] Алг. и геом.', '[ПЗ] Физ-ра', no, no, [no, 'A', 'спортзал', no, no]]
wday_wednesday_2 = [no, '[Л] Алг. и геом.', '[ПЗ] Физ-ра', no, no, [no, 'A', 'спортзал', no, no]]
wday_thursday_1 = [no, '[ЛАБ] Програм.', '[ПЗ] Ин.яз.', no, no, [no, 408, 322, no, no]]
wday_thursday_2 = [no, '[ЛАБ] Програм.', '[ПЗ] Ин.яз.', '[ПЗ] Ин. яз.', no, [no, 408, 322, 322, no]]
wday_friday_1 = ['[ПЗ] Алг. и геом.', '[Л] Пед. и псих.', '[ПЗ] Пед. и псих.', no, no, ['Б204', 'Б', 'А211', no, no]]
wday_friday_2 = ['[ПЗ] Алг. и геом.', '[ЛАБ] Информат.', '[ПЗ] Пед. и псих.', no, no, ['Б204', 408, 'А211', no, no]]

time = ['8:00-9:35', '9:45-11:20', '11:30-13:05', '13:20-14:55', '15:05-16:40']

ADMINS = [124361528]
bot = telebot.TeleBot(token)
table = PrettyTable()
table_r = PrettyTable()

@bot.message_handler(commands=["start"])
def start_handler(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        users.insert_one({
            'first_name': m.from_user.first_name,
            'last_name': m.from_user.last_name,
            'user_id': m.from_user.id,
            'username': m.from_user.username,
            'state': 'default'
        })
    else:
        bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\nВот главное меню:', reply_markup=kbm)
        set_state(m.from_user.id, 'default')

@bot.message_handler(commands=["whatis"])
def whatis(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        key = raw_text.split(' ', maxsplit=1)[1]
        try:
            value = globals()[f'{key}']
            bot.send_message(m.chat.id, f'Сейчас `{key}` == `{value}`', parse_mode='Markdown')
        except KeyError:
            bot.send_message(m.chat.id, f'Переменная `{key}` не найдена!', parse_mode='Markdown')



@bot.message_handler(commands=["users"])
def users_handler(m):
    text = '*Список пользователей бота:*\n\n'
    for user in users.find():
        first_name = user['first_name']
        last_name = user['last_name']
        user_id = user['user_id']
        if last_name != None:
            text += f'[{first_name} {last_name}](tg://user?id={user_id})\n'
        else:
            text += f'[{first_name}](tg://user?id={user_id})\n'
    bot.send_message(m.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=["broadcast"])
def broadcast(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        text = raw_text.split(' ', maxsplit=1)[1]
        for user in users.find():
            user_id = user['user_id']
            bot.send_message(user_id, text)

@bot.message_handler(commands=["exec"])
def execute(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        cmd = raw_text.split(' ', maxsplit=1)[1]
        try:
            exec(cmd)
            bot.send_message(m.chat.id, f'{cmd} - успешно выполнено!')
        except Exception as e:
            bot.send_message(m.chat.id, f'Произошла ошибка!\n\n`{e}`')

kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(text='📅 Расписание по дням', callback_data='days'))
kbm.row(types.InlineKeyboardButton(text='⚡️ Сегодня', callback_data='today'), types.InlineKeyboardButton(text='⚡️ Завтра', callback_data='tomorrow'))
kbm.row(types.InlineKeyboardButton(text='🔔 Расписание пар', callback_data='rings'))
kbm.row(types.InlineKeyboardButton(text='🏠 Найти корпус по аудитории', callback_data='building'))

kb_r = types.InlineKeyboardMarkup()
kb_r.row(types.InlineKeyboardButton(text='Понедельник', callback_data='r_monday'))
kb_r.row(types.InlineKeyboardButton(text='Остальные дни', callback_data='r_others'))
kb_r.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))

kb_dn = types.InlineKeyboardMarkup()
kb_dn.row(types.InlineKeyboardButton(text='1️⃣ Пн', callback_data='wday_monday'),
types.InlineKeyboardButton(text='2️⃣ Вт', callback_data='wday_tuesday'),
types.InlineKeyboardButton(text='3️⃣ Ср', callback_data='wday_wednesday'))
kb_dn.row(types.InlineKeyboardButton(text='4️⃣ Чт', callback_data='wday_thursday'),
types.InlineKeyboardButton(text='5️⃣ Пт', callback_data='wday_friday'))
kb_dn.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))

kbb = types.InlineKeyboardMarkup()
kbb.row(types.InlineKeyboardButton(text='↩️ Назад', callback_data='days'))

kbbb = types.InlineKeyboardMarkup()
kbbb.row(types.InlineKeyboardButton(text='🔄 В главное меню', callback_data='tomain'))

kb_cancel_building = types.InlineKeyboardMarkup()
kb_cancel_building.row(types.InlineKeyboardButton(text='🚫 Отмена'))

@bot.message_handler(content_types=["text"])
def anymess(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        bot.send_message(m.chat.id, 'Для начала работы с ботом выполните команду /start')
    elif users.find_one({'user_id': m.from_user.id}) != None and get_state(m.from_user.id) == 'default':
        bot.send_message(m.chat.id, text='Главное меню:', reply_markup=kbm)
    elif get_state(m.from_user.id) == 'find_class':
        if re.match(r'(\b[1-9][1-9]\b|\b[1-9]\b)', m.text):
            bot.send_photo(m.chat.id, photo=building_1, caption=f'Аудитория {m.text} находится в корпусе №1 (Институтская, 16).')
            bot.send_location(m.chat.id, latitude=53.305077, longitude=34.305080)
            set_state(m.chat.id, 'default')
            bot.send_message(m.chat.id, 'Главное меню', reply_markup=kbm)
        elif re.match(r'\b[1-9][0-9][0-9]\b', m.text):
            bot.send_photo(m.chat.id, photo=building_2, caption=f'Аудитория {m.text} находится в корпусе №2 (бульвар 50 лет Октября, 7).')
            bot.send_location(m.chat.id, latitude=53.304442, longitude=34.303849)
            set_state(m.chat.id, 'default')
            bot.send_message(m.chat.id, 'Главное меню', reply_markup=kbm)
        elif re.match(r'(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)', m.text):
            bot.send_photo(m.chat.id, photo=building_3, caption=f'Аудитория {m.text} находится в корпусе №3 (Харьковская, 8).')
            bot.send_location(m.chat.id, latitude=53.304991, longitude=34.306688)
            set_state(m.chat.id, 'default')
            bot.send_message(m.chat.id, 'Главное меню', reply_markup=kbm)
        elif re.match(r'\bБ\d{3}\b', m.text):
            bot.send_photo(m.chat.id, photo=building_4, caption=f'Аудитория {m.text} находится в корпусе №4 (Харьковская, 10Б).')
            bot.send_location(m.chat.id, latitude=53.303513, longitude=34.305085)
            set_state(m.chat.id, 'default')
            bot.send_message(m.chat.id, 'Главное меню', reply_markup=kbm)
        else:
            bot.send_message(m.chat.id, 'Данный номер аудитории некорректен. Повторите попытку или отмените действие:', reply_markup=kb_cancel_building)

@bot.callback_query_handler(func=lambda call: True)
def button_func(call):
    if call.data == 'days':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите день недели:',
        reply_markup=kb_dn)
    elif call.data[:5] == 'wday_':
        cdata = str(call.data)
        table.clear()
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            lesson = globals()[f'{cdata}_1'][0:5]
            room = globals()[f'{cdata}_1'][5]
        else:
            lesson = globals()[f'{cdata}_2'][0:5]
            room = globals()[f'{cdata}_2'][5]
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Пара", column=lesson)
        table.add_column(fieldname="Кабинет", column=room)
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Расписание: {wdays.translate(cdata[5:])}\n\n```{table}```\n\nЛ - лекция\nПЗ - практическое занятие\nЛАБ - лабораторное занятие',
        reply_markup=kbb, parse_mode='Markdown')
    elif call.data == 'today':
        wd = datetime.datetime.today().isoweekday()
        table.clear()
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            lesson = globals()[f'wday_{wdays.names(wd)[1]}_1'][0:5]
            room = globals()[f'wday_{wdays.names(wd)[1]}_1'][5]
        else:
            lesson = globals()[f'wday_{wdays.names(wd)[1]}_2'][0:5]
            room = globals()[f'wday_{wdays.names(wd)[1]}_2'][5]
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Пара", column=lesson)
        table.add_column(fieldname="Кабинет", column=room)
        if wd == 6 or wd == 7:
            text = f'Сегодня: {wdays.names(wd)[0]}\n\nУдачных выходных!'
        else:
            text = f'Сегодня: {wdays.names(wd)[0]}\n\n```{table}```\n\nЛ - лекция\nПЗ - практическое занятие\nЛАБ - лабораторное занятие'
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text, reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'rings':
        table_r.clear()
        table_r.add_column(fieldname="№", column=index)
        table_r.add_column(fieldname="Время", column=time)
        text = f'Расписание пар\n\n```{table_r}```'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomorrow':
        wd = datetime.datetime.today().isoweekday()
        table.clear()
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            lesson = globals()[f'wday_{wdays.names(wd+1)[1]}_1'][0:5]
            room = globals()[f'wday_{wdays.names(wd+1)[1]}_1'][5]
        else:
            lesson = globals()[f'wday_{wdays.names(wd+1)[1]}_2'][0:5]
            room = globals()[f'wday_{wdays.names(wd+1)[1]}_2'][5]
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Пара", column=lesson)
        table.add_column(fieldname="Кабинет", column=room)
        if wd == 5 or wd == 6:
            text = f'Завтра: {wdays.names(wd+1)[0]}\n\nУдачных выходных!'
        else:
            text = f'Завтра: {wdays.names(wd+1)[0]}\n\n```{table}```\n\nЛ - лекция\nПЗ - практическое занятие\nЛАБ - лабораторное занятие'
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomain':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Главное меню',
        reply_markup=kbm, parse_mode='Markdown')
    elif call.data == 'building':
        set_state(call.from_user.id, 'find_class')
        print('hello from the other siiiiideeee')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отправьте номер аудитории:', reply_markup=kb_cancel_building, parse_mode='Markdown')



@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://dnevnikxhb.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', '8443')))