import asyncio
from asyncio import sleep as asleep
from http.cookiejar import MozillaCookieJar
from random import randint, choice
from json import loads
from bot import (bot,
                 LOGGER,
                 config_dict)
from pyrogram.filters import (command,
                              regex)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from bot.helper.telegram_helper.button_build import ButtonMaker
from pyrogram import filters
from bot.helper.telegram_helper.message_utils import(sendMessage,
                                                     editMessage,
                                                     deleteMessage,
                                                     customSendAudio,
                                                     customSendVideo)
from bot.helper.ext_utils.yt_dlp_download_helper import YtDlp
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
import re
import httpx

# Constants
tiktokregex = r"(https?:\/\/)?(vm|vt|www|v)?\.?tiktok\.com\/"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
]

# Storage dictionaries
tiktok = [] ## For auto tiktok download
tiktok_searches = {} ## For paginated search

####################
## Helper Functions
####################

def format_count(count):
    try:
        count = int(count)
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        else:
            return str(count)
    except:
        return str(count)

def format_duration(seconds):
    try:
        seconds = int(seconds)
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}:{seconds:02d}"
    except:
        return "0:00"

def get_file_size(duration):
    try:
        minutes = duration / 60
        size_mb = minutes * 5
        
        if size_mb > 1024:
            return f"{size_mb/1024:.2f} GB"
        else:
            return f"{size_mb:.2f} MB"
    except:
        return "Unknown size"


####################
## tiktok downloader
####################

