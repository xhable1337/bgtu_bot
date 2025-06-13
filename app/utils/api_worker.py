"""api_worker.py

Этот модуль осуществляет всю работу с API, включая получение
расписания, списка групп, преподавателей и информации о них.

Для работы с модулем, нужно его импортировать и создать инстанс класса APIWorker:

```
from api_worker import DBWorker

api = APIWorker('my_endpoint')
```
"""

from typing import Union

import requests
from loguru import logger

from app.models import Schedule


class APIWorker:
    """Класс для работы с API."""

    def __init__(self, api_endpoint="https://bgtu-parser.darx.zip/api/v2"):
        self.base_url = api_endpoint
        self.session = requests.session()

    def _handle_request(self, path: str, params: dict = None) -> Union[dict, list]:
        with self.session as session:
            response = session.get(self.base_url + path, params=params)
            status = response.status_code
            if response.status_code == 200:
                logger.debug(f"Request '{path}' finished with status {status}")
                return response.json()

            logger.error(f"Request '{path}' failed with status {status}")
            logger.error(f"Request params: {params}")
            logger.error(f"Response text: {response.text}")
            return None

    def schedule(self, group: str) -> Schedule:
        """Получает из API расписание заданной группы.

        Аргументы:
            group (str): группа, для которой нужно получить расписание

        Возвращает:
            Schedule: объект расписания
        """
        path = "/schedule"
        params = {"group": group}
        response = self._handle_request(path, params)

        return Schedule(**response)

    def groups(self, faculty: str, year: str) -> list[str]:
        """Получает из API список групп по заданным параметрам.

        Аргументы:
            faculty (str): факультет
            year (str): год поступления

        Возвращает:
            list[str]: список групп
        """
        path = "/groups"
        params = {"faculty": faculty, "year": year}
        response = self._handle_request(path, params)

        return response

    def teacher_list(self) -> list[str]:
        """Получает из API список всех преподавателей.

        Возвращает:
            list[str]: список преподавателей
        """
        path = "/teacher_list"
        response = self._handle_request(path)

        return response

    def teacher(self, name: str) -> dict:
        """Получает информацию о преподавателе из API.

        Аргументы:
            name (str): полное имя преподавателя

        Возвращает:
            dict: словарь с информацией о преподавателе
        """
        path = "/teacher"
        params = {"name": name}
        response = self._handle_request(path, params)

        return response
