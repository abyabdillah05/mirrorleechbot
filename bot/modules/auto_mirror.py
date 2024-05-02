from bot import bot
from asyncio import sleep as asleep
from pyrogram import filters
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from bot.modules.mirror_leech import Mirror
from bot.modules.clone import Clone
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.modules.ytdlp import YtDlp
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.links_utils import is_gdrive_link, is_magnet, is_mega_link
from urllib.parse import urlparse

#Auto Detect Mirror by: Pikachu
#https://github.com/aenulrofik

urlregex = r"^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$"
magnetregex = r"magnet:\?xt=urn:(btih|btmh):[a-zA-Z0-9]*\s*"
cache = []
async def auto_mirror(client, message):
    user_id = message.from_user.id
    caches = {
        user_id: message
    }
    cache.append(caches)
    if message.caption is not None:
        text = message.caption
    else:
        text = message.text
    urls = text
    domain = urlparse(urls).hostname
    if ' ' in urls.strip() or len(urls.split()) != 1:
        pass
    if any(
        x in domain
        for x in [
            "youtube.com",
            "youtu.be",
            "instagram.com",
            "facebook.com",
            "tiktok.com",
            "twitter.com"
            "x.com"
        ]
    ):
        pass
    else: 
        for caches in cache:
            if user_id in caches:
                msgs = caches
        msg, buttons = await msg_button(urls, user_id)
        mess = await sendMessage(message, msg, buttons)
        await asleep(30)
        await editMessage(mess, "Waktu habis, tugas dibatalkan")
        try:
            del msgs[user_id]
        except:
            pass
    
async def msg_button(url, user_id):
    uid = user_id
    if is_magnet(url):
        msg = f"<b>Link Magnet Terdeteksi pada pesan anda...</b>\n\nApakah anda mau Mirror/Leech dengan Qbittorent ?"
        butt = ButtonMaker()
        butt.ibutton("☁️ Mirror", f"auto qbit mirror {uid} none")
        butt.ibutton("☀️ Leech", f"auto qbit leech {uid} none")
        butt.ibutton("⛔️ Batal", f"auto cancel all {uid} none")
        butts = butt.build_menu(2)
        return msg, butts
    elif is_gdrive_link(url):
        msg = f"<b>Link Google Drive Terdeteksi pada pesan anda...</b>\n\nApakah anda mau Clone/Leech ?"
        butt = ButtonMaker()
        butt.ibutton("☁️ Clone", f"auto gd clone {uid} none")
        butt.ibutton("☀️ Leech", f"auto gd leech {uid} none")
        butt.ibutton("⛔️ Batal", f"auto cancel all {uid} none")
        butts = butt.build_menu(2)
        return msg, butts
    elif is_mega_link(url):
        msg = f"<b>Link Mega Terdeteksi pada pesan anda...\n\n</b>Apakah anda mau Mirror/Leech ?\n\n<blockquote><b>⚠️Note:</b> Mega Free Acc hanya memberikan limit quota 5GB/6Jam jadi tolong jangan diabuse, jika task anda stuck artinya quota sudah habis.</blockquote>"
        butt = ButtonMaker()
        butt.ibutton("☁️ Mirror", f"auto mega mirror {uid} none")
        butt.ibutton("☀️ Leech", f"auto mega leech {uid} none")
        butt.ibutton("⛔️ Batal", f"auto cancel all {uid} none")
        butts = butt.build_menu(2)
        return msg, butts
    else:
        msg = f"<b>Sebuah Link terdeteksi di pesan anda...</b>\n\nApakah anda mau Mirror/Leech dengan Aria2 atau Yt-Dlp ?"
        butt = ButtonMaker()
        butt.ibutton("☁️ Mirror", f"auto direct mirror {uid} none")
        butt.ibutton("☀️ Leech", f"auto direct leech {uid} none")
        butt.ibutton("⛔️ Batal", f"auto cancel all {uid} none")
        butts = butt.build_menu(2)
        return msg, butts

