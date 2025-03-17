"""app/handlers/common.py

Хэндлеры кнопок меню.
"""

import datetime
from html import escape

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Filter, Text
from loguru import logger

from app.keyboards import days_keyboard, kb_cancel, kb_notifications_days, kbbb, kbm
from app.properties import MONGODB_URI, week_is_odd
from app.utils import wdays
from app.utils.db_worker import DBWorker

# TODO: Избавиться от wd_name и wd_numbers, переместив в другую точку
from app.utils.text_generator import rings_table, schedule_text, wd_name, wd_numbers

db = DBWorker(MONGODB_URI)


class _Maintenance(Filter):
    # pylint: disable=arguments-differ
    # Hey, pylint, 2 == 2, isn't it? c:
    key = "is_maintenance"

    async def check(self, message: types.Message):
        settings = db.settings()

        return settings.maintenance and not message.from_user.id in settings.admins


async def cb_days(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание по дням»."""
    if week_is_odd():
        weektype = "[Н] - нечётная"
        buttons = ["[Н]", "Ч"]
    else:
        weektype = "[Ч] - чётная"
        buttons = ["Н", "[Ч]"]

    kb_dn = days_keyboard(buttons)

    await call.message.edit_text(
        text=f"Выберите неделю и день (сейчас идёт {weektype}):\n", reply_markup=kb_dn
    )

    await call.answer()


async def cb_rings(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание пар»."""
    await call.message.edit_text(text=rings_table(), reply_markup=kbbb)
    await call.answer()


async def cb_today(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание на сегодня»."""
    user = db.user(call.from_user.id)

    isoweekday = datetime.datetime.today().isoweekday()

    if week_is_odd():
        weektype = "odd"
    else:
        weektype = "even"

    # Расписание на день из БД
    if isoweekday != 7:
        schedule = db.schedule(user.group, wd_name[isoweekday][1], weektype)
    else:
        schedule = None

    # Сгенерированный текст
    text = schedule_text("today", isoweekday, user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


async def cb_tomorrow(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание на завтра»."""
    user = db.user(call.from_user.id)

    isoweekday = datetime.datetime.today().isoweekday() + 1

    _week_is_odd = week_is_odd()

    # Если завтра понедельник, неделя должна меняться
    if isoweekday == 8:
        # т.е. меняем условие чётности недели на обратное
        _week_is_odd = not _week_is_odd

    if _week_is_odd:
        weektype = "odd"
    else:
        weektype = "even"

    # Расписание на день из БД
    if isoweekday != 7:
        schedule = db.schedule(user.group, wd_name[isoweekday][1], weektype)
    else:
        schedule = None

    # Сгенерированный текст
    text = schedule_text("tomorrow", isoweekday, user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


async def cb_wday(call: types.CallbackQuery):
    """### [`Callback`] Кнопки выбора дня недели расписания."""
    user = db.user(call.from_user.id)

    # День недели
    weekday = call.data.split("_")[1]

    # Тип недели (odd - нечет, even - чёт)
    weektype = call.data.split("_")[2]

    # Номер дня недели
    isoweekday = wd_numbers[weekday]

    # Расписание на день из БД
    schedule = db.schedule(user.group, wd_name[isoweekday][1], weektype)

    # Сгенерированный текст
    text = schedule_text("other", isoweekday, user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


async def cb_tomain(call: types.CallbackQuery):
    """### [`Callback`] Кнопка возврата в главное меню."""
    user = db.user(call.from_user.id)
    user.state = "default"
    weekname = "нечётная" if week_is_odd() else "чётная"
    await call.message.edit_text(
        text=f"Привет, {escape(user.full_name)}!\n"
        f"<b>Твоя группа: {user.group}.</b>\n"
        f"<b>Сейчас идёт {weekname} неделя.</b>\n"
        "Вот главное меню:",
        reply_markup=kbm,
    )
    await call.answer()


async def cb_building(call: types.CallbackQuery):
    """### [`Callback`] Кнопка поиска аудитории."""
    user = db.user(call.from_user.id)
    user.state = "find_class"
    await call.message.edit_text(
        text="Отправьте номер аудитории:", reply_markup=kb_cancel
    )
    await call.answer()


async def cb_cancel(call: types.CallbackQuery):
    """### [`Callback`] Кнопка отмены поиска аудитории."""
    user = db.user(call.from_user.id)
    user.state = "default"
    weekname = "нечётная" if week_is_odd() else "чётная"
    await call.message.edit_text(
        text=f"Привет, {escape(user.full_name)}!\n"
        f"<b>Твоя группа: {user.group}.</b>\n"
        f"<b>Сейчас идёт {weekname} неделя.</b>\n"
        "Вот главное меню:",
        reply_markup=kbm,
    )
    await call.answer()


async def cb_change_faculty(call: types.CallbackQuery):
    """### [`Callback`] Кнопка смены факультета."""
    # Выбор факультета
    kb_faculty = types.InlineKeyboardMarkup()

    for faculty in db.faculties():
        kb_faculty.row(
            types.InlineKeyboardButton(
                text=faculty["full"], callback_data=f"f_{faculty['short']}"
            )
        )

    kb_faculty.row(types.InlineKeyboardButton(text="🚫 Отмена", callback_data="tomain"))

    await call.message.edit_text(
        text="Выберите факультет:",  # Выберите год поступления:
        reply_markup=kb_faculty,
    )

    await call.answer()


async def cb_f(call: types.CallbackQuery):
    """### [`Callback`] Кнопка смены факультета -> выбор года."""
    # Выбор года поступления
    faculty = str(call.data[2:])

    kb_years = types.InlineKeyboardMarkup()

    for year in db.years():
        callback_year = f"y_{year}_{faculty}"
        kb_years.row(
            types.InlineKeyboardButton(text=str(year), callback_data=callback_year)
        )

    kb_years.row(types.InlineKeyboardButton(text="🚫 Отмена", callback_data="tomain"))

    await call.message.edit_text(
        text="Выберите год поступления:",
        reply_markup=kb_years,
    )

    await call.answer()


async def cb_y(call: types.CallbackQuery):
    """### [`Callback`] Кнопка смены факультета -> выбор года -> выбор группы."""
    year = call.data.split("_")[1]
    faculty = call.data.split("_")[2]

    kb_group = types.InlineKeyboardMarkup()
    for _faculty in db.faculties():
        if _faculty["short"] == faculty:
            faculty = _faculty["full"]

    for group in db.groups(faculty, year):
        kb_group.row(types.InlineKeyboardButton(text=group, callback_data=f"g_{group}"))

    kb_group.row(types.InlineKeyboardButton(text="🚫 Отмена", callback_data="tomain"))

    await call.message.edit_text(text="Выберите группу:", reply_markup=kb_group)

    await call.answer()


async def cb_g(call: types.CallbackQuery):
    """### [`Callback`] Кнопки выбора/удаления группы."""
    user = db.user(call.from_user.id)
    group = str(call.data).split("g_")[1]
    if str(call.data).endswith("__del"):
        #! Группа удаляется из избранных
        group = group.split("__")[0]
        user = db.user(call.from_user.id)
        favorite_groups = user.favorite_groups
        favorite_groups.pop(favorite_groups.index(group))
        user.favorite_groups = favorite_groups

        await cb_tomain(call)

        await call.answer(f"❌ Группа {group} удалена из избранных!", show_alert=True)
    else:
        if user.state == "default":
            user.group = group
            await cb_tomain(call)

        elif user.state == "add_favorite":
            #! Группа добавляется в избранные
            favorite_groups = user.favorite_groups
            favorite_groups.append(call.data.split("g_")[1])
            user.favorite_groups = favorite_groups
            await cb_tomain(call)


async def cb_add_favorite(call: types.CallbackQuery):
    """### [`Callback`] Кнопка добавления группы в избранное."""
    user = db.user(call.from_user.id)
    user.state = "add_favorite"
    kb_faculty = types.InlineKeyboardMarkup()

    for faculty in db.faculties():
        kb_faculty.row(
            types.InlineKeyboardButton(
                text=faculty["full"], callback_data=f"f_{faculty['short']}"
            )
        )

    kb_faculty.row(types.InlineKeyboardButton(text="🚫 Отмена", callback_data="tomain"))

    await call.message.edit_text(text="Выберите факультет:", reply_markup=kb_faculty)

    await call.answer()


async def cb_notifications(call: types.CallbackQuery):
    """### [`Callback`] Кнопка управления уведомлениями."""
    user = db.user(call.from_user.id)
    notification_time = user.notification_time

    notification_is_empty = notification_time is None or notification_time == {}

    if notification_is_empty:
        await call.message.edit_text(
            text="Уведомления с расписанием отсутствуют.\n"
            "Выберите день недели для установки времени автоматической отправки расписания:",
            reply_markup=kb_notifications_days,
        )
    else:
        text = "Дни недели, по которым вы получаете уведомления с расписанием: \n\n"
        for day in notification_time:
            if notification_time[day] != "":
                day_ru = wdays.translate(day)
                text += f"{day_ru.capitalize()}: {notification_time[day]}\n"

        text += (
            "\nХотите изменить время, добавить или удалить напоминания? Выберите день:"
        )

        await call.message.edit_text(text=text, reply_markup=kb_notifications_days)

    await call.answer()


async def cb_notify(call: types.CallbackQuery):
    """### [`Callback`] Кнопка управления уведомлением на конкретный день."""
    user = db.user(call.from_user.id)
    weekday = str(call.data).split("_")[1]

    notification_is_empty = (
        user.notification_time is None
        or user.notification_time == {}
        or user.notification_time.get(weekday) is None
        or user.notification_time.get(weekday) == ""
    )

    if notification_is_empty:
        user.state = f"add_notification_{weekday}"
        text = (
            f"Добавление напоминания ({wdays.translate(weekday)})\n\n"
            "Введите время, в которое вы хотите получать расписание:\n"
            "————————————————————\n"
            "Если введённое время в диапазоне от 00:00 до 12:59, "
            "то бот отправит расписание на сегодня.\n"
            "Если же введённое время в диапазоне от 13:00 до 23:59, "
            "то расписание на завтра."
        )
        reply_markup = kb_cancel
    else:
        text = f"Изменение напоминания ({wdays.translate(weekday)}):"
        kb_notifications = types.InlineKeyboardMarkup(row_width=1)
        kb_notifications.add(
            types.InlineKeyboardButton(
                text="❌ Удалить", callback_data=f"del_notification_{weekday}"
            ),
            types.InlineKeyboardButton(
                text="✍ Изменить", callback_data=f"edit_notification_{weekday}"
            ),
            types.InlineKeyboardButton(
                text="🔄 В главное меню", callback_data="tomain"
            ),
        )
        reply_markup = kb_notifications

    await call.message.edit_text(
        text=text,
        reply_markup=reply_markup,
    )

    await call.answer()


async def cb_del_notification(call: types.CallbackQuery):
    """### [`Callback`] Кнопка удаления уведомления на конкретный день."""
    user = db.user(call.from_user.id)
    weekday = str(call.data).split("_")[2]

    user_time = user.notification_time.get(weekday)

    # Структура хранения списка рассылки
    # {
    #     'monday': {
    #         '07:00': [id1, id2, ...],
    #         '08:00': [id3, id4, ...]
    #     },
    #     'tuesday': {...},
    #     ...
    # }

    sample_notification_time = {
        "monday": "",
        "tuesday": "",
        "wednesday": "",
        "thursday": "",
        "friday": "",
        "saturday": "",
        "sunday": "",
    }

    # * Удаляем из общего списка рассылки сообщения для текущего юзера и дня недели
    schedule_list: dict = db._scheduled_msg.find_one({"id": 1})
    if len(schedule_list[weekday][user_time]) == 1:
        schedule_list[weekday].pop(user_time)
    else:
        user_index = schedule_list[weekday][user_time].index(user.user_id)
        schedule_list[weekday][user_time].pop(user_index)

    # TODO: сделать метод для вызова вместо обращения к полю с коллекцией
    db._scheduled_msg.update_one({"id": 1}, {"$set": schedule_list})

    # TODO: заменить обнуление на удаление поля (сейвим место в БД)
    notification_time = user.notification_time
    notification_time[weekday] = ""

    # REVIEW - частичный фикс, замена на пустой объект
    if notification_time == sample_notification_time:
        notification_time = {}

    user.notification_time = notification_time

    await call.message.edit_text(
        text=f"Уведомление ({wdays.translate(weekday)}) выключено.",
        reply_markup=kbbb,
    )

    await call.answer()


async def cb_edit_notification(call: types.CallbackQuery):
    """### [`Callback`] Кнопка изменения уведомления на конкретный день."""
    user = db.user(call.from_user.id)
    weekday = str(call.data).split("_")[2]
    notification_time = user.notification_time[weekday]

    text = (
        f"Сейчас вы получаете расписание ({wdays.translate(weekday)}) в {notification_time}.\n"
        "Введите время, в которое вы хотите получать расписание:\n"
        "————————————————————\n"
        "Если введённое время в диапазоне от 00:00 до 12:59, "
        "то бот отправит расписание на сегодня.\n"
        "Если же введённое время в диапазоне от 13:00 до 23:59, "
        "то расписание на завтра."
    )

    user.state = f"add_notification_{weekday}"

    await call.message.edit_text(text=text, reply_markup=kb_cancel)

    await call.answer()


async def dummycb_maintenance(call: types.CallbackQuery):
    """### [`DummyCallback`] Обработчик на время техработ."""
    await call.answer(
        text="⚡ Бот находится на тех.работах. Возвращайтесь позже.", show_alert=True
    )


async def cb_favorite_groups(call: types.CallbackQuery):
    """### [`Callback`] Кнопка "Избранные группы"."""
    kb_favorite = types.InlineKeyboardMarkup()

    user = db.user(call.from_user.id)
    fav_count = 0

    if user.favorite_groups is not None:
        #! Пользователь уже заходил в раздел избранных групп
        for group in user.favorite_groups:
            kb_favorite.row(
                types.InlineKeyboardButton(text=group, callback_data=f"g_{group}"),
                types.InlineKeyboardButton(text="❌", callback_data=f"g_{group}__del"),
            )
            fav_count += 1

        # Оставшиеся слоты для избранных групп
        space_left = 5 - fav_count

        for _ in range(space_left):
            kb_favorite.row(
                types.InlineKeyboardButton(
                    text="➕ Добавить", callback_data="add_favorite"
                )
            )
    else:
        #! Пользователь первый раз зашёл в раздел избранных групп
        user.favorite_groups = []

        for _ in range(5):
            kb_favorite.row(
                types.InlineKeyboardButton(
                    text="➕ Добавить", callback_data="add_favorite"
                )
            )

    kb_favorite.row(
        types.InlineKeyboardButton(text="🔄 В главное меню", callback_data="tomain")
    )

    await call.message.edit_text(
        text="Твой список избранных групп:", reply_markup=kb_favorite
    )

    await call.answer()


def register_handlers_menu(dp: Dispatcher):
    """Регистрирует хэндлеры кнопок меню.

    Аргументы:
        dp (aiogram.types.Dispatcher): диспетчер aiogram
    """
    # pylint: disable=invalid-name
    # dp - рекомендованное короткое имя для диспетчера

    dp.bind_filter(_Maintenance)
    dp.register_callback_query_handler(dummycb_maintenance, _Maintenance())
    dp.register_callback_query_handler(cb_days, Text("days"))
    dp.register_callback_query_handler(cb_today, Text("today"))
    dp.register_callback_query_handler(cb_tomorrow, Text("tomorrow"))
    dp.register_callback_query_handler(cb_wday, Text(startswith="wday_"))
    dp.register_callback_query_handler(cb_rings, Text("rings"))
    dp.register_callback_query_handler(cb_tomain, Text("tomain"))
    dp.register_callback_query_handler(cb_building, Text("building"))
    dp.register_callback_query_handler(cb_cancel, Text("cancel"))
    dp.register_callback_query_handler(cb_change_faculty, Text("change_faculty"))
    dp.register_callback_query_handler(cb_f, Text(startswith="f_"))
    dp.register_callback_query_handler(cb_g, Text(startswith="g_"))
    dp.register_callback_query_handler(cb_y, Text(startswith="y_"))
    dp.register_callback_query_handler(cb_add_favorite, Text("add_favorite"))
    dp.register_callback_query_handler(cb_notifications, Text("notifications"))
    dp.register_callback_query_handler(cb_notify, Text(startswith="notify_"))
    dp.register_callback_query_handler(
        cb_del_notification, Text(startswith="del_notification_")
    )
    dp.register_callback_query_handler(
        cb_edit_notification, Text(startswith="edit_notification_")
    )
    dp.register_callback_query_handler(
        cb_favorite_groups, Text(startswith="favorite_groups")
    )
