from aiogram import Bot, Dispatcher
import config
from database import Database

bot = Bot(token=config.TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher(bot)

db = Database(config.DATABASE_URL)