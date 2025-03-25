import random

import requests
import re
import httpx
import niquests
import os
import subprocess
import time
import pickle
import asyncio
import aiofiles

from asyncio import sleep as asleep, create_subprocess_exec
from http.cookiejar import MozillaCookieJar
from random import randint
from json import loads
from bot import bot, DATABASE_URL, LOGGER
from aiofiles.os import remove as aioremove, path as aiopath, mkdir, makedirs
from os import listdir, path as ospath, getcwd
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from shutil import rmtree
from bot import config_dict
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.telegram_helper.button_build import ButtonMaker
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      editMessage,
                                                      deleteMessage,
                                                      customSendVideo,
                                                      customSendPhoto,
                                                      customSendAudio)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import sync_to_async
from pyrogram.enums import ChatType
from bot.modules.ytdlp import YtDlp
from bot.helper.ext_utils.bot_utils import update_user_ldata, new_task
from bot.helper.ext_utils.db_handler import DbManger
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

tiktok = []
file_url = "https://gist.github.com/aenulrofik/33be032a24c227952a4e4290a1c3de63/raw/asupan.json"
user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"

###############################################
#ASUPAN
###############################################
async def get_url(url):
    try:
        r = requests.get(url).json()
        if r:
            if isinstance(r, list):
                random.shuffle(r)
                video_link = random.choice(r)
                return video_link
    except Exception as e:
        return ("ERROR:", e)

@new_task
async def asupan(client, message, ganti=None):
    mess = await sendMessage(message, "<b>Tunggu sebentar tuan...</b>")
    uid = message.from_user.id
    try_count = 5
    attempt = 1
    while attempt <= try_count:
        try:
            butt = ButtonMaker()
            butt.ibutton("🔄 Ganti Asupan", f"asupan {uid} ganti" )
            butts = butt.build_menu(1)
            video_link = await get_url(file_url)
            await message.reply_video(video_link, reply_markup=butts)
            break
        except:
            attempt += 1
            if attempt <= try_count:
                await editMessage(mess, f"Gagal mengirim asupan, Mencoba lagi untuk ke-{attempt} kali...")
            else:
                await sendMessage(mess, f"Gagal mengupload asupan setelah 5x percobaan.")
                break
    await deleteMessage(mess)
        

async def asupan_query(_, query):
    message = query.message
    edit_media = query.edit_message_media
    uid = query.from_user.id
    data = query.data.split()
    if uid != int(data[1]):
        return await query.answer(text="Bukan asupan anda tuan !", show_alert=True)
    elif data[2] == "ganti":
        try_count = 5
        attempt = 1
        while attempt <= try_count:
            try:
                butt = ButtonMaker()
                butt.ibutton("🔄 Ganti Asupan", f"asupan {uid} ganti" )
                butts = butt.build_menu(1)
                video_link = await get_url(file_url)
                caption = None
                if video_link.endswith('.mp4'):
                    await edit_media(media=InputMediaVideo(video_link, caption=caption), reply_markup=butts)
                else:
                    await edit_media(video_link, reply_markup=butts)
                break
            except Exception as e:
                attempt += 1
                if attempt == try_count:
                    await sendMessage(message, f"Gagal mengupload asupan setelah 5x percobaan.\n\n{e}")
                    break

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

############################################
#Tiktok Downloader
############################################
async def tiktokdl(client, message, url, audio=False, type="video"):
    mess = await sendMessage(message, "<b>⌛ Sedang mencoba mengunduh...</b>")
    
    try:
        # Process URL to get direct link
        async with httpx.AsyncClient() as http_client:
            hasil = await http_client.get(
                url="https://tiktok-dl-api.vercel.app/api",
                params={"url": url},
                timeout=30
            )
            hasil.raise_for_status()
            data = hasil.json()
            
        if not data.get("success"):
            await editMessage(mess, f"<b>❌ Error:</b> {data.get('message', 'Link tidak dapat diproses')}")
            return None
        
        # Get TikTok info
        title = data.get("desc", "No description")
        author = data.get("author", {}).get("nickname", "Unknown author")
        
        # Handle different download types
        if audio:
            # Download audio
            audio_url = data.get("music_url")
            if not audio_url:
                await editMessage(mess, "<b>❌ Error:</b> Audio tidak ditemukan")
                return None
                
            await editMessage(mess, f"<b>⬇️ Mengunduh audio dari TikTok...</b>\n\n<i>{title}</i>")
            
            # Download and send audio
            audio_file = f"{config_dict['TEMP_PATH']}/{message.id}_audio.mp3"
            await download_file(audio_url, audio_file)
            
            caption = f"<b>🎵 Audio TikTok</b>\n\n<b>Judul:</b> {title}\n<b>Pembuat:</b> {author}"
            
            await message.reply_audio(
                audio=audio_file,
                caption=caption,
                title=f"TikTok Audio - {author}"
            )
            
            await deleteMessage(mess)
            await aioremove(audio_file)
            
        elif type == "nowm":
            # Download video without watermark
            nowm_url = data.get("video_no_wm")
            if not nowm_url:
                await editMessage(mess, "<b>❌ Error:</b> Video tanpa watermark tidak tersedia")
                return None
                
            await editMessage(mess, f"<b>⬇️ Mengunduh video TikTok tanpa watermark...</b>\n\n<i>{title}</i>")
            
            # Download and send video
            video_file = f"{config_dict['TEMP_PATH']}/{message.id}_nowm.mp4"
            await download_file(nowm_url, video_file)
            
            caption = f"<b>🎬 Video TikTok (Tanpa Watermark)</b>\n\n<b>Judul:</b> {title}\n<b>Pembuat:</b> {author}"
            
            await message.reply_video(
                video=video_file,
                caption=caption
            )
            
            await deleteMessage(mess)
            await aioremove(video_file)
            
        else:  # Regular video with watermark
            # Download video with watermark
            video_url = data.get("video_url")
            if not video_url:
                await editMessage(mess, "<b>❌ Error:</b> Video tidak ditemukan")
                return None
                
            await editMessage(mess, f"<b>⬇️ Mengunduh video TikTok...</b>\n\n<i>{title}</i>")
            
            # Download and send video
            video_file = f"{config_dict['TEMP_PATH']}/{message.id}_video.mp4"
            await download_file(video_url, video_file)
            
            caption = f"<b>🎬 Video TikTok</b>\n\n<b>Judul:</b> {title}\n<b>Pembuat:</b> {author}"
            
            await message.reply_video(
                video=video_file,
                caption=caption
            )
            
            await deleteMessage(mess)
            await aioremove(video_file)
            
    except Exception as e:
        await editMessage(mess, f"<b>❌ Error:</b> {str(e)}")
        LOGGER.error(f"TikTok download error: {str(e)}")

