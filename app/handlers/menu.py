from contextlib import suppress

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
import datetime
# from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified

# TODO: Избавиться от wildcard import
from app.keyboards import *
from app.utils.db_worker import DBWorker
# TODO: Избавиться от wd_name и wd_numbers, переместив в другую точку
from app.utils.text_generator import schedule_text, wd_name, wd_numbers

db = DBWorker()


async def cb_days(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание по дням».
    """
    # TODO: Вынести определение чёт/нечет в другое место [DRY]
    if datetime.datetime.today().isocalendar()[1] % 2 != 0:
        weektype = '[Н] - нечётная'
        buttons = ['[Н]', 'Ч']
    else:
        weektype = '[Ч] - чётная'
        buttons = ['Н', '[Ч]']

    kb_dn = days_keyboard(buttons)

    await call.message.edit_text(
        text=f'Выберите неделю и день (сейчас идёт {weektype}):\n',
        reply_markup=kb_dn
    )

    await call.answer()


async def cb_today(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание на сегодня».
    """
    user = db.user(call.from_user.id)

    isoweekday = datetime.datetime.today().isoweekday()

    # TODO: Вынести определение чёт/нечет в другое место [DRY]
    week_is_odd = datetime.datetime.today().isocalendar()[1] % 2 != 0

    if week_is_odd:
        weektype = 'odd'
    else:
        weektype = 'even'

    # Расписание на день из БД
    schedule = db.schedule(user.group, wd_name[isoweekday], weektype)

    # Сгенерированный текст
    text = schedule_text('today', isoweekday, user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


async def cb_tomorrow(call: types.CallbackQuery):
    """### [`Callback`] Кнопка «Расписание на завтра».
    """
    user = db.user(call.from_user.id)

    isoweekday = datetime.datetime.today().isoweekday() + 1

    # TODO: Вынести определение чёт/нечет в другое место [DRY]
    week_is_odd = datetime.datetime.today().isocalendar()[1] % 2 != 0

    # Если завтра понедельник, неделя должна меняться
    if isoweekday == 8:
        # т.е. меняем условие чётности недели на обратное
        week_is_odd = not week_is_odd

    if week_is_odd:
        weektype = 'odd'
    else:
        weektype = 'even'

    # Расписание на день из БД
    schedule = db.schedule(user.group, wd_name[isoweekday], weektype)

    # Сгенерированный текст
    text = schedule_text('tomorrow', isoweekday,
                         user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


async def cb_wday(call: types.CallbackQuery):
    """### [`Callback`] Кнопки выбора дня недели расписания.
    """
    user = db.user(call.from_user.id)

    # Номер недели (1 - нечет, 2 - чёт)
    # TODO: переделать callback_data с 1/2 на odd/even
    weeknum = str(call.data)[-1]

    # День недели
    weekday = call.data[5:-2]

    # Номер дня недели
    isoweekday = wd_numbers[weekday]

    if weeknum == 1:
        weektype = 'odd'
    else:
        weektype = 'even'

    # Расписание на день из БД
    schedule = db.schedule(user.group, wd_name[isoweekday], weektype)

    # Сгенерированный текст
    text = schedule_text('other', isoweekday,
                         user.group, weektype, schedule)

    await call.message.edit_text(text, reply_markup=kbbb)
    await call.answer()


def register_handlers_menu(dp: Dispatcher):
    dp.register_callback_query_handler(cb_days, Text('days'))
