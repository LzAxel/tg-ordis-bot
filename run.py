from bot import dp
from main import send_articles
from parse import update_api_dump
import logging, coloredlogs

from handlers import register_handlers
from aiogram import executor
import asyncio
from pathlib import Path
import aioschedule

logging.basicConfig(level=logging.INFO)


async def scheduler():
    aioschedule.every().hour.do(send_articles)
    aioschedule.every().minute.do(update_api_dump)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    logging.info("On startupc")
    if not Path("src", "articles.json").exists(): Path("src").mkdir(exist_ok=True)
    if not Path("logs").exists(): Path("logs").mkdir()
    
    coloredlogs.install()
    register_handlers(dp)
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)