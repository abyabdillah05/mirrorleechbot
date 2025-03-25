from aiofiles.os import remove as aioremove, path as aiopath
from bot import bot
from pyrogram import filters
from pyrogram.filters import command, regex, user
from pyrogram.handlers import CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.ext_utils.links_utils import is_gdrive_link, is_magnet, is_mega_link, is_url
from bot.helper.ext_utils.bot_utils import (
    new_task,
    new_thread,
)
from bot.helper.ext_utils.media_utils import createThumb
from functools import partial
from time import time
import re
import asyncio
from asyncio import wait_for, Event, wrap_future
from bot.helper.ext_utils.status_utils import get_readable_file_size, get_readable_time

#Auto Detect Mirror by: Pikachu
#https://github.com/aenulrofik

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()

    if data[1] =="leech" or data[1] == "mirror":
        await obj.send_sub_pesan(data[1])

    elif data[1] == "rename":
        msg = f"<b>Silahkan masukkan Nama Baru untuk file anda!</b>\n\n❗️ <i>Klik <b>/batal</b> untuk membatalkan.</i>"
        await obj.update_dict(msg, data[1])
    elif data[1] == "custom_upload":
        await obj.select_upload()
    elif data[1] == "zip":
        msg = f"<b>Silahkan masukkan Password untuk membuat file ZIP anda!</b>\n\n<i>❗️ Klik <b>/skip</b> untuk membuat zip tanpa password.</i>"
        await obj.update_dict(msg, data[1])
    elif data[1] == "extract":
        msg = f"<b>Silahkan masukkan Password untuk extract file anda!</b>\n\n❗️ Klik <b>/skip</b> jika file tidak menggunakan password."
        await obj.update_dict(msg, data[1])
    
    elif data[1] == "custom_thumb":
        await obj.thumbnail()
    
    elif data[1] == "ss":
        await obj.set_dict_ss()
    elif data[1] == "sv":
        await obj.set_dict_sv()
        
    elif data[1] == "start_leech":
        await obj.start_leech()

    elif data[1] == "start_mirror":
        await obj.start_mirror()
    
    elif data[1] == "cu_buzzheavier":
        obj._auto_args["custom_upload"] = "buzzheavier"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_pixeldrain":
        obj._auto_args["custom_upload"] = "pixeldrain"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_gofile":
        obj._auto_args["custom_upload"] = "gofile"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_gdrive":
        obj._auto_args["custom_upload"] = "gd"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_rclone":
        obj._auto_args["custom_upload"] = "rc"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_gdrive_user":
        obj._auto_args["custom_upload"] = "gdl"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_rclone_user":
        obj._auto_args["custom_upload"] = "rcl"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_default":
        del obj._auto_args["custom_upload"]
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_back":
        await obj.send_sub_pesan("mirror")

    elif data[1] == "back":
        await obj.back()

    elif data[1] == "help":
        await obj.help()

    elif data[1] == "cancel":
        await editMessage(message, "<b>Tugas dibatalkan oleh User!</b>")
        obj.is_cancelled = True
        obj.event.set()
        
