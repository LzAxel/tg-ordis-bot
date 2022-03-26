from bot import dp
from scheduled import send_articles, send_events
from parse import get_new_articles, update_api_dump, update_relic_dump
import logging, coloredlogs

from handlers import register_handlers
from aiogram import executor
import asyncio
from pathlib import Path
import aioschedule

logging.basicConfig(level=logging.INFO)


async def scheduler():
    aioschedule.every().day.do(update_relic_dump)
    aioschedule.every().minute.do(update_api_dump)
    aioschedule.every().hour.do(send_articles)
    aioschedule.every(10).seconds.do(send_events)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    if not Path("src", "articles.json").exists(): 
        Path("src").mkdir(exist_ok=True)
        await get_new_articles()

    if not Path("src", "api_dump.json").exists(): await update_api_dump()
    if not Path("src", "relics_dump.json").exists(): await update_relic_dump()
    if not Path("logs").exists(): Path("logs").mkdir()

    register_handlers(dp)
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    coloredlogs.install()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)