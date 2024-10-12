from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

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
    one_time_keyboard=True,
    input_field_placeholder="Выберите вариант.. "
)

def inline_builder(num: int, emoji: str, action: str):
    builder = InlineKeyboardBuilder()

    for x in range(num):
        builder.button(text=str(f"{emoji} {x + 1}"), callback_data=f"{action}_{x + 1}")
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data='back_to_edit'))
    builder.adjust(5)

    return builder.as_markup()