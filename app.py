# School Diary Robot by xhable
# v6, added a parser for university schedule (BSTU)
# Now you must put your bot's token into config vars. (they're getting here by os.environ())

from site_parser import get_schedule, get_groups, get_state, set_state, get_group, set_group
from prettytable import PrettyTable
from telebot import types, apihelper
from flask import Flask, request
from pymongo import MongoClient
from transliterate import translit
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
index = [i for i in range(1, 6)]

time = ['8:00-9:35', '9:45-11:20', '11:30-13:05', '13:20-14:55', '15:05-16:40']

ADMINS = [124361528]
bot = telebot.TeleBot(token, 'Markdown')


table.field_names = ['№', 'Пара', 'Кабинет']

table = PrettyTable()
table_r = PrettyTable()

def ru_en(text):
    """Функция транслитерации с русского на английский."""
    return translit(text, 'ru', reversed=True)

def en_ru(text):
    """Функция транслитерации с английского на русский."""
    return translit(text, 'ru', reversed=False)

@bot.message_handler(commands=["start"])
def start_handler(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        users.insert_one({
            'first_name': m.from_user.first_name,
            'last_name': m.from_user.last_name,
            'user_id': m.from_user.id,
            'username': m.from_user.username,
            'state': 'default',
            'group': 'О-20-ИВТ-1-по-Б'
        })
    else:
        group = get_group(m.from_user.id)
        bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Выбранная группа: {group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
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

@bot.message_handler(commands=["users_reset"])
def users_reset(m):
    if m.chat.id in ADMINS:
        for user in users.find():
            user_id = user['user_id']
            state = 'default'
            group = 'О-20-ИВТ-1-по-Б'
            set_state(user_id, state)
            set_group(user_id, group)
        bot.send_message(m.chat.id, f'Параметры пользователей сброшены!\n\nСостояние = {state}\nГруппа = {group}')

@bot.message_handler(commands=["users"])
def users_handler(m):
    if m.chat.id in ADMINS:
        text = '*Список пользователей бота:*\n\n'
        for user in users.find():
            first_name = user['first_name']
            last_name = user['last_name']
            user_id = user['user_id']
            group = user['group']
            if last_name != None:
                text += f'[{first_name} {last_name}](tg://user?id={user_id}) ◼ *Группа №{group}*\n'
            else:
                text += f'[{first_name}](tg://user?id={user_id}) ◼ *Группа №{group}*\n'
        bot.send_message(m.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=["broadcast"])
def broadcast(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        group = raw_text.split(' ', maxsplit=2)[1]
        text = raw_text.split(' ', maxsplit=2)[2]
        if group == 'all':
            text = f'🔔 *Сообщение для всех групп ИВТ!*\n' + text
            for user in users.find():
                user_id = user['user_id']
                bot.send_message(user_id, text, parse_mode='Markdown')
        else:
            text = f'🔔 *Сообщение для группы {group}!*\n' + text
            for user in users.find({'group': group}):
                user_id = user['user_id']
                bot.send_message(user_id, text, parse_mode='Markdown')

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

# Блок создания клавиатур для бота
kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(text='📅 Расписание по дням', callback_data='days'))
kbm.row(types.InlineKeyboardButton(text='⚡️ Сегодня', callback_data='today'), types.InlineKeyboardButton(text='⚡️ Завтра', callback_data='tomorrow'))
kbm.row(types.InlineKeyboardButton(text='🔔 Расписание пар', callback_data='rings'))
kbm.row(types.InlineKeyboardButton(text='🏠 Найти корпус по аудитории', callback_data='building'))
kbm.row(types.InlineKeyboardButton(text='🔂 Сменить номер группы', callback_data='change_group'))

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
kb_cancel_building.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))

#kb_group = types.InlineKeyboardMarkup()
#kb_group.row(types.InlineKeyboardButton(text='1️⃣', callback_data='group_1'), types.InlineKeyboardButton(text='2️⃣', callback_data='group_2'))
#kb_group.row(types.InlineKeyboardButton(text='🚫 Отмена', callback_data='cancel_find_class'))

