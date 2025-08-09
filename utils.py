from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from config import ADMIN_ID
from database.postgres import StatsRepository, UserRepository, VipRepository, initiate_pool


class TaskForm(StatesGroup):
    task_name = State()

class PostForm(StatesGroup):
    text = State()
    picture = State()
    confirm = State()

class PaymentForm(StatesGroup):
    payment = State()
    waiting_for_payment= State()

class VipForm(StatesGroup):
    user_name = State()
    date= State()

class BanForm(StatesGroup):
    user_id = State()

class UnBanForm(StatesGroup):
    user_id = State()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def check_and_notify_registration(message, user_repo) -> bool:

    if not await user_repo.is_user_in_database(telegram_id=message.from_user.id):
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

async def send_user_message(user_id: int, text: str, keyboard=None) -> None:
    try:
        from config import BOT_TOKEN
        from aiogram import Bot
        from aiogram.enums import ParseMode

        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard or ReplyKeyboardRemove())
    except Exception as e:
        print(f"Failed to send message to user {user_id}: {e}")