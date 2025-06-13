"""app/routers/admin_menu.py

Роутер для кнопок админ-меню.
"""

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.filters import IsAdminFilter
from app.keyboards import kb_admin, kb_admin_back
from app.properties import MONGODB_URI
from app.utils.api_worker import APIWorker
from app.utils.db_worker import DBWorker
from app.utils.schedule_management import update_schedule

# Создаём роутер
admin_menu_router = Router()

# Применяем фильтр администратора ко всем хэндлерам в этом роутере
admin_menu_router.callback_query.filter(IsAdminFilter())

db = DBWorker(MONGODB_URI)
api = APIWorker()


@admin_menu_router.callback_query(F.data.startswith("force-update-"))
async def cb_force_update(call: CallbackQuery):
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


@admin_menu_router.callback_query(F.data == "user_list")
async def cb_user_list(call: CallbackQuery):
    """### [`Callback`] Кнопка получения списка пользователей."""
    count = db._users.count_documents({})
    text = f"<u>Список пользователей бота (всего {count}):</u>\n\n"
    block_count = 0
    await call.answer("Ожидайте загрузки из базы...")
    last_msg: CallbackQuery.message

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


@admin_menu_router.callback_query(F.data == "toadmin")
async def cb_toadmin(call: CallbackQuery):
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


@admin_menu_router.callback_query(F.data == "toggle_maintenance")
async def cb_toggle_maintenance(call: CallbackQuery):
    """### [`Callback`] Кнопка включения/выключения техработ."""
    # TODO: вынести settings как отдельный метод DBWorker
    settings = db.settings()
    settings.maintenance = not settings.maintenance
    await cb_toadmin(call)
