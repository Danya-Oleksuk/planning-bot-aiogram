from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, cache_ttl: float = 0.5) -> None:
        self.cache = TTLCache(maxsize=100000, ttl=cache_ttl)

    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:
        if event.chat.id in self.cache:
            return
        else:
            self.cache[event.chat.id] = None
        result = await handler(event, data)