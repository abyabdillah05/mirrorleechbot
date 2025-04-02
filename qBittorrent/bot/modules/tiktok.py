import asyncio
import httpx
import niquests
import re
import json
import time
import os
import random
from datetime import datetime

###############################
## Import Libraries Pyrogram ##
###############################

from pyrogram import filters
from pyrogram.filters import (command,
                              regex)
from pyrogram.handlers import (MessageHandler,
                               CallbackQueryHandler)
from pyrogram.types import (InputMediaPhoto,
                            InputMediaVideo)

####################################################

from json import loads
from random import randint
from http.cookiejar import MozillaCookieJar

###################################
## Import Libraries From Project ##
###################################

from bot import (bot,
                 LOGGER)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      deleteMessage,
                                                      editMessage,
                                                      customSendAudio,
                                                      customSendVideo)

########################
## Required Variables ##
########################

tiktok = []
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
tiktokregex = r"(https?://(?:www\.)?[a-zA-Z0-9.-]*tiktok\.com/)"

############################################
## Tiktok Downloader | Credit @aenulrofik ##
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

################################################
## Tiktok Auto Detection | Credit @aenulrofik ##
################################################

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

async def auto_tk_query(_, query):
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

#######################################
# TikTok Search | Credit @aenulrofik ##
#######################################

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

############################################
## Tiktok Handler And Command ##
############################################

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
        auto_tk_query,
        filters=regex(
            r'^tk '
        )
    )
)

## Thanks to @aenulrofik for this feature ##