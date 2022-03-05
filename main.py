import random
import csv
import json
import time

import aiogram.utils.exceptions
from bs4 import BeautifulSoup
import requests
import lxml

from aiogram import Bot, types, filters
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from aiogram.utils.markdown import hlink, bold
import asyncio
from pathlib import Path

import config
from parse import get_articles, get_relic_data, get_cycles, get_sortie, get_relic_names_list, get_relics_with_current_item, read_cached_json, get_alerts
from utils import reformat_time
import keyboards as kb


cwd = Path(__file__).parent

relic_names = []

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)


async def check_new_alerts():
    saved_alerts = []
    with open(fr'{cwd}\chats.txt', 'r', encoding='UTF-8') as file:
        chats = file.readlines()
    while True:
        print('Проверка новых Сигналов Тревоги... - ', time.strftime("%d/%m/%Y %H:%M:%S"))
        get_alerts()
        alerts = read_cached_json('alerts')
        if not saved_alerts:
            saved_alerts = alerts
            print('Первый запуск - ', time.strftime("%d/%m/%Y %H:%M:%S"))
        elif all(alert in saved_alerts for alert in alerts):
            print("Новых тревог не найдено - ", time.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            print("Обнаружены новые тревоги - ", time.strftime("%d/%m/%Y %H:%M:%S"))
            for chat in chats:
                message = "❕*Новые Сигналы Тревоги*\n\n"
                for alert in alerts:
                    if alert not in saved_alerts:
                        message += f"*Тип:* {alert['description']}\n*Миссия*: {alert['mission']}\n*Фракция*: {alert['faction']}\n"
                        message += f"*Награда*: {alert['reward']}\n"
                        print('отправка тревоги к ', chat)
                        await bot.send_message(chat, message, parse_mode='Markdown',
                                               reply_markup=kb.mainMenu)
            saved_alerts = alerts
        await asyncio.sleep(random.randrange(100, 200))


async def check_new_articles():
    saved_articles = []
    with open(fr'{cwd}\chats.txt', 'r', encoding='UTF-8') as file:
        chats = file.readlines()

    while True:
        print('Проверка новых записей... - ', time.strftime("%d/%m/%Y %H:%M:%S"))
        await get_articles()
        with open(rf'{cwd}\src\articles.json', 'r', encoding='UTF-8') as file:
            got_articles = json.load(file)
        saved_articles_names = [i['Title'] for i in saved_articles]
        got_articles_names = [i['Title'] for i in got_articles]

        if not saved_articles:
            saved_articles = got_articles
            print('Первый запуск - ', time.strftime("%d/%m/%Y %H:%M:%S"))
        elif all(get in saved_articles_names for get in got_articles_names):
            print("Новых записей не найдено - ", time.strftime("%d/%m/%Y %H:%M:%S"))
        else:
            print("Обнаружены новые записи - ", time.strftime("%d/%m/%Y %H:%M:%S"))
            new_articles = [get for get in got_articles if get not in saved_articles]
            saved_articles = got_articles
            for chat in chats:
                for article in new_articles:
                    try:
                        await bot.send_photo(chat, article['Photo'])
                    except:
                        print('Отправка фото не удалась')
                    link = hlink('Подробнее', article['Read_More'])
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
    with open(fr'{cwd}\relics_table.csv', 'w', encoding='UTF-8') as file:
        writer = csv.writer(file)
        writer.writerows(write_list)


@dp.message_handler(commands=['start'])
async def process_start_command(msg: types.Message):
    await msg.reply("🤖 Привет, Я - Ордис, бот - информатор ивентов Warframe'a \n\n" +
                    "🔔 Вот список моих возможностей: \n\n" +
                    " - Я буду автоматически присылать новости с оф. сайта \n" +
                    " - Можно узнать дроп с любой реликвии \n" +
                    " - Откуда выпадают конкретные прайм части \n" +
                    " - Посмотреть текущую вылазку и статусы открытых миров \n\n" +
                    "⁉ Все подробности по команде /help", parse_mode="Markdown",
                    reply_markup=kb.mainMenu)

    chat_id = str(msg.chat.id)
    with open(fr'{cwd}\chats.txt', 'r', encoding='UTF-8') as file:
        chat_id_list = file.readline()
        if chat_id not in chat_id_list:
            with open(fr'{cwd}\chats.txt', 'a', encoding='UTF-8') as write_file:
                write_file.write(chat_id)
                write_file.write('\n')
        else:
            print('Этот айди уже есть в базе')


@dp.message_handler(commands=['help'])
async def process_help_command(msg: types.Message):
    await msg.reply("⁉ Помощь по командам бота \n\n" +
                    "- /latest - посмотреть последнюю новость с оф. сайта \n" +
                    "- 🌗Циклы - узнать статус всех открытых миров \n" +
                    "- 🛡Вылазка - узнать данные вылазки, включая миссии и оставшееся время \n\n" +
                    "- Посмотреть дроп с реликвии - {Эра} {Название} {Улучшение от 0 до 3 (не обяз.)}\n" +
                    "_Например:_ *Лит k7* или *lith k7*\n\n" +
                    "- Посмотреть с каких реликвий падает часть - {Название}\n" +
                    "_Например:_ *Рино Прайм* или *Rhino Prime*\n\n" +
                    "- Чтобы посмотреть конкретные части - {Название} Прайм {Часть}\n" +
                    "_Например:_ *Рино Прайм Чертёж* или *Rhino Prime Blueprint*\n\n" +
                    "📌 *Важная информация:* Не все предметы переведены на русский язык, поэтому,\n" +
                    "если бот не может найти предмет - то попробуйте написать его название на английском\n" +
                    "В будущем все предметы будут обязательно переведены"
                    , parse_mode="Markdown", reply_markup=kb.mainMenu)


@dp.message_handler(commands=['latest'])
async def send_latest_article(msg: types.Message):
    await get_articles()
    with open(rf'{cwd}\src\articles.json', 'r', encoding='UTF-8') as file:
        article = json.load(file)[0]
    try:
        await bot.send_photo(msg.from_user.id, article['Photo'])

    except:
        print('Отправка фото не удалась')
    link = hlink('Подробнее', article['Read_More'])
    message = f"✨ <b>{article['Title']}</b> ✨\n\n📃 {article['Description']}\n\n📅 {article['Date']}\t{link}"
    await bot.send_message(msg.from_user.id, message, parse_mode="HTML", disable_web_page_preview=True,
                           reply_markup=kb.mainMenu)
    print(relic_names)


@dp.message_handler(commands=['list'])
async def send_articles(msg: types.Message):
    await get_articles()
    with open(rf'{cwd}\src\articles.json', 'r', encoding='UTF-8') as file:
        articles = json.load(file)

    for article in articles:
        try:
            await bot.send_photo(msg.from_user.id, article['Photo'])

        except:
            print('Отправка фото не удалась')
        message = f"✨ <b>{article['Title']}</b> ✨\n\n📃 {article['Description']}\n\n📅 {article['Read_More']}\n{article['Date']}"
        await bot.send_message(msg.from_user.id, message, parse_mode="HTML", disable_web_page_preview=True,
                               reply_markup=kb.mainMenu)


@dp.message_handler(filters.Text("🌗 World Cycles"))
async def world_cycles(msg: types.Message):
    print('Вывод циклов')
    message = ""
    cycles = await get_cycles()
    for world in cycles:
        message += f"{world['name']}\n{bold('Статус:')} {world['state']}\n{bold('Оставшееся время:')} {reformat_time(world['timeLeft'])}\n\n"
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


@dp.message_handler(filters.Text("🛡 Sortie"))
async def sortie_info(msg: types.Message):
    print('Вывод вылазки')
    message = ""
    sortie = await get_sortie()
    message += f"🎭 *Фракция:* {sortie['faction']}\n\n☠️ *Босс:* {sortie['boss']}\n\n⏱ *Оставшееся время:* {reformat_time(sortie['timeLeft'])}\n\n"
    for num, mission in enumerate(sortie['missions']):
        message += f"*{num + 1}-я Миссия* - {mission['missionType']} - {mission['node']}\n*Модификатор:* {mission['modifier']}\n\n"
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


@dp.message_handler(filters.Text("⚔️ Invasions"))
async def sortie_info(msg: types.Message):
    print('Вывод вторжений')
    invasions_list = read_cached_json('invasions')
    message = "⚔*Вторжения*\n\n"
    for invasion in invasions_list:
        message += f"*Миссия:* {invasion['mission']}\n*Защита*: {invasion['defendingFaction']} | *Награда*: {invasion['defenderReward']}\n"
        message += f"*Атака*: {invasion['attackingFaction']} | *Награда*: {invasion['attackerReward']}\n"
        message += f"⏱*Оставшееся время:* {invasion['eta']}\n\n"
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


# @dp.message_handler(Command(commands=['Сигналы'], prefixes='❕'))
# async def sortie_info(msg: types.Message):
#     print(msg.text)
#     if msg.text == '❕Сигналы Тревоги':
#         print('Вывод Сигналов Тревоги')
#         alerts_list = read_cached_json('alerts')
#         if alerts_list:
#             message = "❕*Сигналы Тревоги*\n\n"
#             for alert in alerts_list:
#                 message += f"*Тип:* {alert['description']}\n*Миссия*: {alert['mission']}\n*Фракция*: {alert['faction']}\n"
#                 message += f"*Награда*: {alert['reward']}\n"
#                 message += f"⏱*Оставшееся время:* {alert['eta']}\n\n"
#             await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)
#         else:
#             message = "❗ Сигналов Тревоги сейчас нет."
#             await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


@dp.message_handler()
async def relic_info(msg: types.Message):
    print('Получение релика или дропа вызвано')
    command = msg.text.lower()
    split_command = command.split(' ')
    if split_command[0] in config.RELIC_COMMANDS:
        message = await get_relic_data(split_command)
        if message:
            await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)
        else:
            await bot.send_message(msg.from_user.id, '❗ Такой реликвии не существует. Проверьте правильность написания.',
                                   reply_markup=kb.mainMenu)
    else:
        message = await get_relics_with_current_item(command)
        try:
            if message:
                await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)
            else:
                await bot.send_message(msg.from_user.id, '❗ Такого предмета не существует. Проверьте правильность написания.',
                                       reply_markup=kb.mainMenu)
        except aiogram.utils.exceptions.MessageIsTooLong:
            await bot.send_message(msg.from_user.id, '❗ Слишком большой запрос. Указывайте конкретные предметы.',
                                   reply_markup=kb.mainMenu)



async def async_tasks(*args):
    loop = asyncio.get_event_loop()
    loop.create_task(check_new_articles())
    loop.create_task(check_new_alerts())


def main():
    executor.start_polling(dp, skip_updates=True, on_startup=async_tasks)


if __name__ == '__main__':
    main()
