import requests
from typing import Union
from app.models import Schedule
from loguru import logger


class APIWorker:
    def __init__(self, api_endpoint='https://parser.zgursky.tk/api/v2'):
        self.base_url = api_endpoint
        self.session = requests.session()

    def _handle_request(
        self, path: str, params: dict = {}
    ) -> Union[dict, list]:
        with self.session as session:
            response = session.get(self.base_url + path, params=params)
            status = response.status_code
            logger.debug(f"Request '{path}' finished with status {status}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request '{path}' failed with status {status}")
                logger.error(f"Request params: {params}")
                logger.error(f"Response text: {response.text}")

    def schedule(self, group: str) -> Schedule:
        path = '/schedule'
        params = {'group': group}
        response = self._handle_request(path, params)

        return Schedule(**response)

    def groups(self, faculty: str, year: str) -> list[str]:
        path = '/groups'
        params = {'faculty': faculty, 'year': year}
        response = self._handle_request(path, params)

        return response

    def teacher_list(self) -> list[str]:
        path = '/teacher_list'
        response = self._handle_request(path)

        return response
    
    def teacher(self, name: str):
        """Функция получения информации о преподавателе от API."""
        path = '/teacher'
        params = {'name': name}
        response = self._handle_request(path, params)

        return response
