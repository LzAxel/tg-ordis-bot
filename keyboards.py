from ast import Call
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,\
                        InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.utils.callback_data import CallbackData


# ---- Menu ----

cyclesBtn = KeyboardButton('🌗 World Cycles')
sortieBtn = KeyboardButton('🛡 Sortie')
invasionsBtn = KeyboardButton('⚔️ Invasions')

mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(cyclesBtn, sortieBtn, invasionsBtn)


# ---- Trader buttons ----

trader_callback = CallbackData("trader", "action")

trader_open = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Open Inventory", callback_data=trader_callback.new(action="open"))]])
trader_close = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("Close Inventory", callback_data=trader_callback.new(action="close"))]])
