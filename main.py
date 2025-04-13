import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

import admin_panel
import database
import handlers
from middlewares import AntiSpamMiddleware

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                        filename="bot.log", filemode="a")
    await database.init_pool()
    await database.create_telegram_channel_db()
    await database.create_mongo_database()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    handlers.router_1.message.middleware(AntiSpamMiddleware(cache_ttl=0.5))
    handlers.router_2.message.middleware(AntiSpamMiddleware(cache_ttl=0.3))

    dp.include_routers(handlers.router_1,
                       handlers.router_2,
                       admin_panel.router,)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass