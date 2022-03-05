import json
from bs4 import BeautifulSoup
import requests
import asyncio
import random
from pathlib import Path
import utils
import config
import time
from pydantic import BaseModel, Field, validator, parse_raw_as


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
    name: str = None
    state: str = None or Field(alias="active")
    eta: str = Field(alias="timeLeft")

    class Config:
        allow_population_by_field_name = True
    
    @validator("state")
    def capitalize_state(cls, value):
        
        return value.capitalize()


async def get_articles():
    print('Start parsing - ', time.strftime("%d/%m/%Y %H:%M:%S"))
    url = config.OFFICIAL_URL
    headers = config.HEADERS
    articles_list = []
    response = requests.get(url, headers).text
    soup = BeautifulSoup(response, 'lxml')

    try:
        parse_articles_list = soup.find(id='newsSection').find_all(class_='post')

        for parse_article in parse_articles_list:
            title = parse_article.find(class_='title').text.strip()
            description = parse_article.find(class_='description').text.strip()
            date = parse_article.find(class_='date').text.strip()
            read_more = parse_article.find(class_='read-more').get('href')
            photo = 'https:' + parse_article.find(class_='image').find('img').get('src')
            articles_list.append({
                'Title': title,
                'Description': description,
                'Date': date,
                'Read_More': read_more,
                'Photo': photo
            })

    except Exception as ex:
        print(f'Ошибка парсинга - {ex}')
    with open(Path("src", "articles.json"), 'w+', encoding='UTF-8') as file:
        json.dump(articles_list, file, ensure_ascii=False, indent=4)


async def get_new_articles():
    saved_articles = []
    with open("chats.txt", 'r', encoding='UTF-8') as file:
        chats = file.readlines()

    while True:
        await get_articles()

        with open(Path("src", "articles.json"), 'r', encoding='UTF-8') as file:
            got_articles = json.load(file)
        saved_articles_names = [i['Title'] for i in saved_articles]
        got_articles_names = [i['Title'] for i in got_articles]

        if saved_articles:
            saved_articles = got_articles
            print('Первый запуск')
        elif all(get in saved_articles_names for get in got_articles_names):
            print("Новых записей не найдено")
        else:
            print("Обнаружены новые записи")
            new_articles = [get for get in got_articles if get not in saved_articles]
            saved_articles = got_articles
            print(new_articles)
            return new_articles
        await asyncio.sleep(random.randrange(60, 90))


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
        print(value)
        name = value[0]
        data = requests.get(value[1], config.HEADERS).text
        
        cycle = WorldState.parse_raw(data)
        cycle.name = name
        cycle_list.append(cycle)
        
    return cycle_list
    

async def get_sortie() -> Sortie:
    data = requests.get('https://api.warframestat.us/pc/sortie?language=eu', config.HEADERS).text
    sortie = Sortie.parse_raw(data)
    
    return sortie


def get_alerts():
    raw_alerts_list = requests.get('https://api.warframestat.us/pc/alerts?language=en').json()
    alerts_list = []
    for alert in raw_alerts_list:
        if alert['active']:
            mission_info = alert['mission']
            reward_info = mission_info['reward']
            reward_name = utils.translate_item_name(str(reward_info['asString']).replace('cr', ' кредитов'))
            for word in config.TERRIBLE_WORDS:
                if word in reward_name:
                    reward_name = word + ' ' + reward_name.replace(f'{word}', '')
            alerts_list.append({
                'description': mission_info['description'],
                'mission': f"{mission_info['node']} - {mission_info['type']}",
                'faction': mission_info['faction'],
                'reward': reward_name
            })
    cache_json(alerts_list, 'alerts')


def get_invasions():
    raw_data = requests.get('https://api.warframestat.us/pc/invasions?language=eu').text
    print(raw_data)
    data = parse_raw_as(list[Invasion], raw_data)
    #Select only uncompleted invasions
    data = [i for i in data if i.completed == False and '-' not in i.eta]
    print(data)
    return data


async def get_relic_data(relic: str) -> str:
    message = ""

    ru_relic = ' '.join([i.capitalize() for i in relic[:2]])
    translate_table = {
        0: 'Intact',
        1: 'Exceptional',
        2: 'Flawless',
        3: 'Radiant'
    }
    if len(relic) == 3 and relic[2].isdigit() and int(relic[2]) <= 3:
        rarity = int(relic[2])
    else:
        rarity = 0

    relic = [i.capitalize() for i in relic[:2]]
    link = f'https://drops.warframestat.us/data/relics/{relic[0]}/{relic[1]}.json'
    try:
        response = requests.get(link).json()
        name = ' '.join(relic)
        message += f"🎱 *Relic:* {name} ({translate_table[rarity]})\n\n"

        for num, item in enumerate(response['rewards'][translate_table[rarity]]):
            item.pop('_id')
            item.pop('rarity')
            name = item['itemName']
            if len(name) > 19: name = name.replace("Blueprint", "")

            
            message += f"` - {name}".ljust(28) + \
                       f"| {'🟨' if num == 0 else '⬜' if num <= 2 else '🟫'}\n`"
                       
    except json.decoder.JSONDecodeError:
        message = "❗ Relic doesn't exist"
        
    finally:
        return message


async def get_relics_with_current_item(request: str) -> str:
    url = 'https://drops.warframestat.us/data/relics.json'
    utils.make_reversed_translation_table()
    request = request
    message = ''
    data = requests.get(url, headers=config.HEADERS).json()
    relics = []
    request_list = [i.lower() for i in request.split(' ')]
    for relic in data['relics']:
        relic_name = f"{relic['tier']} {relic['relicName']}"
        for item in relic['rewards']:
            if {item['chance']} & {2, 11, 25.33}:
                if set(request_list).issubset([i.lower() for i in item['itemName'].split(' ')]):
                    if item['itemName'] in [i['name'] for i in relics]:
                        for relic_item in relics:
                            if relic_item['name'] == item['itemName']:
                                relic_item['relic_list'].append({
                                    'relic_name': relic_name,
                                    'rarity': item['chance']
                                })
                                break
                    else:
                        relics.append({
                            'name': item['itemName'],
                            'relic_list': [
                                {
                                    'relic_name': relic_name,
                                    'rarity': item['chance']
                                }],
                        })

    for item in relics:
        message += f"*Item: {item['name']}*\n"
        for relic in item['relic_list']:
            line = ''
            line += " - Relic: {0}| {1}\n"\
                .format(relic['relic_name'].ljust(11), ['🟨' if relic['rarity'] == 2 else '⬜' if relic['rarity'] == 11 else '🟫'][0])
            message += f'`{line}`'
        message += '\n'
        
    return message


def cache_json(json_data, name):
    current_time = time.strftime(f"%d-%m-%Y_%H-{'00' if time.strftime('%M') < '30' else '30'}")
    file_src = Path("src", f"{name}_{current_time}.json")
    del_files_list = [file.unlink(missing_ok=True) for file in Path("src").glob(f'{name}*.json') if file != file_src]
    if not file_src.exists():
        with open(Path("src", f"{name}_{current_time}.json"), 'w', encoding='UTF-8') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)


def read_cached_json(name):
    current_time = time.strftime(f"%d-%m-%Y_%H-{'00' if time.strftime('%M') < '30' else '30'}")
    file_src = Path("src", f"{name}_{current_time}.json")
    print(file_src.exists(), file_src)
    if not file_src.exists():
        get_invasions()
        get_alerts()
    with open(Path("src", f"{name}_{current_time}.json"), 'r', encoding='UTF-8') as file:
        return json.load(file)