from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
import markup

from database import is_user_in_database, new_user_insert

router = Router()

@router.message(Command('start'))
async def start(message: Message):
    if is_user_in_database(telegram_id=message.from_user.id):
        await message.reply("Привет, вы уже зарегистрировались!", reply_markup=markup.main_menu)
    else:
        new_user_insert(user_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
        await message.answer("Привет, вы зарегистрировались, удачи в планировании!", reply_markup=markup.main_menu)

@router.message(F.text.in_(['ℹ️Помощь', '/help']))
async def help(message: Message):
    await message.answer(
        "Информация по командам\n\n/plan - начало планирования дня\n"
        "/plan - показ текущего плана\n"
        "/edit_plan - редактирование плана\n",
        reply_markup=markup.main_menu
    )



@router.message()
async def start(message: Message):
    await message.answer("Непонятная команда, попробуйте снова!", reply_markup=markup.main_menu)