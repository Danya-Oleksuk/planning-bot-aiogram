from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from dotenv import load_dotenv
import os

import markup
from utils import  check_and_notify_registration, check_and_notify_fsm_state, PostForm
from handlers import admin_id
from database import (is_user_in_database, new_user_insert,get_tasks, add_task,
                      edit_task_status,delete_all_tasks, delete_task, count_tasks, get_all_tasks,
                      get_all_users, get_all_users_id, is_vip, get_user_is_banned)

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
        users_data = [f"{i} - {x} - @{z} - {y}" for i, x, z, y in users]
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

@router.message(F.text == '🪧 Создать пост рекламы')
async def create_post_advertisement(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("📖 Введите текст поста:", parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        await state.set_state(PostForm.text)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(PostForm.text, F.text)
async def post_text(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    await state.update_data(text=message.md_text)
    await message.answer("✔️ Текст добавлен\n\n🖼 Добавьте фото:")
    await state.set_state(PostForm.picture)


@router.message(PostForm.picture)
async def post_picture(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not message.photo:
        return
    await state.update_data(picture=message.photo[-1].file_id)
    data = await state.get_data()
    await state.set_state(PostForm.confirm)

    await message.answer_photo(data['picture'], caption=data['text'], parse_mode=ParseMode.MARKDOWN, reply_markup=markup.get_post_confirm())

@router.callback_query(PostForm.confirm)
async def is_post_confirm(callback_query: CallbackQuery, state: FSMContext):

    if callback_query.data == 'post_confirm':
        load_dotenv()
        bot_token = os.environ.get('BOT_TOKEN')

        bot = Bot(token=bot_token)
        counter = 0
        data = await state.get_data()

        for (tg_id, ) in get_all_users_id():
            if not get_user_is_banned(user_id=tg_id):
                if not is_vip(user_id=tg_id):
                    await bot.send_photo(chat_id=tg_id, photo=data['picture'], caption=data['text'], parse_mode=ParseMode.MARKDOWN)
                    counter += 1

        await state.clear()
        await callback_query.message.answer(f"🆒 Реклама успешно доставлена, {counter} юзеров получили рекламу.", reply_markup=markup.admin_panel)
        await callback_query.answer()

    elif callback_query.data == 'post_cancel':
        await state.clear()
        await callback_query.message.answer("😞 Рассылка была отменена", reply_markup=markup.admin_panel)
        await callback_query.answer()

@router.message()
async def error(message: Message):
    if not await check_and_notify_registration(message):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(True))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))