async def download_file(url, path):
    """Helper function to download files from URL"""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async with aiofiles.open(path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)

#########################################
#Tiktok Search
#########################################
async def tiktok_search(_, message):
    if message.from_user.username:
            uname = f'@{message.from_user.username}'
    else:
            uname = f'<code>{message.from_user.first_name}</code>'
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        await sendMessage(message, f"Silahkan masukkan keyword pencarian setelah perintah !")
    mess = await sendMessage(message, f"<b>⌛️Sedang mencari video tiktok dengan keyword:</b>\n\n<code>🔎 {keyword}</code>")
    #session = create_scraper()
    try:
        jar = MozillaCookieJar()
        jar.load("tiktok.txt", ignore_discard=True, ignore_expires=True)
    except Exception as e:
        await editMessage(mess, f"ERROR: {e.__class__.__name__}")
        return None
    
    cookies = {}
    for cookie in jar:
        cookies[cookie.name] = cookie.value
    params = {
                "aid": 1988,
                "app_language": "en",
                "app_name": "tiktok_web",
                "browser_language": "en-US",
                "browser_name": "Mozilla",
                "browser_online": True,
                "browser_platform": "Win32",
                "browser_version": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
                "channel": "tiktok_web",
                "cookie_enabled": True,
                "device_id": 7335161018286622210,
                "device_platform": "web_pc",
                "device_type": "web_h264",
                "focus_state": True,
                "from_page": "search",
                "history_len": 3,
                "is_fullscreen": False,
                "is_page_visible": True,
                "keyword": keyword,
                "offset": 0,
                "os": "windows",
                "priority_region": "id",
                "referer": "",
                "region": "id",
                "screen_height": 1080,
                "screen_width": 1920,
                "search_source": "normal_search",
                "tz_name": "Asia/Jakarta",
                "count": 10,
                "web_search_code": {
                    "tiktok": {
                        "client_params_x": {
                            "search_engine": {
                                "ies_mt_user_live_video_card_use_libra": 1,
                                "mt_search_general_user_live_card": 1
                            }
                        }, 
                        "search_server": {}
                    }
                }
            }
    async with httpx.AsyncClient() as client:
        try:
            num = 0
            search = ""
            while len(search) == 0:
                num += 1
                r = await client.get(
                    url="https://www.tiktok.com/api/search/item/full/",
                    params=params,
                    cookies=cookies
                )

                search += r.text

            data = loads(search)
        except httpx.HTTPStatusError as e:
            await sendMessage(mess, f"Hai {uname}, Terjadi kesalahan saat mencoba mengakses url, silahkan coba kembali.\n\n<blockquote>{e}</blockquote>")
            await deleteMessage(mess)
            return None
        except httpx.RequestError as e:
            await sendMessage(mess, f"Hai {uname}, Respon dari url terlalu lama, silahkan coba kembali.\n\n<blockquote>{e}</blockquote>")
            await deleteMessage(mess)
            return None
        #try:
        #    id = (f"{data['item_list'][randint(0, len(data['item_list']) - 1)]['id']}")
        #except Exception as e:
        #    await editMessage(mess, f"ERROR: {e}")
        #    return None
        #await deleteMessage(mess)
        #await tiktokdl(_, message, id=id)
    async with niquests.AsyncSession() as client:
        video = ""
        try:
            while len(video) == 0:
                r = await client.get(
                        url=f"https://api16-normal-useast5.us.tiktokv.com/aweme/v1/feed/?aweme_id={data['item_list'][randint(0, len(data['item_list']) - 1)]['id']}",
                        headers={
                            "User-Agent": user_agent,
                        }
                    )
                r.raise_for_status()
                video = r.text
            data = loads(video)
        except Exception as e:
            await sendMessage(mess, f"Hai {uname}, Terjadi kesalahan saat mencoba mengakses url, silahkan coba kembali.\n\n<blockquote>{e}</blockquote>")
            await deleteMessage(mess)
            return None
        try:
            capt = (f'<code>{data["aweme_list"][0]["desc"]}</code>\n\n<b>Pencarian Oleh:</b> {uname}')
            link = (data["aweme_list"][0]["video"]["play_addr"]["url_list"][-1])    
            await customSendVideo(message, link, capt, None, None, None, None, None)
        except Exception as e:
            await sendMessage(message, f"<b>Hai {uname}, tugas pencarian gagal karena:\n\n{e}")
        finally:
            await deleteMessage(mess)

