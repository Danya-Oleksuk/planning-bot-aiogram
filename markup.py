from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📋План"),
        ],
        [
            KeyboardButton(text="📝Редактировать план"),
        ],
        [
            KeyboardButton(text="ℹ️Помощь"),
        ],
    ],

    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите вариант.. "
)

