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
                    link = hlink(article.title, article.url)
                    message = f"✨<b>{link}</b>✨\n\n📃 {article.description}\n\n📅 {article.date}"
                    await bot.send_photo(chat, article.photo, caption=message, parse_mode="HTML")

                except aiogram.utils.exceptions.ChatNotFound:
                    logging.error(f"Chat {chat} Not Found")
                    db.remove_user(chat)
                    continue
                    

async def send_alerts():
    chat_list = db.get_users()
    api = await parse.read_api_dump()
    alerts = [i for i in api.alerts if not i.notified and i.active]
    if alerts:
        for alert in alerts:
            for chat in chat_list:
                chat = chat[0]
                mission = alert.mission
                logging.info(f"Sending alert | User ID: {chat} Mission: {mission.location}")
                message = f"✨<b>New Alert: {mission.description}</b>✨\n\n<b>Mission:</b> {mission.location}\n"\
                            f"<b>Type:</b> {mission.type}\n<b>Faction:</b> {mission.faction}\n"\
                            f"<b>Reward: {mission.reward.name}</b>\n\n"\
                            f"<b>Time left:</b> {alert.eta}"
                try:
                    await bot.send_message(chat, message, parse_mode="HTML")
                
                except aiogram.utils.exceptions.ChatNotFound:
                    logging.error(f"Chat {chat} Not Found")
                    db.remove_user(chat)
            await parse.set_alert_notified(alert.id)