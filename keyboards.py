from aiogram import types
# Файл создания клавиатур для бота

# Главное меню
kbm = types.InlineKeyboardMarkup()
kbm.row(types.InlineKeyboardButton(
    text='📅 Расписание по дням',
    callback_data='days'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='⚡️ Сегодня', 
        callback_data='today'
    ),
    types.InlineKeyboardButton(
        text='⚡️ Завтра', 
        callback_data='tomorrow'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='🕔 Расписание пар', 
        callback_data='rings'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='🏠 Найти корпус по аудитории', 
        callback_data='building'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='🔂 Сменить факультет/группу', 
        callback_data='change_faculty'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='🔔 Ежедневные уведомления', 
        callback_data='notifications'
    )
)
kbm.row(
    types.InlineKeyboardButton(
        text='⭐ Избранные группы', 
        callback_data='favorite_groups'
    )
)


# Кнопка возврата от сообщения с расписанием
kbb = types.InlineKeyboardMarkup()
kbb.row(
    types.InlineKeyboardButton(
        text='↩️ Назад', 
        callback_data='days'
    )
)

# Кнопка возврата в главное меню
kbbb = types.InlineKeyboardMarkup()
kbbb.row(
    types.InlineKeyboardButton(
        text='🔄 В главное меню', 
        callback_data='tomain'
    )
)

# Кнопка отмены действия
kb_cancel_building = types.InlineKeyboardMarkup()
kb_cancel_building.row(
    types.InlineKeyboardButton(
        text='🚫 Отмена', 
        callback_data='cancel_find_class'
    )
)

# Меню правки ежедневных уведомлениий
kb_notifications = types.InlineKeyboardMarkup()
kb_notifications.row(
    types.InlineKeyboardButton(
        text='❌ Удалить', 
        callback_data='del_notification'
    )
)
kb_notifications.row(
    types.InlineKeyboardButton(
        text='✍ Изменить', 
        callback_data='edit_notification'
    )
)
kb_notifications.row(
    types.InlineKeyboardButton(
        text='🔄 В главное меню', 
        callback_data='tomain'
    )
)


# Меню ежедневных уведомлений по дням
kb_notifications_days = types.InlineKeyboardMarkup()
kb_notifications_days.row(
    types.InlineKeyboardButton(
        text='Пн', 
        callback_data='notify_monday'
    ),
    types.InlineKeyboardButton(
        text='Вт', 
        callback_data='notify_tuesday'
    ),
    types.InlineKeyboardButton(
        text='Ср', 
        callback_data='notify_wednesday'
    ),
    types.InlineKeyboardButton(
        text='Чт', 
        callback_data='notify_thursday'
    ),
    types.InlineKeyboardButton(
        text='Пт', 
        callback_data='notify_friday'
    ),
    types.InlineKeyboardButton(
        text='Сб', 
        callback_data='notify_saturday'
    ),
    types.InlineKeyboardButton(
        text='Вс', 
        callback_data='notify_sunday'
    )
)

kb_notifications_days.row(
    types.InlineKeyboardButton(
        text='🔄 В главное меню', 
        callback_data='tomain'
    )
)

def days_keyboard(buttons):
    """Функция создания клавиатуры, исходя из кнопок чётной и нечётной недели."""
    kb_dn = types.InlineKeyboardMarkup()
    kb_dn.row(
        types.InlineKeyboardButton(
            text=buttons[0], 
            callback_data='week_1'
        ),
        types.InlineKeyboardButton(
            text='Пн', 
            callback_data='wday_monday_1'
        ),
        types.InlineKeyboardButton(
            text='Вт', 
            callback_data='wday_tuesday_1'
        ),
        types.InlineKeyboardButton(
            text='Ср',
            callback_data='wday_wednesday_1'
        ),
        types.InlineKeyboardButton(
            text='Чт', 
            callback_data='wday_thursday_1'
        ),
        types.InlineKeyboardButton(
            text='Пт', 
            callback_data='wday_friday_1'
        ),
        types.InlineKeyboardButton(
            text='Сб', 
            callback_data='wday_saturday_1'
        )
    )
    kb_dn.row(
        types.InlineKeyboardButton(
            text=buttons[1], 
            callback_data='week_2'
        ),
        types.InlineKeyboardButton(
            text='Пн', 
            callback_data='wday_monday_2'
        ),
        types.InlineKeyboardButton(
            text='Вт', 
            callback_data='wday_tuesday_2'
        ),
        types.InlineKeyboardButton(
            text='Ср', 
            callback_data='wday_wednesday_2'
        ),
        types.InlineKeyboardButton(
            text='Чт', 
            callback_data='wday_thursday_2'
        ),
        types.InlineKeyboardButton(
            text='Пт', 
            callback_data='wday_friday_2'
        ),
        types.InlineKeyboardButton(
            text='Сб', 
            callback_data='wday_saturday_2'
        )
    )
    kb_dn.row(
        types.InlineKeyboardButton(
            text='🔄 В главное меню', 
            callback_data='tomain'
        )
    )
    return kb_dn

# Админ-меню
kb_admin = types.InlineKeyboardMarkup()
kb_admin.row(
    types.InlineKeyboardButton(
        text='✉ Рассылка',
        callback_data='mailing'
    ),
    types.InlineKeyboardButton(
        text='👥 Список пользователей',
        callback_data='user_list'
    )
    
)

# Кнопка возврата в админ-меню
kb_admin_back = types.InlineKeyboardMarkup()
kb_admin_back.row(
    types.InlineKeyboardButton(
        text='🔄 В админ-меню', 
        callback_data='toadmin'
    )
)