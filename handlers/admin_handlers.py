import datetime
import os

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from dotenv import load_dotenv

from keyboards import markup
from config import admin_id
from database import (get_all_not_vip_users, get_all_tasks, get_all_users,
                      get_all_users_id, get_all_vip_users, get_user_is_banned,
                      is_user_in_database, is_vip, set_vip)
from utils import (PostForm, VipForm, check_and_notify_fsm_state,
                   check_and_notify_registration)

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
        users = await get_all_users()
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

@router.message(F.text == 'ℹ️ Вывести кол. vip пользователей')
async def create_post_advertisement(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        vip_users = await get_all_vip_users()
        await message.answer(f"{len(vip_users)} vip пользователей", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(F.text == 'ℹ️ Вывести кол. не vip пользователей')
async def create_post_advertisement(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        not_vip_users = await get_all_not_vip_users()
        await message.answer(f"{len(not_vip_users)} не vip пользователей", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))

@router.message(F.text == '🎁 Подарить вип пользователю')
async def gift_the_vip(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if message.from_user.id == int(admin_id):
        await message.answer("🆔 Введите id пользователя:", parse_mode=ParseMode.MARKDOWN,
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(VipForm.user_name)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(False))


@router.message(VipForm.user_name, F.text)
async def post_text(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    await state.update_data(user_name=message.md_text)
    await message.answer("✔️ Юзер добавлен\n\n📅 Введите дату vip статуса (1w/1m/1y):")
    await state.set_state(VipForm.date)

@router.message(VipForm.date, F.text)
async def post_text(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    await state.update_data(until_date=message.md_text)
    data = await state.get_data()

    if not await is_user_in_database(telegram_id=int(data['user_name'])):
        await message.answer(f"⚠️ Был введен <b>не правильный id</b>", parse_mode=ParseMode.HTML,
                             reply_markup=markup.get_menu(True))
        await state.clear()
        return
    try:
        if data['until_date'] in ('1w', '1m', '1y'):
            until_date = None

            if data['until_date'] == '1w':
                until_date = datetime.datetime.now() + datetime.timedelta(days=7)
            elif data['until_date'] == '1m':
                until_date = datetime.datetime.now() + datetime.timedelta(days=30)
            elif data['until_date'] == '1y':
                until_date = datetime.datetime.now() + datetime.timedelta(days=365)

            await set_vip(user_id=int(data['user_name']), until=until_date)
            await message.answer(f'🥳 Vip статус успешно подарен', reply_markup=markup.get_menu(True))
        else:
            await message.answer(f'⚠️ <b>Дата</b> введена не правильно', parse_mode=ParseMode.HTML,
                                 reply_markup=markup.get_menu(True))
    except Exception as ex:
        await message.answer(f'⚠️ <b>Не получилось подарить vip, ошибка</b> - {ex}', parse_mode=ParseMode.HTML,
                             reply_markup=markup.get_menu(True))
    finally:
        await state.clear()


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

        for (tg_id) in await get_all_users_id():
            if not await get_user_is_banned(user_id=tg_id):
                if not await is_vip(user_id=tg_id):
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