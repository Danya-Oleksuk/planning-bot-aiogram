from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from cachetools import TTLCache


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, cache_ttl: float = 0.5) -> None:
        self.cache = TTLCache(maxsize=100000, ttl=cache_ttl)

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        if isinstance(event, Message) or isinstance(event, CallbackQuery):
            if user_id in self.cache:
                return
            else:
                self.cache[event.from_user.id] = None
        return await handler(event, data)
