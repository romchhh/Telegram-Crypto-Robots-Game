import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from data.config import *
from data.functions.db_functions import Database

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)
bot = Bot(token=api_key_bot, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage) 
mdb = Database('data/db.sqlite')
mdb.create_market_tables()
mdb.create_game_tables()
mdb.create_robots_tables()
scheduler = AsyncIOScheduler()

scheduler.start()

if __name__ == '__main__':
    from handlers import dp, on_startup, on_shutdown
    loop = asyncio.get_event_loop()

    executor.start_polling(dp, loop=loop, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
