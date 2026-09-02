"""app/handlers/admin.py

    Хэндлеры сообщений и команд админов.
"""
from datetime import datetime

from app.config import config
from app.utils.api_worker import APIWorker
from app.utils.db_worker import DBWorker

db = DBWorker(config.mongodb_uri)
api = APIWorker()


async def update_groups():
    """Генератор для обновления списка групп в БД.

    Генерирует:
        str: статус процесса на каждом этапе
    """
    text = "⚙ <b><u>Обновление групп в процессе...</u></b>\n"
    for year in db.years():
        groups_count = 0
        for faculty in db.faculties():
            # TODO: переделать API для работы с 4-х значными годами
            groups = api.groups(faculty["full"], str(year)[2:4])
            db.add_groups(faculty["full"], str(year), groups, replace=True)
            groups_count += len(groups)

        text += f"✅ <b>{year} год поступления:</b> {groups_count} групп\n"
        yield text


async def update_schedule():
    """Генератор для обновления расписания групп в БД.

    Генерирует:
        str: статус процесса на каждом этапе
    """
    text = '⚙ <b><u>Обновление расписания</u></b>...\n\n'

    for year in db.years():
        groups_count = 0
        for faculty in db.faculties():
            error_groups = []
            error_text = ''

            groups = db.groups(faculty=faculty["full"], year=str(year))

            # Последовательное добавление расписания каждой группы в БД
            for group in groups:
                try:
                    schedule = api.schedule(group)
                    db.add_schedule(schedule)
                except Exception as e:
                    # TODO: сузить круг отлавливаемых исключений
                    error_groups.append(group)

            # Создание строки с группами, парсинг расписания которых не удался
            if error_groups:
                error_text = ','.join(error_groups)
                error_text = f"\n<blockquote>{error_text}</blockquote>"
            error_count = len(error_groups)
            success_count = len(groups) - error_count
            dt = datetime.now().strftime('%H:%M:%S')

            text += (
                f"🎓 <b>{faculty['short']}-{year}:</b>\n"
                f"✅ {success_count} | ❌ {error_count} | 📆 {dt}"
                f"{error_text}\n\n"
            )

            yield text


async def update_data():
    raise NotImplementedError()


async def update_teachers():
    raise NotImplementedError()
