import asyncio
import logging

from aiogram import Dispatcher

from db_directory.database import engine, close_db
from db_directory.models import Base

from routers.create_profile import router as create_profile
from routers.unforeseen_cases import router as unforeseen_cases
from routers.change_profile import router as change_profile
from routers.looking_partner import router as looking_partner

from redis_storage import storage

logging.basicConfig(level=logging.INFO)

from main import my_bot

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    dp = Dispatcher(storage=storage)

    dp.include_routers(
        create_profile,
        change_profile,
        looking_partner,
        unforeseen_cases
    )

    await my_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(my_bot)
    await close_db()

if __name__ == '__main__':
    asyncio.run(main())