import logging
from random import randint
import aiogram

from bot import bot, db
from aiogram.utils.markdown import hlink
import asyncio
from pathlib import Path

import parse
import keyboards as kb

async def check_new_alerts():
    saved_alerts = []
    with open(Path("chats.txt"), 'r', encoding='UTF-8') as file:
        chats = file.readlines()
    while True:
        logging.info("Checking for new lotus gifts")
        parse.get_alerts()
        alerts = parse.read_cached_json('alerts')
        if not saved_alerts:
            saved_alerts = alerts
            logging.info("First lotus gift checking")
        elif all(alert in saved_alerts for alert in alerts):
            logging.info("New lotus gifts not found")
        else:
            logging.info("Founded new lotus gifts")
            for chat in chats:
                message = "❕*Новые Сигналы Тревоги*\n\n"
                for alert in alerts:
                    if alert not in saved_alerts:
                        message += f"*Тип:* {alert['description']}\n*Миссия*: {alert['mission']}\n*Фракция*: {alert['faction']}\n"
                        message += f"*Награда*: {alert['reward']}\n"
                        logging.info('Sending lotus gifts message to ', chat)
                        await bot.send_message(chat, message, parse_mode='Markdown',
                                               reply_markup=kb.mainMenu)
            saved_alerts = alerts
        await asyncio.sleep(randint(100, 200))


async def send_articles():
    chat_list = db.get_users()

    new_articles = await parse.get_new_articles()
    if new_articles:
        for chat in chat_list:
            chat = chat[0]
            for article in new_articles:
                logging.info(f"Sending articles.. | User ID: {chat} Title: {article.title}")
                try:
                    await bot.send_photo(chat, article.photo)

                except aiogram.utils.exceptions.ChatNotFound:
                    logging.error(f"Chat {chat} Not Found")
                    db.remove_user(chat)
                    continue
                    
                link = hlink(article.title, article.url)
                message = f"✨<b>{link}</b>✨\n\n📃 {article.description}\n\n📅 {article.date}"
                await bot.send_message(chat, message, parse_mode="HTML", disable_web_page_preview=True)