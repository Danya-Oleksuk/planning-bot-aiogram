from aiogram import Bot, Dispatcher
import asyncio
import logging
import os
from dotenv import load_dotenv

import handlers
import admin_panel
import database

from middlewares import AntiSpamMiddleware

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", )
    database.create_telegram_channel_db()
    await database.create_mongo_database()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    handlers.router_1.message.middleware(AntiSpamMiddleware(cache_ttl=0.5))
    handlers.router_2.message.middleware(AntiSpamMiddleware(cache_ttl=0.2))

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