import logging
import aiogram

from bot import bot, db
from aiogram.utils.markdown import hlink

import parse


async def send_articles():
    chat_list = db.get_users()

    new_articles = await parse.get_new_articles()
    if new_articles:
        for chat in chat_list:
            chat = chat[0]
            for article in new_articles:
                logging.info(f"Sending articles | User ID: {chat} Title: {article.title}")
                try:
                    await bot.send_photo(chat, article.photo)

                except aiogram.utils.exceptions.ChatNotFound:
                    logging.error(f"Chat {chat} Not Found")
                    db.remove_user(chat)
                    continue
                    
                link = hlink(article.title, article.url)
                message = f"✨<b>{link}</b>✨\n\n📃 {article.description}\n\n📅 {article.date}"
                await bot.send_message(chat, message, parse_mode="HTML", disable_web_page_preview=True)