# Хэндлер для текста
@bot.message_handler(content_types=["text"])
def anymess(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        bot.send_message(m.chat.id, 'Для начала работы с ботом выполните команду /start')
    elif users.find_one({'user_id': m.from_user.id}) != None and get_state(m.from_user.id) == 'default':
        group = get_group(m.from_user.id)
        bot.send_message(m.chat.id, text=f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа №{group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
    elif get_state(m.from_user.id) == 'find_class':
        if re.match(r'(\b[1-9][1-9]\b|\b[1-9]\b)', m.text):
            bot.send_photo(m.chat.id, photo=building_1, caption=f'Аудитория {m.text} находится в корпусе №1 _(Институтская, 16)_.', parse_mode='Markdown')
            bot.send_location(m.chat.id, latitude=53.305077, longitude=34.305080)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа №{group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'\b[1-9][0-9][0-9]\b', m.text):
            bot.send_photo(m.chat.id, photo=building_2, caption=f'Аудитория {m.text} находится в корпусе №2 _(бульвар 50 лет Октября, 7)_.', parse_mode='Markdown')
            bot.send_location(m.chat.id, latitude=53.304442, longitude=34.303849)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа №{group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)', m.text):
            bot.send_photo(m.chat.id, photo=building_3, caption=f'Аудитория {m.text} находится в корпусе №3 _(Харьковская, 8)_.', parse_mode='Markdown')
            bot.send_location(m.chat.id, latitude=53.304991, longitude=34.306688)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа №{group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        elif re.match(r'\bБ\d{3}\b', m.text):
            bot.send_photo(m.chat.id, photo=building_4, caption=f'Аудитория {m.text} находится в корпусе №4 _(Харьковская, 10Б)_.', parse_mode='Markdown')
            bot.send_location(m.chat.id, latitude=53.303513, longitude=34.305085)
            set_state(m.chat.id, 'default')
            group = get_group(m.from_user.id)
            bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\n*Сейчас выбрана группа №{group}.*\nВот главное меню:', reply_markup=kbm, parse_mode='Markdown')
        else:
            bot.send_message(m.chat.id, 'Данный номер аудитории некорректен. Повторите попытку или отмените действие:', reply_markup=kb_cancel_building)
    elif get_group(m.from_user.id) != 1 and get_group(m.from_user.id) != 2:
        set_group(m.from_user.id, 1)

# Хэндлер обработки действий кнопок
@bot.callback_query_handler(func=lambda call: True)
def button_func(call):
    if call.data == 'days':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите день недели:',
        reply_markup=kb_dn)
    elif call.data[:5] == 'wday_':
        group = get_group(call.from_user.id)
        weekday = call.data[5:]
        
        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            weeknum = '1'
        else:
            weeknum = '2'
        
        schedule = get_schedule(group, weekday, weeknum)

        for lesson in schedule:
            table.add_row(lesson)
        
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'*Выбрана группа №{group}*\nРасписание: {wdays.translate(weekday)}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*',
        reply_markup=kbb, parse_mode='Markdown')

        table.clear()
    elif call.data == 'today':
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
        
        if isoweekday == 6 or isoweekday == 7:
            text = f'Сегодня: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        else:
            text = f'*Выбрана группа №{group}*\nСегодня: {wdays.names(isoweekday)[0]}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*'

        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text, reply_markup=kbbb, parse_mode='Markdown')

        table.clear()
    elif call.data == 'rings':
        table_r.clear()
        table_r.add_column(fieldname="№", column=index)
        table_r.add_column(fieldname="Время", column=time)
        text = f'Расписание пар\n\n```{table_r}```'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomorrow':
        group = get_group(call.from_user.id)
        isoweekday = datetime.datetime.today().isoweekday() + 1
        weekday = wdays.names(isoweekday)[1]

        if datetime.datetime.today().isocalendar()[1] % 2 == 0:
            weeknum = '1'
        else:
            weeknum = '2'
        
        schedule = get_schedule(group, weekday, weeknum)

        for lesson in schedule:
            table.add_row(lesson)
        
        if isoweekday == 6 or isoweekday == 7:
            text = f'*Выбрана группа №{group}*\nЗавтра: {wdays.names(isoweekday)[0]}\n\nУдачных выходных!'
        else:
            text = f'*Выбрана группа №{group}*\nЗавтра: {wdays.names(isoweekday)[0]}\n\n```{table}```\n\n`[Л]` - *лекция*\n`[ПЗ]` - *практическое занятие*\n`[ЛАБ]` - *лабораторное занятие*'

        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='Markdown')

        table.clear()
    elif call.data == 'tomain':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа №{get_group(call.from_user.id)}.*\nВот главное меню:',
        reply_markup=kbm, parse_mode='Markdown')
    elif call.data == 'building':
        set_state(call.from_user.id, 'find_class')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отправьте номер аудитории:', reply_markup=kb_cancel_building, parse_mode='Markdown')
    elif call.data == 'cancel_find_class':
        set_state(call.from_user.id, 'default')
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа №{get_group(call.from_user.id)}.*\nВот главное меню:',
        reply_markup=kbm, parse_mode='Markdown')
    elif call.data == 'change_group':
        group_list = get_groups()
        kb_group = types.InlineKeyboardMarkup()

        for group in group_list:
            kb_group.row(types.InlineKeyboardButton(text=group, callback_data=ru_en(group)))

        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Выберите группу:',
        reply_markup=kb_group, parse_mode='Markdown')
    elif str(call.data).startswith('O-20'):
        group = en_ru(str(call.data))
        set_group(call.from_user.id, group)
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Привет, {call.from_user.first_name}!\n*Сейчас выбрана группа №{get_group(call.from_user.id)}.*\nВот главное меню:',
        reply_markup=kbm, parse_mode='Markdown')


# Установка Webhook для быстрого взаимодействия с ботом

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