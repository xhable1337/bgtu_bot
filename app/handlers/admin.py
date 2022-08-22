"""app/handlers/admin.py

    Хэндлеры сообщений и команд админов.
"""
from asyncio import sleep

from aiogram import Dispatcher, types
from loguru import logger

from app.keyboards import kb_admin, kb_update_teachers
from app.utils.db_worker import DBWorker
from app.utils.api_worker import APIWorker
from app.properties import MONGODB_URI

db = DBWorker(MONGODB_URI)
api = APIWorker()


async def cmd_broadcast(message: types.Message):
    """### [`Command`] Команда /broadcast.
    """
    settings = db.settings()
    if message.chat.id in settings.admins:
        if message.text == '/broadcast':
            return await message.answer(
                "📨 /broadcast: Рассылка пользователям.\n"
                "<b>Использование:</b> <code>/broadcast &lt;group|all&gt; &lt;message&gt;</code>"
            )

        group, text = message.text.split(' ', maxsplit=2)[1:3]

        i = 1
        if group == 'all':
            text = '🔔 <b>Сообщение для всех групп!</b>\n' + text
            for user in db._users.find():
                if i % 25 == 0:
                    sleep(1)
                user_id = user['user_id']
                try:
                    await message.bot.send_message(user_id, text)
                    i += 1
                except Exception as exc:
                    logger.error(
                        f"Exception caught while broadcasting to all: {exc}"
                    )
        elif group == 'test':
            text = '🔔 <b>Тестовое сообщение!</b>\n' + text
            await message.answer(text)
        else:
            text = f'🔔 <b>Сообщение для группы {group}!</b>\n' + text
            # TODO: Вынести получение всех пользователей в отдельный метод
            for user in db._users.find({'group': group}):
                if i == 25:
                    sleep(1)
                user_id = user['user_id']
                try:
                    await message.bot.send_message(user_id, text)
                    i += 1
                except Exception as exc:
                    logger.error(
                        f"Exception caught while broadcasting to group {group}: {exc}"
                    )


async def cmd_admin(message: types.Message):
    """### [`Command`] Команда /admin.
    """
    settings = db._settings.find_one({})
    user = db.user(message.from_user.id)
    if message.chat.id in settings['admins']:
        count = db._users.count_documents({})
        maintenance_state = '🟢 Включены' if settings['maintenance'] else '🔴 Выключены'
        await message.answer(
            text=f'Добро пожаловать в админ-панель, {user.full_name}.\n'
            f'<b>Количество пользователей: <u>{count}</u></b>\n'
            f'<b>Состояние тех.работ: <u>{maintenance_state}</u></b>\n'
            'Выберите пункт в меню для дальнейших действий:',
            reply_markup=kb_admin
        )


async def cmd_update_groups(message: types.Message):
    """### [`Command`] Команда /update_groups.
    """
    settings = db.settings()
    if message.chat.id in settings.admins:
        if message.text == "/update_groups":
            return await message.answer(
                "🆙 /update_groups: Обновление расписания заданных групп.\n"
                "<b>Использование:</b> <code>/update_groups &lt;groups&gt;</code>"
            )

        groups = message.get_args().lstrip()
        text = '⚙ Запущено обновление расписания для указанных групп...\n\n'
        main_message = await message.answer(text)
        for group in groups.splitlines():
            schedule = api.schedule(group)
            db.add_schedule(schedule, replace=True)
            text += f'✔ {group}\n'
            await main_message.edit_text(text)

        await main_message.edit_text(text + '\n✅ Расписание успешно обновлено!')


async def cmd_force_update(message: types.Message):
    """### [`Command`] Команда /force_update.
    """
    settings = db.settings()
    if message.chat.id in settings.admins:
        groups_text = ''
        await message.answer(
            text='⚙ Запущено обновление групп...\n\n'
            'Пожалуйста, ожидайте завершения. Это занимает некоторое время (обычно 1-2 минуты).'
        )

        for year in db.years():
            for faculty in db.faculties():
                groups_text += f'{faculty["full"]} ({year} год): \n'
                # TODO: переделать API для работы с 4-х значными годами
                groups = api.groups(faculty["full"], str(year)[2:4])
                db.add_groups(faculty["full"], str(year), groups, replace=True)

                for group in groups:
                    groups_text += f'{group}\n'

                groups_text += '\n'
            await message.answer(text=groups_text)
            groups_text = ''
            # REVIEW - надо или нет?
            year -= 1

        prompt_text = 'Хотите ли вы обновить расписание всех групп? (может занять много времени)'
        keyboard = types.InlineKeyboardMarkup()
        # TODO: Убрать v2
        keyboard.row(
            types.InlineKeyboardButton(
                text='✔ Да', callback_data='force-update-yes'),
            types.InlineKeyboardButton(
                text='✔ Да (v2)', callback_data='force-update-yes-v2'),
            types.InlineKeyboardButton(
                text='❌ Нет', callback_data='force-update-no')
        )

        await message.answer(text=prompt_text, reply_markup=keyboard)


async def cmd_update_teachers(message: types.Message):
    """### [`Command`] Команда /update_teachers.
    """
    settings = db.settings()
    if message.chat.id in settings.admins:
        teacher_list = api.teacher_list()
        processed_count = 0
        succeeded_count = 0

        text = (
            f'⚙ <b>Найдено преподавателей:</b> {len(teacher_list)}\n\n'
            f'♻️ <b>Обработано:</b> {processed_count}/{len(teacher_list)}\n'
            f'✅ <b>Без ошибок:</b> {succeeded_count}\n'
            f'❌ <b>С ошибкой:</b> {processed_count - succeeded_count}'
        )

        message = await message.answer(
            text,
            reply_markup=kb_update_teachers
        )

        for teacher_name in teacher_list:
            teacher = api.teacher(teacher_name)

            if teacher:
                db.add_teacher(teacher, replace=True)
                succeeded_count += 1

            processed_count += 1

            text = (
                f'⚙ <b>Найдено преподавателей:</b> {len(teacher_list)}\n\n'
                f'♻️ <b>Обработано:</b> {processed_count}/{len(teacher_list)}\n'
                f'✅ <b>Без ошибок:</b> {succeeded_count}\n'
                f'❌ <b>С ошибкой:</b> {processed_count - succeeded_count}'
            )

            await message.edit_text(text)


def register_handlers_admin(dp: Dispatcher):
    """Регистрирует хэндлеры команд и сообщений админов.

    Аргументы:
        dp (aiogram.types.Dispatcher): диспетчер aiogram
    """
    # pylint: disable=invalid-name
    # dp - рекомендованное короткое имя для диспетчера
    dp.register_message_handler(cmd_broadcast, commands="broadcast")
    dp.register_message_handler(cmd_admin, commands="admin")
    dp.register_message_handler(cmd_update_groups, commands="update_groups")
    dp.register_message_handler(cmd_force_update, commands="force_update")
    dp.register_message_handler(
        cmd_update_teachers, commands="update_teachers")
