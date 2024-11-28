from aiofiles.os import remove as aioremove, path as aiopath
from bot import bot
from pyrogram import filters
from pyrogram.filters import command, regex, user
from pyrogram.handlers import CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.ext_utils.bot_utils import (
    new_task,
    new_thread,
)
from bot.helper.ext_utils.media_utils import storeSubFile, createWM
from functools import partial
from time import time
from asyncio import wait_for, Event, wrap_future
from bot.helper.ext_utils.status_utils import get_readable_time

#Video Editor by: Pikachu
#https://github.com/aenulrofik

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()

    if data[1] == "compress":
        await obj.compress_button()
    elif data[1] == "watermark":
        await obj.watermark_main_button()
    elif data[1] == "hardsub":
        await obj.belum_siap()
    elif data[1] == "softsub":
        await obj.belum_siap()
    elif data[1] == "rename":
        await obj.rename_button()
    elif data[1] == "extension":
        await obj.extension_button()
    
    elif data[1] == "file_wm":
        await obj.watermark_file_button()
    elif data[1] == "position_wm":
        await obj.watermark_position_button()
    elif data[1] == "size_wm":
        await obj.watermark_size_button()

    elif data[1] in ["1920:1080", "1280:720", "854:480", "640:360"]:
        if 'compress' not in obj.video_editor:
            obj.video_editor['compress'] = {}
        obj.video_editor['compress']['resolution'] = data[1]
        await obj.update_pesan()
    
    elif data[1] in ["top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right"]:
        if 'watermark' not in obj.video_editor:
            obj.video_editor['watermark'] = {}
        obj.video_editor['watermark']['position'] = data[1]
        await obj.watermark_main_button()
    
    elif data[1] in ["kecil", "sedang", "besar", "extra", "super"]:
        if 'watermark' not in obj.video_editor:
            obj.video_editor['watermark'] = {}
        obj.video_editor['watermark']['size'] = data[1]
        await obj.watermark_main_button()

    elif data[1] == "back":
        await obj.back()
    
    elif data[1] == "back_wm":
        await obj.watermark_main_button()

    elif data[1] == "start":
        await obj.start()
    
    elif data[1] == "cancel":
        await editMessage(message, "<b>Tugas dibatalkan !</b>")
        obj.is_cancelled = True
        obj.event.set()


