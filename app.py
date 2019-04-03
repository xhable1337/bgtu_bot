# School Diary Robot by xhable
# v2.0, fully refreshed code
import telebot
from prettytable import PrettyTable
from telebot import types, apihelper
import datetime
import wdays
from flask import Flask, request
import os

server = Flask(__name__)
token = '633625028:AAEgHBOPx7yBaNgM9GsAYgtR85K8Jshaoos'
no = '-'
index = [1, 2, 3, 4, 5, 6, 7, 8]
wday_monday = [no, 'Русский язык', 'Математика', 'География', 'Химия', 'Литература', 'История', 'Физкультура', [no, 318, 219, 301, 309, 318, 229, 'б/з']]
wday_tuesday = [no, 'Информатика', 'Обществознание', 'Иссл. деят.', 'Ин.язык', 'Математика', '[ЭЛ] Рус.яз.', '[ЭЛ] Геогр.', [no, '202/204', 305, 219, '318/223', 219, 318, 301]]
wday_wednesday = [no, 'Литература', 'Ин.язык', 'Физика', 'Физкультура', 'Математика', 'История', no, [no, 318, '318/223', 217, 'б/з', 219, 229, no]]
wday_thursday = [no, 'Биология', 'Литература', 'Химия', 'ОБЖ', 'Математика', 'Астрономия', no, [no, 228, 318, 309, 303, 219, 217, no]]
wday_friday = [no, 'Физика', 'Ин.язык', 'Информатика', 'Обществознание', 'Физкультура', 'Математика', no,[no, 217, '229/223', '202/204', 305, 'б/з', 219, no]]

bot = telebot.TeleBot(token)
table = PrettyTable()
wd = datetime.datetime.today().isoweekday()


kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(text='Расписание на сегодня', callback_data='today'))
kbm.row(types.InlineKeyboardButton(text='Расписание на завтра', callback_data='tomorrow'))
kbm.row(types.InlineKeyboardButton(text='Расписание по дням', callback_data='days'))

kb_dn = types.InlineKeyboardMarkup()
kb_dn.row(types.InlineKeyboardButton(text='Пн', callback_data='wday_monday'),
types.InlineKeyboardButton(text='Вт', callback_data='wday_tuesday'),
types.InlineKeyboardButton(text='Ср', callback_data='wday_wednesday'))
kb_dn.row(types.InlineKeyboardButton(text='Чт', callback_data='wday_thursday'),
types.InlineKeyboardButton(text='Пт', callback_data='wday_friday'))
kb_dn.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))

kbb = types.InlineKeyboardMarkup()
kbb.row(types.InlineKeyboardButton(text='Назад', callback_data='days'))

kbbb = types.InlineKeyboardMarkup()
kbbb.row(types.InlineKeyboardButton(text='В главное меню', callback_data='tomain'))

@bot.message_handler(content_types=["text"])
def anymess(m):
    bot.send_message(m.chat.id, text='Главное меню', reply_markup=kbm)

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
    elif call.data == 'tomorrow':
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