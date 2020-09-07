import requests
import ast
import os

password = os.environ.get('password')
API_URL = 'https://bgtu-parser.herokuapp.com/'


def api_get_schedule(group, weekday, weeknum):
    """Функция получения расписания от API."""
    url = API_URL + password + '/get_schedule/'
    params = {
        'group': group,
        'weekday': weekday,
        'weeknum': weeknum
    }
    response = requests.get(url, params=params).text
    schedule = ast.literal_eval(response)
    return schedule

def api_get_groups(faculty='Факультет информационных технологий', year='20'):
    """Функция получения расписания от API."""
    url = API_URL + password + '/get_groups/'
    params = {
        'faculty': faculty,
        'year': year
    }
    response = requests.get(url, params=params).text
    group_list = ast.literal_eval(response)
    return group_list