class VideEditor:
    def __init__(self, listener):
        self._listener = listener
        self.video_editor = {}
        self.video_editor["extension"] = "mp4"
        self._reply_to = None
        self._sub_pesan = None
        self._time = time()
        self._timeout = 160
        self.event = Event()
        self.is_cancelled = False

    @new_thread
    async def _event_handler(self):
        pfunc = partial(main_select, obj=self)
        handler = self._listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^ve") & user(self._listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except:
            await editMessage(self._reply_to, "<b>Waktu habis, Tugas dibatalkan !</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
    
    async def home_button(self):
        video_editor = self.video_editor
        compress = video_editor.get("compress", None)
        watermark = video_editor.get("watermark", None)
        hardsub = video_editor.get("hardsub", None)
        softsub = video_editor.get("softsub", None)
        rename = video_editor.get("rename", None)
        extension = video_editor.get("extension", "mp4")
        butt = ButtonMaker()
        msg = "<b>Silahkan pilih menu video editor dibawah:</b>\n\n"
        if compress:
            reso = compress['resolution']
            reso = reso.split(':')[1] + "p"
            msg += f"<b>▪️ Kompres ke resolusi:</b> <code>{reso}</code>\n"
        if rename:
            msg += f"<b>▪️ Rename ke:</b> <code>{rename}</code>\n"
        if watermark:
            msg += f"<b>▪️ Watermark ke:</b> <code>Watermark ditambahkan</code>\n"
        msg += f"<b>▪️ Format video:</b> <code>{extension}</code>\n"
        s = "" if not compress else "✅"
        butt.ibutton(f"{s} Kompres", f"ve compress")
        s = "" if not rename else "✅"
        butt.ibutton(f"{s} Rename", f"ve rename")
        s = "" if not watermark else "✅"
        butt.ibutton(f"{s} Watermark", f"ve watermark")
        butt.ibutton(f"✅ Convert: {extension}", f"ve extension")
        s = "🔒" if not hardsub else "✅"
        butt.ibutton(f"{s} Hardsub", f"ve hardsub")
        s = "🔒" if not softsub else "✅"
        butt.ibutton(f"{s} Softsub", f"ve softsub")

        butt.ibutton(f"▶️ Mulai", f"ve start")
        butt.ibutton(f"⛔️ Batal", f"ve cancel")
        butts = butt.build_menu(2)
        return msg, butts
            
    async def main_pesan(self):
        future = self._event_handler()
        msg, buttons = await self.home_button()
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        self._reply_to = await sendMessage(self._listener.message, msg, buttons)
        await wrap_future(future)
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self.video_editor
        else:
            return None
    
    async def update_pesan(self):
        msg, buttons = await self.home_button()
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        await editMessage(self._reply_to, msg, buttons)
    
    async def compress_button(self):
        msg = "<b>📌 Pilih resolusi untuk kompres video anda </b>\n\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        compress = self.video_editor.get("compress", None)
        resolution = compress.get("resolution", "") if compress else ""
        butt = ButtonMaker()
        s = "" if "1920:1080" not in resolution else "✅"
        butt.ibutton(f"1080p {s}", f"ve 1920:1080")
        s = "" if "1280:720" not in resolution else "✅"
        butt.ibutton(f"720p {s}", f"ve 1280:720")
        s = "" if "854:480" not in resolution else "✅"
        butt.ibutton(f"480p {s}", f"ve 854:480")
        s = "" if "640:360" not in resolution else "✅"
        butt.ibutton(f"360p {s}", f"ve 640:360")

        butt.ibutton("↩️ Kembali", f"ve back")
        butt.ibutton("⛔️ Batal", f"ve cancel")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def hardsub_main_button(self):
        msg = "<b>📌 Pilih format hardsub anda </b>\n\n"
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        subfile = hardsub.get("subfile", "") if hardsub else ""
        font_size = hardsub.get("font_size", "24") if hardsub else ""
        font_color = hardsub.get("font_color", "white") if hardsub else ""
        font_style = hardsub.get("font_style", "Bold=1") if hardsub else ""
        butt = ButtonMaker()
        s = "" if not subfile else "✅"
        butt.ibutton(f"File Sub {s}", f"ve filesub")
        s = "" if not font_size else f"{font_size}"
        butt.ibutton(f"Ukuran Teks {s}", f"ve fontsize")
        s = "" if not font_color else f"{font_color}"
        butt.ibutton(f"Warna Teks {s}", f"ve fontcolor")
        s = "" if not font_style else f"{font_style}"
        butt.ibutton(f"Format Teks {s}", f"ve font_style")

        butt.ibutton("↩️ Kembali", f"ve back")
        butt.ibutton("⛔️ Batal", f"ve cancel")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def rename_button(self):
        msg = "<b>📌 Silahkan masukan nama baru untuk video anda ! </b>\n\nKlik /batal untuk membatalkan"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        rename = self.video_editor.get("rename", "") if self.video_editor else ""
        if not rename:
            try:
                ask = await sendMessage(self._listener.message, msg)
                respon = await bot.listen(
                    filters=filters.text & filters.user(self._listener.user_id), timeout=30
                    )
                if respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    data = respon.text
                    upd = {"rename": data}
                    self.video_editor.update(upd)
                await respon.delete()
                await deleteMessage(ask)
                await self.update_pesan()
            except:
                await self.update_pesan
        else:
            del self.video_editor["rename"]
            await self.update_pesan()
    
    async def extension_button(self):
        extension = self.video_editor.get("extension", None)
        if extension == "mkv":
            extension = "mp4"
        else:
            extension = "mkv"
        self.video_editor["extension"] = extension
        await self.update_pesan()
    
    async def watermark_main_button(self):
        watermark = self.video_editor.get("watermark", None)
        if not watermark:
            watermark = self.video_editor["watermark"] = {}
        path = watermark.get("file", "")
        size = watermark.get("size", "sedang")
        positions = watermark.get("position", "top_left")
        msg = "<b>📌 Silahkan pilih menu watermark !</b>\n\n"
        if path:
            msg += f"<b>▪️ File Watermark:</b> <code>Sudah ditambahkan</code>\n"
        else:
            msg += f"<b>▪️ File Watermark:</b> <code>Belum ditambahkan !!</code>\n"
        msg += f"<b>▪️ Ukuran Watermark:</b> <code>{size}</code>\n"
        msg += f"<b>▪️ Posisi Watermark:</b> <code>{positions}</code>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"

        butt = ButtonMaker()
        s = "" if not path else "✅"
        butt.ibutton(f"File Watermark {s}", f"ve file_wm", position="header")
        butt.ibutton(f"Ukuran", f"ve size_wm")
        butt.ibutton(f"Posisi", f"ve position_wm")
        butt.ibutton("↩️ Kembali", f"ve back")
        butt.ibutton("⛔️ Batal", f"ve cancel")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)

    async def watermark_position_button(self):
        watermark = self.video_editor.get("watermark", None)
        if not watermark:
            watermark = self.video_editor["watermark"] = {}
        positions = watermark.get("position", "top_left")
        msg = "<b>📌 Silahkan pilih posisi watermark anda !</b>\n\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"

        butt = ButtonMaker()
        s = "" if not positions == "top_left" else "✅"
        butt.ibutton(f"Kiri Atas {s}", f"ve top_left")
        s = "" if not positions == "top_center" else "✅"
        butt.ibutton(f"Atas Tengah {s}", f"ve top_center")
        s = "" if not positions == "top_right" else "✅"
        butt.ibutton(f"Kanan Atas {s}", f"ve top_right")
        s = "" if not positions == "bottom_left" else "✅"
        butt.ibutton(f"Bawah Kiri {s}", f"ve bottom_left")
        s = "" if not positions == "bottom_center" else "✅"
        butt.ibutton(f"Bawah Tengah {s}", f"ve bottom_center")
        s = "" if not positions == "bottom_right" else "✅"
        butt.ibutton(f"Bawah Kanan {s}", f"ve bottom_right")
        butt.ibutton("↩️ Kembali", f"ve back_wm")
        butt.ibutton("⛔️ Batal", f"ve cancel")
        buttons = butt.build_menu(3)
        await editMessage(self._reply_to, msg, buttons)
    
    async def watermark_size_button(self):
        watermark = self.video_editor.get("watermark", None)
        if not watermark:
            watermark = self.video_editor["watermark"] = {}
        size = watermark.get("size", "sedang")
        msg = "<b>📌 Silahkan pilih ukuran watermark anda !</b>\n\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"

        butt = ButtonMaker()
        s = "" if not size == "kecil" else "✅"
        butt.ibutton(f"Kecil {s}", f"ve kecil")
        s = "" if not size == "sedang" else "✅"
        butt.ibutton(f"Sedang {s}", f"ve sedang")
        s = "" if not size == "besar" else "✅"
        butt.ibutton(f"Besar {s}", f"ve besar")
        s = "" if not size == "extra" else "✅"
        butt.ibutton(f"Extra {s}", f"ve extra")
        s = "" if not size == "ultra" else "✅"
        butt.ibutton(f"Ultra {s}", f"ve ultra")
        s = "" if not size == "super" else "✅"
        butt.ibutton(f"Super {s}", f"ve super")

        butt.ibutton("↩️ Kembali", f"ve back_wm", position="footer")
        butt.ibutton("⛔️ Batal", f"ve cancel", position="footer")
        buttons = butt.build_menu(3)
        await editMessage(self._reply_to, msg, buttons)
        
    
    async def watermark_file_button(self):
        msg = "<b>📌 Silahkan kirimkan file watermark anda, support jenis .jpg, .png, dan .jpeg</b>\n\n<b>Catatan:</b> Supaya watermark anda bisa tetap transparan, kirim dalam bentuk file, bukan gambar.\n\n"
        watermark = self.video_editor.get("watermark", None)
        if not watermark:
            watermark = self.video_editor["watermark"] = {}
        watermark_path = watermark.get("file", "") if watermark else ""
        if not watermark_path:
            try:
                ask = await sendMessage(self._listener.message, f"{msg}\n\nKlik /batal untuk membatalkan")
                respon = await bot.listen(
                    filters= filters.user(self._listener.user_id), timeout=30
                    )
                if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    try:
                        msg = respon
                        uid = self._listener.user_id
                        wm = await createWM(msg, uid)
                        watermark = self.video_editor["watermark"]
                        watermark["file"] = wm
                    except: 
                        pass
                await respon.delete()
                await deleteMessage(ask)
                await self.watermark_main_button()
            except:
                await deleteMessage(ask)
                await self.watermark_main_button()


    async def hardsub_file_button(self):
        msg = "<b>📌 Silahkan kirimkan file subs anda, support jenis .srt, .ass, dan .sub </b>\n\n"
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        subfile = hardsub.get("subfile", "") if hardsub else ""
        if not subfile:
            try:
                ask = await sendMessage(self._listener.message, f"{msg}\n\nKlik /batal untuk membatalkan")
                respon = await bot.listen(
                    filters= filters.user(self._listener.user_id), timeout=30
                    )
                if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    try:
                        msg = respon
                        uid = self._listener.user_id
                        sub = await storeSubFile(msg, uid)
                        upd = {"subfile": sub}
                        hardsub.update(upd)
                    except: 
                        pass
                await respon.delete()
                await self.hardsub_main_button()
                await deleteMessage(ask)
            except:
                await self.hardsub_main_button()
                await deleteMessage(ask)
        else:
            if aiopath.exists(subfile):
                await aioremove(subfile)
            del hardsub["subfile"]
            await self.hardsub_main_button()
    
    async def belum_siap(self):
        msg = "<b>Fitur ini belum bisa digunakan hehe 👻 </b>\n\n"
        butt = ButtonMaker()
        butt.ibutton("↩️ Kembali", f"ve back")
        butt.ibutton("⛔️ Batal", f"ve cancel")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)

    async def start(self):
        self.event.set()

    async def back(self):      
        msg, buttons = await self.home_button()
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        await editMessage(self._reply_to, msg, buttons)