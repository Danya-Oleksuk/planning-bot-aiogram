from aiogram import Router, F
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, IS_NOT_MEMBER, IS_MEMBER
from dotenv import load_dotenv
import os
import datetime

import markup
from utils import check_and_notify_registration, check_and_notify_fsm_state, TaskForm, PaymentForm
from database import (add_task, delete_task, get_tasks, edit_task_status, count_tasks, get_all_tasks, delete_all_tasks,
                      is_user_in_database, new_user_insert, is_vip, set_vip, set_vip_off, get_vip_until,
                      user_blocked_bot, user_unblocked_bot)


load_dotenv()
admin_id = os.getenv('ADMIN_ID')

router_1 = Router()
router_2 = Router()

@router_1.message(Command('start'))
async def start(message: Message, state: FSMContext):
    if not await check_and_notify_fsm_state(message, state):
        return

    if await is_user_in_database(telegram_id=message.from_user.id):
        if message.from_user.id == int(admin_id):
            await message.answer("Вы уже зарегистрировались!", reply_markup=markup.get_menu(True))
        else:
            await message.answer("Вы уже зарегистрировались!", reply_markup=markup.get_menu(False))
    else:
        await new_user_insert(user_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        username=message.from_user.username,
                        last_name=message.from_user.last_name,
                        is_vip=True if message.from_user.id == int(admin_id) else False)
        await message.answer("👋 Привет, вы зарегистрировались, удачи в планировании!",
                             reply_markup=markup.get_menu(True if message.from_user.id == int(admin_id) else False))

@router_1.message(F.text.in_(['ℹ️Помощь по командам', '/help', '/info']))
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
                "/clear_plan — <i>удалить все задачи</i>\n"
                "/pay - <i>Отключить все лимиты и поддержать бота</i>\n",
                             parse_mode=ParseMode.HTML, reply_markup=markup.get_menu(True))
    else:
        await message.answer(
                "<b>Информация по командам</b>\n\n"
                "/plan — <i>показ текущего плана</i>\n"
                "/edit_plan — <i>редактирование плана</i>\n"    
                "/add_task — <i>добавить новую задачу</i>\n"
                "/remove_task — <i>удалить некоторые задачи</i>\n"
                "/clear_plan — <i>удалить все задачи</i>\n"
                "/pay - <i>Отключить все лимиты и поддержать бота</i>\n",
                            parse_mode=ParseMode.HTML, reply_markup=markup.get_menu(False))

@router_1.message(F.text.in_(['📋План', '/plan']))
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
        if await is_vip(user_id=message.from_user.id) and not message.from_user.id == int(admin_id):
            is_still_vip = datetime.datetime.now() < datetime.datetime.strptime(await get_vip_until(message.from_user.id),
                                                                                "%Y-%m-%d %H:%M:%S.%f")
            if not is_still_vip:
                await set_vip_off(user_id=message.from_user.id)

        if await is_vip(user_id=message.from_user.id) or message.from_user.id == int(admin_id):
            completed_tasks = []
            not_completed_tasks = []
            status = True if message.from_user.id == int(admin_id) else False

            for x in tasks:
                if list(x.values())[0] == '✅':
                    completed_tasks.append(x)
                else:
                    not_completed_tasks.append(x)

            if not completed_tasks:
                answer = "🗂 <b>Твой план:</b>\n\n" + "\n".join(
                    [f"{i + 1}. {list(task.keys())[0]} - {list(task.values())[0]}" for i, task in
                     enumerate(not_completed_tasks)])
            else:
                answer = "🗂 <b>Твой план:</b>\n\n" + "\n".join(
                    [f"{i + 1}. {list(task.keys())[0]} - {list(task.values())[0]}" for i, task in
                     enumerate(not_completed_tasks)]) + "\n————————\n\n" + '\n'.join(
                    [f"{i + 1}. <s>{list(task.keys())[0]}</s> - {list(task.values())[0]}" for i, task in
                     enumerate(completed_tasks)])
            await message.answer(text=answer, reply_markup=markup.get_menu(status), parse_mode=ParseMode.HTML)
        else:
            await message.answer(
                "🗂 <b>Твой план:</b>\n\n" +
                "\n".join(
                    [f"{i + 1}. {list(task.keys())[0]} — {list(task.values())[0]}" for
                     i, task in
                     enumerate(tasks)]),
                reply_markup=markup.get_menu(False),
                parse_mode=ParseMode.HTML
            )