async def auto_query(_, query):   
    user_id = query.from_user.id
    message = query.message
    data = query.data.split()
    uid = int(data[3])
    for caches in cache:
        if uid in caches:
            msgs = caches
            msg = msgs[uid]
            auto_url = msg.text
    if user_id != uid:
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)

    elif data[1] == "direct":
        if data[2] == "mirror":
            mess = f"Silahkan pilih engine untuk mirror link anda, jika tidak yakin, pilih saja <b>Mirror dengan Aria2</b>"
            butt = ButtonMaker()
            butt.ibutton("⚙️ Aria2", f"auto direct mirror {uid} aria2")
            butt.ibutton("⚙️ Yt-Dlp", f"auto direct mirror {uid} ytdl")
            butt.ibutton("↩️ Kembali", f"auto direct mirror {uid} back")
            butt.ibutton("⛔️ Batal", f"auto cancel none {uid} none")
            butts = butt.build_menu(2)
            await editMessage(message, mess, butts)
            if data[4] == "aria2":
                Mirror(bot, msg, auto_url=auto_url).newEvent()
                del msgs[uid]
                await deleteMessage(message)
            elif data[4] == "ytdl":
                YtDlp(bot, msg, yturl=auto_url).newEvent()
                del msgs[uid]
                await deleteMessage(message)
            elif data[4] == "back":
                mss, buttons = await msg_button(auto_url, uid)
                await editMessage(message, mss, buttons)

        elif data[2] == "leech":
            mess = f"Silahkan pilih engine untuk leech link anda, jika tidak yakin, pilih saja <b>Aria2</b>"
            butt = ButtonMaker()
            butt.ibutton("⚙️ Aria2", f"auto direct leech {uid} aria2")
            butt.ibutton("⚙️ Yt-Dlp", f"auto direct leech {uid} ytdl")
            butt.ibutton("↩️ Kembali", f"auto direct leech {uid} back")
            butt.ibutton("⛔️ Batal", f"auto cancel none {uid} none")
            butts = butt.build_menu(2)
            await editMessage(message, mess, butts)
            if data[4] == "aria2":
                Mirror(bot, msg, auto_url=auto_url, isLeech=True).newEvent()
                del msgs[uid]
                await deleteMessage(message)
            elif data[4] == "ytdl":
                YtDlp(bot, msg, yturl=auto_url, isLeech=True).newEvent()
                del msgs[uid]
                await deleteMessage(message)
            elif data[4] == "back":
                mss, buttons = await msg_button(auto_url, uid)
                await editMessage(message, mss, buttons)

    elif data[1] == "qbit":
        if data[2] == "mirror":
            Mirror(bot, msg, auto_url=auto_url, isQbit=True).newEvent()
            del msgs[uid]
            await deleteMessage(message)
        if data[2] == "leech":
            Mirror(bot, msg, auto_url=auto_url, isQbit=True, isLeech=True).newEvent()
            del msgs[uid]
            await deleteMessage(message)
    elif data[1] == "gd":
        if data[2] == "clone":
            Clone(bot, msg, auto_url=auto_url).newEvent()
            del msgs[uid]
            await deleteMessage(message)
        if data[2] == "leech":
            Mirror(bot, msg, auto_url=auto_url, isQbit=True, isLeech=True).newEvent()
            del msgs[uid]
            await deleteMessage(message)
    elif data[1] == "mega":
        if data[2] == "mirror":
            Mirror(bot, message, auto_url=auto_url).newEvent()
            del msgs[uid]
            await deleteMessage(message)
        if data[2] == "leech":
            Mirror(bot, msg, auto_url=auto_url, isQbit=True, isLeech=True).newEvent()
            del msgs[uid]
            await deleteMessage(message)
    else:
        await query.answer(text="Tugas Dibatalkan", show_alert=True)
        del msgs[uid]
        await deleteMessage(message)

bot.add_handler(
    CallbackQueryHandler(
        auto_query,
        filters=regex(
            r'^auto'
        )
    )
)

bot.add_handler(
    MessageHandler(
        auto_mirror,
        filters=CustomFilters.authorized
        & filters.regex(
            f"{urlregex}|{magnetregex}"
        )
    )
)