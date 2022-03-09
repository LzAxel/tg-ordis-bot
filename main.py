import logging
from random import randint
import csv
import aiogram

from bs4 import BeautifulSoup
import requests

from bot import bot, db
from aiogram.utils.markdown import hlink
import asyncio
from pathlib import Path

import config
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

    while True:
        await asyncio.sleep(config.NEWS_CHECK_RATE)
        new_articles = await parse.get_new_articles() 
        if not new_articles: continue
        
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


async def get_relic_items():
    response = requests.get(config.RELICS_URL, headers=config.HEADERS).text
    soup = BeautifulSoup(response, 'lxml')
    table = soup.find(class_="wikitable")
    rows = table.find_all('tr')
    write_list = []
    lith = []
    meso = []
    neo = []
    axi = []
    relic_switch = {
        0: lith,
        1: meso,
        2: neo,
        3: axi,
    }
    for row in rows:
        count = 0
        columns = row.find_all(['th', 'td'])[:-1]
        for column in columns:
            if column.text != '' and column.text not in relic_switch[count]:
                try:
                    relic_switch[count].append({'name': column.text,
                                                'link': 'https://warframe.fandom.com' +
                                                column.find('a', href=True)['href']})

                except:
                    relic_switch[count].append({'name': column.text, 'link': ''})
            else:
                relic_switch[count].append({'name': ''})
            count += 1
        write_list.append((lith[-1], meso[-1], neo[-1], axi[-1]))
    with open('relics_table.csv', 'w', encoding='UTF-8') as file:
        writer = csv.writer(file)
        writer.writerows(write_list)
