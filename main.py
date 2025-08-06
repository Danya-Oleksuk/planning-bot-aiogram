import asyncio
import logging

from aiogram import Bot, Dispatcher

from handlers.user_handlers import router_1, router_2
from handlers.admin_handlers import router

from database import postgres, mongo

from middlewares.anti_spam_middleware import AntiSpamMiddleware
from middlewares.check_ban_middleware import BanCheckMiddleware

import config


BOT_TOKEN = config.BOT_TOKEN

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                        filename="bot.log", filemode="a")
    
    await postgres.initiate_pool()
    
    await postgres.create_telegram_bot_db()
    await mongo.create_mongo_database()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    router_1.message.middleware(AntiSpamMiddleware(cache_ttl=0.5))
    router_2.message.middleware(AntiSpamMiddleware(cache_ttl=0.3))

    router_1.message.middleware(BanCheckMiddleware(db=postgres))
    router_2.message.middleware(BanCheckMiddleware(db=postgres))

    dp.include_routers(router_1,
                       router_2,
                       router,)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass