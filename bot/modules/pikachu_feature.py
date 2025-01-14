import random
import requests
import re
import httpx
import niquests
import os
import subprocess
import pickle

from asyncio import sleep as asleep, create_subprocess_exec
from http.cookiejar import MozillaCookieJar
from random import randint
from json import loads
from bot import bot, DATABASE_URL
from aiofiles.os import remove as aioremove, path as aiopath, mkdir, makedirs
from os import path as ospath, getcwd
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
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
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.ext_utils.db_handler import DbManger
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

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
async def tiktokdl(client, message, url, audio=False):
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
        
        pattern = r"^(?:https?://(?:www\.)?tiktok\.com)/(?P<user>[\a-zA-Z0-9-]+)(?P<content_type>video|photo)+/(?P<id>\d+)"
        match = re.match(pattern, str(hasil))
        if match:  
            content_type = match.group("content_type")
            id = match.group('id')
        else:
            await editMessage(message, f"Link yang anda berikan sepertinya salah atau belum support, silahkan coba dengan link yang lain !")
            return None
        
    async with niquests.AsyncSession() as client:
        data = ""
        try:
            while len(data) == 0:
                r = await client.get(
                        url=f"https://api16-normal-useast5.us.tiktokv.com/aweme/v1/feed/?aweme_id={id}",
                        headers={
                            "User-Agent": user_agent,
                        }
                    )
                r.raise_for_status()
                data = r.text
            data = loads(data)
        except Exception as e:
            await sendMessage(mess, f"Hai {uname}, Terjadi kesalahan saat mencoba mengambil data, silahkan coba kembali.\n\n<blockquote>{e}</blockquote>")
            await deleteMessage(mess)
            return None
        try:
            music = data["aweme_list"][0]["music"]["play_url"]["url_list"][-1]
            m_capt = data["aweme_list"][0]["music"]["title"]
            if content_type == "video":
                link = data["aweme_list"][0]["video"]["play_addr"]["url_list"][-1]
                filename = data["aweme_list"][0]["desc"]
                capt = f"<code>{filename}</code> \n\n<b>Tugas Oleh:</b> {uname}"
                if audio is False:                
                    await customSendVideo(message, link, capt, None, None, None, None, None)
                else:
                    await customSendAudio(message, music, m_capt, None, None, None, None, None)
            if content_type == "photo":
                if audio is False:
                    photo_urls = []
                    for aweme in data["aweme_list"][0]["image_post_info"]["images"]:
                        for link in aweme["display_image"]["url_list"][1:]:
                            photo_urls.append(link)
                    photo_groups = [photo_urls[i:i+10] for i in range(0, len(photo_urls), 10)]
                    for photo_group in photo_groups:
                        await message.reply_media_group([InputMediaPhoto(photo_url) for photo_url in photo_group])
                else:
                    await customSendAudio(message, music, m_capt, None, None, None, None, None)
               
        except Exception as e:
                await sendMessage(message, f"ERROR: Gagal mengupload media {e}")
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
    butt.ibutton("🔈 Audio", f"tk audio {user_id}")
    butt.ibutton("⛔️ Batal", f"tk cancel {user_id}")
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
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)
    
    elif data[1] == "media":
        await deleteMessage(message)
        del msgs[uid]   
        await tiktokdl(bot, msg, url=tkurl) 
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

####################################################################
#YT_SEARCH
####################################################################
youtube = {}
async def yt_request(uid, keyword):
    try:
        api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU" #please use your own api_key (this is pikachu api_key)
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&type=video&regionCode=ID&maxResults=10&key={api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url)
            data = response.json()
        results = []

        if "items" in data:
            for item in data["items"]:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                results.append({'title': title, 'id': video_id})
                if len(results) >= 10:
                    break
        
        msg = f"<b>Hasil Pencarian dengan Keyword: <code>{keyword}</code></b>\n\n"
        butt = ButtonMaker()
        butt.ibutton("⛔️ Batal", f"youtube cancel {uid}", position="footer")          
        for index,video in enumerate(results, start=1):      
            judul = video['title']
            video_id = video['id']
            msg += f"<a href='https://www.youtube.com/watch?v={video_id}'><b>{index:02d}. </b></a>{judul}\n"
            butt.ibutton(f"{index}", f"youtube select {uid} {video_id}")
        butts = butt.build_menu(5)
        upd = {"msg": msg, "butts": butts}
        youtube[uid].update(upd)
        return msg, butts
    except Exception as e:
        return f"Terjadi kesalahan saat mengambil video, atau video ini belum tersedia \n\n{e}"

async def edit_durasi(duration):
    duration = duration[2:]
    duration = duration.replace("M", " menit ")
    duration = duration.replace("S", " detik")
    duration = duration.replace("H", " jam ")
    duration = duration.replace("D", " hari ")
    duration = duration.replace("T", "")
    return duration

