from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from dotenv import load_dotenv
import os


import markup
from utils import TaskForm, check_and_notify_registration, check_and_notify_fsm_state
from database import (is_user_in_database, new_user_insert,get_tasks, add_task, edit_task_status,
                      delete_all_tasks, delete_task, count_tasks, get_all_tasks, get_all_users)

load_dotenv()

admin_id = os.getenv('ADMIN_ID')
router = Router()


@router.message(F.text == '➡️ Админ панель')
async def admin_panel(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return
    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("👨🏻‍💻 Админ панель активирована:", reply_markup=markup.admin_panel)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(F.text == '👥 Вывести пользователей')
async def show_all_users(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        users = get_all_users()
        users_data = [f"{i} - {x} - {z}" for i, x, z in users]
        await message.answer(text="\n".join(users_data))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(F.text == '📋 Вывести все коллекции')
async def show_all_collections(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        collections = await get_all_tasks()
        await message.answer(text=f"\n".join(collections))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    if not await check_and_notify_fsm_state(message, state):
        return

    if is_user_in_database(telegram_id=message.from_user.id):
        if message.from_user.id == int(admin_id):
            await message.answer("Вы уже зарегистрировались!", reply_markup=markup.get_menu(True))
        else:
            await message.answer("Вы уже зарегистрировались!", reply_markup=markup.get_menu(False))
    else:
        new_user_insert(user_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
        await message.answer("👋 Привет, вы зарегистрировались, удачи в планировании!", reply_markup=markup.get_menu(False))

@router.message(F.text.in_(['ℹ️Помощь по командам', '/help', '/info']))
async def help(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return
    if message.from_user.id == int(admin_id):
        await message.answer("<b>Информация по командам</b>\n\n"
                "/plan — <i>показ текущего плана</i>\n"
                "/edit_plan — <i>редактирование плана</i>\n"
                "/add_task — <i>добавить новую задачу</i>\n"
                "/remove_task — <i>удалить некоторые задачи</i>\n"
                "/clear_plan — <i>удалить все задачи</i>\n",
                             parse_mode=ParseMode.HTML, reply_markup=markup.get_menu(True))
    else:
        await message.answer(
                "<b>Информация по командам</b>\n\n"
                "/plan — <i>показ текущего плана</i>\n"
                "/edit_plan — <i>редактирование плана</i>\n"
                "/add_task — <i>добавить новую задачу</i>\n"
                "/remove_task — <i>удалить некоторые задачи</i>\n"
                "/clear_plan — <i>удалить все задачи</i>\n", parse_mode=ParseMode.HTML, reply_markup=markup.get_menu(False))

@router.message(F.text.in_(['📋План', '/plan']))
async def show_plan(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    tasks = await get_tasks(user_id=message.from_user.id)
    if not tasks:
        if message.from_user.id == int(admin_id):
            await message.answer("❗️Ваш план на сегодня пуст!", reply_markup=markup.get_menu(True))
        else:
            await message.answer("❗️Ваш план на сегодня пуст!", reply_markup=markup.get_menu(False))
    else:
        if message.from_user.id == int(admin_id):
            await message.answer(
                "🗂 <b>Твой план:</b>\n\n" +
                "\n".join(
                    [f"{i + 1}. {list(task.keys())[0]} — {'✅' if list(task.values())[0] == 'Выполнено' else '❌'}" for
                     i, task in
                     enumerate(tasks)]),
                reply_markup=markup.get_menu(True),
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer(
                "🗂 <b>Твой план:</b>\n\n" +
                "\n".join(
                    [f"{i + 1}. {list(task.keys())[0]} — {'✅' if list(task.values())[0] == 'Выполнено' else '❌'}" for
                     i, task in
                     enumerate(tasks)]),
                reply_markup=markup.get_menu(False),
                parse_mode=ParseMode.HTML
            )

@router.message(F.text.in_(['🧹 Очистить весь план', '/clear_plan']))
async def clear_plan(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    res = await delete_all_tasks(user_id=message.from_user.id)
    if res is True:
        if message.from_user.id == int(admin_id):
            await message.answer(f"❗️Теперь ваш план пуст", reply_markup=markup.get_menu(True))
        else:
            await message.answer(f"❗️Теперь ваш план пуст", reply_markup=markup.get_menu(False))
    else:
        await message.answer(f"❗️План и так пуст", reply_markup=markup.edit_menu)

@router.message(F.text.in_(['📝Редактировать план', '/edit_plan']))
async def edit_plan(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    await message.answer("🖋 Меню редактирования: ", reply_markup=markup.edit_menu)

@router.message(F.text.in_(['➕ Добавить задачу', '/add_task']))
async def create_task(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    await message.answer("✍️ Введите название задачи:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TaskForm.task_name)

@router.message(F.text.in_(['❌ Удалить задачу', '/remove_task']))
async def initiate_task_removal(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    tasks = await get_tasks(user_id=message.from_user.id)

    if not tasks:
        await message.answer("❗️Ваш план пуст", reply_markup=markup.edit_menu)
    else:

        tasks = [key for task in tasks for key in task.keys()]
        await message.answer(f"Выберете задачу, которую вы хотите удалить:\n\n" + "\n".join(
            [f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                             reply_markup=markup.inline_builder(num=await count_tasks(user_id=message.from_user.id),
                                                                emoji="🗑", action="delete"))

@router.message(F.text.in_(['✔️ Изменить статус задачи', '/edit_task_status']))
async def edit_task_status_(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    tasks = await get_tasks(user_id=message.from_user.id)
    if not tasks:
        await message.answer("❗️Ваш план пуст", reply_markup=markup.edit_menu)
    else:
        tasks = [key for task in tasks for key in task.keys()]
        ReplyKeyboardRemove()
        await message.answer(f"Выберете задачу, которую вы хотите выполнить:\n\n" + "\n".join(
            [f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                             reply_markup=markup.inline_builder(num=await count_tasks(user_id=message.from_user.id),
                                                                emoji="✅", action="update"))

@router.message(F.text.in_(['⬅️ Назад', ]))
async def back_1(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return
    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer('⚙️ Меню', reply_markup=markup.get_menu(True))
    else:
        await message.answer('⚙️ Меню', reply_markup=markup.get_menu(False))

@router.message(TaskForm.task_name)
async def task_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer("❗️Название задачи не должно быть больше 50 символов\n\n✍️  Введите название задачи:")
        return
    await add_task(user_id=message.from_user.id, task_description=message.text)
    await state.clear()
    await message.answer('✅ Задача была добавлена', reply_markup=markup.edit_menu)

@router.callback_query(F.data.startswith('delete_'))
async def confirm_task_removal(call: CallbackQuery):
    task_num = int(call.data.split('_')[1])
    result = await delete_task(number_of_task=task_num, user_id=call.from_user.id)

    if result is True:
        tasks = await get_tasks(user_id=call.from_user.id)

        tasks = [key for task in tasks for key in task.keys()]

        if not tasks:
            await call.message.answer("❗️Ваш план пуст", reply_markup=markup.edit_menu)
        else:
            await call.message.answer(f"Выберете задачу, которую вы хотите удалить:\n\n" + "\n".join(
                [f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                                 reply_markup=markup.inline_builder(num=await count_tasks(user_id=call.from_user.id),
                                                                    emoji="🗑", action="delete"))
        await call.answer("Удалил")

    elif result is False:
        await call.answer("Что то пошло не так!")

@router.callback_query(F.data.startswith('update_'))
async def update_task_status(call: CallbackQuery):
    task_num = int(call.data.split('_')[1])
    result = await edit_task_status(user_id=call.from_user.id, task_number=task_num)

    if result is True:
        tasks = await get_tasks(user_id=call.from_user.id)

        if not tasks:
            if call.from_user.id == int(admin_id):
                await call.message.answer("❗️Ваш план теперь пуст", reply_markup=markup.get_menu(True))
            else:
                await call.message.answer("❗️Ваш план теперь пуст", reply_markup=markup.get_menu(False))
            return

        tasks_list = [
            f"{i + 1}. {list(task.keys())[0]} - <i>{list(task.values())[0]}</i>"
            for i, task in enumerate(tasks)
        ]

        await call.message.answer(
            f"Выберите задачу, которую вы хотите выполнить:\n\n" + "\n".join(tasks_list), parse_mode=ParseMode.HTML,
            reply_markup=markup.inline_builder(num=await count_tasks(user_id=call.from_user.id), emoji="✅", action="update"))
        await call.answer("Обновил")

    elif result is False:
        await call.answer("Что-то пошло не так!")

@router.message()
async def error(message: Message):
    if not await check_and_notify_registration(message):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(True))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))