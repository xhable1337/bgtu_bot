import requests
import ast
import os

password = os.environ.get('password')
API_URL = os.environ.get('PARSER_URL')


def api_get_schedule(group):
    """Функция получения расписания от API."""
    url = API_URL + password + '/get_schedule/'
    params = {
        'group': group
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        response = response.text
        schedule = ast.literal_eval(response)
        return schedule
    else:
        return None

def api_get_groups(faculty='Факультет информационных технологий', year='20'):
    """Функция получения расписания от API."""
    url = API_URL + password + '/get_groups/'
    params = {
        'faculty': faculty,
        'year': year
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        response = response.text
        group_list = ast.literal_eval(response)
        return group_list
    else:
        return None
