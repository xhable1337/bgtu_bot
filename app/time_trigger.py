"""time_trigger.py

Этот модуль представляет собой шедулер для запуска
отложенных задач или задач по расписанию.
"""

from asyncio import sleep
from datetime import datetime

from aiogram import Bot
from loguru import logger

from app.models import User
from app.properties import MONGODB_URI, week_is_odd
from app.utils.db_worker import DBWorker
from app.utils.text_generator import schedule_text, wd_name

db = DBWorker(MONGODB_URI)


async def _scheduled_send(bot: Bot, user: User, day: str):
    isoweekday = datetime.today().isoweekday()

    if day == "tomorrow":
        isoweekday += 1

    _week_is_odd = week_is_odd()

    # Если завтра понедельник, неделя должна меняться
    if isoweekday == 8:
        # т.е. меняем условие чётности недели на обратное
        _week_is_odd = not _week_is_odd

    if _week_is_odd:
        weektype = "odd"
    else:
        weektype = "even"

    weekday = wd_name[isoweekday][1]

    # Расписание на день из БД
    try:
        schedule = db.schedule(user.group, weekday, weektype)
    except KeyError:
        logger.error(f"User {user.user_id} set wrong weekday: {weekday}.")
        return

    # Сгенерированный текст
    text = schedule_text(day, isoweekday, user.group, weektype, schedule)

    try:
        await bot.send_message(user.id, text)
    except Exception as e:
        logger.error(f"Scheduled message was not sent. Exception: {e}")


async def time_trigger(bot: Bot):
    """Шедулер для запуска отложенных задач.

    Аргументы:
        bot (aiogram.types.Bot): инстанс aiogram бота
    """
    logger.info("Successfully started.")

    while True:
        current_time = datetime.now().strftime("%H:%M")
        hour = datetime.now().strftime("%H")
        weekday_name = datetime.now().strftime("%A").lower()

        need_to_update = weekday_name == "sunday" and current_time == "04:00"
        # logger.debug(f'time_trigger(): {current_time}')

        if int(hour) < 24 and int(hour) >= 12:
            day = "tomorrow"
        else:
            day = "today"

        chosen_sunday = (
            day == "today"
            and weekday_name == "sunday"
            or day == "tomorrow"
            and weekday_name == "saturday"
        )

        # Отправка уведомлений о парах
        if not chosen_sunday:
            timetable = db._scheduled_msg.find_one({"id": 1})
            if not timetable:
                return

            timetable = timetable.get(weekday_name)
            if not timetable:
                return

            if current_time in timetable:
                for user_id in timetable[current_time]:
                    user = db.user(user_id)
                    if user:
                        await _scheduled_send(bot, user, day)
                    else:
                        logger.error(f"User with ID {user_id} not found!")
                    await sleep(1)

        if need_to_update:
            # FIXME: update schedule in the DB
            ...

        await sleep(60)
