import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_ID = os.getenv('ADMIN_ID')

TROLL_STICKER_ID = "CAACAgIAAxkBAAIUAWJQf3dcOKY8HikXvcP3g5fG_4oFAAK1SwAC6VUFGD-0J0GWs82RIwQ"

RELIC_COMMANDS = ['lith', 'neo', 'meso', 'axi']

OFFICIAL_URL = 'https://www.warframe.com/'

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Host': 'www.warframe.com'
}


