import datetime

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from keyboards import markup

from database.postgres import (get_all_users, get_all_users_id, get_user_is_banned,
                               is_user_in_database, is_user_vip, activate_vip, get_all_vip_users,
                               get_all_not_vip_users)

from database.mongo import fetch_all_tasks

from utils import is_admin, PostForm, VipForm, check_and_notify_fsm_state, check_and_notify_registration

from config import BOT_TOKEN


router = Router()

@router.message(F.text == '➡️ Админ панель')
async def admin_panel(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return
    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        await message.answer("👨🏻‍💻 Админ панель активирована:", reply_markup=markup.admin_panel)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == '👥 Вывести пользователей')
async def show_all_users(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        users = await get_all_users()
        users_data = [f"{i} - {x} - @{z} - {y}" for i, x, z, y in users]
        await message.answer(text="\n".join(users_data))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == '📋 Вывести все коллекции')
async def show_all_collections(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        collections = await fetch_all_tasks()
        await message.answer(text="\n".join(collections))
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == '🪧 Создать пост рекламы')
async def create_post_advertisement(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        await message.answer("📖 Введите текст поста:", parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
        await state.set_state(PostForm.text)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == 'ℹ️ Вывести кол. vip пользователей')
async def show_vip_count(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        vip_users = await get_all_vip_users()
        await message.answer(f"{len(vip_users)} vip пользователей", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == 'ℹ️ Вывести кол. не vip пользователей')
async def show_non_vip_count(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        not_vip_users = await get_all_not_vip_users()
        await message.answer(f"{len(not_vip_users)} не vip пользователей", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))

@router.message(F.text == '🎁 Подарить вип пользователю')
async def gift_the_vip(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    if not await check_and_notify_fsm_state(message, state):
        return

    if is_admin(message.from_user.id):
        await message.answer("🆔 Введите id пользователя:", parse_mode=ParseMode.MARKDOWN,
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(VipForm.user_name)
    else:
        await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))


@router.message(VipForm.user_name, F.text)
async def post_text_vip(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return

    try:
        user_id = int(message.md_text)

        if not await is_user_in_database(telegram_id=user_id):
            raise ValueError

        await state.update_data(user_name=message.md_text)
        await message.answer("✔️ Юзер добавлен\n\n📅 Введите дату vip статуса (1w/1m/1y/forever):")
        await state.set_state(VipForm.date)
    except ValueError:
        await message.answer("⚠️ Был введен <b>не правильный id</b>", parse_mode=ParseMode.HTML, reply_markup=markup.admin_panel)
        await state.clear()
        return

    
@router.message(VipForm.date, F.text)
async def post_text_regular(message: Message, state: FSMContext):
    if not await check_and_notify_registration(message):
        return
    
    bot = Bot(token=BOT_TOKEN)

    await state.update_data(until_date=message.md_text)
    data = await state.get_data()

    try:
        if data['until_date'] in ('1w', '1m', '1y', 'forever'):
            until_date = None
            period_str = ''

            if data['until_date'] == '1w':
                until_date = datetime.datetime.now() + datetime.timedelta(days=7)
                period_str = 'на неделю'
            elif data['until_date'] == '1m':
                until_date = datetime.datetime.now() + datetime.timedelta(days=30)
                period_str = 'на месяц'
            elif data['until_date'] == '1y':
                until_date = datetime.datetime.now() + datetime.timedelta(days=365)
                period_str = 'на год'
            elif data['until_date'] == 'forever':
                until_date = datetime.datetime.now() + datetime.timedelta(days=9999)
                period_str = 'на всегда'


            await activate_vip(user_id=int(data['user_name']), until=until_date)

            await message.answer('🥳 Vip статус успешно подарен', reply_markup=markup.get_menu(message.from_user.id))
                
            await bot.send_message(
                    int(data['user_name']),
                    f"🎉 <b>Поздравляем!</b>\n\n"
                    f"Вам был подарен <b>VIP статус</b> {period_str} ✨\n"
                    f"Статус действителен до <b><u>{'неограниченно' if until_date > datetime.datetime.now() + datetime.timedelta(days=999) else until_date.strftime('%Y-%m-%d')}</u></b> 🎁\n\n"
                    f"Наслаждайтесь привилегиями! 💎",
                    parse_mode=ParseMode.HTML
                )
        else:
            await message.answer('⚠️ <b>Дата</b> введена не правильно', parse_mode=ParseMode.HTML, reply_markup=markup.admin_panel)
    except Exception as ex:
        await message.answer(f'⚠️ <b>Не получилось подарить vip, ошибка</b> - {ex}', parse_mode=ParseMode.HTML, reply_markup=markup.get_menu(message.from_user.id))
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

        bot = Bot(token=BOT_TOKEN)
        counter = 0
        data = await state.get_data()

        for (tg_id) in await get_all_users_id():
            if not await get_user_is_banned(user_id=tg_id):
                if not await is_user_vip(user_id=tg_id):
                    await bot.send_photo(chat_id=tg_id, photo=data['picture'], caption=data['text'], parse_mode=ParseMode.MARKDOWN)
                    counter += 1

        await state.clear()
        await callback_query.message.answer(f"🎯 <b>Реклама успешно доставлена!</b>\n👤 Кол-во получателей: <b><u>{counter}</u></b>",
                                            reply_markup=markup.admin_panel, parse_mode=ParseMode.HTML)
        await callback_query.answer()

    elif callback_query.data == 'post_cancel':
        await state.clear()
        await callback_query.message.answer("😞 Рассылка была отменена", reply_markup=markup.admin_panel)
        await callback_query.answer()

@router.message()
async def error(message: Message):
    if not await check_and_notify_registration(message):
        return

    await message.answer("🤷🏻 Непонятная команда, попробуйте снова", reply_markup=markup.get_menu(message.from_user.id))