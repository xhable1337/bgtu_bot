from datetime import datetime

################################
# Constants
################################

# Совпадает ли чет/нечет с календарем
odd_week_calendar = True

# ANCHOR: переместить URI БД к настройкам
# URI для подключения к базе данных MongoDB
MONGODB_URI = 'mongodb://heroku_38n7vrr9:8pojct20ovk5sgvthiugo3kmpa@dnevnikcluster-shard-00-00.7tatu.mongodb.net:27017,dnevnikcluster-shard-00-01.7tatu.mongodb.net:27017,dnevnikcluster-shard-00-02.7tatu.mongodb.net:27017/heroku_38n7vrr9?ssl=true&replicaSet=atlas-106r53-shard-0&authSource=admin&retryWrites=true&w=majority'

# Токен бота в Telegram
# bot_token = '1147506878:AAGi4Uo6IIGm55TNgG9IIcYIfRZak-HFxN4'
bot_token = '2036333661:AAE9ocZfHf-lkrU9SFi8d0DlnB8ftrx5ioE'

################################
# Functions
################################

def week_is_odd() -> bool:
    
    if odd_week_calendar:
        return datetime.today().isocalendar()[1] % 2 != 0
    else:
        return datetime.today().isocalendar()[1] % 2 == 0