@new_task
async def home_button(url=None, message=None):
    butt = ButtonMaker()
    media_info = {}
    
    if url is None and message is not None:
        if message.text:
            urls = re.findall(r'https?://[^\s]+', message.text)
            if urls:
                url = urls[0]
        
        media_info = extract_media_info(message)
    
    if url and (is_url(url) or is_magnet(url)):
        platform = detect_url_platform(url)
        
        msg = f"<b>🔎 Link {platform['name']} terdeteksi di pesan Anda</b>\n\n"
        
        if platform['description']:
            msg += f"<i>{platform['description']}</i>\n\n"
            
        msg += "<i>Silahkan pilih aksi yang diinginkan:</i>"
        
        butt.ibutton("☁️ Mirror", f"auto mirror")
        butt.ibutton("☀️ Leech", f"auto leech")
        
        if platform['special_buttons']:
            for button in platform['special_buttons']:
                butt.ibutton(button['label'], button['callback'])
    
    elif media_info and media_info['type']:
        file_type = media_info['type']
        file_name = media_info.get('file_name', 'Tidak ada nama')
        file_size = media_info.get('file_size', 0)
        
        readable_size = get_readable_file_size(file_size) if file_size else "Unknown size"
        
        msg = f"<b>📁 {file_type.capitalize()} terdeteksi pada pesan Anda</b>\n\n"
        msg += f"<b>Nama:</b> <code>{file_name}</code>\n"
        msg += f"<b>Ukuran:</b> <code>{readable_size}</code>\n\n"
        
        if file_type == 'video':
            duration = media_info.get('duration', 0)
            if duration:
                readable_duration = get_readable_time(duration)
                msg += f"<b>Durasi:</b> <code>{readable_duration}</code>\n\n"
        
        msg += "<i>Silahkan pilih aksi yang diinginkan:</i>"
        
        butt.ibutton("☁️ Mirror", f"auto mirror")
        butt.ibutton("☀️ Leech", f"auto leech")
        
        if file_type == 'video':
            butt.ibutton("🎬 Edit Video", f"auto video_edit")
    
    else:
        msg = "<b>🔍 Silahkan pilih aksi yang diinginkan:</b>"
        butt.ibutton("☁️ Mirror", f"auto mirror")
        butt.ibutton("☀️ Leech", f"auto leech")
    
    butt.ibutton("⛔️ Batal", f"auto cancel")
    butts = butt.build_menu(2)
    
    return msg, butts

def extract_media_info(message): 
    info = {'type': None, 'file_name': None, 'file_size': None}
    
    if message.document:
        info['type'] = 'document'
        info['file_name'] = message.document.file_name
        info['file_size'] = message.document.file_size
        info['mime_type'] = message.document.mime_type
        
    elif message.video:
        info['type'] = 'video'
        info['file_name'] = message.video.file_name
        info['file_size'] = message.video.file_size
        info['duration'] = message.video.duration
        info['width'] = message.video.width
        info['height'] = message.video.height
        
    elif message.audio:
        info['type'] = 'audio'
        info['file_name'] = message.audio.file_name
        info['file_size'] = message.audio.file_size
        info['duration'] = message.audio.duration
        
    elif message.photo:
        info['type'] = 'photo'
        # Use the largest photo
        photo = message.photo[-1]
        info['file_size'] = photo.file_size
        info['width'] = photo.width
        info['height'] = photo.height
    
    return info

def detect_url_platform(url):
    platform = {
        'name': 'URL',
        'description': '',
        'special_buttons': []
    }
    
    if 'youtube.com' in url or 'youtu.be' in url:
        platform['name'] = 'YouTube'
        platform['description'] = 'Video YouTube dapat diunduh dalam berbagai format dan kualitas.'
        platform['special_buttons'] = [
            {'label': '🎬 YT-DLP', 'callback': 'auto ytdl'},
            {'label': '🎵 Audio', 'callback': 'auto ytdl_audio'}
        ]
        
    elif is_magnet(url) or url.endswith('.torrent'):
        platform['name'] = 'Torrent'
        platform['description'] = 'File torrent akan diunduh menggunakan qBittorrent.'
        platform['special_buttons'] = [
            {'label': '🧲 Qbit', 'callback': 'auto qbit'}
        ]
        
    elif 'drive.google.com' in url:
        platform['name'] = 'Google Drive'
        platform['description'] = 'File Google Drive dapat dimirror atau dileech.'
        
    elif 'mediafire.com' in url:
        platform['name'] = 'MediaFire'
        
    else:
        platform['name'] = 'URL'
        platform['description'] = 'Link akan diproses menggunakan Direct Link Generator.'
    
    return platform


