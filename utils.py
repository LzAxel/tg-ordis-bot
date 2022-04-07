from bot import bot
from config import ADMIN_ID
import time
import traceback

async def send_report(ex: Exception, message: str, file = None):
    error_time = time.strftime('%d-%m-%Y %S:%M:%H', time.gmtime())
    await bot.send_message(ADMIN_ID, f"❗️ Unexpected Error ❗️\n\n{traceback.format_exc()}\nAdditional Message: {message}\n\nTime: {error_time}",
                           parse_mode="HTML")

    if file:
        await bot.send_document(ADMIN_ID, file)