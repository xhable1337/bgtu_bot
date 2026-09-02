"""app/routers/common.py

Роутер для команд и сообщений обычных пользователей.
"""

import re
from html import escape

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from loguru import logger

from app.config import config
from app.keyboards import kb_cancel, kbbb, kbm
from app.models import User
from app.states import AddNotification, FindClass
from app.utils.db_worker import DBWorker
from app.utils.wdays import week_is_odd

# Создаём роутер
common_router = Router()

db = DBWorker(config.mongodb_uri)


async def _get_user_or_reply(message: Message):
    """Возвращает пользователя либо отправляет подсказку, если он недоступен.

    Отправляет ответ и возвращает `None`, если пользователя нет в базе или
    бот находится на тех.работах.
    """
    user = db.user(message.from_user.id)

    if not user:
        await message.answer(
            "Для начала работы с ботом выполните команду /start."
        )
        return None

    settings = db.settings()
    if settings.maintenance and user.user_id not in settings.admins:
        await message.reply(
            "⚡ Бот находится на тех.работах. Возвращайтесь позже."
        )
        return None

    return user


@common_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """### [`Command`] Команда /start."""
    await message.bot.send_chat_action(message.from_user.id, ChatAction.TYPING)
    await state.clear()

    user = db.user(message.from_user.id)

    if not user:
        # TODO: Перейти на группу undefined при первом входе в бота
        user = User(
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            user_id=message.from_user.id,
            username=message.from_user.username,
            group="О-20-ИВТ-1-по-Б",
            favorite_groups=[],
        )
        db.add_user(user, replace=False)

        kb_faculty = InlineKeyboardMarkup(inline_keyboard=[])
        for faculty in db.faculties():
            kb_faculty.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=faculty["full"], callback_data=f"f_{faculty['short']}"
                    )
                ]
            )

        user = db.user(message.from_user.id)

        await message.answer(
            f"Привет, {escape(user.full_name)}!\n"
            "<b>Для начала работы с ботом выбери свою группу "
            "(впоследствии выбор можно изменить):</b>",
            reply_markup=kb_faculty,
        )

        logger.info(f"New user! ID: {user.user_id}")
    else:
        db.add_user(user.obj(), replace=True)

        btn = MenuButtonWebApp(
            text="Бот v2", web_app=WebAppInfo(url="https://tgweb.darx.zip")
        )
        await message.bot.set_chat_menu_button(message.chat.id, btn)

        weekname = "нечётная" if week_is_odd() else "чётная"
        await message.answer(
            f"Привет, {escape(user.full_name)}!\n"
            f"<b>Твоя группа: {user.group}.</b>\n"
            f"<b>Сейчас идёт {weekname} неделя.</b>\n"
            "Вот главное меню:",
            reply_markup=kbm,
        )


@common_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """### [`Command`] Команда /cancel."""
    await state.clear()
    await message.answer(
        "Действие отменено. Для дальнейшей работы нажмите /start.",
        reply_markup=ReplyKeyboardRemove(),
    )


@common_router.message(Command("support"))
async def cmd_support(message: Message):
    """### [`Command`] Команда /support."""
    await message.answer(
        "💁‍♂️ По всем вопросам, предложениям, пожеланиям и проблемам "
        "обращаться сюда: <b>@BGTU_Feedback_bot</b>."
    )


@common_router.message(Command("dev"))
async def cmd_dev(message: Message):
    """### [`Command`] Команда /dev."""
    await message.answer(
        "👨‍💻 <b>Разработчик бота:</b> @xhable.\n"
        "💻 <b>Использованные технологии:</b>:\n"
        "└ 🤖 <b>Бот:</b> "
        '<a href="https://www.python.org">Python 3</a> + '
        '<a href="https://github.com/aiogram/aiogram">aiogram</a>\n'
        "└ 🌐 <b>Веб-приложение:</b> "
        '<a href="https://nodejs.org/en/">Node.js</a> + '
        '<a href="https://reactjs.org">React</a>\n'
        "🔡 <b>Исходный код:</b> "
        "coming soon...",
        disable_web_page_preview=True,
    )


@common_router.message(F.text.lower() == "отмена")
async def msg_cancel_text(message: Message, state: FSMContext):
    """### [`Message`] Текстовое сообщение 'отмена'."""
    await cmd_cancel(message, state)


@common_router.message(StateFilter(None))
async def msg_default(message: Message, state: FSMContext):
    """### [`Message`] Обычное сообщение без активного состояния — показываем меню."""
    if await _get_user_or_reply(message) is None:
        return

    await cmd_start(message, state)


