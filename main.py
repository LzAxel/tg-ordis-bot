import logging
import random
import csv
import json
import time

from bs4 import BeautifulSoup
import requests


from bot import dp, bot
from aiogram.utils.markdown import hlink
import asyncio
from pathlib import Path

import config
import parse
import keyboards as kb



async def check_new_alerts():
    saved_alerts = []
    with open('chats.txt', 'r', encoding='UTF-8') as file:
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
        await asyncio.sleep(random.randrange(100, 200))


async def check_new_articles():
    saved_articles = []
    with open('\chats.txt', 'r', encoding='UTF-8') as file:
        chats = file.readlines()

    while True:
        logging.info("Checking for website news")
        await parse.get_articles()
        with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
            got_articles = json.load(file)
        saved_articles_names = [i['Title'] for i in saved_articles]
        got_articles_names = [i['Title'] for i in got_articles]

        if not saved_articles:
            saved_articles = got_articles
            logging.info("First website news checking")
        elif all(get in saved_articles_names for get in got_articles_names):
            logging.info("Website news not found")
        else:
            logging.info("Founded website news")
            new_articles = [get for get in got_articles if get not in saved_articles]
            saved_articles = got_articles
            for chat in chats:
                for article in new_articles:
                    try:
                        await bot.send_photo(chat, article['Photo'])
                    except Exception as ex:
                        logging.error("Photo send error - ", ex)
                    link = hlink('Read More', article['Read_More'])
                    message = f"✨<b>{article['Title']}</b>✨\n\n📃 {article['Description']}\n\n📅 {article['Date']}\t{link}"
                    await bot.send_message(chat, message, parse_mode="HTML", disable_web_page_preview=True)
            print(new_articles)
        await asyncio.sleep(random.randrange(60, 90))


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
