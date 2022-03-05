import aiogram
from aiogram import types, filters, Dispatcher
from aiogram.utils.markdown import hlink, bold
import json
from pathlib import Path

import parse
from bot import dp, bot
import keyboards as kb
import config


async def process_start_command(msg: types.Message):
    await msg.reply("🤖 Привет, Я - Ордис, бот - информатор ивентов Warframe'a \n\n"
                    "🔔 Вот список моих возможностей: \n\n"
                    " - Я буду автоматически присылать новости с оф. сайта \n"
                    " - Можно узнать дроп с любой реликвии \n"
                    " - Откуда выпадают конкретные прайм части \n"
                    " - Посмотреть текущую вылазку и статусы открытых миров \n\n"
                    "⁉ Все подробности по команде /help", parse_mode="Markdown",
                    reply_markup=kb.mainMenu)

    chat_id = str(msg.chat.id)
    with open('chats.txt', 'r', encoding='UTF-8') as file:
        chat_id_list = file.readline()
        if chat_id not in chat_id_list:
            with open('chats.txt', 'a', encoding='UTF-8') as write_file:
                write_file.write(chat_id)
                write_file.write('\n')
        else:
            print('Этот айди уже есть в базе')


async def process_help_command(msg: types.Message):
    await msg.reply("⁉ Помощь по командам бота \n\n"
                    "- /latest - посмотреть последнюю новость с оф. сайта \n"
                    "- 🌗Циклы - узнать статус всех открытых миров \n"
                    "- 🛡Вылазка - узнать данные вылазки, включая миссии и оставшееся время \n\n"
                    "- Посмотреть дроп с реликвии - {Эра} {Название} {Улучшение от 0 до 3 (не обяз.)}\n"
                    "_Например:_ *Лит k7* или *lith k7*\n\n"
                    "- Посмотреть с каких реликвий падает часть - {Название}\n"
                    "_Например:_ *Рино Прайм* или *Rhino Prime*\n\n"
                    "- Чтобы посмотреть конкретные части - {Название} Прайм {Часть}\n"
                    "_Например:_ *Рино Прайм Чертёж* или *Rhino Prime Blueprint*\n\n"
                    "📌 *Важная информация:* Не все предметы переведены на русский язык, поэтому,\n"
                    "если бот не может найти предмет - то попробуйте написать его название на английском\n"
                    "В будущем все предметы будут обязательно переведены"
                    , parse_mode="Markdown", reply_markup=kb.mainMenu)


async def send_latest_article(msg: types.Message):
    await parse.get_articles()
    with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
        article = json.load(file)[0]
    try:
        await bot.send_photo(msg.from_user.id, article['Photo'])

    except:
        print('Отправка фото не удалась')
    link = hlink('Read More', article['Read_More'])
    message = f"✨ <b>{article['Title']}</b> ✨\n\n📃 {article['Description']}\n\n📅 {article['Date']}\t{link}"
    await bot.send_message(msg.from_user.id, message, parse_mode="HTML", disable_web_page_preview=True,
                           reply_markup=kb.mainMenu)


async def send_articles(msg: types.Message):
    await parse.get_articles()
    with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
        articles = json.load(file)

    for article in articles:
        try:
            await bot.send_photo(msg.from_user.id, article['Photo'])

        except:
            print('Отправка фото не удалась')
        message = f"✨ <b>{article['Title']}</b> ✨\n\n📃 {article['Description']}\n\n📅 {article['Read_More']}\n{article['Date']}"
        await bot.send_message(msg.from_user.id, message, parse_mode="HTML", disable_web_page_preview=True,
                               reply_markup=kb.mainMenu)


async def send_world_cycles(msg: types.Message):
    print('Вывод циклов')
    message = ""
    cycle_list = await parse.get_cycles()
    
    for cycle in cycle_list:
        message += f"{cycle.name}\n{bold('Status:')} {cycle.state}\n{bold('Time left:')} {cycle.eta}\n\n"
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_sortie_info(msg: types.Message):
    print('Вывод вылазки')
    sortie = await parse.get_sortie()
    message = f"🎭 *Faction:* {sortie.faction}\n\n" \
    f"☠️ *Boss:* {sortie.boss}\n\n" \
    f"⏱ *Time left:* {sortie.eta}\n\n"
    
    for num, mission in enumerate(sortie.missions):
        message += f"*{num + 1} Mission* - {mission.mission_type} - {mission.location}\n*Modifier:* {mission.modifier}\n"
        message += f"*Modifier Description:* {mission.description}\n\n"
        
    await msg.answer(message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_invasions_info(msg: types.Message):
    print('Вывод вторжений')
    invasions = parse.get_invasions()
    message = "*⚔️ Invasions*\n\n"
    for invasion in invasions:
        message += f"*Mission:* {invasion.location}\n*Defender*: {invasion.defender.faction} | *Reward*: {invasion.defender.reward.name}\n"
        message += f"*Attacker*: {invasion.attacker.faction} | *Reward*: {invasion.attacker.reward.name}\n"
        message += f"⏱*Time Left:* {invasion.eta}\n\n"

    await msg.answer(message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_relic_info(msg: types.Message):
    print('Получение релика или дропа вызвано')
    command = msg.text.lower()
    split_command = command.split(' ')
    if split_command[0] in config.RELIC_COMMANDS:
        message = await parse.get_relic_data(split_command)
        if message:
            await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)
        else:
            await bot.send_message(msg.from_user.id, "❗ Relic doesn't exist.",
                                   reply_markup=kb.mainMenu)
    else:
        message = await parse.get_relics_with_current_item(command)
        try:
            if message:
                await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)
            else:
                await bot.send_message(msg.from_user.id, "❗ Item doesn't exist.",
                                       reply_markup=kb.mainMenu)
        except aiogram.utils.exceptions.MessageIsTooLong:
            await bot.send_message(msg.from_user.id, "❗ Too big request. Input specific items.",
                                   reply_markup=kb.mainMenu)


def register_handlers(dp: Dispatcher): 
    dp.register_message_handler(process_start_command, commands=['start'])
    dp.register_message_handler(process_help_command, commands=['help'])
    dp.register_message_handler(send_latest_article, commands=['latest'])
    dp.register_message_handler(send_articles, commands=['list'])
    dp.register_message_handler(send_world_cycles, filters.Text("🌗 World Cycles"))
    dp.register_message_handler(send_sortie_info, filters.Text("🛡 Sortie"))
    dp.register_message_handler(send_invasions_info, filters.Text("⚔️ Invasions"))
    dp.register_message_handler(send_relic_info)