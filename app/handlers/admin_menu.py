from contextlib import suppress

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
import datetime
# from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified

# TODO: Избавиться от wildcard import
from app.keyboards import *
from app.utils.db_worker import DBWorker
from app.utils.api_worker import APIWorker
from app.properties import MONGODB_URI

db = DBWorker(MONGODB_URI)
api = APIWorker()

async def cb_force_update(call: types.CallbackQuery):
    """### [`Callback`] Кнопки да/нет при обновлении расписания.
    """
    await call.answer()
    
    choice = str(call.data).split('-')[2]
    text = ''
    if choice == 'no':
        await call.message.edit_text('Хорошо, не обновляем расписание.')
    else:
        text = '⚙ Запущено обновление расписания...\n\n'
        msg = await call.bot.send_message(call.message.chat.id, text=text, parse_mode='HTML')
        msgid = msg.message_id

        for year in db.years():
            for faculty in db.faculties():
                text += f'{faculty["full"]} ({year} год): \n'
                groups = db.groups(
                    faculty=faculty["full"], 
                    year=str(year)
                )
                for group in groups:
                    schedule = api.schedule(group)
                    db.add_schedule(schedule)
                    text += f'✔ {group}\n'
                    
                text += '\n'
            
                await call.bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=msgid,
                    text=text,
                    parse_mode='HTML'
                )

            text = '⚙ Продолжаем обновлять расписание...\n\n'
            msg = await call.bot.send_message(call.message.chat.id, text=text, parse_mode='HTML')
            msgid = msg.message_id
            # year -= 1

        await msg.edit_text('✅ Расписание успешно обновлено!')


async def cb_user_list(call: types.CallbackQuery):
    """### [`Callback`] Кнопка получения списка пользователей.
    """
    count = db._users.count_documents({})
    text = f'<u>Список пользователей бота (всего {count}):</u>\n\n'
    block_count = 0
    await call.answer("Ожидайте загрузки из базы...")
    last_msg: types.Message
    
    for user in db._users.find():
        first_name = user['first_name']
        last_name = user['last_name']
        user_id = user['user_id']
        group = user['group']
        if last_name != None or last_name != "None":
            add = f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a> ◼ <b>Группа {group}</b>\n'
            if len(text + add) <= 4096:
                text += add
            else:
                if block_count == 0:
                    await call.message.edit_text(text=text)
                else:
                    last_msg = await call.bot.send_message(call.message.chat.id, text, parse_mode='HTML')
                    text = f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a> ◼ <b>Группа {group}</b>\n'
        else:
            if len(text + f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n') <= 4096:
                text += f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n'
            else:
                if block_count == 0:
                    await call.message.edit_text(text=text)
                else:
                    last_msg = await call.bot.send_message(
                        chat_id=call.message.chat.id, 
                        text=text
                    )
                    text = f'<a href="tg://user?id={user_id}">{first_name}</a> ◼ <b>Группа {group}</b>\n'

        block_count += 1
    

    if block_count == 0:
        await call.message.edit_reply_markup(
            reply_markup=kb_admin_back
        )
    else:
        await call.bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=last_msg.message_id,
            reply_markup=kb_admin_back
        )


async def cb_toadmin(call: types.CallbackQuery):
    """### [`Callback`] Кнопка возврата в админ-меню.
    """
    # TODO: вынести settings как отдельный метод DBWorker
    count = db._users.count_documents({})
    maintenance_state = '🟢 Включены' if db._settings.find_one({})['maintenance'] else '🔴 Выключены'
    await call.message.edit_text(
        text=f'Добро пожаловать в админ-панель, {call.from_user.first_name}.\n'
        f'<b>Количество пользователей: <u>{count}</u></b>\n'
        f'<b>Состояние тех.работ: <u>{maintenance_state}</u></b>\n'
        'Выберите пункт в меню для дальнейших действий:',
        reply_markup=kb_admin
    )


async def cb_toggle_maintenance(call: types.CallbackQuery):
    """### [`Callback`] Кнопка включения/выключения техработ.
    """
    # TODO: вынести settings как отдельный метод DBWorker
    new_state = False if db._settings.find_one({})['maintenance'] else True
    db._settings.update_one({}, {'$set': {'maintenance': new_state}})
    await cb_toadmin(call)


def register_handlers_admin_menu(dp: Dispatcher):
    dp.register_callback_query_handler(cb_force_update, Text(startswith='force-update-'))
    dp.register_callback_query_handler(cb_user_list, Text('user_list'))
    dp.register_callback_query_handler(cb_toadmin, Text('toadmin'))
    dp.register_callback_query_handler(cb_toggle_maintenance, Text('toggle_maintenance'))
    