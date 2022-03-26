import asyncio
import logging

import aiogram
from aiogram.utils.markdown import hlink

import parse
from bot import bot, db
import keyboards as kb

async def send_articles() -> None:
    chat_list = db.get_users()

    new_articles = await parse.get_new_articles()
    if new_articles:
        for chat in chat_list:
            # chat = chat[0]
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
                    

# Send a new events (alerts, void trader)
async def send_events() -> None:
    # chat_list = db.get_users()
    chat_list = [(1083151565),]
    api = await parse.read_api_dump()
    alerts = [i for i in api.alerts if not i.notified]
    trader = api.trader
    if not trader.notified and trader.active:
        for chat in chat_list:
            # chat = chat[0]
            logging.info(f"Sending Enevt | User ID: {chat} Event: Void Trader has arrived")
            message = f"✨<b>Void Trader has arrived!</b>✨\n\nCheck out his new products\n"\
                        f"<b>Relay:</b> {trader.loc}\n\n<b>Time left:</b> {trader.eta}\n"

            await bot.send_message(chat, message, parse_mode="HTML", reply_markup=kb.trader_open)

        await parse.set_event_notified("trader")
        # raise RecursionError
        
    if alerts:
        for alert in alerts:
            for chat in chat_list:
                chat = chat[0]
                mission = alert.mission
                logging.info(f"Sending event | User ID: {chat} Event: New alert")
                message = f"✨<b>New Alert: {mission.description}</b>✨\n\n<b>Mission:</b> {mission.location}\n"\
                            f"<b>Type:</b> {mission.type}\n<b>Faction:</b> {mission.faction}\n"\
                            f"<b>Reward: {mission.reward.name}</b>\n\n"\
                            f"<b>Time left:</b> {alert.eta}"
                try:
                    await bot.send_message(chat, message, parse_mode="HTML")
                
                except aiogram.utils.exceptions.ChatNotFound:
                    logging.error(f"Chat {chat} Not Found")
                    db.remove_user(chat)
            await parse.set_event_notified("alert", alert.id)


if __name__ == "__main__":
    asyncio.run(send_events())