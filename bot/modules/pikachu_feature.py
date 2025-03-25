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
    url = url
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<code>{message.from_user.first_name}</code>'
    
    if audio:
        mess = await sendMessage(message, f"<b>⌛️Mendownload audio dari tiktok, silahkan tunggu sebentar...</b>")
    else:
        mess = await sendMessage(message, f"<b>⌛️Mendownload video dari tiktok, silahkan tunggu sebentar...</b>")
    
    async with niquests.AsyncSession() as client:
        try:
            r = await client.get(url, allow_redirects=False)
            if r.status_code == 301:
                new_url = r.headers['Location']
                r = await client.get(new_url)
                hasil = r.url
            else:
                hasil = r.url
        except Exception as e:
            await sendMessage(mess, f"Terjadi kesalahan saat mencoba mengakses url, silahkan coba kembali.\n\n<blockquote>{e}</blockquote>")
            await deleteMessage(mess)
            return None
        
        pattern = r"^(?:https?://(?:www\.)?tiktok\.com)/(?P<user>[\w\.-]+)/(?P<content_type>video|photo)+/(?P<id>\d+)"
        match = re.match(pattern, str(hasil))
        if match:  
            content_type = match.group("content_type")
            id = match.group('id')
        else:
            await editMessage(mess, f"Link yang anda berikan sepertinya salah atau belum support, silahkan coba dengan link yang lain!")
            await deleteMessage(mess)
            return None
    
    try:
        async with niquests.AsyncSession() as client:
            data = ""
            try:
                for _ in range(3):
                    try:
                        r = await client.get(
                            url=f"https://api16-normal-useast5.us.tiktokv.com/aweme/v1/feed/?aweme_id={id}",
                            headers={"User-Agent": user_agent},
                            timeout=10
                        )
                        r.raise_for_status()
                        data = r.text
                        if data:
                            break
                    except Exception as e:
                        LOGGER.error(f"TikTok API attempt failed: {e}")
                        await asleep(1)
                
                if not data:
                    raise Exception("Failed to get data from TikTok API after multiple attempts")
                
                data = loads(data)
                
                if "aweme_list" in data and len(data["aweme_list"]) > 0:
                    music = data["aweme_list"][0]["music"]["play_url"]["url_list"][-1]
                    m_capt = data["aweme_list"][0]["music"]["title"]
                    
                    if content_type == "video":
                        link = data["aweme_list"][0]["video"]["play_addr"]["url_list"][-1]
                        filename = data["aweme_list"][0]["desc"]
                        capt = f"<code>{filename}</code> \n\n<b>Tugas Oleh:</b> {uname}"
                        
                        if audio is True or type == "audio":
                            await customSendAudio(message, music, m_capt, None, None, None, None, None)
                        else:
                            if type == "nowm":
                                nowm_link = link
                                for play_addr in data["aweme_list"][0]["video"]["play_addr"]["url_list"]:
                                    if "watermark=0" in play_addr:
                                        nowm_link = play_addr
                                        break
                                link = nowm_link
                            
                            await customSendVideo(message, link, capt, None, None, None, None, None)
                    
                    elif content_type == "photo":
                        if audio is True or type == "audio":
                            await customSendAudio(message, music, m_capt, None, None, None, None, None)
                        else:
                            photo_urls = []
                            for aweme in data["aweme_list"][0]["image_post_info"]["images"]:
                                for link in aweme["display_image"]["url_list"][1:]:
                                    photo_urls.append(link)
                            photo_groups = [photo_urls[i:i+10] for i in range(0, len(photo_urls), 10)]
                            for photo_group in photo_groups:
                                await message.reply_media_group([InputMediaPhoto(photo_url) for photo_url in photo_group])
                
            except Exception as e:
                LOGGER.error(f"TikTok API Error: {str(e)}")
                
                try:
                    LOGGER.info(f"Trying TikSave API fallback...")
                    headers = {
                        "User-Agent": user_agent,
                        "Referer": "https://tiksave.ai/"
                    }
                    
                    data = {
                        "id": url
                    }
                    
                    response = await client.post(
                        "https://tiksave.ai/api/download", 
                        headers=headers,
                        data=data
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"TikSave API Error: Status {response.status_code}")
                    
                    result = response.json()
                    
                    if "type" in result and result["type"] in ["success", "ok"]:
                        if audio is True or type == "audio":
                            if "music" in result and result["music"]:
                                music_url = result["music"]
                                title = result.get("title", "TikTok Audio")
                                await customSendAudio(message, music_url, title, None, None, None, None, None)
                            else:
                                raise Exception("Audio not found")
                        else:
                            video_url = None
                            if type == "nowm" and "video_no_wm" in result and result["video_no_wm"]:
                                video_url = result["video_no_wm"]
                            elif "video" in result and result["video"]:
                                video_url = result["video"]
                            else:
                                raise Exception("Video not found")
                            
                            title = result.get("title", "TikTok Video")
                            capt = f"<code>{title}</code> \n\n<b>Tugas Oleh:</b> {uname}"
                            await customSendVideo(message, video_url, capt, None, None, None, None, None)
                    else:
                        raise Exception("Failed to download from TikSave API")
                    
                except Exception as fallback_error:
                    LOGGER.error(f"TikSave API Error: {str(fallback_error)}")
                    await sendMessage(mess, f"Hai {uname}, Terjadi kesalahan saat mencoba mengunduh. Silahkan coba lagi nanti.\n\n<blockquote>{str(e)}</blockquote>")
                    await deleteMessage(mess)
                    return None
    
    except Exception as e:
        await sendMessage(mess, f"ERROR: Gagal mengunduh media: {str(e)}")
    finally:
        await deleteMessage(mess)

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
    msg = f"<b>Link Tiktok terdeteksi, silahkan pilih untuk download Media atau Audio saja...</b>"
    user_id = message.from_user.id
    butt = ButtonMaker()
    butt.ibutton("🎞 Media", f"tk media {user_id}")
    butt.ibutton("🎞 No WM", f"tk nowm {user_id}")
    butt.ibutton("🔈 Audio", f"tk audio {user_id}")
    butt.ibutton("⛔️ Batal", f"tk cancel {user_id}", "footer")
    butts = butt.build_menu(2)
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
        await deleteMessage(message)
        del msgs[uid]   
        await tiktokdl(bot, msg, url=tkurl) 
    elif data[1] == "nowm":
        await deleteMessage(message)
        del msgs[uid]
        await tiktokdl(bot, msg, url=tkurl, type="nowm")
    elif data[1] == "audio":
        await deleteMessage(message)
        del msgs[uid]
        await tiktokdl(bot, msg, url=tkurl, audio=True)
    else:
        await query.answer()
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

