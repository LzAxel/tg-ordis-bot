from aiogram import types, filters, Dispatcher
from aiogram.utils.markdown import bold
import logging
 
import parse
from bot import bot, db
import keyboards as kb
import config


async def process_start_command(msg: types.Message):
    await msg.reply("🤖 Hi, I'm - Ordis, Warframe's events informator bot. \n\n"
                    "🔔 There are my opportunities: \n\n"
                    " - I'll *automatically* send news from official site.\n"
                    " - You can know drops from *any* relic. \n"
                    " - Or relics with *current* items.\n"
                    "   *Just type name to bot and see it!* (case doesn't matter)\n"
                    "   *Examples:* 'axi o5', 'baza prime', 'loki'\n"
                    " - Check current *world cycles*, *sortie* and *invasions*. \n\n", parse_mode="Markdown",
                    reply_markup=kb.mainMenu)

    db.add_user(msg.from_user.id, msg.from_user.full_name)


async def send_world_cycles(msg: types.Message):
    logging.info(f"Sending World Cycles | User ID: {msg.from_user.id}")
    message = ""
    api = await parse.read_api_dump()
    
    for cycle in api.cycles:
        message += f"{cycle.name}\n{bold('Status:')} {cycle.state}\n{bold('Time left:')} {cycle.eta}\n\n"
    
    await bot.send_message(msg.from_user.id, message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_sortie_info(msg: types.Message):
    logging.info(f"Sending Sortie | User ID: {msg.from_user.id}")
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
    logging.info(f"Sending Invasions | User ID: {msg.from_user.id}")
    api = await parse.read_api_dump()
    message = "*⚔️ Invasions*\n\n"
    for invasion in api.invasions:
        message += f"*Mission:* {invasion.location}\n*Defender*: {invasion.defender.faction} | *Reward*: {invasion.defender.reward.name}\n"
        message += f"*Attacker*: {invasion.attacker.faction} | *Reward*: {invasion.attacker.reward.name}\n"
        message += f"⏱*Time Left:* {invasion.eta}\n\n"

    await msg.answer(message, parse_mode='Markdown', reply_markup=kb.mainMenu)


async def send_relic_drop(msg: types.Message):
    command = msg.text.title()
    logging.info(f"Sending Relic Drop | Relic: {command} | User ID: {msg.from_user.id}")
    relic = await parse.get_relic_drop(command)
    if relic:
        answer_message = f"🎱 *Relic:* {relic.tier} {relic.name}\n\n"
        for item in relic.rewards:
            answer_message += f"{'🟨' if item.rarity == '6' else '⬜' if item.rarity == '17' else '🟫'}  *Item:* {item.name}\n"

        await msg.answer(answer_message, reply_markup=kb.mainMenu)
    else:
        await msg.answer("❌ *Relic Doesn't Exist*", reply_markup=kb.mainMenu)


async def send_item_relic(msg: types.Message):
    command = msg.text.title()
    logging.info(f"Sending Relics With Item | Item: {command} | User ID: {msg.from_user.id}")
    relics = await parse.get_relics_with_item(command)

    if relics:
        answer_message = f"🎱 *Relics with:* {command}\n"
        latest_name = ""

        for relic in relics:
            item = relic.rewards[0]
            item_message = ""
            if latest_name != item.name:
                latest_name = item.name
                item_message = f"\n*Item:* {item.name}\n"
            
            relic_message = f"{'🟨' if item.rarity == '6' else '⬜' if item.rarity == '17' else '🟫'}  *Relic:* {relic.tier} {relic.name}\n"
                
            answer_message += item_message + relic_message

        await msg.answer(answer_message, reply_markup=kb.mainMenu)
    else:
        await msg.answer("❌ *Relics With This Item Doesn't Exist*", reply_markup=kb.mainMenu)


def register_handlers(dp: Dispatcher): 
    dp.register_message_handler(process_start_command, commands=['start'])
    dp.register_message_handler(send_world_cycles, filters.Text("🌗 World Cycles"))
    dp.register_message_handler(send_sortie_info, filters.Text("🛡 Sortie"))
    dp.register_message_handler(send_invasions_info, filters.Text("⚔️ Invasions"))
    dp.register_message_handler(send_relic_drop, filters.Text(startswith=config.RELIC_COMMANDS, ignore_case=True))
    dp.register_message_handler(send_item_relic)