class AutoMirror:
    def __init__(self, listener):
        self._listener = listener
        self._reply_to = None
        self._sub_pesan = None
        self._time = time()
        self._timeout = 160
        self.event = Event()
        self._auto_args = {}
        self.auto_mode = False
        self.is_cancelled = False
        self._type = None
        self._url = None
        self.gofile = False
        self.buzzheavier = False

    @new_thread
    async def _event_handler(self):
        pfunc = partial(main_select, obj=self)
        handler = self._listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^auto") & user(self._listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except:
            await editMessage(self._reply_to, "<b>Waktu habis, Tugas dibatalkan!</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
            
    async def main_pesan(self, url, type=None):
        if type:
            self._type = type
        self._url = url
        future = self._event_handler()
        msg, buttons = await home_button(self._url)
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        self._reply_to = await sendMessage(self._listener.message, msg, buttons)

        await wrap_future(future)
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self._auto_args
    
    async def main_pesan_custom(self, url, type, gofile=False, buzzheavier=False, pixeldrain=False):
        if type:
            self._type = type
        if gofile:
            self.gofile = True
            self._auto_args["custom_upload"] = "gofile"
        elif buzzheavier:
            self.buzzheavier = True
            self._auto_args["custom_upload"] = "buzzheavier"
        elif pixeldrain:
            self.pixeldrain = True
            self._auto_args["custom_upload"] = "pixeldrain"
        self._url = url
        future = self._event_handler()
        msg, buttons = await self.sub_button()
        self._reply_to = await sendMessage(self._listener.message, msg, buttons)

        await wrap_future(future)
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self._auto_args
    
    async def sub_button(self):
        auto_args = self._auto_args
        cust_up = auto_args.get("custom_upload", None)
        cust_thumb = auto_args.get("custom_thumb", None)
        rename = auto_args.get("rename", None)
        extract = auto_args.get("extract", None)
        zip = auto_args.get("zip", None)
        mess = "<b>📌 Pilih option untuk tugas anda ?</b>\n\n"
        if rename:
            mess += f"<b>✓ Nama Baru:</b> <code>{rename}</code>\n"
        if extract:
            if extract is True:
                mess += f"<b>✓ Extract:</b> <code>Tanpa password</code>\n"
            else:
                mess += f"<b>✓ Passw extract:</b> <code>{extract}</code>\n"
        if zip:
            if zip is True:
                mess += f"<b>✓ Membuat Zip:</b> <code>Tanpa password</code>\n"
            else:
                mess += f"<b>✓ Passw ZIP:</b> <code>{zip}</code>\n"
        if cust_up:
            mess += f"<b>✓ Custom Upload:</b> <code>{cust_up}</code>\n"
        if cust_thumb:
            mess += f"<b>✓ Thumbnail:</b> <code>Custom Thumbnail Ditambahkan.</code>\n"
        mess += f"\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        if self._type == "mirror":
            butt.ibutton("▶️ 𝚂𝚝𝚊𝚛𝚝 𝙼𝚒𝚛𝚛𝚘𝚛", f"auto start_mirror", position="header")
        if self._type == "leech":
            butt.ibutton("▶️ 𝚂𝚝𝚊𝚛𝚝 𝚕𝚎𝚎𝚌𝚑", f"auto start_leech", position="header")

        s = "" if "rename" not in auto_args else "✅"
        butt.ibutton(f"Rename {s}", f"auto rename")

        if self._type == "leech":
            s = "" if "custom_thumb" not in auto_args else "✅"
            butt.ibutton(f"Thumbnail {s}", f"auto custom_thumb")
        else:
            if "custom_upload" not in auto_args: s = "--" 
            elif auto_args["custom_upload"] == "gofile": s = "GF"
            elif auto_args["custom_upload"] == "buzzheavier": s = "BH"
            elif auto_args["custom_upload"] == "pixeldrain": s = "PD"
            elif auto_args["custom_upload"] == "rc": s = "RC"
            elif auto_args["custom_upload"] == "gd": s = "GD"
            elif auto_args["custom_upload"] == "rcl": s = "RCL"
            elif auto_args["custom_upload"] == "gdl": s = "GDL"
            butt.ibutton(f"Upload: {s}", f"auto custom_upload")
        
        if not self.gofile and not self.buzzheavier:
            s = "" if "extract" not in auto_args else "✅"
            butt.ibutton(f"Extract {s}", f"auto extract")

            s = "" if "zip" not in auto_args else "✅"
            butt.ibutton(f"Buat ZIP  {s}", f"auto zip")

        # Tambahkan opsi kompresi untuk ZIP
        if "zip" in auto_args and not self.gofile and not self.buzzheavier:
            s = "" if "compress_level" not in auto_args else "✅"
            butt.ibutton(f"Kompresi {s}", f"auto compress_level")

        #s = "❌" if "multi" not in auto_args else "✅"
        #butt.ibutton(f"{s} Multi", f"auto multi")

        #s = "❌" if "bulk" not in auto_args else "✅"
        #butt.ibutton(f"{s} Bulk", f"auto bulk")

        if self._type == "leech":
            s = "" if "ss" not in auto_args else "✅"
            butt.ibutton(f"Screenshot {s}", f"auto ss")
            s = "" if "sv" not in auto_args else "✅"
            butt.ibutton(f"Sample Vid {s}", f"auto sv")

        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"auto back")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"auto cancel")
        butt.ibutton("❓ 𝙱𝚊𝚗𝚝𝚞𝚊𝚗 𝚂𝚒𝚗𝚐𝚔𝚊𝚝", f"auto help", position="footer")
        butts = butt.build_menu(2)
        return mess, butts

    async def send_sub_pesan(self, type):
        self._type = type
        mess, butts = await self.sub_button()
        await editMessage(self._reply_to, mess, butts)
    
    async def select_upload(self):
        msg = "<b>Silahkan pilih custom upload tujuan anda:</b>\n\n"
        msg += "DFL = Kembalikan ke Default\n"
        msg += "BH = Buzzheavier\n"
        msg += "GF = Gofile\n"
        msg += "PD = Pixeldrain\n"
        msg += "RC = Config Rclone Owner\n"
        msg += "GD = Google Drive owner\n"
        msg += "RCL = Config Rclone User\n"
        msg += "GDL = Google Drive User\n"
        but = ButtonMaker()
        but.ibutton("DFL", f"auto cu_default")
        but.ibutton("BH", f"auto cu_buzzheavier")
        but.ibutton("GF", f"auto cu_gofile")
        but.ibutton("PD", f"auto cu_pixeldrain")
        but.ibutton("RC", f"auto cu_rclone")
        but.ibutton("GD", f"auto cu_gdrive")
        but.ibutton("RCL", f"auto cu_rclone_user")
        but.ibutton("GDL", f"auto cu_gdrive_user")
        but.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"auto cu_back")
        butts = but.build_menu(4)
        await editMessage(self._reply_to, msg, butts)
    
    async def update_dict(self, msg, option):
        if f"{option}" not in self._auto_args:
            try:
                ask = await self._reply_to.edit_text(msg)
                respon = await bot.listen(
                    filters=filters.text & filters.user(self._listener.user_id), timeout=30
                    )
            
                if respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    data = respon.text
                    if respon.text == "/skip" or respon.text == f"/skip@{bot.me.username}":
                        data = True
                    upd = {f"{option}": data}
                    self._auto_args.update(upd)
                await respon.delete()
                sub_pesan, sub_buttons = await self.sub_button()
                await editMessage(ask, sub_pesan, sub_buttons)
            except:
                sub_pesan, sub_buttons = await self.sub_button()
                await editMessage(ask, sub_pesan, sub_buttons)
        else:
            del self._auto_args[f"{option}"]
            sub_pesan, sub_buttons = await self.sub_button()
            await editMessage(self._reply_to, sub_pesan, sub_buttons)
    
    async def set_dict_ss(self):
        if "ss" not in self._auto_args:
            upd = {"ss": "8"}
            self._auto_args.update(upd)
            if "sv" in self._auto_args:
                del self._auto_args["sv"]
        else:
            del self._auto_args[f"ss"]
        sub_pesan, sub_buttons = await self.sub_button()
        await editMessage(self._reply_to, sub_pesan, sub_buttons)
    
    async def thumbnail(self):
        if f"custom_thumb" not in self._auto_args:
            try:
                ask = await self._reply_to.edit_text("<b>Silahkan kirimkan photo untuk thumbnail anda !</b>\n\nKlik /batal untuk membatalkan")
                respon = await bot.listen(
                    filters= filters.user(self._listener.user_id), timeout=30
                    )
                if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    try:
                        msg = respon
                        uid = self._listener.user_id
                        thumb = await createThumb(msg, uid, temp=True)
                        upd = {"custom_thumb": thumb}
                        self._auto_args.update(upd)
                    except:
                        pass
                await respon.delete()
                sub_pesan, sub_buttons = await self.sub_button()
                await editMessage(ask, sub_pesan, sub_buttons)
            except:
                sub_pesan, sub_buttons = await self.sub_button()
                await editMessage(ask, sub_pesan, sub_buttons)
        else:
            thumb = self._auto_args["custom_thumb"]
            if aiopath.exists(thumb):
                await aioremove(thumb)
            del self._auto_args["custom_thumb"]
            sub_pesan, sub_buttons = await self.sub_button()
            await editMessage(self._reply_to, sub_pesan, sub_buttons)
    
    async def set_dict_sv(self):
        if "sv" not in self._auto_args:
            upd = {"sv": True}
            self._auto_args.update(upd)
            if "ss" in self._auto_args:
                del self._auto_args["ss"]
        else:
            del self._auto_args["sv"]
        sub_pesan, sub_buttons = await self.sub_button()
        await editMessage(self._reply_to, sub_pesan, sub_buttons)
    
    async def help(self):
        mess = f"""<b>Bantuan Singkat:</b>

<b>• Rename:</b> Mengganti nama file atau folder yang anda mirror atau leech.

<b>• Custom Upload:</b> Mengupload hasil leech anda ke grup atau channel pribadi atau upload hasil mirror ke rclone atau Gdrive pribadi.

<b>• Custom Thumbnail:</b> Memberikan custom thumbnail pada hasil leech.

<b>• Extract:</b> Mengextract file zip.

<b>• Buat Zip:</b> Membuat file anda menjadi arsip ZIP

<b>• Screenshot:</b> Mengambil screenshot random dari video yang anda leech.

<b>• Sample Video:</b> Mengambil sample video random dari video yang anda leech.
        
<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"""
        butt = ButtonMaker()
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"auto {self._type}")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"auto cancel")
        butts = butt.build_menu(2)
        await editMessage(self._reply_to, mess, butts)
    
    async def start_leech(self):
        upd = {"leech": True}
        self._auto_args.update(upd)
        self.event.set()

    async def start_mirror(self):
        self.event.set()

    async def back(self):      
        msg, buttons = await home_button(self._url)
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        await editMessage(self._reply_to, msg, buttons)
    
    async def upload_thumbnail(self):
        try:
            ask = await sendMessage(self._listener.message, "<b>Silahkan kirimkan photo untuk thumbnail anda !</b>\n\nKlik /batal untuk membatalkan")
            respon = await bot.listen(
                filters= filters.user(self._listener.user_id), timeout=30
                )
            if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                try:
                    msg = respon
                    uid = self._listener.user_id
                    thumb = await createThumb(msg, uid, temp=True)
                    await respon.delete()
                    await deleteMessage(ask)
                    return thumb
                except:
                    await respon.delete()
                    await deleteMessage(ask)
                    pass
            else:
                await respon.delete()
                await deleteMessage(ask)
                pass
        except:
            return
    
    async def batch_process(self):
        if "multi" not in self._auto_args:
            msg = "<b>Mode Batch Activated</b>\n\nKirim semua link yang ingin diproses, satu per baris.\nSetelah selesai, kirim <code>/done</code> untuk memulai pemrosesan."
            await editMessage(self._reply_to, msg)
            
            batch_links = []
            while True:
                try:
                    msg = await bot.listen(filters=filters.text & filters.user(self._listener.user_id), timeout=120)
                    
                    if msg.text == "/done" or msg.text == f"/done@{bot.me.username}":
                        await msg.delete()
                        break
                    elif msg.text == "/batal" or msg.text == f"/batal@{bot.me.username}":
                        await msg.delete()
                        await editMessage(self._reply_to, "<b>Batch processing cancelled!</b>")
                        return
                    
                    urls = re.findall(r'https?://[^\s]+', msg.text) or re.findall(r'magnet:\?[^\s]+', msg.text)
                    batch_links.extend(urls)
                    
                    await msg.delete()
                    await editMessage(self._reply_to, f"<b>Mode Batch Activated</b>\n\n<b>Total links added:</b> {len(batch_links)}\n\nKirim lebih banyak link atau kirim <code>/done</code> untuk memulai pemrosesan.")
                    
                except asyncio.TimeoutError:
                    break
            
            if batch_links:
                self._auto_args["multi"] = batch_links
                await editMessage(self._reply_to, f"<b>Batch processing ready:</b> {len(batch_links)} links\n\nSemua link akan diproses dengan pengaturan yang sama.")
                
                butt = ButtonMaker()
                butt.ibutton("▶️ Start Batch Processing", f"auto start_batch")
                butt.ibutton("🔙 Kembali", f"auto back")
                butt.ibutton("⛔️ Batal", f"auto cancel")
                await editMessage(self._reply_to, f"<b>Batch processing ready:</b> {len(batch_links)} links\n\nSemua link akan diproses dengan pengaturan yang sama.", butt.build_menu(2))
            else:
                await editMessage(self._reply_to, "<b>No links provided for batch processing!</b>")
                await asyncio.sleep(3)
                sub_pesan, sub_buttons = await self.sub_button()
                await editMessage(self._reply_to, sub_pesan, sub_buttons)
        else:
            del self._auto_args["multi"]
            sub_pesan, sub_buttons = await self.sub_button()
            await editMessage(self._reply_to, sub_pesan, sub_buttons)
    
    async def start_batch_processing(self):
        if "multi" not in self._auto_args:
            sub_pesan, sub_buttons = await self.sub_button()
            await editMessage(self._reply_to, sub_pesan, sub_buttons)
            return
            
        batch_links = self._auto_args["multi"]
        total_links = len(batch_links)
        
        msg = f"<b>Memulai batch processing</b>\n\n<b>Total links:</b> {total_links}\n\n"
        await editMessage(self._reply_to, msg)
        
        batch_settings = self._auto_args.copy()
        del batch_settings["multi"]
        
        self._auto_args["batch_settings"] = batch_settings
        self._auto_args["batch_links"] = batch_links
        self.event.set()

    async def set_compression_level(self):
        if "compress_level" not in self._auto_args and "zip" in self._auto_args:
            msg = "<b>Pilih level kompresi ZIP:</b>\n\n"
            msg += "• <b>1</b> - Tercepat, kompresi minimal\n"
            msg += "• <b>5</b> - Seimbang (default)\n"
            msg += "• <b>9</b> - Terkecil, kompresi maksimal\n\n"
            msg += "<i>Semakin tinggi level kompresi akan menghasilkan file lebih kecil tetapi waktu pemrosesan lebih lama.</i>"
            
            butt = ButtonMaker()
            butt.ibutton("1️⃣ Tercepat", f"auto set_level_1")
            butt.ibutton("5️⃣ Seimbang", f"auto set_level_5")
            butt.ibutton("9️⃣ Terkecil", f"auto set_level_9")
            butt.ibutton("🔙 Kembali", f"auto back_to_options")
            butts = butt.build_menu(3)
            
            await editMessage(self._reply_to, msg, butts)
        else:
            del self._auto_args["compress_level"]
            sub_pesan, sub_buttons = await self.sub_button()
            await editMessage(self._reply_to, sub_pesan, sub_buttons)