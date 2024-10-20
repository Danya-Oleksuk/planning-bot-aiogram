from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def get_menu(is_admin: bool):
    buttons = [
        [
            KeyboardButton(text="📋План"),
        ],
        [
            KeyboardButton(text="📝Редактировать план"),
        ],
        [
            KeyboardButton(text="ℹ️Помощь по командам"),
        ],
    ]

    if is_admin:
        buttons.append([KeyboardButton(text="➡️ Админ панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, input_field_placeholder="Выберите вариант.. ")

edit_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить задачу"),
            KeyboardButton(text="✔️ Изменить статус задачи"),
        ],
        [
                KeyboardButton(text="❌ Удалить задачу"),
                KeyboardButton(text="🧹 Очистить весь план"),
        ],
        [
            KeyboardButton(text="⬅️ Назад"),
        ],
    ],

    resize_keyboard=True,
    input_field_placeholder="Выберите вариант.. "
)

admin_panel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👥 Вывести пользователей"),
            KeyboardButton(text="📋 Вывести все коллекции"),
            KeyboardButton(text="🪧 Создать пост рекламы"),
        ],
        [
            KeyboardButton(text="⬅️ Назад"),
        ],
    ],

    resize_keyboard=True,
)

vip_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="7 дней за 100 ⭐️ / $1.99", callback_data='vip_1_week_access'),
        ],
        [
            InlineKeyboardButton(text="1 месяц за 200 ⭐️ / $3.99", callback_data='vip_1_month_access'),
        ],
        [
            InlineKeyboardButton(text="1 год за 500 ⭐️ / $9.49", callback_data='vip_1_year_access'),
        ],
    ],

    resize_keyboard=True,
)

def inline_builder(num: int, emoji: str, action: str):
    builder = InlineKeyboardBuilder()

    for x in range(num):
        builder.button(text=str(f"{emoji} {x + 1}"), callback_data=f"{action}_{x + 1}")
    builder.adjust(5)

    return builder.as_markup()

def get_post_confirm():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отправить сейчас", callback_data="post_confirm"),
        InlineKeyboardButton(text="Отменить", callback_data="post_cancel")
    )

    return builder.as_markup()