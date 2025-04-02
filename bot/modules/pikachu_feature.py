import random
import requests
import httpx
import os
import subprocess

from asyncio import sleep as asleep, create_subprocess_exec
from bot import bot
from aiofiles.os import remove as aioremove, path as aiopath, mkdir, makedirs
from os import path as ospath, getcwd
from pyrogram.filters import command
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      editMessage,
                                                      deleteMessage)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.modules.ytdlp import YtDlp
from bot.helper.ext_utils.bot_utils import new_task


user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"

################################################
#Upload Telegraph
################################################
@new_task
async def upload_media(_, message):
    rply = message.reply_to_message
    if rply:
        if rply.video or rply.photo or rply.video_note or rply.animation:
            if file := next(
                (
                    i
                    for i in [
                        rply.video,
                        rply.photo,
                        rply.video_note,
                        rply.animation
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
            await sendMessage(message, "Jenis file tidak didukung, upload telegraph hanya support Photo, Video, dan Animation.")   
    else:
        await sendMessage(message, f"Silahkan balas photo atau video pendek yang mau anda upload ke Telegraph")


##############################################
#SUBDL by Pikachu
##############################################

keywords = []
async def get_data(name=None, id=None):
    url = "https://api.subdl.com/api/v1/subtitles"
    if name:
        data = {
            "api_key": "J23oFXWYe-GMQZgddqKx6JiUkPgkymlE",
            "languages": "ID",
            "type": "movie",
            "film_name": name
            }
    if id:
        data = {
            "api_key": "J23oFXWYe-GMQZgddqKx6JiUkPgkymlE",
            "languages": "ID",
            "type": "movie",
            "sd_id": id
            }
    try:
        r = requests.get(url, params=data).json()
        return r
    except Exception as e:
        return e
        
async def subdl_butt(uid):
    for kueri in keywords:
        if uid in kueri:
            keyword = kueri
            keyword = (keyword[uid])
    butt = ButtonMaker()
    msg = ""
    r = await get_data(name=keyword, id=None)
    if isinstance(r, dict) and "status" in r:
        if (r["status"]):
            results = (r["results"])
            for index, result in enumerate(results, start=1):
                name = (result["name"])
                year = (result["year"])
                id = int(result["sd_id"])
                msg += f"<b>{index:02d}. </b>{name} [{year}]"
                msg += f"\n"
                butt.ibutton(f"{index}", f"sub s {uid} {id}")
            butt.ibutton("⛔️ Batal", f"sub x {uid}", position="footer")
            butts = butt.build_menu(6)
            return msg, butts
        else:
            butt.ibutton("⛔️ Batal", f"sub x {uid}", position="footer")
            butts = butt.build_menu(1)
            return f"Gagal mendapatkan subtitle dari film \n<code>{keyword}</code>\n\n{r}", butts
    else:
        butt.ibutton("⛔️ Batal", f"sub x {uid}", position="footer")
        butts = butt.build_menu(1)
        return f"Gagal mendapatkan subtitle dari film \n<code>{keyword}</code>\n\n{r}", butts


async def subdl(client, message):
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        keyword = None

    if keyword:
        mess = await sendMessage(message, f"<b>Tunggu sebentar tuan...</b>")
        uid = message.from_user.id
        kueri = {
            uid: keyword
        }
        keywords.append(kueri)     
        msg,butts = await subdl_butt(uid)
        await sendMessage(message, msg, butts)
        await deleteMessage(mess)
    else:
        await sendMessage(message, "Silahkan masukkan perintah disertai dengan nama film.")

async def subdl_result(uid, id):
    r = await get_data(name=None, id=id)
    
    for kueri in keywords:
        if uid in kueri:
            keyword = kueri
            keyword = (keyword[uid])
    butt = ButtonMaker()
    butt.ibutton("⬅️ Kembali", f"sub b {uid}")
    butt.ibutton("⛔️ Batal", f"sub x {uid}")
    butts = butt.build_menu(2)    
    if (r["status"]):
        name = (r["results"][0]["name"])
        msg  = f"<b>Nama:</b> <code>{name}</code>\n<b>Bahasa:</b> <code>Indonesia</code>\n\n"
        subs = (r["subtitles"])
        for index, result in enumerate(subs, start=1):
            name = (result["release_name"])
            url = (result["url"])
            sub = f"https://dl.subdl.com{url}"
            msg += f"<b>{index:02d}. </b><a href='{sub}'>{name}</a>"
            msg += f"\n"   
        return msg, butts
    else:
        return f"Terjadi kesalahan saat mengambil subtitle atau subtitle untuk film ini belum tersedia", butts
            
async def subdl_query(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    uid = int(data[2])
    for kueri in keywords:
        if uid in kueri:
            keyword = kueri
            keyword = (keyword[uid])
    if user_id != uid:
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)
    elif data[1] == "s":
        await editMessage(message, "⌛")
        id = int(data[3])
        try:
            msg,butts = await subdl_result(uid,id)
            await editMessage(message, msg, butts)
        except Exception as e:
            await editMessage(message, f"Gagal mengambil hasil, atau subtitle untuk film ini belum tersedia.")
            del keyword[uid]
        
    elif data[1] == "b":
        await editMessage(message, "⌛")
        try:
            msg,butts = await subdl_butt(uid)
            await editMessage(message, msg, butts)
        except Exception as e:
            await editMessage(message, f"Gagal mengambil hasil, atau subtitle untuk film ini belum tersedia. \n\n{e}")
            del keyword[uid]
    else:
        await query.answer()
        await editMessage(message, "Tugas Dibatalkan.")
        del keyword[uid]


#####################################
#GALLERY-DL
#####################################
async def downloader(url):
    output_dir = "gallery_dl/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Perintah untuk menjalankan gallery-dl
    command = ['gallery-dl', '-d', output_dir, url]
    if "instagram" in url:
        command.extend(['--cookies', 'instagram.txt'])
        
    process = await create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        file_paths = []
        for root, _, files in os.walk(output_dir):
            for file_name in files:
                file_paths.append(os.path.join(root, file_name))
        return file_paths
    else:
        return None
    
async def gallery_dl(client, message, auto=False):
    if auto:
        url = message.text
    else:
        rply = message.reply_to_message
        if rply:
            url = rply.text if rply.caption is None else rply.caption
        else:
            msg = message.text.split(maxsplit=1)
            if len(msg) > 1:
                url = msg[1].strip()
            else:
                await sendMessage (message, "Silahkan kirimkan link yang akan diunduh dengan gallery-dl !!.")
                return

    mess = await sendMessage(message, f"<b>Mengunduh media dengan Gallery-DL...</b>\n\n<b>Link: </b><code>{url}</code>")
    file_paths = await downloader(url)
    if file_paths is None:
        await editMessage(mess, f"Gagal mendownload media dari link anda.\n\n<b>Link: </b><code>{url}</code>")
        return

    media_group = []
    for file_path in file_paths:
        if file_path.endswith(('.mp4', '.mkv', '.webm')):
            media_group.append(InputMediaVideo(media=file_path))
        elif file_path.endswith(('.png', '.jpeg', '.jpg')):
            media_group.append(InputMediaPhoto(media=file_path))

    if media_group:
        for i in range(0, len(media_group), 10):
            batch = media_group[i:i+10]
            await message.reply_media_group(media=batch)
        await deleteMessage(mess)
        await sendMessage(message, f"Hai {message.from_user.mention}, tugas anda sudah selesai diupload.")

        for file_path in file_paths:
            os.remove(file_path)
    else:
        await editMessage(mess, "Tidak ada media yang ditemukan untuk diunggah.")

async def gallery_dl_auto(client, message):
    if len(message.text.split()) == 1:
        await gallery_dl(client, message, auto=True)

########################################################################################

gallery_dl_regex = r'https?:\/\/(www\.)?(instagram\.com\/[a-zA-Z0-9._-]+|twitter\.com\/[a-zA-Z0-9_]+|x\.com\/[a-zA-Z0-9_]+)'


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
        gallery_dl, 
        filters=command(
            BotCommands.GallerydlCommand
        ) & CustomFilters.authorized
    )
)