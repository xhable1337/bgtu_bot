"""app/routers/admin.py

Роутер для команд и сообщений админов.
"""

from asyncio import sleep
from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from loguru import logger

from app.config import config
from app.filters import IsAdminFilter
from app.keyboards import kb_admin, kb_update_teachers
from app.utils.api_worker import APIWorker
from app.utils.db_worker import DBWorker
from app.utils.schedule_management import update_groups

# Создаём роутер
admin_router = Router()

# Применяем фильтр администратора ко всем хэндлерам в этом роутере
admin_router.message.filter(IsAdminFilter())

db = DBWorker(config.mongodb_uri)
api = APIWorker()


@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """### [`Command`] Команда /broadcast."""
    if message.text == "/broadcast":
        return await message.answer(
            "📨 /broadcast: Рассылка пользователям.\n"
            "<b>Использование:</b> <code>/broadcast &lt;group|all&gt; &lt;message&gt;</code>"
        )

    group, text = message.text.split(" ", maxsplit=2)[1:3]

    i = 1
    if group == "all":
        text = "🔔 <b>Сообщение для всех групп!</b>\n" + text
        for user in db._users.find():
            if i % 25 == 0:
                sleep(1)
            user_id = user["user_id"]
            try:
                await message.bot.send_message(user_id, text)
                i += 1
            except Exception as exc:
                logger.error(f"Exception caught while broadcasting to all: {exc}")
    elif group == "test":
        text = "🔔 <b>Тестовое сообщение!</b>\n" + text
        await message.answer(text)
    else:
        text = f"🔔 <b>Сообщение для группы {group}!</b>\n" + text
        # TODO: Вынести получение всех пользователей в отдельный метод
        for user in db._users.find({"group": group}):
            if i == 25:
                await sleep(1)
            user_id = user["user_id"]
            try:
                await message.bot.send_message(user_id, text)
                i += 1
            except Exception as exc:
                logger.error(
                    f"Exception caught while broadcasting to group {group}: {exc}"
                )


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """### [`Command`] Команда /admin."""
    settings = db._settings.find_one({})
    user = db.user(message.from_user.id)
    count = db._users.count_documents({})
    maintenance_state = "🟢 Включены" if settings["maintenance"] else "🔴 Выключены"
    await message.answer(
        text=f"Добро пожаловать в админ-панель, {escape(user.full_name)}.\n"
        f"<b>Количество пользователей: <u>{count}</u></b>\n"
        f"<b>Состояние тех.работ: <u>{maintenance_state}</u></b>\n"
        "Выберите пункт в меню для дальнейших действий:",
        reply_markup=kb_admin,
    )


@admin_router.message(Command("update_groups"))
async def cmd_update_groups(message: Message):
    """### [`Command`] Команда /update_groups."""
    if message.text == "/update_groups":
        return await message.answer(
            "🆙 /update_groups: Обновление расписания заданных групп.\n"
            "<b>Использование:</b> <code>/update_groups &lt;groups&gt;</code>"
        )

    # В aiogram 3 нет метода get_args(), используем обработку текста
    groups = message.text.replace("/update_groups", "").strip()
    text = "⚙ Запущено обновление расписания для указанных групп...\n\n"
    main_message = await message.answer(text)
    for group in groups.splitlines():
        schedule = api.schedule(group)
        db.add_schedule(schedule, replace=True)
        text += f"✔ {group}\n"
        await main_message.edit_text(text)

    await main_message.edit_text(text + "\n✅ Расписание успешно обновлено!")


@admin_router.message(Command("force_update"))
async def cmd_force_update(message: Message):
    """### [`Command`] Команда /force_update."""
    msg = await message.answer(
        text="⚙ Запущено обновление групп...\n\n"
        "Пожалуйста, ожидайте завершения. Это занимает некоторое время (обычно 1-2 минуты)."
    )

    # Обновление списка групп с помощью генератора
    async for updated_text in update_groups():
        await msg.edit_text(updated_text)

    prompt_text = (
        "Хотите ли вы обновить расписание всех групп? (может занять много времени)"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ Да", callback_data="force-update-yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="force-update-no"),
            ]
        ]
    )

    await message.answer(text=prompt_text, reply_markup=keyboard)


@admin_router.message(Command("update_teachers"))
async def cmd_update_teachers(message: Message):
    """### [`Command`] Команда /update_teachers."""
    teacher_list = api.teacher_list()
    processed_count = 0
    succeeded_count = 0

    text = (
        f"⚙ <b>Найдено преподавателей:</b> {len(teacher_list)}\n\n"
        f"♻️ <b>Обработано:</b> {processed_count}/{len(teacher_list)}\n"
        f"✅ <b>Без ошибок:</b> {succeeded_count}\n"
        f"❌ <b>С ошибкой:</b> {processed_count - succeeded_count}"
    )

    sent_message = await message.answer(text, reply_markup=kb_update_teachers)

    for teacher_name in teacher_list:
        teacher = api.teacher(teacher_name)

        if teacher:
            db.add_teacher(teacher, replace=True)
            succeeded_count += 1

        processed_count += 1

        text = (
            f"⚙ <b>Найдено преподавателей:</b> {len(teacher_list)}\n\n"
            f"♻️ <b>Обработано:</b> {processed_count}/{len(teacher_list)}\n"
            f"✅ <b>Без ошибок:</b> {succeeded_count}\n"
            f"❌ <b>С ошибкой:</b> {processed_count - succeeded_count}"
        )

        await sent_message.edit_text(text)
