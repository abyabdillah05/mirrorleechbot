import random
import requests
import re

from json import loads
from bot import bot
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler
from pyrogram.types import InputMediaPhoto
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, deleteMessage, customSendAudio, customSendPhoto, customSendVideo
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import sync_to_async


file_url = "https://gist.github.com/aenulrofik/33be032a24c227952a4e4290a1c3de63/raw/asupan.json"
user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"

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

async def tiktokdl(_, message):
    url = message.text
    mess = await sendMessage(message, f"<b>⌛️Link tiktok terdeteksi, silahkan tunggu sebentar...</b>")
    with requests.Session() as session:
        try:
            r = session.get(url)
        except Exception as e:
            return f"ERROR: {e}"
        
        if not r.ok:
            await editMessage(mess, f"ERROR: Gagal mendapatkan data")
            return None
        pattern = r"^(?:https?://(?:www\.)?tiktok\.com)/(?P<user>[\a-zA-Z0-9-]+)(?P<content_type>video|photo)+/(?P<id>\d+)"
        match = re.match(pattern, string=r.url)
        if match:  
            content_type = match.group("content_type")
        else:
            await editMessage(message, f"Link yang anda berikan sepertinya salah atau belum support, silahkan coba dengan link yang lain !")
            return None
        data = ""
        while len(data) == 0:
            r = session.get(
                url=f"https://api22-normal-c-useast2a.tiktokv.com/aweme/v1/feed/?aweme_id={match.group('id')}",
                headers={
                    "User-Agent": user_agent,
                }
            )
            data += r.text
        data = loads(data) 
        try:
            #music = data["aweme_list"][0]["music"]["play_url"]["url_list"][-1]
            #m_capt = data["aweme_list"][0]["music"]["title"]
            if content_type == "video":
                link = data["aweme_list"][0]["video"]["play_addr"]["url_list"][-1]
                filename = data["aweme_list"][0]["desc"]
                capt = f"<code>{filename}</code>"                
                await customSendVideo(message, link, capt, None, None, None, None, None)
                #await customSendAudio(message, music, m_capt, None, None, None, None, None)
            if content_type == "photo":
                photo_urls = []
                for aweme in data["aweme_list"][0]["image_post_info"]["images"]:
                    for link in aweme["display_image"]["url_list"][1:]:
                        photo_urls.append(link)
                photo_groups = [photo_urls[i:i+10] for i in range(0, len(photo_urls), 10)]
                for photo_group in photo_groups:
                    await message.reply_media_group([InputMediaPhoto(photo_url) for photo_url in photo_group])
                #await customSendAudio(message, music, m_capt, None, None, None, None, None)
               
        except Exception as e:
                await sendMessage(message, f"ERROR: Gagal mengupload media {e}")
        finally:
            await deleteMessage(mess)

tiktokregex = r"(https?://(?:www\.)?[a-zA-Z0-9.-]*tiktok\.com/)"

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
bot.add_handler(
    MessageHandler(
        tiktokdl,
        filters=CustomFilters.authorized
        & filters.regex(
            f"{tiktokregex}"
        )
    )
)