async def yt_extra(video_id):
    api_key = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU" #please use your own api_key (this is pikachu api_key)
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
            butt.ibutton("⛔️ Batal", f"youtube cancel {uid}")
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
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)
    elif data[1] == "select":
        try:
            details = await yt_extra(data[3])
        except Exception as e:
            return await query.answer(text=f"Terjadi kesalahan saat mengambil video, atau video ini belum tersedia. {e}", show_alert=True)
        try:
            msg = f"<b>🎬 Judul: </b><code>{details['title']}</code>\n\n"
            msg += f"<b>📢 Channel: </b><code>{details['channel_title']}</code>\n"
            msg += f"<b>⏱ Durasi: </b><code>{await edit_durasi(details['duration'])}</code>\n"
            msg += f"<b>🌐 Link: </b><code>https://www.youtube.com/watch?v={data[3]}</code>"
            butt = ButtonMaker()
            butt.ibutton("☁️ Mirror", f"youtube mirror {uid} {data[3]}")
            butt.ibutton("☀️ Leech", f"youtube leech {uid} {data[3]}")
            butt.ibutton("⬅️ Kembali", f"youtube back {uid}")
            butt.ibutton("⛔️ Batal", f"youtube cancel {uid}")
            butts = butt.build_menu(2)
            new_media = InputMediaPhoto(details['thumbnail_url'], caption=msg)
            no_thumbnail = InputMediaPhoto("https://telegra.ph/file/5e7fde2b232ae1b682625.jpg", caption=msg)
            try:
                await edit_media(new_media, reply_markup=butts)
            except:
                await edit_media(no_thumbnail, reply_markup=butts)
        except Exception as e:
            await editMessage(message, f"Gagal mengambil video, atau video ini tidak tersedia. \n\n{e}")
            del youtube[uid]
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

###########################
#Pickle Generator
###########################
OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
client_id = "177372616802-uiilrh4sbafdibf4lvkn3sspg9vajkok.apps.googleusercontent.com"
client_secret = "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"

async def get_token(client, message):
    private = bool(message.chat.type == ChatType.PRIVATE)
    if not private:
        butt = ButtonMaker()
        butt.ubutton("❇️ LETS GO", f"https://t.me/{bot.me.username}")
        await sendMessage(message, "This command can only be used in private chat, click the button below and use /gettoken command on Private Chat.", butt.build_menu(1))
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
        
        msg = f"<b>Follow the steps below to get your Google Drive Token.</b>\n\n• Open the Authorization URL and login to your Google Drive account.\n"
        msg += f"• Allow the app to access your Google Drive.\n"
        msg += f"• Click Continue and you will redirected to error page.\n"
        msg += f"• Copy the url from the page and Paste Here !\n"
        butt = ButtonMaker()
        butt.ubutton("Authorization URL", auth_url)
        butts = butt.build_menu(1)
        
        try:
            ask = await sendMessage(message, msg, butts)
            respon = await bot.listen(
                filters=filters.text & filters.user(uid)
            )
            code = respon.text.split('code=')[1].split('&')[0]
            await respon.delete()
            wait = await editMessage(ask, f"Memverifikasi kode anda...")
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            with open(pickle_path, "wb") as token:
                pickle.dump(credentials, token)
            
            caption = "📋 <b>Google Drive Token Info:</b>\n\n"
            caption += f"🔑 <b>Client ID:</b> <code>{client_id}</code>\n"
            caption += f"🔒 <b>Client Secret:</b> <code>{client_secret}</code>\n"
            caption += f"🔄 <b>Refresh Token:</b> <code>{credentials.refresh_token}</code>"
    
            try:
                await message.reply_document(
                    document=pickle_path,
                    caption=caption,
                    )
            except Exception as e:
                await message.reply_text(f"Failed to send file: {str(e)}")
            
            await deleteMessage(wait)
            await deleteMessage(ask)
            return True
            
        except IndexError:
            await deleteMessage(ask)
            raise Exception("Authorization code not found, give the correct url and try again.")
        except Exception as e:
            await deleteMessage(ask)
            raise Exception(str(e))
    except Exception as e:
        await message.reply_text(f"<b>❌ Error:</b> {e}")
    finally:
        if os.path.exists(pickle_path):
            os.remove(pickle_path)

async def gen_token(client, message):
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
                raise Exception("Token google drive anda sudah ada dan sudah diperbaharui.")
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
            msg = f"<b>Ikuti langkah dibawah untuk generate token google drive:</b>\n\n• Klik link dibawah untuk autorisasi google drive\n"
            msg += f"• Pilih akun googledrive yang akan digunakan untuk mirroring.\n"
            msg += f"• Klik Lanjutkan dan anda akan dibawa ke halaman error.\n"
            msg += f"• Silahkan salin semua alamat url di halaman error tersebut dan kirim ke bot.\n"
            butt = ButtonMaker()
            butt.ubutton("Autorisasi Google Drive", auth_url)
            butts = butt.build_menu(1)
            try:
                ask = await sendMessage(message, msg, butts)
                respon = await bot.listen(
                        filters=filters.text & filters.user(uid)
                        )
                code = respon.text.split('code=')[1].split('&')[0]
                await respon.delete()
                wait = await editMessage(ask, f"Memferifikasi kode anda...")
                credentials = flow.fetch_token(code=code)
                with open(pickle_path, "wb") as token:
                    pickle.dump(flow.credentials, token)
                await deleteMessage(wait)
                await deleteMessage(ask)
                return True
            except IndexError:
                await deleteMessage(ask)
                raise Exception("Kode tidak ditemukan, url yang anda berikan sepertinya tidak valid, silahkan coba lagi.")
            except Exception as e:
                await deleteMessage(ask)
                raise Exception(e)
    try:
        credentials = await generate_token(message)
        if credentials and os.path.exists(pickle_path):
            update_user_ldata(uid, "token_pickle", f"tokens/{uid}.pickle")
            if DATABASE_URL:
                await DbManger().update_user_doc(uid, "token_pickle", pickle_path)
            await sendMessage(message, f"✅ <b>Token google drive anda berhasil dibuat</b>\n\nGunakan <code>-up gdl</code> dan pilih <b>My Token</b> untuk upload ke drive sendiri.\n<b>Contoh:</b> <blockquote><code>/mirror Link -up gdl</code></blockquote>")
    except Exception as e:
        await message.reply_text(f"<b>❌ Error:</b> {e}")

########################################################################################

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
