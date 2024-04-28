import random
import requests
import re
import uuid
import os

from http.cookiejar import MozillaCookieJar
from random import randint
from cloudscraper import create_scraper
from json import loads
from bot import bot
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd
from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler
from pyrogram.types import InputMediaPhoto
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from pyrogram import filters
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, deleteMessage, customSendAudio, customSendPhoto, customSendVideo
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.bot_utils import sync_to_async

tiktok = []
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
    mess = await sendMessage(message, "Tunggu sebentar tuan...")
    try_count = 5
    attempt = 1
    while attempt <= try_count:
        try:
            json_data = await get_url(file_url)
            if json_data:
                if isinstance(json_data, list):
                    video_link = random.choice(json_data)
                    await message.reply_video(video_link)
                    break
                else:
                    break
        except:
            attempt += 1
            if attempt <= try_count:
                await sendMessage(mess, f"Gagal mengirim asupan, Mencoba lagi untuk ke-{attempt} kali...")
            else:
                await editMessage(mess, "Gagal mengupload asupan setelah 5x percobaan.")
                break
        finally:
            await deleteMessage(mess)

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

async def tiktokdl(client, message, url, audio=False):
    url = url
    if audio is False:
        mess = await sendMessage(message, f"<b>⌛️Mendownload media dari tiktok, silahkan tunggu sebentar...</b>")
    else:
        mess = await sendMessage(message, f"<b>⌛️Mendownload audio dari tiktok, silahkan tunggu sebentar...</b>")
    with create_scraper() as session:
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

async def tiktok_search(_, message):
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        await sendMessage(message, f"Silahkan masukkan keyword pencarian setelah perintah !")
    mess = await sendMessage(message, f"<b>⌛️Sedang mencari video tiktok dengan keyword:</b>\n\n<code>🔎 {keyword}</code>")
    session = create_scraper()
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
    num = 0
    search = ""
    while len(search) == 0:
        num += 1
        r = session.get(
            url="https://www.tiktok.com/api/search/item/full/",
            params=params,
            cookies=cookies
        )

        search += r.text

    data = loads(search)
    #try:
    #    id = (f"{data['item_list'][randint(0, len(data['item_list']) - 1)]['id']}")
    #except Exception as e:
    #    await editMessage(mess, f"ERROR: {e}")
    #    return None
    #await deleteMessage(mess)
    #await tiktokdl(_, message, id=id)
    num = 0
    video = ""
    if message.from_user.username:
            uname = f'@{message.from_user.username}'
    else:
            uname = f'<code>{message.from_user.first_name}</code>'
    try:
        while len(video) == 0:
            num += 1
            r = session.get(
                url=f"https://api22-normal-c-useast2a.tiktokv.com/aweme/v1/feed/?aweme_id={data['item_list'][randint(0, len(data['item_list']) - 1)]['id']}",
            )

            video += r.text
        data = loads(video)
    
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
async def download_photo(url):
    filename = os.path.join("downloads", str(uuid.uuid4()) + ".jpg")
    with open(filename, "wb") as f:
        response = requests.get(url)
        f.write(response.content)
    return filename

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

<b>Note:</b> Kirim hanya printah <code>/{BotCommands.AnimekCommand}</code> untuk hasil random.
        """
        await editMessage(mess, msg)
        return None
    query = None
    for tag in tags:
        for key in tag:
            if key in keyword:
                query = tag[key]
                break
        if query:
            break

    if not query:
        random_tag = random.choice(tags)
        random_value = list(random_tag.values())[0]
        query = random_value

    try_count = 5
    attempt = 1
    while attempt <= try_count:
        try:
            r = requests.get(f"https://api.waifu.im/search?included_tags={query}")
            data = r.json()
            if r.status_code == 200:
                for picts in data:
                    pict = (data[picts][0]["url"])
                    path = await download_photo(pict)
                await customSendPhoto(message, path, None, None)
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
            os.remove(path)
        
@bot.on_message(filters.group, group=1)
async def welcome(client, message):
    if (message.chat_joined_by_request or message.new_chat_members):
        for mess in m_id:
            try:
                await deleteMessage(mess)
                m_id.clear()
            except:
                pass
        user = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        med = "https://telegra.ph/file/075ceb9aabce1646eaad1.mp4"
        capt = f"""
<b>Hai {user} !!</b>
Selamat datang di <b>PikaMirror Group</b>.

Gunakan <code>/help</code> untuk melihat bantuan dan jangan lupa ikutin rules. Untuk full fitur dari bot, bisa cek <a href='https://t.me/pikachukocak/13'><b>DISINI</b></a>.
    
<b>Rules:</b>
✓ Tidak boleh mirror/leech konten 18+ (Auto Ban)
✓ Sisanya ngikutin mood admin
"""

        mess = await bot.send_animation(chat_id=message.chat.id, animation=med, caption=capt)
        m_id.append(mess)
    else:
        return

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

tiktokregex = r"(https?://(?:www\.)?[a-zA-Z0-9.-]*tiktok\.com/)"

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