#####################################################
# Fitur Waifu
#####################################################
async def animek(_, message):
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        keyword = ""
    mess = await sendMessage(message, f"<b>Tunggu sebentar tuan...</b>")
    tags = [
        {"maid": "maid"},
        {"wife": "waifu"},
        {"marin": "marin-kitagawa"},
        {"mori": "mori-calliope"},
        {"raiden": "raiden-shogun"},
        {"oppai": "oppai"},
        {"selfie": "selfies"},
        {"uniform": "uniform"},
        {"ayaka": "kamisato-ayaka"}
    ]
    if keyword.lower() == "list":
        msg = f"""
        <b>Daftar list keyword</b>:    
<blockquote>• <code>maid</code>
• <code>wife</code>
• <code>marin</code>
• <code>mori</code>
• <code>raiden</code>
• <code>oppai</code>
• <code>selfie</code>
• <code>uniform</code>
• <code>ayaka</code></blockquote>

<b>🔞 Kategori Nsfw hanya bisa dipakai di Private Message.</b>
<spoiler><blockquote>• ass
• hentai
• milf
• oral
• paizuri
• ecchi
• ero</blockquote></spoiler>

<b>Note:</b> Kirim hanya printah <code>/{BotCommands.AnimekCommand[0]}</code> untuk hasil random.
        """
        await editMessage(mess, msg)
        return None
    
    private = bool(message.chat.type == ChatType.PRIVATE)
    if keyword == "":
        query = "waifu"
    
    elif any(
        tag in keyword.lower() for tag in [
        "ass",
        "hentai",
        "milf",
        "oral",
        "paizuri",
        "ecchi",
        "ero"
            ]
        ):
            if private:
                query = keyword
            else:
                await editMessage(mess, "🔞 <b>Keyword ini hanya tersedia di private message.</b>")
                return None
                

    else:
        keyword_cocok = False
        query = None
        for tag in tags:
            for key in tag:
                if key in keyword:
                    keyword_cocok = True
                    query = tag[key]
                    break
            
            if keyword_cocok:
                break

        if not keyword_cocok:
            await editMessage(mess, f"<b>Keyword yang anda masukkan belum tersedia.</b>\n\nGunakan perintah: <blockquote><code>/{BotCommands.AnimekCommand[0]} list</code></blockquote>Untuk melihat list keyword yang tersedia, atau kirimkan perintah tanpa keyword untuk hasil random.")
            return None
        if not query:
            query = "waifu"

    try_count = 5
    attempt = 1
    while attempt <= try_count:
        try:
            r = requests.get(f"https://api.waifu.im/search?included_tags={query}")
            data = r.json()
            if r.status_code == 200:
                for picts in data:
                    url = (data[picts][0]["url"])
                    desc = (data[picts][0]["tags"][0]["description"])
                    capt = (f"<b>[{query}]</b>\n<code>{desc}</code>\n\n<a href='{url}'><b>⬇️Download HD</b></a>")
                await customSendPhoto(message, url, capt, None)
                break
            else:
                break
        except:
            attempt += 1
            if attempt <= try_count:
                await editMessage(mess, f"Gagal mengirim photo, Mencoba lagi untuk ke-{attempt} kali...")
            else:
                await editMessage(message, "Gagal mengupload foto setelah 5x percobaan.")
                break
        finally:
            await deleteMessage(mess)

async def auto_tk(client, message):
    user_id = message.from_user.id
    isi = {user_id: message}
    tiktok.append(isi)
    
    text = message.text
    urls = re.findall(r"https?://[^\s]+", text)
    if not urls:
        return
        
    tkurl = urls[0]
    
    try:
        preview_img = None
        video_info = "Mengambil info..."
        
        pattern = r"^(?:https?://(?:www\.)?tiktok\.com)/(?P<user>[\a-zA-Z0-9-]+)(?P<content_type>video|photo)+/(?P<id>\d+)"
        match = re.match(pattern, tkurl)
        
        if match:
            username = match.group("user")
            content_type = match.group("content_type")
            video_id = match.group('id')
            
            preview_img = f"https://p16-sign-va.tiktokcdn.com/obj/tos-useast2a-p-0037-aiso/{video_id}?x-expires=1623456789&x-signature=XXXXX"
            video_info = f"<b>TikTok dari:</b> @{username}\n<b>Tipe:</b> {content_type.capitalize()}"
    except Exception as e:
        LOGGER.error(f"Error getting TikTok preview: {e}")
        preview_img = None
        video_info = "TikTok video/audio"
    
    msg = "<b>🎵 Link TikTok terdeteksi</b>\n\n"
    
    if video_info:
        msg += f"{video_info}\n\n"
        
    msg += f"<b>URL:</b> <code>{tkurl}</code>\n\n"
    msg += "<i>Silahkan pilih format yang diinginkan:</i>"
    
    butt = ButtonMaker()
    butt.ibutton("🎬 Unduh Video", f"tk media {user_id}")
    butt.ibutton("🔊 Unduh Audio", f"tk audio {user_id}")
    butt.ibutton("📽️ Video Tanpa Watermark", f"tk nowm {user_id}")
    butt.ibutton("⛔️ Batal", f"tk cancel {user_id}")
    butts = butt.build_menu(2)
    
    if preview_img:
        try:
            await message.reply_photo(
                photo=preview_img,
                caption=msg,
                reply_markup=butts
            )
            return
        except Exception as e:
            LOGGER.error(f"Error sending TikTok preview: {e}")
    
    await sendMessage(message, msg, butts)

async def tk_query(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    uid = int(data[2])
    
    for isi in tiktok:
        if uid in isi:
            msgs = isi
            msg = (msgs[uid])
            text = msg.text
            urls = re.findall(r"https?://[^\s]+", text)
            if urls:
                tkurl = urls[0]
    
    if user_id != uid:
        return await query.answer(text="Bukan Tugas Anda!", show_alert=True)
    
    elif data[1] == "media":
        await query.answer(text="Mengunduh video dengan watermark...", show_alert=False)
        await deleteMessage(message)
        del msgs[uid]   
        await tiktokdl(bot, msg, url=tkurl, type="video") 
        
    elif data[1] == "audio":
        await query.answer(text="Mengunduh audio saja...", show_alert=False)
        await deleteMessage(message)
        del msgs[uid]
        await tiktokdl(bot, msg, url=tkurl, audio=True)
        
    elif data[1] == "nowm":
        await query.answer(text="Mengunduh video tanpa watermark...", show_alert=False)
        await deleteMessage(message)
        del msgs[uid]
        await tiktokdl(bot, msg, url=tkurl, type="nowm")
        
    else:
        await query.answer(text="Dibatalkan", show_alert=False)
        del msgs[uid]
        await editMessage(message, "Tugas Dibatalkan.")

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
            "api_key": "J23oFXWYe-GMQZkddqKx6JiUkPgkymlE",
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
            butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"sub x {uid}", position="footer")
            butts = butt.build_menu(6)
            return msg, butts
        else:
            butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"sub x {uid}", position="footer")
            butts = butt.build_menu(1)
            return f"Gagal mendapatkan subtitle dari film \n<code>{keyword}</code>\n\n{r}", butts
    else:
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"sub x {uid}", position="footer")
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
    butt.ibutton("🔙 𝙱𝚊𝚌𝚔", f"sub b {uid}")
    butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"sub x {uid}")
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

