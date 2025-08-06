from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Awaitable, Dict

from aiogram.types import ReplyKeyboardRemove

class BanCheckMiddleware(BaseMiddleware):
    def __init__(self, db):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict], Awaitable],
        event: TelegramObject,
        data: Dict
    ) -> Awaitable:
        if isinstance(event, Message):
            user_id = event.from_user.id
            user_is_banned = await self.db.get_user_is_banned_by_admin(user_id)

            if user_is_banned:
                await event.answer("🚫 Вы были забанены и не можете пользоваться ботом.", reply_markup=ReplyKeyboardRemove())
                return

        return await handler(event, data)