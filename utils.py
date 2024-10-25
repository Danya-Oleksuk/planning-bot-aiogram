from aiogram import BaseMiddleware
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, CallbackQuery

from database import is_user_in_database


class TaskForm(StatesGroup):
    task_name = State()

class PostForm(StatesGroup):
    text = State()
    picture = State()
    confirm = State()

class PaymentForm(StatesGroup):
    payment = State()
    waiting_for_payment= State()

async def check_and_notify_registration(message) -> bool:
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
        return False
    return True

async def check_and_notify_fsm_state(message, state) -> bool:
    current_state = await state.get_state()

    if current_state == 'TaskForm:task_name':
        await message.answer("❗️Команда не может быть выполнена, вы находитесь в процессе ввода\n\n✍️ Введите название задачи:")
        return False
    elif current_state == 'PostForm:text' or current_state == 'PostForm:picture':
        await message.answer("❗️Команда не может быть выполнена, вы находитесь в процессе ввода")
        return False
    return True