####################################################################
#YT_SEARCH
####################################################################
youtube = {}
async def yt_request(uid, keyword):
    """
    Approve Fungsi Yt Search
    """
    try:
        msg = f"<b>🔎 Hasil Pencarian YouTube untuk:</b> <code>{keyword}</code>\n\n"
        api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU"
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&type=video&maxResults=10&key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url)
            data = response.json()
        
        if "items" not in data or not data["items"]:
            return f"<b>❌ Tidak ditemukan hasil untuk:</b> <code>{keyword}</code>\n\nCoba dengan kata kunci lain."
        
        video_ids = [item["id"]["videoId"] for item in data["items"]]
        ids_str = ",".join(video_ids)
        
        details_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,statistics&id={ids_str}&key={api_key}"
        async with httpx.AsyncClient() as client:
            details_response = await client.get(details_url)
            details_data = details_response.json()
        
        video_details = {}
        if "items" in details_data:
            for item in details_data["items"]:
                video_details[item["id"]] = {
                    "duration": item["contentDetails"]["duration"],
                    "views": item["statistics"].get("viewCount", "0"),
                    "likes": item["statistics"].get("likeCount", "0")
                }
        
        def parse_duration(duration_str):
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if not match:
                return "00:00"
            
            hours, minutes, seconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            
            if hours > 0:
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                return f"{minutes:02}:{seconds:02}"
        
        def format_count(count_str):
            count = int(count_str)
            if count >= 1000000000:
                return f"{count/1000000000:.1f}B"
            elif count >= 1000000:
                return f"{count/1000000:.1f}M"
            elif count >= 1000:
                return f"{count/1000:.1f}K"
            else:
                return str(count)
        
        results = []
        for i, item in enumerate(data["items"], 1):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            
            detail_text = ""
            if video_id in video_details:
                detail = video_details[video_id]
                duration = parse_duration(detail["duration"])
                views = format_count(detail["views"])
                likes = format_count(detail["likes"])
                detail_text = f"⏱️ {duration} | 👁️ {views} | 👍 {likes}"
            
            msg += f"<b>{i}.</b> <a href='https://youtube.com/watch?v={video_id}'>{title}</a>\n"
            msg += f"<i>📢 {channel}</i> {detail_text}\n\n"
            
            results.append({'title': title, 'id': video_id, 'channel': channel, 'thumbnail': thumbnail})
        
        butt = ButtonMaker()
        for index, video in enumerate(results, 1):
            butt.ibutton(f"{index}", f"youtube select {uid} {video['id']}")
            
        butt.ibutton("⛔️ Batal", f"youtube cancel {uid}", position="footer")
        butts = butt.build_menu(5)
        
        upd = {"msg": msg, "butts": butts, "results": results}
        youtube[uid].update(upd)
        
        return msg, butts
    except Exception as e:
        LOGGER.error(f"Error in YouTube search: {e}")
        return f"<b>❌ Terjadi kesalahan saat mencari video:</b>\n\n<code>{str(e)}</code>"

async def edit_durasi(duration):
    duration = duration[2:]
    duration = duration.replace("M", " menit ")
    duration = duration.replace("S", " detik")
    duration = duration.replace("H", " jam ")
    duration = duration.replace("D", " hari ")
    return duration

async def yt_extra(video_id):
    api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU" 
    video_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=contentDetails,snippet&key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(video_url)
        data = response.json()
    details = {}
    if "items" in data:
        for item in data["items"]:
            video_id = item["id"]
            duration = item["contentDetails"]["duration"]
            channel_title = item["snippet"]["channelTitle"]
            thumbnail_url = item["snippet"]["thumbnails"]["standard"]["url"]
            title = item["snippet"]["title"]
            details = {
                'duration': duration,
                'channel_title': channel_title,
                'thumbnail_url': thumbnail_url,
                'title': title,
                'video_id': video_id
            }
    return details
    
async def yt_search(client, message, keyword=None):
    uid = message.from_user.id
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        keyword = None
    if keyword:
        mess = await sendMessage(message, f"<b>Tunggu sebentar tuan...</b>")
        if uid in youtube:
            butt = ButtonMaker()
            butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"youtube cancel {uid}")
            butts = butt.build_menu(1)
            await editMessage(mess, "<b>Silahkan selesaikan atau batalkan proses sebelumnya !</b>", butts)
            return None
        youtube[uid] = {"message": message, "keyword": keyword}
        try:
            msg, butts = await yt_request(uid, keyword)
            await deleteMessage(mess)
            await message.reply_photo("https://telegra.ph/file/9fbae069402df1710585f.jpg", caption=msg, reply_markup=butts)
        except Exception as e:
            await editMessage(mess, f"{e}")
            del youtube[uid]
    else:
        await sendMessage(message, "<b>Silahkan masukkan perintah disertai keyword pencarian !</b>")