@common_router.message(FindClass.choosing_number)
async def msg_find_class(message: Message, state: FSMContext):
    """### [`Message`] Ввод номера аудитории."""
    if await _get_user_or_reply(message) is None:
        return

    building_1 = "https://telegra.ph/file/49ec8634ab340fa384787.png"
    regex_1 = re.compile(r"(\b[1-9][1-9]\b|\b[1-9]\b)")

    building_2 = "https://telegra.ph/file/7d04458ac4230fd12f064.png"
    regex_2 = re.compile(r"\b[1-9][0-9][0-9]\b")

    building_3 = "https://telegra.ph/file/6b801965b5771830b67f0.png"
    regex_3 = re.compile(
        r"(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)"
    )

    building_4 = "https://telegra.ph/file/f79c20324a0ba6cd88711.png"
    regex_4 = re.compile(r"\bБ\d{3}\b")

    text = message.text or ""

    if re.match(regex_1, text):
        #! Найдена аудитория в корпусе №1
        await message.answer_photo(
            photo=building_1,
            caption=f"Аудитория {text} находится в корпусе "
            "№1 <i>(Институтская, 16)</i>.",
        )

        await message.answer_location(latitude=53.305077, longitude=34.305080)

        await cmd_start(message, state)
    elif re.match(regex_2, text):
        #! Найдена аудитория в корпусе №2
        await message.answer_photo(
            photo=building_2,
            caption=f"Аудитория {text} находится в корпусе "
            "№2 <i>(бульвар 50 лет Октября, 7)</i>.",
        )

        await message.answer_location(latitude=53.304442, longitude=34.303849)

        await cmd_start(message, state)
    elif re.match(regex_3, text):
        await message.answer_photo(
            photo=building_3,
            caption=f"Аудитория {text} находится в корпусе "
            "№3 <i>(Харьковская, 8)</i>.",
        )

        await message.answer_location(latitude=53.304991, longitude=34.306688)

        await cmd_start(message, state)
    elif re.match(regex_4, text):
        await message.answer_photo(
            photo=building_4,
            caption=f"Аудитория {text} находится в корпусе "
            "№4 <i>(Харьковская, 10Б)</i>.",
        )

        await message.answer_location(latitude=53.303513, longitude=34.305085)

        await cmd_start(message, state)
    else:
        await message.answer(
            "Данный номер аудитории некорректен. Повторите попытку или отмените действие:",
            reply_markup=kb_cancel,
        )


@common_router.message(AddNotification.choosing_time)
async def msg_add_notification(message: Message, state: FSMContext):
    """### [`Message`] Ввод времени для уведомления."""
    user = await _get_user_or_reply(message)
    if user is None:
        return

    data = await state.get_data()
    weekday = data["weekday"]

    time_regex = re.compile(
        r"^2[0-3]:[0-5][0-9]$|^[0]{1,2}:[0-5][0-9]$|^1[0-9]:[0-5][0-9]$|^0?[1-9]:[0-5][0-9]$"
    )

    if not re.match(time_regex, message.text or ""):
        return await message.answer(
            "Вы ввели некорректное время. Повторите попытку или отмените действие:",
            reply_markup=kb_cancel,
        )

    # Валидация времени в формат ЧЧ:ММ
    if re.match(r"\b[0-9]:[0-5][0-9]\b", message.text or ""):
        notification_time = f"0{message.text}"
    else:
        notification_time = message.text

    # TODO: Переделать инициализацию всеми днями недели (сейвим место в БД)
    # Инициализация словаря при отсутствии
    user_time_dict = user.notification_time
    if user_time_dict is None or user_time_dict == {}:
        user_time_dict = {
            "monday": "",
            "tuesday": "",
            "wednesday": "",
            "thursday": "",
            "friday": "",
            "saturday": "",
            "sunday": "",
        }

    scheduled_msg = db._scheduled_msg.find_one({"id": 1})

    #! Если уже было установлено уведомление, нужно сначала удалить его
    if user_time_dict[weekday] != "":
        user_time = user_time_dict[weekday]
        user_index = scheduled_msg[weekday][user_time].index(user.user_id)
        scheduled_msg[weekday][user_time].pop(user_index)

    user_time_dict[weekday] = notification_time

    #! Добавление записи в общий список рассылки
    if scheduled_msg[weekday].get(notification_time) is None:
        scheduled_msg[weekday][notification_time] = [user.user_id]
    else:
        scheduled_msg[weekday][notification_time].append(user.user_id)

    #! Применение апдейтов к базе
    user.notification_time = user_time_dict
    db._scheduled_msg.update_one({"id": 1}, {"$set": scheduled_msg})

    await message.answer(
        f"⏰ Уведомление на {message.text} установлено!", reply_markup=kbbb
    )

    await state.clear()
