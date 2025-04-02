import httpx
from html import escape
from urllib.parse import quote
import time

####################################
## Import Libraries From Pyrogram ##
####################################

from pyrogram.filters import (command,
                              regex)
from pyrogram.types import (InputMediaPhoto,
                            InputMediaVideo)
from pyrogram.handlers import (MessageHandler,
                               CallbackQueryHandler)

###################################
## Import Variables From Project ##
###################################

from bot import (bot,
                 LOGGER)
from bot.modules.ytdlp import YtDlp
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      editMessage,
                                                      deleteMessage)

############################
## Requirements Variables ##
############################
## You can change API_KEY to your own API Key ##
## https://developers.google.com/youtube/v3/getting-started ##

youtube = {}
API_KEY = "AIzaSyBmQVnzf5khHZE8GSbVzNmVefzPFGPW7aU"
BOT_NICKNAME = bot.get_me().first_name

#########################################
## Helper Functions For Youtube Search ##
#########################################

async def format_duration(duration):
    if not duration:
        return "Tidak diketahui"
        
    duration = duration[2:]  # Remove PT prefix
    duration = duration.replace("H", " jam ")
    duration = duration.replace("M", " menit ")
    duration = duration.replace("S", " detik")
    return duration.strip()

async def format_number(number):
    try:
        return f"{int(number):,}".replace(",", ".")
    except:
        return "Tidak diketahui"

async def truncate_text(text, max_length=150):
    if not text:
        return "Tidak ada deskripsi"
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."

#####################################
## Yt Request | Credit @aenulrofik ##
#####################################

async def yt_search_request(keyword, max_results=40):
    try:
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={quote(keyword)}&type=video&regionCode=ID&maxResults={max_results}&key={API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url)
            data = response.json()
        
        results = []
        if "items" in data:
            for item in data["items"]:
                if "videoId" in item["id"]:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    channel = item["snippet"]["channelTitle"]
                    thumbnail = item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", "")
                    description = item["snippet"].get("description", "")
                    
                    results.append({
                        'title': title,
                        'id': video_id,
                        'channel': channel,
                        'thumbnail': thumbnail,
                        'description': description
                    })
                    
                    if len(results) >= max_results:
                        break
        
        return results
    except Exception as e:
        LOGGER.error(f"Error in YouTube search: {str(e)}")
        return []

#####################################
## Yt Extract | Credit @aenulrofik ##
#####################################

