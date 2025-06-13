"""app/keyboards.py

Этот модуль создаёт и хранит в себе клавиатуры меню.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

# Файл создания клавиатур для бота

# Главное меню
kbm = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📅 Расписание по дням", callback_data="days")],
        [
            InlineKeyboardButton(text="⚡️ Сегодня", callback_data="today"),
            InlineKeyboardButton(text="⚡️ Завтра", callback_data="tomorrow"),
        ],
        [InlineKeyboardButton(text="🕔 Расписание звонков", callback_data="rings")],
        [
            InlineKeyboardButton(
                text="🏠 Найти корпус по аудитории", callback_data="building"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔂 Сменить факультет/группу", callback_data="change_faculty"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Ежедневные уведомления", callback_data="notifications"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ Избранные группы", callback_data="favorite_groups"
            )
        ],
        [
            InlineKeyboardButton(
                text="📱 Веб-приложение",
                web_app=WebAppInfo(url="https://tgweb.darx.zip"),
            )
        ],
    ]
)


# Кнопка возврата от сообщения с расписанием
kbb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="↩️ Назад", callback_data="days")]]
)

# Кнопка возврата в главное меню
kbbb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 В главное меню", callback_data="tomain")]
    ]
)

# Кнопка отмены действия
kb_cancel = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="🚫 Отмена", callback_data="tomain")]]
)

# Меню правки ежедневных уведомлениий
kb_notifications = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить", callback_data="del_notification")],
        [InlineKeyboardButton(text="✍ Изменить", callback_data="edit_notification")],
        [InlineKeyboardButton(text="🔄 В главное меню", callback_data="tomain")],
    ]
)


# Меню ежедневных уведомлений по дням
kb_notifications_days = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Пн", callback_data="notify_monday"),
            InlineKeyboardButton(text="Вт", callback_data="notify_tuesday"),
            InlineKeyboardButton(text="Ср", callback_data="notify_wednesday"),
            InlineKeyboardButton(text="Чт", callback_data="notify_thursday"),
            InlineKeyboardButton(text="Пт", callback_data="notify_friday"),
            InlineKeyboardButton(text="Сб", callback_data="notify_saturday"),
            InlineKeyboardButton(text="Вс", callback_data="notify_sunday"),
        ],
        [InlineKeyboardButton(text="🔄 В главное меню", callback_data="tomain")],
    ]
)


def days_keyboard(buttons):
    """Функция создания клавиатуры, исходя из кнопок чётной и нечётной недели."""
    kb_dn = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=buttons[0], callback_data="week_odd"),
                InlineKeyboardButton(text="Пн", callback_data="wday_monday_odd"),
                InlineKeyboardButton(text="Вт", callback_data="wday_tuesday_odd"),
                InlineKeyboardButton(text="Ср", callback_data="wday_wednesday_odd"),
                InlineKeyboardButton(text="Чт", callback_data="wday_thursday_odd"),
                InlineKeyboardButton(text="Пт", callback_data="wday_friday_odd"),
                InlineKeyboardButton(text="Сб", callback_data="wday_saturday_odd"),
            ],
            [
                InlineKeyboardButton(text=buttons[1], callback_data="week_even"),
                InlineKeyboardButton(text="Пн", callback_data="wday_monday_even"),
                InlineKeyboardButton(text="Вт", callback_data="wday_tuesday_even"),
                InlineKeyboardButton(text="Ср", callback_data="wday_wednesday_even"),
                InlineKeyboardButton(text="Чт", callback_data="wday_thursday_even"),
                InlineKeyboardButton(text="Пт", callback_data="wday_friday_even"),
                InlineKeyboardButton(text="Сб", callback_data="wday_saturday_even"),
            ],
            [InlineKeyboardButton(text="🔄 В главное меню", callback_data="tomain")],
        ]
    )
    return kb_dn


# Админ-меню
kb_admin = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✉ Рассылка", callback_data="mailing"),
            InlineKeyboardButton(
                text="👥 Список пользователей", callback_data="user_list"
            ),
            InlineKeyboardButton(
                text="⚡ Тех.работы", callback_data="toggle_maintenance"
            ),
        ]
    ]
)

# Кнопка возврата в админ-меню
kb_admin_back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 В админ-меню", callback_data="toadmin")]
    ]
)


kb_update_teachers = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="update_teachers_yes")]
    ]
)
