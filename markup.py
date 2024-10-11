from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋План"),
        ],
        [
            KeyboardButton(text="📝Редактировать план"),
        ],
        [
            KeyboardButton(text="ℹ️Помощь по командам"),
        ],
    ],

    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите вариант.. "
)

edit_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕Добавить задачу"),
            KeyboardButton(text="❌Удалить задачу"),
        ],
        [
            KeyboardButton(text="⬅️Назад"),
        ],
    ],

    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите вариант.. "
)

def inline_builder(num):
    builder = InlineKeyboardBuilder()

    for x in range(num):
        builder.button(text=str(f"🗑 {x + 1}"), callback_data=f"delete_{x + 1}")
    builder.adjust(5)

    return builder