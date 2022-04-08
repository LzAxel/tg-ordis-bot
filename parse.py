import time
import json
import logging
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import config
import time
from pydantic import parse_raw_as
import pydantic
import re
from classes import APIDump, Invasion, Sortie, WorldState, Relic, Article
from utils import send_report

async def parse_articles():
    logging.info("Parsing articles")
    url = config.OFFICIAL_URL
    headers = config.HEADERS
    articles_list = []

    with requests.Session() as session:
        session.cookies.set("landing", "1", domain="warframe.com")
        session.headers.update(headers)
        response = session.get(url)

    soup = BeautifulSoup(response.text, 'lxml')
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
    except AttributeError as ex:
        logging.exception(ex)
        logging.exception("Failed to parse articles")
        
        error_time = time.strftime('%d-%m-%Y_%S-%M-%H', time.gmtime())
        with open(Path("src", f"articles-{error_time}.html"), "w", encoding="UTF-8") as file:
            file.write(response.text)
        
        await send_report(ex, "Failed to parse articles", open(Path("src", f"articles-{error_time}.html"), "rb"))
            
    return articles_list


async def update_api_dump():
    logging.info("Updating API Dump")
    response = requests.get("https://api.warframestat.us/pc").text
    data = APIDump.parse_raw(response)
    cycle_list = [re.findall("\D*Cycle", i) for i in data.dict().keys()]
    cycle_list = {i[0] for i in cycle_list if i}
    if data.alerts and Path("src", "api_dump.json").exists():
        dump = APIDump.parse_file(Path("src", "api_dump.json"))
        for num, alert in enumerate(dump.alerts):
            if alert.notified and alert.active:
                data.alerts[num].notified = True

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


async def read_api_dump():
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
    
    

async def get_cycles() -> list:
    cycle_list = []
    
    for value in config.WORLD_STATE_URLS.values():
        logging.info(f"Parsing {value[0]} cycle")
        name = value[0]
        data = requests.get(value[1], config.HEADERS).text
        
        cycle = WorldState.parse_raw(data)
        cycle.name = name
        cycle_list.append(cycle)
    
    logging.debug(cycle_list)    
        
    return cycle_list
    

async def get_sortie() -> Sortie:
    logging.info(f"Parsing Sortie")
    data = requests.get('https://api.warframestat.us/pc/sortie?language=eu', config.HEADERS).text
    sortie = Sortie.parse_raw(data)
    logging.debug(sortie)
    
    return sortie


def get_invasions() -> list:
    logging.info(f"Parsing Invasions")
    raw_data = requests.get('https://api.warframestat.us/pc/invasions?language=eu').text
    data = parse_raw_as(list[Invasion], raw_data)
    logging.debug(data)
    #Select only uncompleted invasions
    data = [i for i in data if i.completed == False and '-' not in i.eta]
    
    return data


async def get_relic_drop(tier, name) -> str:
    logging.info(f"Parsing Relic Data")

    data = pydantic.parse_file_as(list[Relic], Path("src", "relics_dump.json"))
    for relic in data:
        if relic.name == name and relic.tier == tier:
            return relic


async def get_relics_with_item(req_item: str) -> list[Relic]:
    logging.info(f"Parsing Relic Data With Item")
    item = set(req_item.split())
    relics = []
    
    data = pydantic.parse_file_as(list[Relic], Path("src", "relics_dump.json"))
    for relic in data:
        for reward in relic.rewards:
            if item.issubset(set(reward.name.split())):
                relic.rewards = [i for i in relic.rewards if item.issubset(set(i.name.split()))]
                relics.append(relic)
    
    return sorted(relics, key=lambda x: x.rewards[0].name)


async def set_alert_notified(id):
    api = await read_api_dump()
    for alert in api.alerts:
        if alert.id == id:
            alert.notified = True

    export = api.dict(by_alias=True)
    with open(Path("src", "api_dump.json"), "w", encoding="UTF-8") as file:
        json.dump(export, file, indent=4, ensure_ascii=False)
