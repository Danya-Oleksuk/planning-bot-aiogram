from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

from database import is_user_in_database


class TaskForm(StatesGroup):
    task_name = State()

class PostForm(StatesGroup):
    text = State()
    picture = State()
    confirm = State()

async def check_and_notify_registration(message) -> bool:
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
        return False
    return True

async def check_and_notify_fsm_state(message, state) -> bool:
    current_state = await state.get_state()

    if current_state is not None:
        await message.answer("❗️Команда не может быть выполнена, вы находитесь в процессе ввода\n\n✍️ Введите название задачи:")
        return False
    return True