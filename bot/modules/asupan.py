import json
import random
from bot import bot
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands


file_path = "asupan.json"
async def read_local_json(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        return ("ERROR:", e)

@new_task
async def asupan(client, message):
    json_data = await read_local_json(file_path)
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
