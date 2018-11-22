import telebot
from telebot import types
from prettytable import PrettyTable
from flask import Flask, request
import datetime

wd = datetime.datetime.today().isoweekday()
token = '633625028:AAEgHBOPx7yBaNgM9GsAYgtR85K8Jshaoos'
bot = telebot.TeleBot(token)
table = PrettyTable()
server = Flask(__name__)

no = '-'
index = [1, 2, 3, 4, 5, 6, 7, 8]
monday_lessons = [no, 'Русский язык', 'Математика', 'География', 'Химия', 'Литература', 'История', 'Физкультура',
[no, 318, 219, 301, 309, 318, 229, 'б/з']]
tuesday_lessons = [no, 'Информатика', 'Обществознание', 'Иссл. деят.', 'Ин.язык', 'Математика', no, no,
[no, '202/204', 305, 219, '318/223', 219, no, no]]
wednesday_lessons = ['История', 'Литература', 'Ин.язык', 'Физика', 'Физкультура', 'Математика', no, no,
[229, 318, '318/223', 217, 'б/з', 219, no, no]]
thursday_lessons = [no, 'Биология', 'Литература', 'Химия', 'ОБЖ', 'Математика', 'Астрономия', no,
[no, 228, 318, 309, 303, 219, 217, no]]
friday_lessons = [no, 'Физика', 'Ин.язык', 'Информатика', 'Обществознание', 'Физкультура', 'Математика', no,
[no, 217, '229/223', '202/204', 305, 'б/з', 219, no]]

kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(text='Расписание на сегодня', callback_data='today'))
kbm.row(types.InlineKeyboardButton(text='Расписание по дням', callback_data='days'))

kb_dn = types.InlineKeyboardMarkup()
kb_dn.row(types.InlineKeyboardButton(text='Пн', callback_data='monday'),
types.InlineKeyboardButton(text='Вт', callback_data='tuesday'),
types.InlineKeyboardButton(text='Ср', callback_data='wednesday'))
kb_dn.row(types.InlineKeyboardButton(text='Чт', callback_data='thursday'),
types.InlineKeyboardButton(text='Пт', callback_data='friday'))
kb_dn.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))

kbb = types.InlineKeyboardMarkup()
kbb.row(types.InlineKeyboardButton(text='Назад', callback_data='days'))

kbbb = types.InlineKeyboardMarkup()
kbbb.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id,
    text='Главное меню',
    reply_markup=kbm)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'monday':
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=monday_lessons[0:8])
        table.add_column(fieldname="Кабинет", column=monday_lessons[8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
        table.clear()
    elif call.data == 'tuesday':
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=tuesday_lessons[0:8])
        table.add_column(fieldname="Кабинет", column=tuesday_lessons[8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
        table.clear()
    elif call.data == 'wednesday':
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=wednesday_lessons[0:8])
        table.add_column(fieldname="Кабинет", column=wednesday_lessons[8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
        table.clear()
    elif call.data == 'thursday':
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=thursday_lessons[0:8])
        table.add_column(fieldname="Кабинет", column=thursday_lessons[8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
        table.clear()
    elif call.data == 'friday':
        table.add_column(fieldname="№", column=index)
        table.add_column(fieldname="Урок", column=friday_lessons[0:8])
        table.add_column(fieldname="Кабинет", column=friday_lessons[8])
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'```{table}```',
        reply_markup=kbb, parse_mode='Markdown')
        table.clear()
    elif call.data == 'tomain':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Главное меню',
        reply_markup=kbm)
    elif call.data == 'days':
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Выберите день недели:',
        reply_markup=kb_dn)
    elif call.data == 'today':
        if wd == 1:
            wdt = 'понедельник'
            table.add_column(fieldname="№", column=index)
            table.add_column(fieldname="Урок", column=monday_lessons[0:8])
            table.add_column(fieldname="Кабинет", column=monday_lessons[8])
            text = f'Сегодня: {wdt}.\n\n```{table}```'
        elif wd == 2:
            wdt = 'вторник'
            table.add_column(fieldname="№", column=index)
            table.add_column(fieldname="Урок", column=tuesday_lessons[0:8])
            table.add_column(fieldname="Кабинет", column=tuesday_lessons[8])
            text = f'Сегодня: {wdt}.\n\n```{table}```'
        elif wd == 3:
            wdt = 'среда'
            table.add_column(fieldname="№", column=index)
            table.add_column(fieldname="Урок", column=wednesday_lessons[0:8])
            table.add_column(fieldname="Кабинет", column=wednesday_lessons[8])
            text = f'Сегодня: {wdt}.\n\n```{table}```'
        elif wd == 4:
            wdt = 'четверг'
            table.add_column(fieldname="№", column=index)
            table.add_column(fieldname="Урок", column=thursday_lessons[0:8])
            table.add_column(fieldname="Кабинет", column=thursday_lessons[8])
            text = f'Сегодня: {wdt}.\n\n```{table}```'
        elif wd == 5:
            wdt = 'пятница'
            table.add_column(fieldname="№", column=index)
            table.add_column(fieldname="Урок", column=friday_lessons[0:8])
            table.add_column(fieldname="Кабинет", column=friday_lessons[8])
            text = f'Сегодня: {wdt}.\n\n```{table}```'
        elif wd == 6:
            wdt = 'суббота'
            text = f'Сегодня: {wdt}.\n\nУдачных выходных!'
        elif wd == 7:
            wdt = 'воскресенье'
            text = f'Сегодня: {wdt}.\n\nУдачных выходных!'
        bot.edit_message_text(chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kbbb)
        table.clear()




@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://dnevnikxhb.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', '8443')))