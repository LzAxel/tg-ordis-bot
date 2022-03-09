from bot import dp
from main import send_articles
import logging, coloredlogs

from handlers import register_handlers
from aiogram import executor
import asyncio
from pathlib import Path

logging.basicConfig(level=logging.INFO)

async def async_tasks(*args):
    loop = asyncio.get_event_loop()
    loop.create_task(send_articles())


def main():
    if not Path("src", "articles.json").exists(): Path("src").mkdir(exist_ok=True)
    if not Path("logs").exists(): Path("logs").mkdir()
    
    coloredlogs.install()
    register_handlers(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=async_tasks)


if __name__ == '__main__':
    main()