import asyncio
import time
import json
import logging
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import config
import time
from pydantic import BaseModel, Field, validator, parse_raw_as
import pydantic
import re
from typing import Optional

class SortieMission(BaseModel):
    mission_type: str = Field(alias="missionType")
    modifier: str
    description: str = Field(alias="modifierDescription")
    location: str = Field(alias="node")


class Sortie(BaseModel):
    boss: str
    faction: str
    eta: str
    missions: list[SortieMission] = Field(alias="variants")


class Reward(BaseModel):
    name: str = Field(alias="asString")

    class Config:
        validate_assignment = True

    @validator('name')
    def set_empty_item(cls, name):
        if not name:
            return "None"
        else:
            return name
        

class AlertMission(BaseModel):
    location: str = Field(alias="node")
    description: str
    type: str
    faction: str
    reward: Reward


class Alert(BaseModel):
    mission: AlertMission
    active: bool
    eta: str


class Faction(BaseModel):
    faction: str
    reward: Reward


class Invasion(BaseModel):
    location: str = Field(alias="node")
    eta: str
    defender: Faction
    attacker: Faction
    completed: bool


class WorldState(BaseModel):
    name: str = Field(alias="id")
    state: Optional[str] = Field(alias="active")
    eta: str = Field(alias="timeLeft")

    class Config:
        allow_population_by_field_name = True

    @validator("state")
    def capitalize_state(cls, value):
        
        return value.capitalize()

    @validator("name", always=True)
    def set_name(cls, value):
        template = {
            "earth": "🌎 Earth",
            "cetus": "✨ Cetus",
            "cambion": "🔥 Cambion Drift",
            "vallis": "🌪 Orb Vallis"
        }
        value = value.split("Cycle")[0]
        if value in template.keys():
            return template[value]
        else:
            return value


class Article(BaseModel):
    title: str
    description: str
    date: str
    photo: str
    url: str


class APIDump(BaseModel):
    timestamp: str
    sortie: Sortie
    invasions: list[Invasion]
    alerts: list[Alert]
    cetusCycle: Optional[WorldState]
    vallisCycle: Optional[WorldState]
    cambionCycle: Optional[WorldState]
    earthCycle: Optional[WorldState]
    cycles: Optional[list[WorldState]]

    @validator("invasions")
    def validate_invasion(cls, value):
        value = [i for i in value if not i.completed]

        return value


    @validator("cycles", always=True)
    def validate_cycles(cls, value, values):
        if value:
            return value
        else:
            value = []
            cycle_list = [re.findall("\D*Cycle", i) for i in values.keys()]
            cycle_list = [i[0] for i in cycle_list if i]
            for i in cycle_list:
                value.append(values[i])
            return value


class RelicReward(BaseModel):
    name: str = Field(alias="itemName")
    rarity: Optional[str] = Field(alias="chance")


class Relic(BaseModel):
    name: str = Field(alias="relicName")
    tier: str = Field(alias="tier")
    rewards: list[RelicReward]
        
    @validator("rewards")
    def validate_rewards(cls, value):
        return sorted(value, key = lambda i: (float(i.rarity)))

 

async def parse_articles():
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


async def update_api_dump():
    logging.info("Updating API Dump")
    response = requests.get("https://api.warframestat.us/pc").text
    data = APIDump.parse_raw(response)
    cycle_list = [re.findall("\D*Cycle", i) for i in data.dict().keys()]
    cycle_list = {i[0] for i in cycle_list if i}
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
    dump = APIDump.parse_file(Path("src", "api_dump.json"))
    
    return dump

    
async def get_new_articles():
    articles = await parse_articles()
    try:
        if not Path("src", "articles.json").exists(): Path("src", "articles.json").touch()

        with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
            data = file.read()
            cached_articles = parse_raw_as(list[Article], data)

        if all(a in cached_articles for a in articles):
            logging.info("No articles was founded!")

        else:
            new_articles = [a for a in articles if a not in cached_articles]
            
            return new_articles

    except json.JSONDecodeError:
        logging.info("Creating first articles.json dump")

    finally:
        with open(Path("src", "articles.json"), 'w', encoding='UTF-8') as file:
            json.dump([i.dict() for i in articles], file, ensure_ascii=False, indent=4)
    

async def get_relic_names_list() -> list:
    relic_names_list = []
    with open(Path("src", "relics.json"), 'r', encoding='UTF-8') as file:
        data = json.load(file)
        for era in data:
            relic_names_list += [relic['name'] for relic in data[era]]
        return relic_names_list


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


async def get_relic_drop(req_relic: str) -> str:
    logging.info(f"Parsing Relic Data")

    tier = req_relic.split()[0]
    name = req_relic.split()[1]

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


if __name__ == "__main__":
    # asyncio.run(update_relic_dump())
    asyncio.run(get_relics_with_item("Nikana Prime"))
    # asyncio.run(get_relic_data("Axi A1"))
    # print(asyncio.run((read_api_dump("alerts"))))
