from bot import dp
from main import check_new_alerts, check_new_articles
import logging

from handlers import register_handlers
from aiogram import executor
import asyncio

logging.basicConfig(level=logging.INFO)

async def async_tasks(*args):
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_articles())
    loop.create_task(check_new_alerts())


def main():
    register_handlers(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=async_tasks)


if __name__ == '__main__':
    main()