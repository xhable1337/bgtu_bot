def numbers(name):
    if name == 'monday':
        num = 1
    elif name == 'tuesday':
        num = 2
    elif name == 'wednesday':
        num = 3
    elif name == 'thursday':
        num = 4
    elif name == 'friday':
        num = 5
    elif name == 'saturday':
        num = 6
    elif name == 'sunday':
        num = 7
    return num

def translate(name):
    if name == 'monday':
        newname = 'понедельник'
    elif name == 'tuesday':
        newname = 'вторник'
    elif name == 'wednesday':
        newname = 'среда'
    elif name == 'thursday':
        newname = 'четверг'
    elif name == 'friday':
        newname = 'пятница'
    elif name == 'saturday':
        newname = 'суббота'
    elif name == 'sunday':
        newname = 'воскресенье'
    return newname


def names(wd):
    if wd == 1:
        wdr = 'понедельник'
        wde = 'monday'       
    elif wd == 2:
        wdr = 'вторник'
        wde = 'tuesday'        
    elif wd == 3:
        wdr = 'среда'
        wde = 'wednesday'        
    elif wd == 4:
        wdr = 'четверг'
        wde = 'thursday'        
    elif wd == 5:
        wdr = 'пятница'
        wde = 'friday'
    elif wd == 6:
        wdr = 'суббота'
        wde = 'saturday'
    elif wd == 7:
        wdr = 'воскресенье'
        wde = 'sunday'
    elif wd == 8:
        wdr = 'понедельник'
        wde = 'monday'
    return wdr, wde