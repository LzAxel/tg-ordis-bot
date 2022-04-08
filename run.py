import asyncio
import logging
from pathlib import Path

import aioschedule
import coloredlogs
from aiogram import executor

from bot import dp
from config import ADMIN_ID
from handlers import register_handlers
from main import send_alerts, send_articles
from parse import get_new_articles, update_api_dump, update_relic_dump
from utils import send_report

logging.basicConfig(level=logging.INFO)


async def scheduler():
    aioschedule.every().day.do(update_relic_dump)
    aioschedule.every().minute.do(update_api_dump)
    aioschedule.every().hour.do(send_articles)
    aioschedule.every().minute.do(send_alerts)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await dp.bot.send_message(ADMIN_ID, "Bot started\!")
    if not Path("src", "articles.json").exists(): 
        Path("src").mkdir(exist_ok=True)
        await get_new_articles()

    if not Path("src", "api_dump.json").exists(): await update_api_dump()
    if not Path("src", "relics_dump.json").exists(): await update_relic_dump()
    if not Path("logs").exists(): Path("logs").mkdir()
    
    register_handlers(dp)
    asyncio.create_task(scheduler())


def main():
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
        
    except Exception as ex:
        logging.exception(ex)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(send_report(ex, "Main function exception"))


if __name__ == '__main__':
    coloredlogs.install()
    main()
