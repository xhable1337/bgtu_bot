"""bot.py

    Основной файл бота, точка входа программы.

    Для запуска: `python3 bot.py`
"""

# Standard library imports
import logging
from asyncio import get_event_loop, ensure_future

# Related third party imports
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from loguru import logger

# Local application/library specific imports
from app.handlers.common import register_handlers_common
from app.handlers.admin import register_handlers_admin
from app.handlers.admin_menu import register_handlers_admin_menu
from app.handlers.menu import register_handlers_menu
from app import properties
from app.time_trigger import time_trigger
# ---------------------------------------------------------------

bot = Bot(token=properties.BOT_TOKEN, parse_mode='HTML')
# dp = Dispatcher(bot, storage=MongoStorage(db_name=props.database_name))
dp = Dispatcher(bot)


class _InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info
        ).log(
            level,
            record.getMessage()
        )


async def set_commands(_bot: Bot):
    """Установка команд для меню бота.

    Args:
        _bot (aiogram.types.Bot): инстанс aiogram бота
    """
    commands = [
        BotCommand(command="/start", description="Вернуться в начало"),
        BotCommand(command="/cancel", description="Отменить текущее действие")
    ]
    await _bot.set_my_commands(commands)


async def main():
    """Точка входа бота.
    """
    # Запуск логирования
    logging.basicConfig(handlers=[_InterceptHandler()], level=logging.INFO)

    _bot = await bot.get_me()
    logger.warning(f"Starting bot {_bot.full_name} [{_bot.username}]...")

    # Регистрация хэндлеров
    register_handlers_admin_menu(dp)
    register_handlers_admin(dp)
    register_handlers_menu(dp)
    register_handlers_common(dp)

    # Установка команд
    await set_commands(bot)

    # Пропуск апдейтов и запуск long-polling
    try:
        await dp.skip_updates()
        await dp.start_polling()
    # После завершения работы бота закрываем соединение с хранилищем FSM
    finally:
        logger.error('Terminating bot...')
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()
        logger.error('Goodbye!')


if __name__ == '__main__':
    loop = get_event_loop()
    task = ensure_future(main())

    try:
        loop.run_until_complete(time_trigger(bot))
    except KeyboardInterrupt:
        task.cancel()
