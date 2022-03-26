import json
import logging
import re
import time
from pathlib import Path

import pydantic
import requests
from bs4 import BeautifulSoup
from pydantic import parse_raw_as

import config
from classes import APIDump, Article, Invasion, Relic, Sortie, WorldState


async def parse_articles() -> list:
    logging.info("Parsing articles")
    url = config.OFFICIAL_URL
    headers = config.HEADERS
    articles_list = []

    session = requests.Session()
    session.headers.update(headers)
    session.get(url, headers=headers)
    request = session.get(url, headers=headers)
    soup = BeautifulSoup(request.text, 'lxml')

    try:
        parse_articles_list = soup.find(id='newsSection').find_all(class_='post')

        for parse_article in parse_articles_list:
            title = parse_article.find(class_='title').text.strip()
            description = parse_article.find(class_='description').text.strip()
            date = parse_article.find(class_='date').text.strip()
            read_more = parse_article.get("data-link")
            photo = 'https:' + parse_article.find(class_='image').find('img').get('src')
            articles_list.append(Article(title=title, description=description, 
                                         date=date, photo=photo, url=read_more))

    except Exception as ex:
        logging.exception(ex)
        logging.error('Failed to parse. Check logs please.')
        error_time = time.strftime('%d-%m-%Y_%S-%M-%H', time.gmtime())
        with open(Path("logs", f"articles-{error_time}"), 'w+', encoding='UTF-8') as file:
            file.write(request.text)

    return articles_list


async def update_api_dump() -> None:
    logging.info("Updating API Dump")
    response = requests.get("https://api.warframestat.us/pc").text
    data = APIDump.parse_raw(response)
    cycle_list = [re.findall("\D*Cycle", i) for i in data.dict().keys()]
    cycle_list = {i[0] for i in cycle_list if i}
    if Path("src", "api_dump.json").exists():
        dump = APIDump.parse_file(Path("src", "api_dump.json"))
        for num, alert in enumerate(dump.alerts):
            if alert.notified and alert.active:
                data.alerts[num].notified = True
        
        if dump.trader.notified: data.trader.notified = True

    export = data.dict(exclude=cycle_list, by_alias=True)
    with open(Path("src", "api_dump.json"), "w", encoding="UTF-8") as file:
        json.dump(export, file, indent=4, ensure_ascii=False)
    logging.info("Updating API Dump Complete!")


async def update_relic_dump():
    logging.info("Updating Relic Dump")
    response = requests.get("https://drops.warframestat.us/data/relics.json").json()
    data = pydantic.parse_obj_as(list[Relic], response["relics"])
    data = [i.dict(by_alias=True) for i in data if i.rewards[0].rarity in ["6", "17", "20"]]
    with open(Path("src", "relics_dump.json"), "w", encoding="UTF-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    logging.info("Updating Relics Dump Complete!")       


async def read_api_dump() -> APIDump:
    if not Path("src", "api_dump.json").exists():
        await update_api_dump()
    dump = APIDump.parse_file(Path("src", "api_dump.json"))
    
    return dump

    
async def get_new_articles() -> list:
    articles = await parse_articles()

    if not Path("src", "articles.json").exists(): Path("src", "articles.json").touch()

    try:
        with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
            data = file.read()
            cached_articles = parse_raw_as(list[Article], data)

        if all(a in cached_articles for a in articles):
            logging.info("New Articles Not Found")

        else:
            return [a for a in articles if a not in cached_articles] # New articles

    except json.JSONDecodeError:
        logging.info("First Articles Check")

    finally:            
        with open(Path("src", "articles.json"), 'w', encoding='UTF-8') as file:
            json.dump([i.dict() for i in articles], file, ensure_ascii=False, indent=4)


async def get_relic_drop(relic_name: str) -> str:
    logging.info(f"Parsing Relic Data")

    tier, name = relic_name.split()

    data = pydantic.parse_file_as(list[Relic], Path("src", "relics_dump.json"))
    for relic in data:
        if relic.name == name and relic.tier == tier:
            return relic


async def get_relics_with_item(item_name: str) -> list[Relic]:
    logging.info(f"Parsing Relic Data With Item")
    item = set(item_name.split())
    relics = []
    
    data = pydantic.parse_file_as(list[Relic], Path("src", "relics_dump.json"))
    for relic in data:
        for reward in relic.rewards:
            if item.issubset(set(reward.name.split())):
                relic.rewards = [i for i in relic.rewards if item.issubset(set(i.name.split()))]
                relics.append(relic)
    
    return sorted(relics, key=lambda x: x.rewards[0].name)


async def set_event_notified(name: str, *id: int) -> None:
    api = await read_api_dump()
    match name:
        case "alert":       
            for alert in api.alerts:
                if alert.id == id:
                    alert.notified = True
        case "trader":
            api.trader.notified = True

    export = api.dict(by_alias=True)
    with open(Path("src", "api_dump.json"), "w", encoding="UTF-8") as file:
        json.dump(export, file, indent=4, ensure_ascii=False)