async def yt_query(_, query):
    message = query.message
    user_id = query.from_user.id
    edit_media = query.edit_message_media
    data = query.data.split()
    uid = int(data[2])
    
    if user_id != uid:
        return await query.answer(text="Bukan Tugas Anda!", show_alert=True)
    
    elif data[1] == "select":
        try:
            details = await yt_extra(data[3])
            
            msg = f"<b>🎬 Detail Video YouTube</b>\n\n"
            msg += f"<b>📌 Judul:</b> <code>{details['title']}</code>\n\n"
            msg += f"<b>📢 Channel:</b> <code>{details['channel_title']}</code>\n"
            msg += f"<b>⏱️ Durasi:</b> <code>{await edit_durasi(details['duration'])}</code>\n"
            
            if 'view_count' in details:
                view_count = int(details['view_count'])
                if view_count > 1000000:
                    view_format = f"{view_count/1000000:.1f}M"
                elif view_count > 1000:
                    view_format = f"{view_count/1000:.1f}K"
                else:
                    view_format = str(view_count)
                msg += f"<b>👁️ Views:</b> <code>{view_format}</code>\n"
            
            if 'description' in details and details['description']:
                desc = details['description']
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                msg += f"\n<b>📝 Deskripsi:</b>\n<code>{desc}</code>\n"
            
            msg += f"\n<b>🔗 Link:</b> https://youtu.be/{details['video_id']}\n"
            
            butt = ButtonMaker()
            butt.ibutton("🔄 Mirror", f"youtube mirror {uid} {data[3]}")
            butt.ibutton("📥 Leech", f"youtube leech {uid} {data[3]}")
            butt.ibutton("🎵 Audio", f"youtube audio {uid} {data[3]}")
            butt.ibutton("🔙 Kembali", f"youtube back {uid}")
            butts = butt.build_menu(2)
            
            thumbnail = f"https://i.ytimg.com/vi/{data[3]}/maxresdefault.jpg"
            
            try:
                new_media = InputMediaPhoto(media=thumbnail, caption=msg)
                await edit_media(media=new_media, reply_markup=butts)
            except Exception:
                fallback_thumbnail = f"https://i.ytimg.com/vi/{data[3]}/hqdefault.jpg"
                try:
                    new_media = InputMediaPhoto(media=fallback_thumbnail, caption=msg)
                    await edit_media(media=new_media, reply_markup=butts)
                except Exception:
                    no_thumbnail = InputMediaPhoto("https://telegra.ph/file/5e7fde2b232ae1b682625.jpg", caption=msg)
                    await edit_media(new_media=no_thumbnail, reply_markup=butts)
        except Exception as e:
            await query.answer(text=f"Terjadi kesalahan saat mengambil video: {str(e)}", show_alert=True)
            LOGGER.error(f"Error in YouTube video selection: {e}") 
    elif data[1] == "mirror":
        try:
            details = await yt_extra(data[3])
        except Exception as e:
            return await query.answer(text=f"Terjadi kesalahan saat mengambil video, atau video ini belum tersedia. {e}", show_alert=True)
        video_id = details['video_id']
        if uid in youtube:
            msg = youtube[uid]["message"]
            YtDlp(bot, msg, yturl="https://www.youtube.com/watch?v=" + video_id, isLeech=True).newEvent()
            await deleteMessage(message)
            del youtube[uid]
        else:
            await query.answer(text=f"Terjadi kesalahan, silahkan coba lagi.", show_alert=True)
            await deleteMessage(message)
    elif data[1] == "leech":
        try:
            details = await yt_extra(data[3])
        except Exception as e:
            return await query.answer(text=f"Terjadi kesalahan saat mengambil video, atau video ini belum tersedia. {e}", show_alert=True)
        video_id = details['video_id']
        if uid in youtube:
            msg = youtube[uid]["message"]
            YtDlp(bot, msg, yturl="https://www.youtube.com/watch?v=" + video_id, isLeech=True).newEvent()
            await deleteMessage(message)
            del youtube[uid]
        else:
            await query.answer(text=f"Terjadi kesalahan, silahkan coba lagi.", show_alert=True)
            await deleteMessage(message)
    elif data[1] == "back":
        try:
            #keyword = youtube[uid]["keyword"]
            msg = youtube[uid]["msg"]
            butts = youtube[uid]["butts"]
            #msg, butts = await yt_request(uid, keyword, back=True)
            new_media = InputMediaPhoto("https://telegra.ph/file/9fbae069402df1710585f.jpg", caption=msg)
            await edit_media(new_media, reply_markup=butts)  
        except Exception as e:
            await editMessage(message, f"{e}")
            del youtube[uid]
    else:
        await query.answer(text=f"Tugas sudah dibatalkan", show_alert=True)
        await deleteMessage(message)
        del youtube[uid]

#####################################
#GALLERY-DL
#####################################
@new_task
async def gallery_dl(client, message, auto=False):
    # Periksa apakah ada URL dalam pesan
    url = None
    if auto:
        # Auto mode - gunakan pesan teks sebagai URL
        if message.text:
            urls = re.findall(r'https?://[^\s]+', message.text)
            if urls:
                url = urls[0]
    else:
        # Command mode - periksa argumen perintah
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            possible_url = args[1].strip()
            if is_url(possible_url):
                url = possible_url
    
    # Cek apakah URL valid
    if not url:
        await sendMessage(message, "<b>❌ Error:</b> Silahkan berikan URL yang valid!\n\n"
                                  f"<b>Contoh:</b> <code>/{BotCommands.GallerydlCommand[0]} https://www.instagram.com/p/xxx</code>")
        return
    
    # Deteksi platform
    platform_info = detect_platform(url)
    if not platform_info:
        await sendMessage(message, "<b>❌ Error:</b> URL tidak didukung!\n\n"
                                  "<b>Platform yang didukung:</b>\n"
                                  "- Instagram (Post/Reels/Stories)\n"
                                  "- Twitter/X\n"
                                  "- TikTok\n"
                                  "- Reddit\n"
                                  "- Imgur\n"
                                  "- Flickr\n"
                                  "- Pinterest")
        return
    
    platform_name = platform_info['name']
    platform_type = platform_info['type']
    options = platform_info['options']
    
    mess = await sendMessage(message, f"<b>⏳ Memulai download dari {platform_name} {platform_type}...</b>\n\n"
                                    f"<b>URL:</b> <code>{url}</code>\n\n"
                                    "<i>Gallery-DL sedang mengekstrak informasi media. Harap tunggu...</i>")
    
    temp_folder = f"{config_dict['TEMP_PATH']}/{message.id}"
    await makedirs(temp_folder, exist_ok=True)
    
    try:
        cmd = [
            "gallery-dl",
            "--verbose",
            "--directory", temp_folder
        ]
        
        cmd.extend(options)
        cmd.append(url)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        file_count = 0
        total_files = 0
        update_interval = 3 
        last_update_time = time()
        
        async for line in process.stdout:
            decoded_line = line.decode().strip()
            
            if "file downloaded" in decoded_line or "# files" in decoded_line:
                file_count += 1
                
                current_time = time()
                if current_time - last_update_time >= update_interval:
                    progress_text = f"<b>⏳ Mengunduh {platform_name} {platform_type}...</b>\n\n"
                    progress_text += f"<b>URL:</b> <code>{url}</code>\n"
                    progress_text += f"<b>Diunduh:</b> {file_count} file" + (f" dari {total_files}" if total_files else "") + "\n"
                    
                    await editMessage(mess, progress_text)
                    last_update_time = current_time
                
            total_match = re.search(r"Found (\d+) files", decoded_line)
            if total_match:
                total_files = int(total_match.group(1))
        
        await process.wait()
        exit_code = process.returncode
        
        if exit_code != 0:
            stderr = await process.stderr.read()
            error_message = stderr.decode().strip()
            await editMessage(mess, f"<b>❌ Gagal mengunduh media!</b>\n\n<code>{error_message}</code>")
            return
            
        all_files = await listdir(temp_folder)
        file_paths = [f"{temp_folder}/{file}" for file in all_files if not file.startswith(".")]
        file_paths.sort()  # Urutkan file
        
        if not file_paths:
            await editMessage(mess, f"<b>❌ Tidak ada file yang diunduh dari {platform_name}!</b>\n\n"
                                  f"URL mungkin tidak valid atau konten telah dihapus.")
            return
            
        await editMessage(mess, f"<b>✅ Berhasil mengunduh {len(file_paths)} file dari {platform_name}!</b>\n\n"
                              f"<b>URL:</b> <code>{url}</code>\n\n"
                              f"<i>Sedang memproses file untuk dikirim...</i>")
        
        await send_files_with_caption(message, file_paths, platform_name, platform_type, url)
        
    except Exception as e:
        await editMessage(mess, f"<b>❌ Terjadi kesalahan saat mengunduh media:</b>\n\n<code>{str(e)}</code>")
    finally:
        try:
            await rmtree(temp_folder)
        except:
            pass

