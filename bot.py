from aiogram import Bot, Dispatcher
import config
from database import Database

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

db = Database("db.db")