def format_count(count_str):
    try:
        count = int(count_str)
        if count >= 1000000:
            return f"{count/1000000:.2f}M".replace(".00", "")
        elif count >= 1000:
            return f"{count/1000:.2f}K".replace(".00", "")
        else:
            return str(count)
    except (ValueError, TypeError):
        return "0"

def parse_duration(duration_str):
    hours_match = re.search(r'(\d+)H', duration_str)
    minutes_match = re.search(r'(\d+)M', duration_str)
    seconds_match = re.search(r'(\d+)S', duration_str)
    
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

youtube = {}
async def yt_request(uid, keyword, page=1):
    try:
        api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU"
        results_per_page = 10
        max_results = 30
        
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&type=video&maxResults={max_results}&key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url)
            data = response.json()
        
        if "items" not in data or not data["items"]:
            return f"<b>❌ Tidak ditemukan hasil untuk:</b> <code>{keyword}</code>\n\nCoba dengan kata kunci lain.", None
        
        video_ids = [item["id"]["videoId"] for item in data["items"]]
        ids_str = ",".join(video_ids)
        
        video_url = f"https://www.googleapis.com/youtube/v3/videos?id={ids_str}&part=contentDetails,statistics&key={api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            video_data = response.json()
        
        video_details = {}
        if "items" in video_data:
            for item in video_data["items"]:
                video_details[item["id"]] = {
                    "duration": item["contentDetails"]["duration"],
                    "views": item["statistics"].get("viewCount", "0"),
                    "likes": item["statistics"].get("likeCount", "0")
                }
        
        total_results = len(data["items"])
        total_pages = (total_results + results_per_page - 1) // results_per_page
        
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
            
        start_idx = (page - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        
        msg = f"<b>🔎 Hasil Pencarian YouTube untuk:</b> <code>{keyword}</code>\n\n"
        
        page_items = data["items"][start_idx:end_idx]
        
        for i, item in enumerate(page_items, start_idx + 1):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            
            entry = f"<b>{i}.</b> <a href='https://youtube.com/watch?v={video_id}'>{title}</a>\n"
            
            detail_text = ""
            if video_id in video_details:
                detail = video_details[video_id]
                duration = parse_duration(detail["duration"])
                views = format_count(detail["views"])
                likes = format_count(detail["likes"])
                detail_text = f"⏱️ {duration} | 👁️ {views} | 👍 {likes}"
            
            entry += f"📢 {channel} {detail_text}\n\n"

            if len(msg + entry) > 900:
                msg += f"\n<i>...dan {total_results - i + 1} hasil lainnya</i>"
                break
                
            msg += entry
        
        butt = ButtonMaker()
        
        if page > 1:
            butt.ibutton("◀️ Prev", f"youtube page {uid} {page-1} {keyword}", position="header")
        else:
            butt.ibutton("◀️", f"youtube none {uid}", position="header")
            
        butt.ibutton("🔗 Join", f"youtube join {uid}", position="header")
            
        if page < total_pages:
            butt.ibutton("Next ▶️", f"youtube page {uid} {page+1} {keyword}", position="header")
        else:
            butt.ibutton("▶️", f"youtube none {uid}", position="header")
        
        butt.ibutton(f"Page {page} of {total_pages}", f"youtube none {uid}")
        
        butt.ibutton("Select This Page", f"youtube selectpage {uid} {page}")
        
        butt.ibutton("⛔️ Batalkan", f"youtube cancel {uid}", position="footer")
        
        butts = butt.build_menu(3, 3, 1)
        
        page_results = [{
            'title': item["snippet"]["title"],
            'id': item["id"]["videoId"],
            'channel': item["snippet"]["channelTitle"]
        } for item in page_items]
        
        all_results = [{
            'title': item["snippet"]["title"],
            'id': item["id"]["videoId"],
            'channel': item["snippet"]["channelTitle"],
            'idx': i+1
        } for i, item in enumerate(data["items"])]
        
        upd = {
            "msg": msg, 
            "butts": butts, 
            "results": all_results,
            "page_results": page_results,
            "page": page,
            "total_pages": total_pages,
            "keyword": keyword
        }
        youtube[uid].update(upd)
        
        return msg, butts
    except Exception as e:
        LOGGER.error(f"Error in YouTube search: {e}")
        return f"<b>❌ Terjadi kesalahan saat mencari video:</b>\n\n<code>{str(e)}</code>", None
    

async def edit_durasi(duration):
    return duration.replace("PT", "").replace("H", ":").replace("M", ":").replace("S", "")

async def yt_extra(video_id):
    api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU" 
    video_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,contentDetails,statistics&key={api_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(video_url)
        data = response.json()
    
    details = {}
    if "items" in data and len(data["items"]) > 0:
        item = data["items"][0]
        video_id = item["id"]
        duration = item["contentDetails"]["duration"]
        channel_title = item["snippet"]["channelTitle"]
        thumbnail_url = item["snippet"].get("thumbnails", {}).get("standard", {}).get("url", "")
        title = item["snippet"]["title"]
        description = item["snippet"].get("description", "")
        
        statistics = item.get("statistics", {})
        view_count = statistics.get("viewCount", "0")
        like_count = statistics.get("likeCount", "0")
        
        details = {
            'duration': duration,
            'channel_title': channel_title,
            'thumbnail_url': thumbnail_url,
            'title': title,
            'description': description,
            'video_id': video_id,
            'view_count': view_count,
            'like_count': like_count
        }
    
    return details
    
async def yt_search(client, message, keyword=None):
    uid = message.from_user.id
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        keyword = None
    
    if keyword:
        mess = None
        try:
            mess = await sendMessage(message, f"<b>Tunggu sebentar tuan...</b>")
            
            if uid in youtube:
                butt = ButtonMaker()
                butt.ibutton("⛔️ Batalkan", f"youtube cancel {uid}")
                butts = butt.build_menu(1)
                try:
                    await editMessage(mess, "<b>Silahkan selesaikan atau batalkan proses sebelumnya !</b>", butts)
                except Exception as e:
                    LOGGER.error(f"Edit message error: {e}")
                    await message.reply_text("<b>Silahkan selesaikan atau batalkan proses sebelumnya !</b>", reply_markup=butts)
                return None
                
            youtube[uid] = {"message": message, "keyword": keyword}
            
            msg, butts = await yt_request(uid, keyword, page=1)
            
            try:
                if mess:
                    await deleteMessage(mess)
            except Exception as e:
                LOGGER.error(f"Error deleting message: {e}")
                
            try:
                # Delete the user's command message if possible
                try:
                    await message.delete()
                except Exception as e:
                    LOGGER.error(f"Error deleting command message: {e}")
                
                # Try to send with photo and full caption
                try:
                    sent_message = await message.reply_photo(
                        "https://telegra.ph/file/9fbae069402df1710585f.jpg", 
                        caption=msg, 
                        reply_markup=butts
                    )
                    youtube[uid]["sent_message"] = sent_message
                except pyrogram.errors.exceptions.bad_request_400.MediaCaptionTooLong:
                    # If caption is too long, send with a shorter caption
                    short_msg = f"<b>🔎 Hasil Pencarian:</b> <code>{keyword}</code>\n\n<i>Hasil terlalu panjang, silahkan pilih nomor untuk melihat detail.</i>"
                    sent_message = await message.reply_photo(
                        "https://telegra.ph/file/9fbae069402df1710585f.jpg", 
                        caption=short_msg, 
                        reply_markup=butts
                    )
                    youtube[uid]["sent_message"] = sent_message
                    
                    # Then send the full results as a text message
                    await message.reply_text(
                        msg,
                        disable_web_page_preview=True
                    )
            except Exception as e:
                LOGGER.error(f"Error sending YouTube search results: {e}")
                if uid in youtube:
                    del youtube[uid]
                await message.reply_text(f"<b>❌ Error:</b> {str(e)}")
                
        except Exception as e:
            LOGGER.error(f"YouTube search error: {e}")
            try:
                if mess:
                    await editMessage(mess, f"<b>Error:</b> {str(e)}")
            except Exception:
                await message.reply_text(f"<b>❌ Error:</b> {str(e)}")
            if uid in youtube:
                del youtube[uid]
    else:
        await sendMessage(message, "<b>Silahkan masukkan perintah disertai keyword pencarian !</b>")


async def yt_query(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    uid = int(data[2])
    
    if user_id != uid:
        return await query.answer(text="Bukan Tugas Anda!", show_alert=True)
    
    if uid not in youtube:
        return await query.answer(text="Tugas sudah tidak ada atau dibatalkan!", show_alert=True)
    
    if data[1] == "none":
        await query.answer("No action available", show_alert=True)
        return
        
    elif data[1] == "cancel":
        if uid in youtube:
            del youtube[uid]
        return await query.answer("✅ Tugas pencarian dibatalkan.", show_alert=True)
    
    elif data[1] == "selectpage":
        page = int(data[3])
        page_results = youtube[uid].get("page_results", [])
        
        if not page_results:
            return await query.answer("No videos found on this page", show_alert=True)
        
        butt = ButtonMaker()
        butt.ibutton("🔄 Mirror", f"youtube mirror_page {uid} {page}")
        butt.ibutton("📥 Leech", f"youtube leech_page {uid} {page}")
        butt.ibutton("🎵 Audio", f"youtube audio_page {uid} {page}")
        butt.ibutton("🔙 Kembali", f"youtube back {uid}")
        butt.ibutton("⛔️ Batalkan", f"youtube cancel {uid}", position="footer")
        butts = butt.build_menu(2)
        
        msg = f"<b>🎬 Pilih tindakan untuk halaman {page}:</b>\n\n"
        msg += f"<b>⚠️ Tindakan ini akan mengunduh semua video di halaman ini</b>"
        
        await message.edit_caption(caption=msg, reply_markup=butts)
    
    elif data[1] in ["mirror_page", "leech_page", "audio_page"]:
        page = int(data[3])
        page_results = youtube[uid].get("page_results", [])
        
        if not page_results:
            return await query.answer("No videos found on this page", show_alert=True)
        
        action_type = data[1].split("_")[0]
        
        qualities = ["1080p", "720p", "480p", "360p", "Audio Only"]
        
        msg = f"<b>🎬 Pilih kualitas untuk {action_type} semua video di halaman {page}:</b>\n"
        msg += f"<b>⏱️ Waktu habis:</b> <code>1m59d</code>\n\n"
        msg += f"<b>Total Video:</b> <code>{len(page_results)}</code>"
        
        butt = ButtonMaker()
        for quality in qualities:
            butt.ibutton(quality, f"youtube {action_type}_page_quality {uid} {page} {quality}")
        
        butt.ibutton("🔙 Kembali", f"youtube selectpage {uid} {page}")
        butt.ibutton("⛔️ Batalkan", f"youtube cancel {uid}")
        butts = butt.build_menu(2)
        
        await message.edit_caption(caption=msg, reply_markup=butts)
    
    elif data[1] in ["mirror_page_quality", "leech_page_quality", "audio_page_quality"]:
        page = int(data[3])
        quality = data[4]
        page_results = youtube[uid].get("page_results", [])
        
        if not page_results:
            return await query.answer("No videos found on this page", show_alert=True)
        
        action_parts = data[1].split("_")
        action_type = action_parts[0] 
        is_leech = action_type == "leech" or action_type == "audio"
        
        if action_type == "audio":
            ydl_opts = 'format=bestaudio'
        elif quality == "Audio Only":
            ydl_opts = 'format=bestaudio'
        else:
            ydl_opts = f'format=bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]'
        
        orig_msg = youtube[uid]["message"]
        await deleteMessage(message)
        
        if uid in youtube:
            del youtube[uid]
        
        await orig_msg.reply_text(f"<b>✅ Processing {len(page_results)} videos with quality {quality}</b>")
        
        for i, result in enumerate(page_results):
            video_id = result["id"]
            yt_url = f"https://www.youtube.com/watch?v={video_id}"
            YtDlp(bot, orig_msg, yturl=yt_url, options=ydl_opts, isLeech=is_leech).newEvent()
            await asleep(1)  
    
    elif data[1] == "page":
        page = int(data[3])
        keyword = ' '.join(data[4:])
        
        msg, butts = await yt_request(uid, keyword, page=page)
        
        try:
            await message.edit_caption(caption=msg, reply_markup=butts)
        except Exception as e:
            LOGGER.error(f"Error updating page: {e}")
            await query.answer(text=f"Error updating page: {str(e)}", show_alert=True)
    
    elif data[1] == "join":
        await query.answer("Redirecting to channel...")
        butt = ButtonMaker()
        butt.ubutton("🔗 Join Dizzy Project", "https://t.me/DizzyStuffProject")
        butts = butt.build_menu(1)
        await message.edit_caption(
            caption=f"<b>📣 Join our channel for updates and more features!</b>\n\n<i>Click the button below to join, then return to your search.</i>",
            reply_markup=butts
        )
    
    elif data[1] == "back":
        current_page = youtube[uid].get("page", 1)
        keyword = youtube[uid].get("keyword", "")
        
        msg, butts = await yt_request(uid, keyword, page=current_page)
        
        try:
            input_media = InputMediaPhoto(media="https://telegra.ph/file/9fbae069402df1710585f.jpg", caption=msg)
            await message.edit_media(media=input_media, reply_markup=butts)
        except Exception as e:
            LOGGER.error(f"Error going back to results: {e}")
            await message.edit_caption(caption=msg, reply_markup=butts)


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