###########################
#Pickle Generator
###########################
OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
client_id = "905059780985-usekgpt4cp42u2idqtk089us0cm4qkr.apps.googleusercontent.com"
client_secret = "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"

@new_task
async def get_token(client, message):
    private = bool(message.chat.type == ChatType.PRIVATE)
    if not private:
        butt = ButtonMaker()
        butt.ubutton("🔐 GUNAKAN DI CHAT PRIBADI", f"https://t.me/{bot.me.username}?start=gettoken")
        await sendMessage(message, 
            "<b>⚠️ Perintah ini hanya dapat digunakan di chat pribadi!</b>\n\n"
            "Klik tombol di bawah untuk membuka chat pribadi dengan bot dan otomatis mendapatkan Token Google Drive Anda.", 
            butt.build_menu(1))
        return
    uid = message.from_user.id
    path = f"tokens/{uid}/"
    pickle_path = f"{path}/token.pickle"
    await makedirs(path, exist_ok=True)
    try:
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost:1"],
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            OAUTH_SCOPE,
            redirect_uri='http://localhost:1'
        )
        
        auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        
        # Enhanced detailed instructions message
        msg = (
            "<b>🔐 PANDUAN MENDAPATKAN TOKEN GOOGLE DRIVE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Ikuti langkah-langkah berikut dengan seksama:</b>\n\n"
            "1️⃣ <b>Klik tombol \"Authorization URL\" di bawah</b>\n"
            "   • Halaman Google akan terbuka di browser Anda\n"
            "   • Pilih akun Google Drive yang ingin Anda gunakan\n\n"
            "2️⃣ <b>Berikan akses ke aplikasi</b>\n"
            "   • Jika muncul peringatan \"Google belum memverifikasi aplikasi ini\", klik \"Lanjutkan\"\n"
            "   • Pilih \"Lanjutkan\" untuk mengizinkan akses\n\n"
            "3️⃣ <b>Pada halaman error yang muncul:</b>\n"
            "   • Salin seluruh URL dari address bar browser Anda\n"
            "   • Kembali ke Telegram dan kirimkan URL tersebut ke bot ini\n\n"
            "<i>⚠️ Anda memiliki waktu 120 detik untuk menyelesaikan proses ini</i>\n"
            "<i>🔒 Token yang dihasilkan akan digunakan untuk akses Google Drive Anda</i>\n"
        )
        
        butt = ButtonMaker()
        butt.ubutton("🔗 Authorization URL", auth_url)
        butts = butt.build_menu(1)
        
        try:
            ask = await sendMessage(message, msg, butts)
            respon = await bot.listen(
                filters=filters.text & filters.user(uid), timeout=120
            )
        except:
            await deleteMessage(ask)
            raise Exception("⏱️ Waktu habis! Silakan coba lagi dengan mengirim perintah /gettoken.")
        try:
            code = respon.text.split('code=')[1].split('&')[0]
        except IndexError:
            await deleteMessage(ask)
            raise Exception("❌ Format URL tidak valid. Pastikan Anda menyalin seluruh URL dari address bar browser. Silakan coba lagi.")
        await respon.delete()
        await editMessage(ask, f"<b>⏳ Memproses kode autentikasi...</b>\n\nSedang memverifikasi dan menghasilkan token. Mohon tunggu sebentar.")
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            with open(pickle_path, "wb") as token:
                pickle.dump(credentials, token)
            
            # Enhanced token information message
            caption = (
                "📋 <b>TOKEN GOOGLE DRIVE BERHASIL DIBUAT</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>Informasi Token:</b>\n"
                f"🔑 <b>Client ID:</b> <code>{client_id}</code>\n"
                f"🔒 <b>Client Secret:</b> <code>{client_secret}</code>\n"
                f"🔄 <b>Refresh Token:</b> <code>{credentials.refresh_token}</code>\n\n"
                "<i>⚠️ PENTING: Simpan informasi ini dengan aman!</i>\n"
                "<i>Refresh Token dapat digunakan untuk akses jangka panjang ke akun Google Drive Anda.</i>\n\n"
                "<b>Cara Menggunakan:</b>\n"
                "• Gunakan perintah <code>/gentoken</code> untuk setup otomatis dengan token ini\n"
                "• Atau setup manual dengan memasukkan token ke service accounts"
            )
            
            await message.reply_document(
                document=pickle_path,
                caption=caption,
            )
        except Exception as e:
            raise Exception(f"❌ Gagal memverifikasi kode: {str(e)}\n\nSilakan coba lagi dengan perintah /gettoken.")
        await deleteMessage(ask)
    except Exception as e:
        await sendMessage(message, f"<b>❌ Error:</b> {e}")
    finally:
        if os.path.exists(pickle_path):
            os.remove(pickle_path)

