from asyncio import sleep
from datetime import datetime

from aiogram import Bot
from aiogram.types.chat import Chat
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, UserDeactivated
from loguru import logger
from app.models import User

from app.properties import week_is_odd
# TODO: Избавиться от wildcard import
from app.keyboards import *
from app.utils.db_worker import DBWorker
from app.utils.text_generator import schedule_text, wd_name

db = DBWorker()


async def scheduled_send(bot: Bot, user: User, day: str):
    isoweekday = datetime.datetime.today().isoweekday()
    
    if day == 'tomorrow':
        isoweekday += 1

    _week_is_odd = week_is_odd()

    # Если завтра понедельник, неделя должна меняться
    if isoweekday == 8:
        # т.е. меняем условие чётности недели на обратное
        _week_is_odd = not _week_is_odd

    if _week_is_odd:
        weektype = 'odd'
    else:
        weektype = 'even'

    # Расписание на день из БД
    schedule = db.schedule(user.group, wd_name[isoweekday], weektype)

    # Сгенерированный текст
    text = schedule_text(day, isoweekday,
                         user.group, weektype, schedule)

    await bot.send_message(user.id, text)



async def time_trigger(bot: Bot):
    logger.info('Successfully started.')
    
    while True:
        current_time = datetime.now().strftime("%H:%M")
        hour = datetime.now().strftime("%H")
        weekday_name = datetime.now().strftime('%A').lower()
        logger.debug(f'time_trigger(): {current_time}')

        if int(hour) < 24 and int(hour) >= 12:
            day = 'tomorrow'
        else:
            day = 'today'

        timetable = db._scheduled_msg.find_one({"id": 1})[weekday_name]

        if current_time in timetable:
            for user_id in timetable[current_time]:
                await scheduled_send(bot, db.user(user_id), day)
                await sleep(1)

        await sleep(60)
