# School Diary Robot by xhable
# v2.5, added MongoDB user database to provide some broadcasts
# Now you must put your bot's token into config vars. (they're getting here by os.environ())
import telebot
from prettytable import PrettyTable
from telebot import types, apihelper
import datetime
import wdays
from flask import Flask, request
import os
from pymongo import MongoClient

MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI)
db = client.diary_db
users = db.users

server = Flask(__name__)
token = os.environ['token']
no = '-'
index = [1, 2, 3, 4, 5, 6, 7, 8]
wday_monday = [no, 'История', 'Обществознание', 'Информатика', 'Математика', 'Физкультура', no, no, [no, 229, 305, '202/204', 219, 'б/з', no, no]]
wday_tuesday = [no, 'Физика', 'Биология', 'Математика', 'Рус.язык', 'Ин.язык', 'Литература', 'Физ-ра', [no, 217, 226, 219, 318, '311/223', 318, 'б/з']]
wday_wednesday = ['Обществознание', 'Химия', 'Математика', 'История', 'Информатика', 'Ин.язык', no, no, [305, 314, 219, 229, '202/204', '311/223', no, no]]
wday_thursday = [no, no, 'Математика', 'География', 'Физика', 'Литература', 'ОБЖ', 'Физкультура', [no, no, 219, 301, 217, 318, 303, 'б/з']]
wday_friday = ['Ин.язык', 'Математика', 'Литература', 'Химия', 'История', 'Астрономия', no, no, ['311/223', 219, 318, 309, 221, 217, no, no]]

time_monday = ['8:00-8:40', '8:50-9:30', '9:50-10:30', '10:50-11:30', '11:40-12:20', '12:30-13:10', '13:20-14:00', '14:10-14:50']
time_others = ['8:00-8:45', '8:55-9:40', '10:00-10:45', '11:05-11:50', '12:00-12:45', '12:55-13:40', '13:50-14:30', '14:40-15:20']

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
        })
    else:
        bot.send_message(m.chat.id, f'Привет, {m.from_user.first_name}!\nВот главное меню:', reply_markup=kbm)

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
        text += f'[{first_name} {last_name}](tg://user?id={user_id})\n'
    bot.send_message(m.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=["broadcast"])
def broadcast(m):
    if m.chat.id in ADMINS:
        raw_text = str(m.text)
        text = raw_text.split(' ', maxsplit=1)[1]
        for user in users.find():
            bot.send_message(user, text)

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
kbm.row(types.InlineKeyboardButton(text='🔔 Расписание звонков', callback_data='rings'))

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

@bot.message_handler(content_types=["text"])
def anymess(m):
    if users.find_one({'user_id': m.from_user.id}) == None:
        bot.send_message(m.chat.id, 'Для начала работы с ботом выполните команду /start')
    else:
        bot.send_message(m.chat.id, text='Главное меню:', reply_markup=kbm)

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
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=globals()[cdata][0:8])
        table.add_column(fieldname="Кабинет", column=globals()[cdata][8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Расписание: {wdays.translate(cdata[5:])}\n\n```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
    elif call.data == 'today':
        wd = datetime.datetime.today().isoweekday()
        table.clear()
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=globals()['wday_'+wdays.names(wd)[1]][0:8])
        table.add_column(fieldname="Кабинет", column=globals()['wday_'+wdays.names(wd)[1]][8])
        if wd == 6 or wd == 7:
            text = f'Сегодня: {wdays.names(wd)[0]}\n\nУдачных выходных!'
        else:
            text = f'Сегодня: {wdays.names(wd)[0]}\n\n```{table}```'
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'rings':
    	text = 'Выберите день недели:'
    	bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kb_r, parse_mode='Markdown')
    elif call.data == 'r_monday':
    	table_r.clear()
    	table_r.add_column(fieldname="№", column=index)
    	table_r.add_column(fieldname="Время", column=time_monday)
    	bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Звонки на понедельник\n\n```{table_r}```',
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'r_others':
        table_r.clear()
        table_r.add_column(fieldname="№", column=index)
        table_r.add_column(fieldname="Время", column=time_others)
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Звонки на вт-пт\n\n```{table_r}```',
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomorrow':
        wd = datetime.datetime.today().isoweekday()
        table.clear()
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=globals()['wday_'+wdays.names(wd+1)[1]][0:8])
        table.add_column(fieldname="Кабинет", column=globals()['wday_'+wdays.names(wd+1)[1]][8])
        if wd == 5 or wd == 6:
            text = f'Завтра: {wdays.names(wd+1)[0]}\n\nУдачных выходных!'
        else:
            text = f'Завтра: {wdays.names(wd+1)[0]}\n\n```{table}```'
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb, parse_mode='Markdown')
    elif call.data == 'tomain':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Главное меню',
        reply_markup=kbm, parse_mode='Markdown')



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