async def gen_token(client, message):
    private = bool(message.chat.type == ChatType.PRIVATE)
    if not private:
        butt = ButtonMaker()
        butt.ubutton("🔐 GUNAKAN DI CHAT PRIBADI", f"https://t.me/{bot.me.username}?start=gentoken")
        await sendMessage(message, 
            "<b>⚠️ Perintah ini hanya dapat digunakan di chat pribadi!</b>\n\n"
            "Klik tombol di bawah untuk membuka chat pribadi dengan bot dan otomatis menghasilkan token Google Drive Anda.", 
            butt.build_menu(1))
        return
    
    uid = message.from_user.id
    path = f"tokens/"
    pickle_path = f"{path}{uid}.pickle"
    await makedirs(path, exist_ok=True)
    async def generate_token(message):
        if os.path.exists(pickle_path):
            with open(pickle_path, "rb") as f:
                credentials = pickle.load(f)
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                raise Exception("⚠️ Token Google Drive Anda sudah ada dan telah diperbarui.\n\nUntuk menghapus token yang ada, silakan gunakan menu:\nUsetting → Gdrive Tools → token.pickle")
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost:1"],
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                OAUTH_SCOPE,
                redirect_uri='http://localhost:1'
            )
            auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
            
            msg = (
                "<b>🔐 GENERATE TOKEN GOOGLE DRIVE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>Ikuti langkah-langkah berikut dengan seksama:</b>\n\n"
                "1️⃣ <b>Klik tombol \"Autorisasi Google Drive\" di bawah</b>\n"
                "   • Browser akan terbuka dengan halaman login Google\n"
                "   • Pilih akun Google Drive yang ingin Anda gunakan untuk mirroring\n\n"
                "2️⃣ <b>Berikan izin akses</b>\n"
                "   • Jika muncul peringatan keamanan, klik \"Lanjutkan\"\n"
                "   • Izinkan akses ke Google Drive Anda\n\n"
                "3️⃣ <b>Salin URL dari halaman error</b>\n"
                "   • Setelah memberi izin, Anda akan diarahkan ke halaman error\n"
                "   • Salin SELURUH URL dari address bar browser\n"
                "   • Kirimkan URL tersebut ke bot sebagai balasan\n\n"
                "<i>⏱️ Proses ini akan timeout dalam 120 detik jika tidak ada respon</i>\n"
                "<i>💡 Token yang dibuat akan langsung dikonfigurasi untuk akun Anda</i>"
            )
            
            butt = ButtonMaker()
            butt.ubutton("🔗 Autorisasi Google Drive", auth_url)
            butts = butt.build_menu(1)
            try:
                ask = await sendMessage(message, msg, butts)
                respon = await bot.listen(
                        filters=filters.text & filters.user(uid), timeout=120
                        )
            except:
                await deleteMessage(ask)
                raise Exception("⏱️ Waktu habis! Tidak ada respon dari Anda. Silakan coba lagi dengan perintah /gentoken.")
            try:
                code = respon.text.split('code=')[1].split('&')[0]
            except IndexError:
                await deleteMessage(ask)
                raise Exception("❌ Format URL tidak valid. Pastikan Anda menyalin SELURUH URL dari address bar browser.")
            await respon.delete()
            await editMessage(ask, f"<b>⏳ Memverifikasi kode autentikasi...</b>\n\nSedang memproses permintaan Anda. Mohon tunggu sebentar.")
            try:
                credentials = flow.fetch_token(code=code)
                with open(pickle_path, "wb") as token:
                    pickle.dump(flow.credentials, token)
                    return flow.credentials
            except Exception as e:
                raise Exception(f"❌ Gagal saat memverifikasi kode: {str(e)}")
            finally:
                await deleteMessage(ask)
    try:
        credentials = await generate_token(message)
        if credentials and os.path.exists(pickle_path):
            wait = await sendMessage(message, "<b>⌛ Memproses setup Google Drive...</b>\n\nSedang membuat folder dan mengkonfigurasi pengaturan. Mohon tunggu sebentar.")
            def create_folder():
                try:
                    auth = build("drive", "v3", credentials=credentials, cache_discovery=False)
                    file_metadata = {
                        "name": f"MirrorFolder oleh {bot.me.username}",
                        "description": f"Uploaded by {bot.me.username}",
                        "mimeType": "application/vnd.google-apps.folder",
                    }
                    file = (
                        auth.files()
                        .create(body=file_metadata, supportsAllDrives=True)
                        .execute()
                    )
                    folder_id = file.get("id")
                    LOGGER.info(f"Sukses membuat Folder id: {folder_id}")
                    permissions = {
                        "role": "reader",
                        "type": "anyone",
                        "value": None,
                        "withLink": True,
                    }
                    (auth.permissions()
                    .create(fileId=folder_id, body=permissions, supportsAllDrives=True)
                    .execute())
                    LOGGER.info(f"Sukses membuat Permission id: {folder_id}")
                    return folder_id
                except Exception as e:
                    LOGGER.error(f"Error membuat folder: {str(e)}")
                    return
            update_user_ldata(uid, "token_pickle", f"tokens/{uid}.pickle")
            if DATABASE_URL:
                await DbManger().update_user_doc(uid, "token_pickle", pickle_path)
            if folder_id := create_folder():
                update_user_ldata(uid, "gdrive_id", f"mtp:{folder_id}")
                update_user_ldata(uid, "default_upload", "gd")
                if DATABASE_URL:
                    await DbManger().update_user_data(uid)
                    
            # Enhanced success message
            msg = (
                "✅ <b>SETUP GOOGLE DRIVE BERHASIL</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            
            if folder_id:
                msg += (
                    "<b>Detail Konfigurasi:</b>\n"
                    f"📁 <b>Nama Folder:</b> <code>MirrorFolder oleh {bot.me.username}</code>\n"
                    f"🆔 <b>Folder ID:</b> <code>{folder_id}</code>\n"
                    f"📤 <b>Default Upload:</b> <code>Google Drive</code>\n\n"
                    "<b>Cara Penggunaan:</b>\n"
                    f"• Gunakan perintah <code>/{BotCommands.MirrorCommand[0]}</code> untuk mengupload file ke Google Drive\n"
                    f"• File akan disimpan di folder yang telah dibuat\n"
                    f"• Semua file dapat diakses melalui link\n\n"
                    "<i>🎉 Selamat! Semua pengaturan telah selesai dan siap digunakan!</i>"
                )
            else:
                msg += (
                    "⚠️ <b>Setup Folder Gagal</b>\n\n"
                    "Token berhasil dibuat, namun terjadi kesalahan saat membuat folder di Google Drive Anda.\n\n"
                    "<b>Untuk setup manual:</b>\n"
                    "1. Buat folder di Google Drive Anda\n"
                    "2. Setting folder agar dapat dibagikan melalui link\n"
                    "3. Salin ID folder (bagian terakhir dari URL folder)\n"
                    f"4. Isi gdrive_id di usetting dengan format: <code>mtp:ID_FOLDER_ANDA</code>\n\n"
                    "<i>Jika membutuhkan bantuan, hubungi admin.</i>"
                )
                
            await editMessage(wait, msg)
        else:
            await editMessage(wait, "❌ <b>SETUP GOOGLE DRIVE GAGAL</b>\n\nToken Google Drive tidak berhasil dibuat. Silakan coba lagi atau hubungi admin untuk bantuan.")
    except Exception as e:
        await sendMessage(message, f"<b>❌ Error:</b> {e}")

def detect_platform(url):
    """
    Mendeteksi platform dan tipe konten dari URL
    
    Returns:
        dict: Informasi platform dan opsi khusus
    """
    platforms = [
        {
            'domain': ['instagram.com', 'instagr.am'],
            'name': 'Instagram',
            'types': {
                '/reel/': 'Reel',
                '/reels/': 'Reel',
                '/stories/': 'Story',
                '/p/': 'Post'
            },
            'default_type': 'Post',
            'options': ['--output', '%(uploader)s/%(post_id)s_%(num)s.%(ext)s']
        },
        {
            'domain': ['twitter.com', 'x.com'],
            'name': 'Twitter/X',
            'types': {
                '/status/': 'Tweet'
            },
            'default_type': 'Tweet',
            'options': ['--output', '%(tweet_id)s_%(num)s.%(ext)s']
        },
        {
            'domain': ['tiktok.com'],
            'name': 'TikTok',
            'types': {
                '/@': 'Video'
            },
            'default_type': 'Video',
            'options': ['--output', '%(id)s.%(ext)s']
        },
        {
            'domain': ['reddit.com'],
            'name': 'Reddit',
            'types': {
                '/r/': 'Subreddit',
                '/comments/': 'Post'
            },
            'default_type': 'Post',
            'options': ['--output', '%(id)s_%(num)s.%(ext)s']
        },
        {
            'domain': ['imgur.com'],
            'name': 'Imgur',
            'default_type': 'Album',
            'options': ['--output', '%(title)s_%(num)s.%(ext)s']
        }
    ]
    
    for platform in platforms:
        if any(domain in url for domain in platform['domain']):
            content_type = platform['default_type']
            
            if 'types' in platform:
                for type_url, type_name in platform['types'].items():
                    if type_url in url:
                        content_type = type_name
                        break
            
            return {
                'name': platform['name'],
                'type': content_type,
                'options': platform['options']
            }
    
    return None

async def send_files_with_caption(message, file_paths, platform_name, platform_type, url):
    """
    Mengirim file dengan caption yang sesuai
    """
    from pyrogram.types import InputMediaPhoto, InputMediaVideo
    
    if len(file_paths) == 1:
        file_path = file_paths[0]
        file_ext = file_path.split(".")[-1].lower()
        
        caption = f"<b>🔗 {platform_name} {platform_type}</b>\n\n<code>{url}</code>"
        
        if file_ext in ['jpg', 'jpeg', 'png']:
            await message.reply_photo(
                photo=file_path,
                caption=caption
            )
        elif file_ext in ['mp4', 'webm', 'mkv']:
            await message.reply_video(
                video=file_path,
                caption=caption
            )
        else:
            await message.reply_document(
                document=file_path,
                caption=caption
            )
    else:
        photos = []
        videos = []
        documents = []
        
        for file_path in file_paths:
            file_ext = file_path.split(".")[-1].lower()
            
            if file_ext in ['jpg', 'jpeg', 'png']:
                photos.append(file_path)
            elif file_ext in ['mp4', 'webm', 'mkv']:
                videos.append(file_path)
            else:
                documents.append(file_path)
        
        if photos:
            caption = f"<b>🔗 {platform_name} {platform_type} Photos</b>\n\n<code>{url}</code>"
            
            for i in range(0, len(photos), 10):
                chunk = photos[i:i+10]
                media = []
                
                for idx, photo in enumerate(chunk):
                    media.append(
                        InputMediaPhoto(
                            media=photo,
                            caption=caption if idx == 0 else ""
                        )
                    )
                
                await message.reply_media_group(media=media)
        
        if videos:
            caption = f"<b>🔗 {platform_name} {platform_type} Videos</b>\n\n<code>{url}</code>"
            
            for video in videos:
                await message.reply_video(
                    video=video,
                    caption=caption
                )
                caption = ""
        
        for doc in documents:
            await message.reply_document(
                document=doc,
                caption=f"<b>🔗 {platform_name} {platform_type}</b>\n\n<code>{url}</code>"
            )

tiktokregex = r"(https?://(?:www\.)?[a-zA-Z0-9.-]*tiktok\.com/)"
gallery_dl_regex = r'https?:\/\/(www\.)?(instagram\.com\/[a-zA-Z0-9._-]+|twitter\.com\/[a-zA-Z0-9_]+|x\.com\/[a-zA-Z0-9_]+)'

bot.add_handler(
    MessageHandler(
        asupan, 
        filters=command(
            BotCommands.AsupanCommand
        )
    )
)
bot.add_handler(
    MessageHandler(
        animek, 
        filters=command(
            BotCommands.AnimekCommand
        )
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
        tiktok_search, 
        filters=command(
            BotCommands.TiktokCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        auto_tk,
        filters=filters.regex(
            f"{tiktokregex}"
        )
    )
)

bot.add_handler(
    CallbackQueryHandler(
        tk_query,
        filters=regex(
            r'^tk'
        )
    )
)
bot.add_handler(
    CallbackQueryHandler(
        asupan_query,
        filters=regex(
            r'^asupan'
        )
    )
)
bot.add_handler(
    MessageHandler(
        yt_search, 
        filters=command(
            BotCommands.Yt_searchCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    CallbackQueryHandler(
        yt_query,
        filters=regex(
            r'^youtube'
        )
    )
)
bot.add_handler(
    MessageHandler(
        get_token, 
        filters=command(
            BotCommands.GetTokenCommand
        )
    )
)
bot.add_handler(
    MessageHandler(
        gen_token, 
        filters=command(
            BotCommands.GenTokenCommand
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