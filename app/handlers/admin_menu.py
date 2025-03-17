"""app/handlers/admin_menu.py

Хэндлеры кнопок админ-меню.
"""

from html import escape

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text

from app.keyboards import kb_admin, kb_admin_back
from app.properties import MONGODB_URI
from app.utils.api_worker import APIWorker
from app.utils.db_worker import DBWorker
from app.utils.schedule_management import update_schedule

db = DBWorker(MONGODB_URI)
api = APIWorker()


async def cb_force_update(call: types.CallbackQuery):
    """### [`Callback`] Кнопки да/нет при обновлении расписания."""
    await call.answer()

    choice = str(call.data).split("-")[2]
    text = ""
    if choice == "no":
        await call.message.edit_text("Хорошо, не обновляем расписание.")
    else:
        text = "⚙ Запущено обновление расписания...\n\n"

        msg = await call.bot.send_message(
            call.message.chat.id, text=text, parse_mode="HTML"
        )

        # Обновление расписания с помощью генератора
        async for updated_text in update_schedule():
            await msg.edit_text(updated_text)

        await call.message.answer("✅ Расписание успешно обновлено!")


async def cb_user_list(call: types.CallbackQuery):
    """### [`Callback`] Кнопка получения списка пользователей."""
    count = db._users.count_documents({})
    text = f"<u>Список пользователей бота (всего {count}):</u>\n\n"
    block_count = 0
    await call.answer("Ожидайте загрузки из базы...")
    last_msg: types.Message

    for user in db._users.find():
        first_name = user["first_name"]
        last_name = user["last_name"]
        user_id = user["user_id"]
        group = user["group"]
        if last_name:
            full_name = f"{first_name} {last_name}"
        else:
            full_name = first_name

        add = (
            f'<a href="tg://user?id={user_id}">{full_name}</a>◼ <b>Группа {group}</b>\n'
        )
        if len(text + add) <= 4096:
            text += add
        else:
            if block_count == 0:
                await call.message.edit_text(text=text)
            else:
                last_msg = await call.bot.send_message(call.message.chat.id, text)
                text = (
                    f'<a href="tg://user?id={user_id}">{first_name} {last_name}</a>'
                    f"◼ <b>Группа {group}</b>\n"
                )

        block_count += 1

    if block_count == 0:
        await call.message.edit_reply_markup(reply_markup=kb_admin_back)
    else:
        await call.bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=last_msg.message_id,
            reply_markup=kb_admin_back,
        )


async def cb_toadmin(call: types.CallbackQuery):
    """### [`Callback`] Кнопка возврата в админ-меню."""
    m_s = db.settings().maintenance  # maintenance_state, короткое название
    count = db._users.count_documents({})
    maintenance_state = "🟢 Включены" if m_s else "🔴 Выключены"
    await call.message.edit_text(
        text=f"Добро пожаловать в админ-панель, {escape(call.from_user.first_name)}.\n"
        f"<b>Количество пользователей: <u>{count}</u></b>\n"
        f"<b>Состояние тех.работ: <u>{maintenance_state}</u></b>\n"
        "Выберите пункт в меню для дальнейших действий:",
        reply_markup=kb_admin,
    )


async def cb_toggle_maintenance(call: types.CallbackQuery):
    """### [`Callback`] Кнопка включения/выключения техработ."""
    # TODO: вынести settings как отдельный метод DBWorker
    settings = db.settings()
    settings.maintenance = not settings.maintenance
    await cb_toadmin(call)


def register_handlers_admin_menu(dp: Dispatcher):
    """Регистрирует хэндлеры кнопок админ-меню.

    Аргументы:
        dp (aiogram.types.Dispatcher): диспетчер aiogram
    """
    # pylint: disable=invalid-name
    # dp - рекомендованное короткое имя для диспетчера
    dp.register_callback_query_handler(
        cb_force_update, Text(startswith="force-update-")
    )
    dp.register_callback_query_handler(cb_user_list, Text("user_list"))
    dp.register_callback_query_handler(cb_toadmin, Text("toadmin"))
    dp.register_callback_query_handler(
        cb_toggle_maintenance, Text("toggle_maintenance")
    )