@router_2.message(F.text.in_(['🧹 Очистить весь план', '/clear_plan']))
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

@router_2.message(F.text.in_(['📝Редактировать план', '/edit_plan']))
async def edit_plan(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    await message.answer("🖋 Меню редактирования: ", reply_markup=markup.edit_menu)

@router_1.message(F.text.in_(['➕ Добавить задачу', '/add_task']))
async def create_task(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if await count_tasks(user_id=message.from_user.id) < 3:
        await message.answer("✍️ Введите название задачи:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TaskForm.task_name)
    elif message.from_user.id == int(admin_id):
        await message.answer("✍️ Введите название задачи:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(TaskForm.task_name)
    elif await is_vip(user_id=message.from_user.id):
        is_still_vip = datetime.datetime.now() < datetime.datetime.strptime(await get_vip_until(message.from_user.id),
                                                                            "%Y-%m-%d %H:%M:%S.%f")

        if is_still_vip:
            await message.answer("✍️ Введите название задачи:", reply_markup=ReplyKeyboardRemove())
            await state.set_state(TaskForm.task_name)
        elif not is_still_vip:
            await set_vip_off(user_id=message.from_user.id)
            await message.answer("✍️ К сожалению ваша подписка прошла, продлить - /pay", reply_markup=markup.edit_menu)
    else:
        await message.answer("✍️ К сожалению лимит исчерпан, /pay", reply_markup=markup.edit_menu)

@router_2.message(F.text.in_(['❌ Удалить задачу', '/remove_task']))
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

@router_2.message(F.text.in_(['✔️ Изменить статус задачи', '/edit_task_status']))
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
        await message.answer(f"Выберете задачу, которую вы хотите выполнить:\n\n" + "\n".join(
            [f"{i + 1}. {task}" for i, task in enumerate(tasks)]),
                             reply_markup=markup.inline_builder(num=await count_tasks(user_id=message.from_user.id),
                                                                emoji="✅", action="update"))

@router_2.message(F.text.in_(['⬅️ Назад', ]))
async def back_1(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return
    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer('⚙️ Меню', reply_markup=markup.get_menu(True))
    else:
        await message.answer('⚙️ Меню', reply_markup=markup.get_menu(False))

@router_2.message(Command('pay'))
async def pay(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("👨🏻‍💻 Ты и так админ", reply_markup=markup.get_menu(True))
    else:
        if await is_vip(user_id=message.from_user.id):
            is_still_vip = datetime.datetime.now() < datetime.datetime.strptime(await get_vip_until(message.from_user.id),
                                                                                "%Y-%m-%d %H:%M:%S.%f")
            if not is_still_vip:
                await set_vip_off(user_id=message.from_user.id)

        vip_until_date = await get_vip_until(message.from_user.id)
        await state.set_state(PaymentForm.payment)

        if vip_until_date is None:
            await message.answer("<b>Приобретая премиум, вы открываете для себя расширенные возможности:</b>"
                                 "\n\n📌 <i>Отсутствие лимита задач</i>"
                                 "\n📌<i> Сортировка задач по выполнению</i>"
                                 "\n📌 <i>Отсутствие рекламы</i>"
                                 "\n📌 <i>Поддержка бота</i>"
                                 "\n\n<i>Выберите подходящий для вас срок подписки:</i>", parse_mode=ParseMode.HTML, reply_markup=markup.vip_menu)
        else:
            await message.answer(f"<b><u>Ваша подписка еще активна до {vip_until_date[:10]}\n\n</u></b>"
                                 "<b>Приобретая премиум, вы открываете для себя расширенные возможности:</b>"
                                 "\n\n📌 <i>Отсутствие лимита задач</i>"
                                 "\n📌 <i>Сортировка задач по выполнению</i>"
                                 "\n📌 <i>Отсутствие рекламы</i>"
                                 "\n📌 <i>Поддержка бота</i>"
                                 "\n\n<i>Выберите подходящий для вас срок подписки:</i>", parse_mode=ParseMode.HTML,
                                 reply_markup=markup.vip_menu)

@router_1.message(TaskForm.task_name)
async def task_name(message: Message, state: FSMContext):
    if not message.text:
        return
    elif len(message.text) > 50:
        await message.answer("❗️Название задачи не должно быть больше 50 символов\n\n✍️  Введите название задачи:")
        return

    await add_task(user_id=message.from_user.id, task_description=message.text)
    await state.clear()
    await message.answer('✅ Задача была добавлена', reply_markup=markup.edit_menu)

@router_1.callback_query(F.data.startswith('delete_'))
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

@router_1.callback_query(F.data.startswith('update_'))
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

@router_1.callback_query(F.data == 'vip_1_week_access')
async def vip_1_week_access_(call: CallbackQuery, state: FSMContext):

    await state.set_state(PaymentForm.waiting_for_payment)
    await call.message.answer_invoice(
        title='Покупка премиума',
        description="Приобретая премиум, вы открываете для себя расширенные возможности:"
                                 "\n\n📌 Отсутствие лимита задач"
                                 "\n📌 Сортировка задач по выполнению"
                                 "\n📌 Отсутствие рекламы"
                                 "\n📌 Поддержка бота",
        payload='vip_1_week_access',
        currency='XTR',
        prices=[LabeledPrice(label='XTR', amount=1)]
    )

@router_1.callback_query(F.data == 'vip_1_month_access')
async def vip_1_month_access_(call: CallbackQuery, state: FSMContext):


    await state.set_state(PaymentForm.waiting_for_payment)
    await call.message.answer_invoice(
        title='Покупка премиума',
        description="Приобретая премиум, вы открываете для себя расширенные возможности:"
                                 "\n\n📌 Отсутствие лимита задач"
                                 "\n📌 Сортировка задач по выполнению"
                                 "\n📌 Отсутствие рекламы"
                                 "\n📌 Поддержка бота",
        payload='vip_1_month_access',
        currency='XTR',
        prices=[LabeledPrice(label='XTR', amount=200)]
    )

@router_1.callback_query(F.data == 'vip_1_year_access')
async def vip_1_year_access_(call: CallbackQuery, state: FSMContext):

    await state.set_state(PaymentForm.waiting_for_payment)
    await call.message.answer_invoice(
        title='Покупка премиума',
        description="Приобретая премиум, вы открываете для себя расширенные возможности:"
                                 "\n\n📌 Отсутствие лимита задач"
                                 "\n📌 Сортировка задач по выполнению"
                                 "\n📌 Отсутствие рекламы"
                                 "\n📌 Поддержка бота",
        payload='vip_1_year_access',
        currency='XTR',
        prices=[LabeledPrice(label='XTR', amount=500)]
    )

@router_1.pre_checkout_query()
async def process_pre_checkout_query(event: PreCheckoutQuery, state: FSMContext):
    await event.answer(ok=True)
    await state.clear()

@router_1.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload

    if payload == 'vip_1_week_access':
        vip_until = datetime.datetime.now() + datetime.timedelta(seconds=20) # !!! TEST
    elif payload == 'vip_1_month_access':
        vip_until = datetime.datetime.now() + datetime.timedelta(days=30)
    elif payload == 'vip_1_year_access':
        vip_until = datetime.datetime.now() + datetime.timedelta(days=365)
    else:
        return

    await set_vip(user_id=message.from_user.id, until=vip_until)
    vip_until_date = await get_vip_until(message.from_user.id)
    await message.answer("🥳 Спасибо за поддержку бота. Все услуги предоставлены!"
                         f"\n\n<b><u>Ваша подписка теперь активна до {vip_until_date[:10]}</u></b>",
                         parse_mode=ParseMode.HTML,
                         reply_markup=markup.get_menu(False))

@router_1.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER))
async def user_blocked_bot_(event: ChatMemberUpdatedFilter):
    await user_blocked_bot(user_id=event.from_user.id)

@router_1.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER))
async def user_unblocked_bot_(event: ChatMemberUpdatedFilter):
    await user_unblocked_bot(user_id=event.from_user.id)