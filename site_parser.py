import requests
import ast
import os
import json

password = os.environ.get('password')
API_URL = os.environ.get('PARSER_URL') or 'https://parser.zgursky.tk/'


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


def api_get_schedule_v2(group):
    """Функция получения расписания от API."""
    url = API_URL + '/api/v2/schedule'
    params = {
        'group': group
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        schedule = response.json()
        # response = response.text
        # schedule = ast.literal_eval(response)
        return schedule
    else:
        return None


def api_get_groups(faculty='Факультет информационных технологий', year='20'):
    """Функция получения списка групп от API."""
    url = API_URL + '/api/v2/groups'
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


def api_get_teacher_list():
    """Функция получения списка преподавателей от API."""
    url = API_URL + '/api/v2/teacher_list'
    response = requests.get(url)
    if response.status_code == 200:
        group_list = response.json()
        # group_list = ast.literal_eval(response)
        return group_list
    else:
        return None


def api_get_teacher(name: str):
    """Функция получения преподавателя от API."""
    url = API_URL + '/api/v2/teacher'
    response = requests.get(url, params={'name': name})
    if response.status_code == 200:
        group_list = response.json()
        # group_list = ast.literal_eval(response)
        return group_list
    else:
        return None


def api_get_teacher_schedule(teacher: str):
    """Функция получения расписания преподавателей от API."""
    url = API_URL + '/api/v2/teacher_schedule'
    params = {'teacher': teacher}
    response = requests.get(url, params)
    if response.status_code == 200:
        teacher_schedule = response.json()
        # group_list = ast.literal_eval(response)
        return teacher_schedule
    else:
        return None
