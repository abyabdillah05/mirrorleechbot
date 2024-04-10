import random
import requests

from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd
from bot import bot
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import sync_to_async


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

@new_task
async def upload_media(_, message):
    rply = message.reply_to_message
    if rply:
        if rply.video or rply.photo or rply.video_note:
            if file := next(
                (
                    i
                    for i in [
                        rply.video,
                        rply.photo,
                        rply.video_note,
                    ]
                    if i is not None
                ),
                None,
            ):
                    media = file
            path = "telegraph_upload/"
            if not await aiopath.isdir(path):
                await mkdir(path)
            mess = await sendMessage(message, f"⌛️ Mengupload media ke telegraph, siahkan tunggu sebentar..")
            
                
            des_path = ospath.join(path, media.file_id)
            if media.file_size <= 5000000:
                await rply.download(ospath.join(getcwd(), des_path))
            else:
                await editMessage(mess, f"File yang anda coba upload terlalu besar, maksimal 5MB")
                return None

            try:
                upload_response = await sync_to_async(telegraph.upload_file, des_path)
                await editMessage(mess, f"<b>✅ Berhasil upload ke telegraph:</b>\n\nLink: <code>{upload_response}</code>")
            except Exception as e:
                await editMessage(mess, f"Gagal upload ke Telegraph {e}")          
            finally:
                await aioremove(des_path)    
    else:
        await sendMessage(message, f"Silahkan balas photo atau video pendek yang mau anda upload ke Telegraph")

bot.add_handler(
    MessageHandler(
        asupan, 
        filters=command(
            BotCommands.AsupanCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        upload_media, 
        filters=command(
            BotCommands.UploadCommand
        ) & CustomFilters.authorized
    )
)