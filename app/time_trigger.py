"""time_trigger.py

Этот модуль представляет собой шедулер для запуска
отложенных задач или задач по расписанию.
"""

from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot
from loguru import logger

from app.config import config
from app.utils.db_worker import DBUser, DBWorker
from app.utils.text_generator import schedule_text, wd_name
from app.utils.wdays import week_is_odd

db = DBWorker(config.mongodb_uri)

# Время еженедельного обновления расписания (воскресенье).
SCHEDULE_UPDATE_TIME = "04:00"
# Интервал опроса шедулера в секундах.
POLL_INTERVAL_SECONDS = 59.99
# Начиная с этого часа уведомления относятся к завтрашнему дню.
TOMORROW_AFTER_HOUR = 12


async def _scheduled_send(bot: Bot, user: DBUser, day: str):
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
        if not schedule:
            logger.error(f"Schedule for {user.group} on {weekday} not found.")
            return
    except KeyError:
        logger.error(f"User {user.user_id} set wrong weekday: {weekday}.")
        return

    # Сгенерированный текст
    text = schedule_text(day, isoweekday, user.group, weektype, schedule)

    try:
        await bot.send_message(user.user_id, text)
    except Exception as e:
        logger.error(f"Scheduled message was not sent. Exception: {e}")


@dataclass(frozen=True)
class _TimeContext:
    """Снимок времени, используемый в одной итерации шедулера."""

    current_time: str
    weekday_name: str
    day: str
    is_day_off: bool
    need_update: bool


def _get_time_context(now: datetime) -> _TimeContext:
    """Вычисляет состояние времени для текущей итерации."""
    current_time = now.strftime("%H:%M")
    weekday_name = now.strftime("%A").lower()

    day = "tomorrow" if now.hour >= TOMORROW_AFTER_HOUR else "today"

    # День, для которого готовится уведомление, приходится на воскресенье —
    # пар нет, поэтому отправлять расписание не нужно.
    is_day_off = (
        (day == "today" and weekday_name == "sunday")
        or (day == "tomorrow" and weekday_name == "saturday")
    )

    need_update = (
        weekday_name == "sunday" and current_time == SCHEDULE_UPDATE_TIME
    )

    return _TimeContext(
        current_time=current_time,
        weekday_name=weekday_name,
        day=day,
        is_day_off=is_day_off,
        need_update=need_update,
    )


def _get_due_user_ids(weekday_name: str, current_time: str) -> list[int]:
    """Возвращает user_id, для которых сейчас назначено уведомление."""
    scheduled = db._scheduled_msg.find_one({"id": 1})
    if not scheduled:
        return []

    timetable = scheduled.get(weekday_name)
    if not timetable:
        return []

    return timetable.get(current_time, [])


async def _send_notifications(bot: Bot, user_ids: list[int], day: str) -> None:
    """Отправляет расписание всем пользователям из списка."""
    for user_id in user_ids:
        user = db.user(user_id)
        if user:
            await _scheduled_send(bot, user, day)
        else:
            logger.error(f"User with ID {user_id} not found!")
        await sleep(1)


async def time_trigger(bot: Bot):
    """Шедулер для запуска отложенных задач.

    Аргументы:
        bot (aiogram.types.Bot): инстанс aiogram бота
    """
    logger.info("Successfully started.")

    while True:
        try:
            context = _get_time_context(datetime.now())
            logger.info("Time trigger")

            if not context.is_day_off:
                user_ids = _get_due_user_ids(
                    context.weekday_name, context.current_time
                )
                await _send_notifications(bot, user_ids, context.day)

            if context.need_update:
                # FIXME: update schedule in the DB
                ...
        except Exception:
            logger.exception("Time trigger iteration failed")

        await sleep(POLL_INTERVAL_SECONDS)
