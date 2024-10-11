from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
import markup

from database import is_user_in_database, new_user_insert, tasks_collection, get_tasks, add_task, edit_task, delete_all_tasks

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
        "Информация по командам\n\n"
        "/plan - показ текущего плана\n"
        "/edit_plan - редактирование плана\n",
        reply_markup=markup.main_menu
    )

@router.message(F.text.in_(['📋План', '/plan']))
async def show_plan(message: Message):
    tasks = await get_tasks(user_id=message.from_user.id)
    if not tasks:
        await message.answer("❗️Ваш План на сегодня пуст!", reply_markup=markup.main_menu)
    else:
        await message.answer(f"Твой план:\n\n" + "\n".join([f"⏳{i+1}. {task}" for i, task in enumerate(tasks)]))


@router.message(F.text.in_(['/add']))
async def add_plan(message: Message):
    tasks = await add_task(user_id=message.from_user.id, task_description='Сделать дз')
    await message.answer(f"Добавлено!")

@router.message(F.text.in_(['/clear']))
async def clear_plan(message: Message):
    res = await delete_all_tasks(user_id=message.from_user.id)

    if res is True:
        await message.answer(f"Очищено!", reply_markup=markup.main_menu)
    else:
        await message.answer(f"❗️План и так пуст!", reply_markup=markup.main_menu)

# @router.message(F.text.in_(['📝Редактировать план', '/edit_plan']))
# async def show_plan(message: Message):
#     tasks = await edit_task(user_id=message.from_user.id)
#     await message.answer(f"Твой план: \n {tasks_collection}")

@router.message()
async def error(message: Message):
    await message.answer("Непонятная команда, попробуйте снова!", reply_markup=markup.main_menu)