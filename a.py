import datetime

def get_years():
    years = []
    dt = datetime.datetime.now()
    month = int(dt.strftime('%m'))
    year = int(dt.strftime('%y'))

    month = 1

    if month <= 5:
        # Учебный год ЕЩЁ не кончился
        for _ in range(4):
            year -= 1
            years.append(year)
    else:
        # Учебный год УЖЕ кончился или УЖЕ начался
        for _ in range(4):
            years.append(year)
            year -= 1

    return years

print(get_years())