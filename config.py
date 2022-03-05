import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

RELIC_COMMANDS = ['lith', 'neo', 'meso', 'axi', 'requiem']

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'sec-ch-ua-mobile': '?0'

}

OFFICIAL_URL = 'https://www.warframe.com/eu'

WORLD_STATE_URLS = {
    "cambion": ("🔥 Cambion Drift", "https://api.warframestat.us/pc/cambionCycle"),
    "cetus": ("✨ Cetus", "https://api.warframestat.us/pc/cetusCycle"),
    "earth": ("🌎 Earth", "https://api.warframestat.us/pc/earthCycle"),
    "vallis": ("🌪 Orb Vallis", "https://api.warframestat.us/pc/vallisCycle")
}