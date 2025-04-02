from aiofiles.os import remove as aioremove, path as aiopath
from bot import bot, user_data, config_dict
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
from asyncio import wait_for, Event, wrap_future
from bot.helper.ext_utils.status_utils import get_readable_time

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
        obj._auto_args["custom_upload"] = "gd"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_rclone_user":
        obj._auto_args["custom_upload"] = "rcl"
        await obj.send_sub_pesan("mirror")
    elif data[1] == "cu_default":
        try:
            del obj._auto_args["custom_upload"]
        except:
            pass
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
async def home_button(url):
    butt = ButtonMaker()
    if is_url(url) or is_magnet(url):
        msg = "<b>Sebuah Link terdeteksi di pesan anda...</b>\n\nApakah anda mau Mirror/Leech ?"
    else:
        msg = "<b>File terdeteksi pada pesan anda atau pesan yang anda balas...</b>\n\nApakah anda mau Mirror/Leech ?"
    butt.ibutton("☁️ 𝙼𝚒𝚛𝚛𝚘𝚛", f"auto mirror")
    butt.ibutton("☀️ 𝙻𝚎𝚎𝚌𝚑", f"auto leech")
    butt.ibutton("⛔️ 𝚃𝚞𝚝𝚞𝚙", f"auto cancel")
    butts = butt.build_menu(2)
    return msg, butts


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
        user_dict = user_data.get(self._listener.user_id, {})
        du = user_dict.get("default_upload", "") or config_dict["DEFAULT_UPLOAD"]
        cust_up = auto_args.get("custom_upload", du)
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
            butt.ibutton("▶️ 𝚂𝚝𝚊𝚛𝚝 𝙼𝚒𝚛𝚛𝚘𝚛 ", f"auto start_mirror", position="header")
        if self._type == "leech":
            butt.ibutton("▶️ 𝚂𝚝𝚊𝚛𝚝 𝙻𝚎𝚎𝚌𝚑 ", f"auto start_leech", position="header")

        s = "" if "rename" not in auto_args else "✅"
        butt.ibutton(f"Rename {s}", f"auto rename")

        if self._type == "leech":
            s = "" if "custom_thumb" not in auto_args else "✅"
            butt.ibutton(f"Thumbnail {s}", f"auto custom_thumb")
        else:
            if "custom_upload" not in auto_args: s = du
            elif auto_args["custom_upload"] == "gofile": s = "gf"
            elif auto_args["custom_upload"] == "buzzheavier": s = "bh"
            elif auto_args["custom_upload"] == "pixeldrain": s = "pd"
            elif auto_args["custom_upload"] == "rc": s = "rc"
            #elif auto_args["custom_upload"] == "gd": s = "GD"
            elif auto_args["custom_upload"] == "rcl": s = "rcl"
            elif auto_args["custom_upload"] == "gd": s = "gd"
            butt.ibutton(f"Upload: {s}", f"auto custom_upload")
        
        if not self.gofile and not self.buzzheavier:
            s = "" if "extract" not in auto_args else "✅"
            butt.ibutton(f"Extract {s}", f"auto extract")

            s = "" if "zip" not in auto_args else "✅"
            butt.ibutton(f"Buat ZIP  {s}", f"auto zip")

        #s = "❌" if "multi" not in auto_args else "✅"
        #butt.ibutton(f"{s} Multi", f"auto multi")

        #s = "❌" if "bulk" not in auto_args else "✅"
        #butt.ibutton(f"{s} Bulk", f"auto bulk")

        if self._type == "leech":
            s = "" if "ss" not in auto_args else "✅"
            butt.ibutton(f"Screenshot {s}", f"auto ss")
            s = "" if "sv" not in auto_args else "✅"
            butt.ibutton(f"Sample Vid {s}", f"auto sv")

        butt.ibutton("↩️ 𝙱𝚊𝚌𝚔", f"auto back")
        butt.ibutton("⛔️ 𝙲𝚊𝚗𝚌𝚎𝚕", f"auto cancel")
        butt.ibutton(" 𝙱𝚊𝚗𝚝𝚞𝚊𝚗", f"auto help", position="footer")
        butts = butt.build_menu(2)
        return mess, butts

    async def send_sub_pesan(self, type):
        self._type = type
        mess, butts = await self.sub_button()
        await editMessage(self._reply_to, mess, butts)
    
    async def select_upload(self):
        msg = "<b>Silahkan pilih custom upload tujuan anda:</b>\n\n"
        msg += "Default = Kembalikan ke Default\n"
        msg += "GD = Google Drive User\n"
        msg += "BH = Buzzheavier\n"
        msg += "GF = Gofile\n"
        msg += "PD = Pixeldrain\n"
        msg += "RC = Config Rclone Owner\n"
        #msg += "GD = Google Drive owner\n"
        msg += "RCL = Config Rclone User\n"
        but = ButtonMaker()
        but.ibutton("Default", f"auto cu_default", position="header")
        but.ibutton("GD", f"auto cu_gdrive_user")
        but.ibutton("BH", f"auto cu_buzzheavier")
        but.ibutton("GF", f"auto cu_gofile")
        but.ibutton("PD", f"auto cu_pixeldrain")
        but.ibutton("RC", f"auto cu_rclone")
        #but.ibutton("GD", f"auto cu_gdrive")
        but.ibutton("RCL", f"auto cu_rclone_user")
        but.ibutton("⬅️ 𝙱𝚊𝚌𝚔", f"auto cu_back")
        butts = but.build_menu(3)
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
        butt.ibutton("↩️ 𝙱𝚊𝚌𝚔", f"auto {self._type}")
        butt.ibutton("⛔️ 𝙲𝚊𝚗𝚌𝚎𝚕", f"auto cancel")
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