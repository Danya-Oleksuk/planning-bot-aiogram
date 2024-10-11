from aiogram import Router, F
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command

import markup
from utils import TaskForm
from database import is_user_in_database, new_user_insert, tasks_collection, get_tasks, add_task, edit_task, delete_all_tasks,  delete_task, count_tasks

router = Router()

@router.message(Command('start'))
async def start(message: Message):
    if is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы уже зарегистрировались!", reply_markup=markup.main_menu)
    else:
        new_user_insert(user_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
        await message.answer("Привет, вы зарегистрировались, удачи в планировании!", reply_markup=markup.main_menu)

@router.message(F.text.in_(['ℹ️Помощь по командам', '/help', '/info']))
async def help(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(
            "Информация по командам\n\n"
            "/plan - показ текущего плана\n"
            "/edit_plan - редактирование плана\n"
            "/add_task - добавить новую задачу\n"
            "/remove_task - удалить некоторые задачи\n"
            "/clear_plan - удалить все задачи\n", reply_markup=markup.main_menu)

@router.message(F.text.in_(['📋План', '/plan']))
async def show_plan(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        tasks = await get_tasks(user_id=message.from_user.id)

        if not tasks:
            await message.answer("❗️Ваш План на сегодня пуст!", reply_markup=markup.main_menu)
        else:
            await message.answer(f"Твой план:\n\n" + "\n".join([f"{i+1}. {task} - ⏳" for i, task in enumerate(tasks)]), reply_markup=markup.main_menu)

@router.message(F.text.in_(['/clear_plan']))
async def clear_plan(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        res = await delete_all_tasks(user_id=message.from_user.id)

        if res is True:
            await message.answer(f"❗️Теперь ваш план пуст", reply_markup=markup.main_menu)
        else:
            await message.answer(f"❗️План и так пуст!", reply_markup=markup.main_menu)

@router.message(F.text.in_(['📝Редактировать план', '/edit_plan']))
async def edit_plan(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        tasks = await get_tasks(user_id=message.from_user.id)
        await message.answer(f"Твой план:\n\n" + "\n".join([f"⏳{i + 1}. {task}" for i, task in enumerate(tasks)]),
                             reply_markup=markup.edit_menu)

@router.message(F.text.in_(['➕Добавить задачу', '/add_task']))
async def create_task(message: Message, state: FSMContext):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Введите название задачи:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TaskForm.task_name)

@router.message(TaskForm.task_name)
async def task_name(message: Message, state: FSMContext):
    await add_task(user_id=message.from_user.id, task_description=message.text)
    await state.clear()
    await message.answer('✅Задача была добавлена', reply_markup=markup.edit_menu)

@router.message(F.text.in_(['❌Удалить задачу', '/remove_task']))
async def remove_task(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        tasks = await get_tasks(user_id=message.from_user.id)

        if not tasks:
            await message.answer("❗️Ваш план пуст", reply_markup=markup.edit_menu)
        else:
            await message.answer(f"Выберете задачу, которую вы хотите удалить:\n\n" + "\n".join([f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                                 reply_markup=markup.inline_builder(num=await count_tasks(user_id=message.from_user.id)).as_markup())

@router.callback_query(F.data.startswith('delete_'))
async def task_remove(call: CallbackQuery):
    task_num = int(call.data.split('_')[1])
    result = await delete_task(number_of_task=task_num, user_id=call.from_user.id)

    if result is True:
        tasks = await get_tasks(user_id=call.from_user.id)

        if not tasks:
            await call.message.answer("❗️Теперь ваш план пуст", reply_markup=markup.edit_menu)
        else:
            await call.message.answer(f"Выберете задачу, которую вы хотите удалить:\n\n" + "\n".join([f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                                 reply_markup=markup.inline_builder(num=await count_tasks(user_id=call.from_user.id)).as_markup())
        await call.answer("Удалил")

    elif result is False:
        await call.answer("Что то пошло не так!")

@router.message(F.text.in_(['⬅️Назад', ]))
async def back(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer('⚙️ Меню', reply_markup=markup.main_menu)

@router.message()
async def error(message: Message):
    if not is_user_in_database(telegram_id=message.from_user.id):
        await message.answer("Вы не зарегистрированы, нажмите /start!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Непонятная команда, попробуйте снова!", reply_markup=markup.main_menu)