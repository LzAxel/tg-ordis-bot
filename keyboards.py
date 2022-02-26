from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---- Menu ----

cyclesBtn = KeyboardButton('🌗 World Cycles')
sortieBtn = KeyboardButton('🛡 Sortie')
invasionsBtn = KeyboardButton('⚔️ Invasions')
# alertsBtn = KeyboardButton('❕ Сигналы Тревоги')
mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(cyclesBtn, sortieBtn, invasionsBtn)
