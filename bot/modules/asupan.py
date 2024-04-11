import random
import requests
import re

from random import randint
from cloudscraper import create_scraper
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

async def tiktokdl(_, message, id=None):
    url = message.text
    mess = await sendMessage(message, f"<b>⌛️Mendownload media dari tiktok, silahkan tunggu sebentar...</b>")
    with requests.Session() as session:
        if id is None:
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
                id = match.group('id')
            else:
                await editMessage(message, f"Link yang anda berikan sepertinya salah atau belum support, silahkan coba dengan link yang lain !")
                return None
        else:       
            id = id
            content_type = "video"
        data = ""
        while len(data) == 0:
            r = session.get(
                url=f"https://api22-normal-c-useast2a.tiktokv.com/aweme/v1/feed/?aweme_id={id}",
                headers={
                    "User-Agent": user_agent,
                }
            )
            data += r.text
        data = loads(data)
        if message.from_user.username:
            uname = f'@{message.from_user.username}'
        else:
            uname = f'<code>{message.from_user.first_name}</code>'
        try:
            #music = data["aweme_list"][0]["music"]["play_url"]["url_list"][-1]
            #m_capt = data["aweme_list"][0]["music"]["title"]
            if content_type == "video":
                link = data["aweme_list"][0]["video"]["play_addr"]["url_list"][-1]
                filename = data["aweme_list"][0]["desc"]
                capt = f"<code>{filename}</code> \n\n<b>Tugas Oleh:</b> {uname}"                
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

async def tiktok_search(_, message):
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        await sendMessage(message, f"Silahkan masukkan keyword pencarian setelah perintah !")
    mess = await sendMessage(message, f"Mencari video tiktok dengan keyword <code>{keyword}</code>")
    session = create_scraper()
    session.headers.update({
        "Cookie": "tt_csrf_token=GX36Elxm-IzPlqY84I9Tvr1kEur1nMkUBsZE; tt_chain_token=V1k0U3zHiB6IYmqNCi/ULw==; tiktok_webapp_theme=light; ttwid=1%7C5XR3IKQDX3Z-j6gzdzHyJltpq3c84r0JW0EknblG1QY%7C1707850284%7Cec05b8ce0d447706d505b64e0f52666e98415056c991aba9cde540905e1c2b06; odin_tt=2377ef16d4e71ca25af6865e5873fea22d360caf85546b8bf0b34d2efdbc3b3b7e5283171b534d61e6ea11e0c5611a61210d121625711d0489126458d6956577dd2414bb9a1c4d4edd56a20371a3a916; _ttp=2cZzw9oUTjdEZnWw4doQ8IDaHDQ; passport_csrf_token=7bd001111dd720f4bbd9a696587939e6; passport_csrf_token_default=7bd001111dd720f4bbd9a696587939e6; ak_bmsc=958EBBEC8D841EC70BAFDB1370A8BE2D~000000000000000000000000000000~YAAQFOnOF/lQaciOAQAAwoUOzBcoimpv18E1S0dU/ZbN2ufjvBbjKS+w3IiSPEEQlRgDDtymbFQI1pjBYdKq4VVUuln0/M+eUBKQHgeYGAm6cgST5nhz/YtjRPHhqi/IgeAvpaIKNUgiiDsMPlmusRpl5g1QH0PJaTsfQgl/cHYuD7JgHHfSpBZklMS+u/cUu2qqER9k2wR+RzzGgRk/5BAQtvuRD21RvNATBYDFEoNwMlsuKD2dh9HCc/K69PfaHgEx51TC524b5dhs6BB4tKvxAhckMvAMELoiDIrwV9fyyBD9vNSczGL65HfmmtdIvCsymM3ixKJNTdOTIV+EQ1KDnyensl5gl3SdcG62mVisdmt5LvkduzsY3EPlY3GAxkA9Yh45THk=; perf_feed_cache={%22expireTimestamp%22:1712991600000%2C%22itemIds%22:[%227354684321174686982%22%2C%227343630660034170117%22]}; msToken=BwpAcQ7JFCJBHvI9gsZ8dNwMC4a1kCe8tiHTeYFX93wLU3SgUpsS1bCj6MsKA3nSr9S7-OYtuqGiGpGcxu-1PvqkoN-eBnoTdwtFPaXtGQuM51BWJ-tW1Ptw9DLRWNH5O-_hblv4qAPq7YSsAw==; bm_sv=A7FF973F42B8CF54725255B244CA3503~YAAQC+nOF0++F7OOAQAAxKsdzBftSAowhIcW2HjxPpASPwrSdSmnrpM3fU+iONXPddufPHVfQ5lwxXLOsFwhhqtPP8fw70yY3Gikwp7yYH2hCbnwVevwdI6RdSemimxs66s8SvzX8/sCS5e6Jw0417Fxp5irxSmkWwdKBUGOOKuWnSISW3BuFXUosIt2FjhAJLAotGal+ZjbAIF6q1Z05d5KBTnD0TWkB1sMfTuN9Mg5z9VddEPqwdMXdbH4QMpR~1; msToken=A6HQB6w2ekZFT2FtNq3J-QiQxq8JdEnoiY-33plstM32Su2pF0KyAhJ9275X4TIxzh4jTcskP_hJd2dKB7JL3w57HwO7enrNz8p7P-rS2-6oIr7F3AjLdqQOpVr2dif4bYNtAxlboTpevRAX2w==",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        }
    )
    num = 0
    search = ""
    while len(search) == 0:
        num += 1
        r = session.get(
            url="https://www.tiktok.com/api/search/item/full/",
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
                "cookie_enabled": False,
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
                "priority_region": "",
                "referer": "",
                "region": "ID",
                "screen_height": 1080,
                "screen_width": 1920,
                "search_source": "normal_search",
                "tz_name": "Asia/Jakarta",
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
                },
            }
        )

        search += r.text

    data = loads(search)
    try:
        id = (f"{data['item_list'][randint(0, len(data['item_list']) - 1)]['id']}")
    except Exception as e:
        await editMessage(mess, f"ERROR: {e}")
        return None
    await deleteMessage(mess)
    await tiktokdl(_, message, id=id)

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
        tiktok_search, 
        filters=command(
            BotCommands.TiktokCommand
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