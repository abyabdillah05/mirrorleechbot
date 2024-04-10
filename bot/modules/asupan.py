import json
import random
import requests

from bot import bot
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands


file_url = "https://gist.github.com/aenulrofik/33be032a24c227952a4e4290a1c3de63/raw/asupan.json"

async def get_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return ("ERROR:", e)

@new_task
async def asupan(client, message):
    json_data = await get_url(file_url)
    if json_data:
        if isinstance(json_data, list):
            video_link = random.choice(json_data)
            try:
                await message.reply_video(video_link)
            except Exception as e:
                await sendMessage(message, f"ERROR: {e}")
        else:
            await sendMessage(message, f"Gagal mengirim video")
    else:
        await sendMessage(message, f"Gagal mengambil link")

bot.add_handler(
    MessageHandler(
        asupan, 
        filters=command(
            BotCommands.AsupanCommand
        ) & CustomFilters.authorized
    )
)
