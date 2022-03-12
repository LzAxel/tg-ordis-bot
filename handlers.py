import aiogram
from aiogram import types, filters, Dispatcher
from aiogram.utils.markdown import hlink, bold
import json
from pathlib import Path
import logging
 
import parse
from bot import bot, db
import keyboards as kb
import config


async def process_start_command(msg: types.Message):
    await msg.reply("🤖 Hi, I'm - Ordis, Warframe's events informator bot. \n\n"
                    "🔔 There are my opportunities: \n\n"
                    " - I'll automatically send news from official site.\n"
                    " - You can know drops from any relic. \n"
                    " - You can know relics with current items. \n"
                    " - Check current world cycles, sortie, invasions. \n\n", parse_mode="Markdown",
                    reply_markup=kb.mainMenu)

    db.add_user(msg.from_user.id, msg.from_user.full_name)


async def process_help_command(msg: types.Message):
    await msg.reply("⁉ Commands help \n\n"
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


async def send_world_cycles(msg: types.Message):
    logging.info(f"Sending world cycles to {msg.from_user.id}")
    message = ""
    api = await parse.read_api_dump()
    
    for cycle in api.cycles:
        message += f"{cycle.name}\n{bold('Status:')} {cycle.state}\n{bold('Time left:')} {cycle.eta}\n\n"
    
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_sortie_info(msg: types.Message):
    logging.info(f"Sending sortie to {msg.from_user.id}")
    api = await parse.read_api_dump()
    sortie = api.sortie
    message = f"🎭 *Faction:* {sortie.faction}\n\n" \
    f"☠️ *Boss:* {sortie.boss}\n\n" \
    f"⏱ *Time left:* {sortie.eta}\n\n"
    
    for num, mission in enumerate(sortie.missions):
        message += f"*{num + 1} Mission* - {mission.mission_type} - {mission.location}\n*Modifier:* {mission.modifier}\n"
        message += f"*Modifier Description:* {mission.description}\n\n"
        
    await msg.answer(message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_invasions_info(msg: types.Message):
    logging.info(f"Sending invasions to {msg.from_user.id}")
    api = await parse.read_api_dump()
    message = "*⚔️ Invasions*\n\n"
    for invasion in api.invasions:
        message += f"*Mission:* {invasion.location}\n*Defender*: {invasion.defender.faction} | *Reward*: {invasion.defender.reward.name}\n"
        message += f"*Attacker*: {invasion.attacker.faction} | *Reward*: {invasion.attacker.reward.name}\n"
        message += f"⏱*Time Left:* {invasion.eta}\n\n"

    await msg.answer(message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_relic_info(msg: types.Message):
    logging.info(f"Sending relic drop to {msg.from_user.id}")
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
    dp.register_message_handler(send_world_cycles, filters.Text("🌗 World Cycles"))
    dp.register_message_handler(send_sortie_info, filters.Text("🛡 Sortie"))
    dp.register_message_handler(send_invasions_info, filters.Text("⚔️ Invasions"))
    dp.register_message_handler(send_relic_info)