async def get_video_details(video_id):
    try:
        video_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=contentDetails,snippet,statistics&key={API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            data = response.json()
        
        details = {}
        if "items" in data and data["items"]:
            item = data["items"][0]
            details = {
                'video_id': item["id"],
                'title': item["snippet"]["title"],
                'channel_title': item["snippet"]["channelTitle"],
                'description': item["snippet"].get("description", "Tidak ada deskripsi"),
                'thumbnail_url': item["snippet"]["thumbnails"].get("maxres", 
                                    item["snippet"]["thumbnails"].get("high", 
                                    item["snippet"]["thumbnails"].get("medium", 
                                    item["snippet"]["thumbnails"].get("default", 
                                    {"url": "https://telegra.ph/file/5e7fde2b232ae1b682625.jpg"}))))["url"],
                'duration': item["contentDetails"].get("duration", ""),
                'view_count': item["statistics"].get("viewCount", "0"),
                'like_count': item["statistics"].get("likeCount", "0"),
                'published_at': item["snippet"].get("publishedAt", "")
            }
            
        return details
    except Exception as e:
        LOGGER.error(f"Error fetching video details: {str(e)}")
        return {
            'video_id': video_id,
            'title': "Tidak dapat mengambil detail video",
            'channel_title': "Tidak diketahui",
            'description': "Terjadi kesalahan saat mengambil informasi video.",
            'thumbnail_url': "https://telegra.ph/file/5e7fde2b232ae1b682625.jpg",
            'duration': "",
            'view_count': "0",
            'like_count': "0"
        }

####################################
## Yt Search | Credit @aenulrofik ##
####################################

async def yt_search(client, message):
    uid = message.from_user.id
    user_name = message.from_user.first_name
    
    if len(message.command) > 1:
        keyword = ' '.join(message.command[1:])
    else:
        await sendMessage(message, "<b>📝 Silahkan masukkan kata kunci pencarian!</b>\n\n<i>Contoh: <code>/yts music video</code></i>")
        return

    progress_msg = await sendMessage(message, f"<b>🔍 Mencari video dengan kata kunci:</b> <code>{escape(keyword)}</code>\n<i>Mohon tunggu sebentar...</i>")
    
    if uid in youtube:
        await deleteMessage(progress_msg)
        butt = ButtonMaker()
        butt.ibutton("⛔️ Batalkan Pencarian Sebelumnya", f"youtube cancel {uid}")
        butts = butt.build_menu(1)
        await sendMessage(message, "<b>⚠️ Anda memiliki sesi pencarian yang aktif!</b>\n<i>Silahkan selesaikan atau batalkan proses sebelumnya.</i>", butts)
        return
    
    search_results = await yt_search_request(keyword)
    
    if not search_results:
        await editMessage(progress_msg, f"<b>❌ Tidak ditemukan hasil untuk:</b> <code>{escape(keyword)}</code>\n<i>Silahkan coba dengan kata kunci lain.</i>")
        return
    
    youtube[uid] = {
        "message": message,
        "keyword": keyword,
        "results": search_results,
        "current_page": 0,
        "total_results": len(search_results)
    }
    
    # Show first result
    await show_video_page(progress_msg, uid, user_name)

async def show_video_page(message, uid, user_name=None):
    if uid not in youtube:
        await editMessage(message, "<b>❌ Sesi pencarian tidak ditemukan!</b>")
        return
    
    session = youtube[uid]
    page = session["current_page"]
    results = session["results"]
    
    if not results:
        await editMessage(message, "<b>❌ Tidak ada hasil pencarian!</b>")
        return
    
    video = results[page]
    video_id = video["id"]
    
    try:
        details = await get_video_details(video_id)
        
        msg = f"<b>🎬 Judul:</b> <code>{escape(details['title'])}</code>\n\n"
        msg += f"<b>📢 Channel:</b> <code>{escape(details['channel_title'])}</code>\n"
        msg += f"<b>⏱ Durasi:</b> <code>{await format_duration(details['duration'])}</code>\n\n"
        
        msg += f"<b>👁 Views:</b> <code>{await format_number(details['view_count'])}</code>\n"
        msg += f"<b>👍 Likes:</b> <code>{await format_number(details['like_count'])}</code>\n\n"
        
        msg += f"<b>📝 Deskripsi:</b>\n<i>{escape(await truncate_text(details['description']))}</i>\n\n"
        
        if user_name:
            msg += f"<b>🔍 Pencarian oleh:</b> {user_name}\n"
        msg += f"<b>⚡ Powered by:</b> {BOT_NICKNAME}"
        
        butt = ButtonMaker()
        
        if page > 0:
            butt.ibutton("⬅️ Sebelumnya", f"youtube prev {uid}", "header")
        
        if page < len(results) - 1:
            butt.ibutton("Selanjutnya ➡️", f"youtube next {uid}", "header")
        
        butt.ibutton("☁️ Mirror", f"youtube mirror {uid} {video_id}")
        butt.ibutton(f"{page+1}/{len(results)}", f"youtube info {uid}")
        butt.ibutton("☀️ Leech", f"youtube leech {uid} {video_id}")
        
        butt.ibutton("⛔️ Batalkan", f"youtube cancel {uid}", position="footer")
        
        buttons = butt.build_menu(3)
        
        try:
            new_media = InputMediaPhoto(details['thumbnail_url'], caption=msg)
            await message.edit_media(new_media, reply_markup=buttons)
        except Exception as e:
            LOGGER.error(f"Error setting thumbnail: {str(e)}")
            fallback_media = InputMediaPhoto("https://telegra.ph/file/5e7fde2b232ae1b682625.jpg", caption=msg)
            await message.edit_media(fallback_media, reply_markup=buttons)
            
    except Exception as e:
        LOGGER.error(f"Error in show_video_page: {str(e)}")
        await editMessage(message, f"<b>❌ Terjadi kesalahan:</b>\n<code>{str(e)}</code>")
        if uid in youtube:
            del youtube[uid]

async def yt_query(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    action = data[1]
    uid = int(data[2])
    
    if user_id != uid:
        return await query.answer(text="⚠️ Bukan pencarian Anda! Silahkan buat pencarian sendiri.", show_alert=True)
    
    if uid not in youtube and action not in ["cancel"]:
        await query.answer(text="⚠️ Sesi pencarian telah kedaluwarsa! Silahkan mulai pencarian baru.", show_alert=True)
        await deleteMessage(message)
        return
    
    if action == "next":
        youtube[uid]["current_page"] += 1
        await query.answer("⏩ Menampilkan video berikutnya")
        await show_video_page(message, uid)
        
    elif action == "prev":
        youtube[uid]["current_page"] -= 1
        await query.answer("⏪ Menampilkan video sebelumnya")
        await show_video_page(message, uid)
        
    elif action == "info":
        current = youtube[uid]["current_page"] + 1
        total = youtube[uid]["total_results"]
        keyword = youtube[uid]["keyword"]
        await query.answer(f"📊 Menampilkan hasil {current} dari {total} untuk '{keyword}'", show_alert=True)
        
    elif action == "mirror" or action == "leech":
        video_id = data[3]
        is_leech = action == "leech"
        
        try:
            orig_msg = youtube[uid]["message"]
            
            YtDlp(
                bot, 
                orig_msg, 
                yturl=f"https://www.youtube.com/watch?v={video_id}", 
                isLeech=is_leech
            ).newEvent()
            
            task_type = "Leech" if is_leech else "Mirror"
            await query.answer(f"✅ {task_type} dimulai! Silahkan periksa status tugas.", show_alert=True)
            
            await deleteMessage(message)
            if uid in youtube:
                del youtube[uid]
                
        except Exception as e:
            LOGGER.error(f"Error starting {'leech' if is_leech else 'mirror'}: {str(e)}")
            await query.answer(f"❌ Gagal memulai tugas: {str(e)}", show_alert=True)
        
    elif action == "cancel":
        await query.answer("🛑 Pencarian dibatalkan!")
        
        try:
            await deleteMessage(message)
        except:
            pass
        
        await sendMessage(message, "<b>🚫 Pencarian Youtube telah dibatalkan")
        if uid in youtube:
            try:
                orig_msg = youtube[uid]["message"]
                await deleteMessage(orig_msg)
            except Exception as e:
                LOGGER.error(f"Error deleting original command: {str(e)}")
            
            del youtube[uid]

####################################################
## Youtube Search Command & CallbackQuery Handler ##
####################################################

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

## Enhanced by @WzdDizzyFlasherr with pagination, better UI, and more video details ##