async def tiktokdl(client, message, url, audio=False, type="video"):
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<code>{message.from_user.first_name}</code>'
    
    if audio:
        mess = await sendMessage(message, f"<b>⌛️Mendownload audio dari tiktok, silahkan tunggu sebentar...</b>")
    else:
        mess = await sendMessage(message, f"<b>⌛️Mendownload video dari tiktok, silahkan tunggu sebentar...</b>")
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(url)
            final_url = str(r.url)
            
            video_id = None
            
            pattern1 = r"(?:https?://)?(?:www\.)?tiktok\.com/@[\w\.-]+/video/(\d+)"
            pattern2 = r"(?:https?://)?(?:www\.)?tiktok\.com/t/(\w+)"
            pattern3 = r"(?:https?://)?(?:www\.)?vm\.tiktok\.com/(\w+)"
            pattern4 = r"(?:https?://)?(?:www\.)?vt\.tiktok\.com/(\w+)"
            
            match1 = re.search(pattern1, final_url)
            if match1:
                video_id = match1.group(1)
            else:
                vm_code = None
                for pattern in [pattern2, pattern3, pattern4]:
                    match = re.search(pattern, final_url)
                    if match:
                        vm_code = match.group(1)
                        break
                
                if not vm_code and "tiktok.com" in final_url:
                    path_parts = final_url.split("/")
                    for part in path_parts:
                        if part.isdigit() and len(part) > 8:
                            video_id = part
                            break
                
                if vm_code and not video_id:
                    try:
                        headers = {
                            "User-Agent": choice(user_agents),
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
                        
                        if response.status_code == 200:
                            result = response.json()
                            if "id" in result:
                                video_id = result["id"]
                    except Exception as e:
                        LOGGER.error(f"Error resolving VM code: {e}")
            
            if not video_id:
                try:
                    await deleteMessage(mess)
                    if audio:
                        YtDlp(client, message, yturl=url, options='-x --audio-format mp3', isLeech=True).newEvent()
                    else:
                        YtDlp(client, message, yturl=url, isLeech=True).newEvent()
                    return
                except Exception as e:
                    LOGGER.error(f"Error with yt-dlp fallback: {e}")
                    await editMessage(mess, f"<b>❌ Error:</b> Tidak dapat mengekstrak ID video dari URL: {url}\n\nLink yang anda berikan sepertinya salah atau belum support, silahkan coba dengan link yang lain!")
                    return None
            
            try:
                api_url = f"https://api16-normal-useast5.us.tiktokv.com/aweme/v1/feed/?aweme_id={video_id}"
                r = await client.get(
                    api_url,
                    headers={"User-Agent": choice(user_agents)},
                    timeout=10
                )
                
                data = r.json()
                
                if "aweme_list" in data and len(data["aweme_list"]) > 0:
                    item = data["aweme_list"][0]
                    
                    music_url = item["music"]["play_url"]["url_list"][-1]
                    music_title = item["music"]["title"]
                    
                    if "video" in item:
                        video_desc = item.get("desc", "TikTok Video")
                        capt = f"<code>{video_desc}</code>\n\n<b>Tugas Oleh:</b> {uname}"
                        
                        if audio is True or type == "audio":
                            await customSendAudio(message, music_url, music_title, None, None, None, None, None)
                        else:
                            if type == "nowm":
                                video_url = None
                                for url in item["video"]["play_addr"]["url_list"]:
                                    if "watermark=0" in url:
                                        video_url = url
                                        break
                                
                                if not video_url:
                                    video_url = item["video"]["play_addr"]["url_list"][-1]
                            else:
                                video_url = item["video"]["play_addr"]["url_list"][-1]
                                
                            await customSendVideo(message, video_url, capt, None, None, None, None, None)
                    
                    elif "image_post_info" in item:
                        if audio is True or type == "audio":
                            await customSendAudio(message, music_url, music_title, None, None, None, None, None)
                        else:
                            photo_urls = []
                            for image in item["image_post_info"]["images"]:
                                url = image["display_image"]["url_list"][-1]
                                photo_urls.append(url)
                            
                            photo_groups = [photo_urls[i:i+10] for i in range(0, len(photo_urls), 10)]
                            for photo_group in photo_groups:
                                await message.reply_media_group([InputMediaPhoto(photo_url) for photo_url in photo_group])
                    
                    else:
                        raise Exception("Unsupported content type")
                
                else:
                    raise Exception("No data from TikTok API")
                    
            except Exception as e:
                LOGGER.error(f"TikTok API error: {e}")
                
                headers = {
                    "User-Agent": choice(user_agents),
                    "Referer": "https://tiksave.ai/"
                }
                
                data = {
                    "id": url  
                }
                
                response = await client.post(
                    "https://tiksave.ai/api/download", 
                    headers=headers,
                    data=data,
                    timeout=15
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
                        capt = f"<code>{title}</code>\n\n<b>Tugas Oleh:</b> {uname}"
                        await customSendVideo(message, video_url, capt, None, None, None, None, None)
                else:
                    await deleteMessage(mess)
                    if audio:
                        YtDlp(client, message, yturl=url, options='-x --audio-format mp3', isLeech=True).newEvent()
                    else:
                        YtDlp(client, message, yturl=url, isLeech=True).newEvent()
                    return
    
    except Exception as e:
        LOGGER.error(f"Error in TikTok download: {str(e)}")
        try:
            await editMessage(mess, "<b>Mencoba metode alternatif untuk mengunduh...</b>")
            await asleep(2)
            await deleteMessage(mess)
            
            if audio:
                YtDlp(client, message, yturl=url, options='-x --audio-format mp3', isLeech=True).newEvent()
            else:
                if type == "nowm":
                    YtDlp(client, message, yturl=url, options='--no-check-certificate', isLeech=True).newEvent()
                else:
                    YtDlp(client, message, yturl=url, isLeech=True).newEvent()
        except Exception as e2:
            LOGGER.error(f"Final fallback error: {str(e2)}")
            await message.reply_text(f"<b>❌ Error:</b> Gagal mengunduh: {str(e)}\n\nFinal error: {str(e2)}")
    finally:
        try:
            await deleteMessage(mess)
        except:
            pass


####################
## tiktok search
## tiktok scroll
####################

async def get_tiktok_results(keyword, page=1, count=5):
    try:
        jar = MozillaCookieJar()
        jar.load("tiktok.txt", ignore_discard=True, ignore_expires=True)
    except Exception as e:
        LOGGER.error(f"Cookie error: {e.__class__.__name__}")
        return None, f"ERROR: {e.__class__.__name__}", 0, 0
    
    cookies = {}
    for cookie in jar:
        cookies[cookie.name] = cookie.value
        
    offset = (page - 1) * count
    
    params = {
        "aid": 1988,
        "app_language": "en",
        "app_name": "tiktok_web",
        "browser_language": "en-US",
        "browser_name": "Mozilla",
        "browser_online": True,
        "browser_platform": "Win32",
        "browser_version": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
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
        "offset": offset,
        "os": "windows",
        "priority_region": "id",
        "referer": "",
        "region": "id",
        "screen_height": 1080,
        "screen_width": 1920,
        "search_source": "normal_search",
        "tz_name": "Asia/Jakarta",
        "count": count,
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
    
    try:
        async with httpx.AsyncClient() as client:
            num_retries = 0
            search_data = ""
            
            while len(search_data) == 0 and num_retries < 3:
                num_retries += 1
                response = await client.get(
                    url="https://www.tiktok.com/api/search/item/full/",
                    params=params,
                    cookies=cookies,
                    headers={"User-Agent": choice(user_agents)},
                    timeout=15
                )
                search_data = response.text
            
            data = loads(search_data)
            
            if 'item_list' not in data or len(data['item_list']) == 0:
                return None, f"<b>❌ Tidak ditemukan hasil untuk keyword:</b> <code>{keyword}</code>", 0, 0
            
            total_results = data.get('total', len(data['item_list']))
            total_pages = (total_results + count - 1) // count
            
            results = []
            for item in data['item_list'][:count]:
                video_id = item.get('id', '')
                author = item.get('author', {}).get('uniqueId', 'Unknown')
                nickname = item.get('author', {}).get('nickname', 'Unknown')
                desc = item.get('desc', 'TikTok Video')
                
                stats = {
                    'likes': item.get('stats', {}).get('diggCount', 0),
                    'comments': item.get('stats', {}).get('commentCount', 0),
                    'plays': item.get('stats', {}).get('playCount', 0),
                    'shares': item.get('stats', {}).get('shareCount', 0)
                }
                
                thumb = None
                if 'coverLarger' in item:
                    thumb = item['coverLarger']
                elif 'cover' in item:
                    thumb = item['cover']
                    
                duration = 15
                if 'video' in item and 'duration' in item['video']:
                    duration = item['video']['duration']
                    
                video_url = f"https://www.tiktok.com/@{author}/video/{video_id}"
                
                results.append({
                    'id': video_id,
                    'author': author,
                    'nickname': nickname,
                    'desc': desc,
                    'stats': stats,
                    'thumb': thumb,
                    'url': video_url,
                    'duration': duration
                })
            
            return results, None, page, total_pages
    except Exception as e:
        LOGGER.error(f"Error in TikTok search: {str(e)}")
        return None, f"<b>❌ Error:</b> {str(e)}", 0, 0

async def tiktok_paginated_search(_, message):
    uid = message.from_user.id
    
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
        is_random = False
    else:
        popular_tags = [
            "fyp", "viral", "trending", "dance", "comedy", "music", "funny",
            "challenge", "fashion", "food", "beauty", "foryou", "foryoupage", 
            "tiktok", "indonesia", "anime", "gaming", "memes", "fitness"
        ]
        keyword = choice(popular_tags)
        is_random = True
    
    loading_text = "<b>⌛️ Sedang mencari video TikTok"
    if is_random:
        loading_text += " random"
    loading_text += f"...</b>\n\n<code>🔎 {keyword}</code>"
    
    mess = await sendMessage(message, loading_text)
    
    try:
        results, error_msg, page, total_pages = await get_tiktok_results(keyword)
        
        if error_msg:
            await editMessage(mess, error_msg)
            await asyncio.sleep(5)
            await deleteMessage(mess)
            return
        
        if not results or len(results) == 0:
            await editMessage(mess, f"<b>❌ Tidak ditemukan hasil untuk:</b> <code>{keyword}</code>")
            await asyncio.sleep(5)
            await deleteMessage(mess)
            return
            
        video = results[0]
        
        msg = f"<b>🔰 {config_dict.get('BOT_NAME', 'TikTok Search')}</b>\n\n"
        msg += f"<b>🎬 Video:</b>\n<code>{video['desc']}</code>\n\n"
        msg += f"<b>⏱️ Duration:</b> <code>{format_duration(video['duration'])}</code>\n"
        msg += f"<b>💾 Size:</b> <code>{get_file_size(video['duration'])}</code> (720p)\n\n"
        msg += f"<b>👤 Creator:</b> <code>{video['nickname']} (@{video['author']})</code>\n"
        msg += f"<b>❤️ Likes:</b> <code>{format_count(video['stats']['likes'])}</code>\n"
        msg += f"<b>👁️ Views:</b> <code>{format_count(video['stats']['plays'])}</code>\n"
        msg += f"<b>💬 Comments:</b> <code>{format_count(video['stats']['comments'])}</code>\n\n"
        msg += f"<b>Halaman {page} dari {total_pages}</b>"
        
        butt = ButtonMaker()
        
        if page > 1:
            butt.ibutton("◀️ Prev", f"ttsearch prev {uid} {page} {keyword}")
        else:
            butt.ibutton("◀️", f"ttsearch none {uid}")
            
        butt.ibutton("🔗 Join", f"ttsearch join {uid}")
        
        if page < total_pages:
            butt.ibutton("Next ▶️", f"ttsearch next {uid} {page} {keyword}")
        else:
            butt.ibutton("▶️", f"ttsearch none {uid}")
        
        butt.ibutton("⛔️ Close", f"ttsearch close {uid}")
        
        butts = butt.build_menu(3, 1)
        
        tiktok_searches[uid] = {
            "keyword": keyword,
            "page": page,
            "total_pages": total_pages,
            "results": results,
            "message": message,
            "current_video": video
        }
        
        await deleteMessage(mess)
        
        if video['thumb']:
            sent_msg = await message.reply_photo(
                photo=video['thumb'],
                caption=msg,
                reply_markup=butts
            )
        else:
            sent_msg = await message.reply_photo(
                photo="https://telegra.ph/file/9ac54179d1dbbdd3490d5.jpg",
                caption=msg,
                reply_markup=butts
            )
            
        tiktok_searches[uid]["sent_message"] = sent_msg
        
    except Exception as e:
        LOGGER.error(f"TikTok search error: {str(e)}")
        await editMessage(mess, f"<b>❌ Error:</b> {str(e)}")
        await asyncio.sleep(5)
        await deleteMessage(mess)

async def tiktok_search_callback(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    
    action = data[1]
    uid = int(data[2])
    
    if uid not in tiktok_searches:
        return await query.answer("Tugas tidak ditemukan atau sudah selesai.", show_alert=True)
    
    search_data = tiktok_searches[uid]
    keyword = search_data["keyword"]
    
    is_owner = user_id in config_dict['OWNER_ID']
    is_sudo = user_id in config_dict.get('SUDO_USERS', [])
    
    if not is_owner and not is_sudo and user_id != uid:
        return await query.answer("Bukan tugas Anda!", show_alert=True)
    
    if action == "none":
        await query.answer("Sudah mentok halaman nya.", show_alert=True)
        return
    
    elif action == "close":
        await message.edit_caption("<b>Tugas pencarian dibatalkan.</b>")
        await query.answer("Tugas Dibatalkan.", show_alert=True)
        await asyncio.sleep(2)
        
        try:
            await message.delete()
            
            orig_msg = search_data.get("message")
            if orig_msg:
                try:
                    await orig_msg.delete()
                except:
                    pass
        except:
            pass
        
        if uid in tiktok_searches:
            del tiktok_searches[uid]
        return
    
    elif action == "join":
        butt = ButtonMaker()
        butt.ubutton("🔗 Join Dizzy Project", "https://t.me/DizzyStuffProject")
        butts = butt.build_menu(1)
        
        await message.edit_caption(
            caption=f"<b>📣 Join our channel for updates and more features!</b>\n\n<i>Click the button below to join, then return to your search.</i>",
            reply_markup=butts
        )
        
        search_data["return_from_join"] = True
        return
    
    elif action in ["prev", "next"]:
        await message.edit_caption("<b>⌛️ Loading page...</b>")
        
        current_page = int(data[3])
        
        if action == "prev":
            page = current_page - 1
        else:
            page = current_page + 1
            
        results, error_msg, page, total_pages = await get_tiktok_results(keyword, page=page)
        
        if error_msg:
            await message.edit_caption(error_msg)
            await asyncio.sleep(5)
            if uid in tiktok_searches:
                del tiktok_searches[uid]
            await message.delete()
            return
        
        video = results[0]
        
        search_data.update({
            "page": page,
            "total_pages": total_pages,
            "results": results,
            "current_video": video
        })
        
        msg = f"<b>🔰 {config_dict.get('BOT_NAME', 'TikTok Search')}</b>\n\n"
        msg += f"<b>🎬 Video:</b>\n<code>{video['desc']}</code>\n\n"
        msg += f"<b>⏱️ Duration:</b> <code>{format_duration(video['duration'])}</code>\n"
        msg += f"<b>💾 Size:</b> <code>{get_file_size(video['duration'])}</code> (720p)\n\n"
        msg += f"<b>👤 Creator:</b> <code>{video['nickname']} (@{video['author']})</code>\n"
        msg += f"<b>❤️ Likes:</b> <code>{format_count(video['stats']['likes'])}</code>\n"
        msg += f"<b>👁️ Views:</b> <code>{format_count(video['stats']['plays'])}</code>\n"
        msg += f"<b>💬 Comments:</b> <code>{format_count(video['stats']['comments'])}</code>\n\n"
        msg += f"<b>Halaman {page} dari {total_pages}</b>"
        
        butt = ButtonMaker()
        
        if page > 1:
            butt.ibutton("◀️ Prev", f"ttsearch prev {uid} {page} {keyword}")
        else:
            butt.ibutton("◀️", f"ttsearch none {uid}")
            
        butt.ibutton("🔗 Join", f"ttsearch join {uid}")
        
        if page < total_pages:
            butt.ibutton("Next ▶️", f"ttsearch next {uid} {page} {keyword}")
        else:
            butt.ibutton("▶️", f"ttsearch none {uid}")
        
        butt.ibutton("⛔️ Close", f"ttsearch close {uid}")
        
        butts = butt.build_menu(3, 1)
        
        try:
            if video['thumb']:
                await message.edit_media(
                    media=InputMediaPhoto(
                        media=video['thumb'],
                        caption=msg
                    ),
                    reply_markup=butts
                )
            else:
                await message.edit_caption(caption=msg, reply_markup=butts)
        except Exception as e:
            LOGGER.error(f"Error updating search: {e}")
            await message.edit_caption(caption=msg, reply_markup=butts)


####################
## Auto TikTok Download
####################

async def auto_tk(client, message):
    user_id = message.from_user.id
    isi = {user_id: message}
    tiktok.append(isi)
    msg = f"<b>Link Tiktok terdeteksi, silahkan pilih untuk download Media atau Audio saja...</b>"
    user_id = message.from_user.id
    butt = ButtonMaker()
    butt.ibutton("🎞 Media", f"tiktok media {user_id}")
    butt.ibutton("🎞 No WM", f"tiktok nowm {user_id}")
    butt.ibutton("🔈 Audio", f"tiktok audio {user_id}")
    butt.ibutton("⛔️ Batal", f"tiktok cancel {user_id}", "footer")
    butts = butt.build_menu(2)
    await sendMessage(message, msg, butts)

####################

async def tk_query(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    uid = int(data[2])
    
    tk_msg = None
    for isi in tiktok:
        if uid in isi:
            tk_msg = isi
            break
    
    if not tk_msg or uid not in tk_msg:
        return await query.answer(text="Tugas tidak ditemukan", show_alert=True)
    
    is_owner = user_id in config_dict['OWNER_ID']
    is_sudo = user_id in config_dict.get('SUDO_USERS', [])
    
    if not is_owner and not is_sudo and user_id != uid:
        return await query.answer(text="Bukan Tugas Anda!", show_alert=True)
    
    orig_msg = tk_msg[uid]
    text = orig_msg.text
    urls = re.findall(r"https?://[^\s]+", text)
    
    if not urls:
        await editMessage(message, "<b>Tidak dapat menemukan URL TikTok</b>")
        await query.answer(text="Tugas Dibatalkan.", show_alert=True)
        await asyncio.sleep(2)
        await deleteMessage(message)
        del tk_msg[uid]
        return
        
    tk_url = urls[0]
    
    if data[1] == "media":
        await editMessage(message, "<b>Tugas pencarian dibatalkan.</b>")
        await asyncio.sleep(2)
        await deleteMessage(message)
        del tk_msg[uid]
        await tiktokdl(bot, orig_msg, url=tk_url, type="video")
    
    elif data[1] == "nowm":
        await editMessage(message, "<b>Tugas pencarian dibatalkan.</b>")
        await asyncio.sleep(2)
        await deleteMessage(message)
        del tk_msg[uid]
        await tiktokdl(bot, orig_msg, url=tk_url, type="nowm")
    
    elif data[1] == "audio":
        await editMessage(message, "<b>Tugas pencarian dibatalkan.</b>")
        await asyncio.sleep(2)
        await deleteMessage(message)
        del tk_msg[uid]
        await tiktokdl(bot, orig_msg, url=tk_url, audio=True)
    
    elif data[1] == "cancel":
        await editMessage(message, "<b>Tugas pencarian dibatalkan.</b>")
        await query.answer(text="Tugas Dibatalkan.", show_alert=True)
        await asyncio.sleep(2)
        await deleteMessage(message)
        del tk_msg[uid]

#######################
# Register Handlers
#######################

bot.add_handler(
    MessageHandler(
        tiktok_paginated_search, 
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
            r'^tiktok\s'
        )
    )
)

bot.add_handler(
    CallbackQueryHandler(
        tiktok_search_callback,
        filters=regex(
            r'^ttsearch\s'
        )
    )
)