import os

TOKEN = os.getenv('TOKEN')

RELIC_COMMANDS = ['lith', 'neo', 'meso', 'axi', 'лит', 'нео', 'мезо', 'акси', 'requiem', 'реквием']
TERRIBLE_WORDS = ['Эксилус', 'Адаптер', 'Звезда', 'Осколок', 'Чертёж']

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'Host': 'www.warframe.com'
}

OFFICIAL_URL = 'https://www.warframe.com/'
