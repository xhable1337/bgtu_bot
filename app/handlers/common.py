from asyncio import sleep
import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.utils.exceptions import BotBlocked
from loguru import logger
from requests import get
from app.models import User
from app.properties import week_is_odd, MONGODB_URI

from app.utils.db_worker import DBWorker
# TODO: избавиться от wildcard import
from app.keyboards import *

db = DBWorker(MONGODB_URI)


async def cmd_start(message: types.Message):
    """### [`Command`] Команда /start.
    """
    await message.bot.send_chat_action(message.from_user.id, 'typing')
    user = db.user(message.from_user.id)
    
    if not user:
        # TODO: Перейти на группу undefined при первом входе в бота
        user = User(
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            user_id=message.from_user.id,
            username=message.from_user.username,
            state='default',
            group='О-20-ИВТ-1-по-Б',
            favorite_groups=[]
        )
        db.add_user(user, replace=False)
        
        kb_faculty = types.InlineKeyboardMarkup()
        for faculty in db.faculties():
            kb_faculty.row(
                types.InlineKeyboardButton(
                    text=faculty["full"], 
                    callback_data=f'f_{faculty["short"]}'
                )
            )
        
        user = db.user(message.from_user.id)

        await message.answer(
            f'Привет, {user.full_name}!\n'
            '<b>Для начала работы с ботом выбери свою группу (впоследствии выбор можно изменить):</b>',
            reply_markup=kb_faculty
        )
        
        logger.info(f"New user! ID: {user.user_id}")
    else:
        db.add_user(user.obj(), replace=True)
        user.state = 'default'
        
        btn = types.MenuButtonWebApp(
            'Бот v2',
            types.WebAppInfo(
                url='https://tgweb.zgursky.tk'
            )
        )
        await message.bot.set_chat_menu_button(message.chat.id, btn)
        
        weekname = 'нечётная' if week_is_odd() else 'чётная'
        await message.answer(
            f'Привет, {user.full_name}!\n'
            f'<b>Твоя группа: {user.group}.</b>\n'
            f'<b>Сейчас идёт {weekname} неделя.</b>\n'
            'Вот главное меню:',
            reply_markup=kbm
        )


async def msg_any(message: types.Message, state: FSMContext):
    user = db.user(message.from_user.id)
    settings = db._settings.find_one({})
    
    # TODO: вынести settings в отдельный метод DBWorker
    if settings['maintenance'] and user.user_id not in settings['admins']:
        return await message.reply('⚡ Бот находится на тех.работах. Возвращайтесь позже.')
    
    #! Юзера нет в базе, пусть прожмёт /start
    if not user:
        return await message.answer('Для начала работы с ботом выполните команду /start.')
    
    #? Обычное состояние, юзер хочет получить меню
    if user.state == 'default':
        await cmd_start(message)
    
    #? Поиск аудитории
    elif user.state == 'find_class':
        building_1 = 'https://telegra.ph/file/49ec8634ab340fa384787.png'
        regex_1 = re.compile(r'(\b[1-9][1-9]\b|\b[1-9]\b)')
        
        building_2 = 'https://telegra.ph/file/7d04458ac4230fd12f064.png'
        regex_2 = re.compile(r'\b[1-9][0-9][0-9]\b')
        
        building_3 = 'https://telegra.ph/file/6b801965b5771830b67f0.png'
        regex_3 = re.compile(r'(\bА\d{3}\b|\b[Аа]\b|\b[Бб]\b|\b[Вв]\b|\b[Гг]\b|\b[Дд]\b)')
        
        building_4 = 'https://telegra.ph/file/f79c20324a0ba6cd88711.png'
        regex_4 = re.compile(r'\bБ\d{3}\b')
        
        if re.match(regex_1, message.text):
            #! Найдена аудитория в корпусе №2
            await message.answer_photo(
                photo=building_1,
                caption=f'Аудитория {message.text} находится в корпусе №1 <i>(Институтская, 16)</i>.',
            )
            
            await message.answer_location(
                latitude=53.305077,
                longitude=34.305080
            )
            
            await cmd_start(message)
        elif re.match(regex_2, message.text):
            #! Найдена аудитория в корпусе №2
            await message.answer_photo(
                photo=building_2,
                caption=f'Аудитория {message.text} находится в корпусе №2 <i>(бульвар 50 лет Октября, 7)</i>.',
            )
            
            await message.answer_location(
                latitude=53.304442,
                longitude=34.303849
            )
            
            await cmd_start(message)
        elif re.match(regex_3, message.text):
            await message.answer_photo(
                photo=building_3,
                caption=f'Аудитория {message.text} находится в корпусе №3 <i>(Харьковская, 8)</i>.',
            )
            
            await message.answer_location(
                latitude=53.304991,
                longitude=34.306688
            )
            
            await cmd_start(message)
        elif re.match(regex_4, message.text):
            await message.answer_photo(
                photo=building_4,
                caption=f'Аудитория {message.text} находится в корпусе №4 <i>(Харьковская, 10Б)</i>.',
            )
            
            await message.answer_location(
                latitude=53.303513,
                longitude=34.305085
            )
            
            await cmd_start(message)
        else:
            await message.answer(
                'Данный номер аудитории некорректен. Повторите попытку или отмените действие:',
                reply_markup=kb_cancel,
            )

    #? Добавление уведомления
    elif user.state.startswith('add_notification_'):
        time_regex = re.compile(r'^2[0-3]:[0-5][0-9]$|^[0]{1,2}:[0-5][0-9]$|^1[0-9]:[0-5][0-9]$|^0?[1-9]:[0-5][0-9]$')
        
        if not re.match(time_regex, message.text):
            return await message.answer(
                'Вы ввели некорректное время. Повторите попытку или отмените действие:', 
                reply_markup=kb_cancel
            )
        
        # Валидация времени в формат ЧЧ:ММ
        if re.match(r'\b[0-9]:[0-5][0-9]\b', message.text):
            notification_time = f"0{message.text}"
        else:
            notification_time = message.text
        
        weekday = user.state.split('_')[2]
        
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
                "sunday": ""
            }
        
        scheduled_msg = db._scheduled_msg.find_one({'id': 1})
        
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
        db._scheduled_msg.update_one({'id': 1}, {'$set': scheduled_msg})
        
        await message.answer(
            f'⏰ Уведомление на {message.text} установлено!', 
            reply_markup=kbbb
        )
        
        user.state = 'default'


async def cmd_cancel(message: types.Message):
    user = db.user(message.from_user.id)
    user.state = 'default'
    await message.answer(
        "Действие отменено. Для дальнейшей работы нажмите /start.", 
        reply_markup=types.ReplyKeyboardRemove()
    )


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals="отмена", ignore_case=True), state="*")
    dp.register_message_handler(msg_any)