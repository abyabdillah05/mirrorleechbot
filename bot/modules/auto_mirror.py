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
        msg = f"""<b>Silahkan masukkan Leech destination atau Mirror destination tujuan anda!<b>

<blockquote><b>Notes:</b>
• Untuk leech destination, masukkan username grup atau channel diawali @ atau masukkan id grup diawali <code>-100</code>.
  Dan jangan lupa buat bot ini sebagai admin di grup atau channel tujuan.

• Untuk Custom upload mirror, masukkan <code>gdl</code> untuk upload ke google drive pribadi (butuh token.pickle),
  dan masukkan <code>rcl</code> untuk upload ke config rclone (butuh rclone.conf)."</blockquote>

<i>❗️ Klik <b>/batal</b> untuk membatalkan.</i>"""
        await obj.update_dict(msg, data[1])
    elif data[1] == "zip":
        msg = f"<b>Silahkan masukkan Password untuk membuat file ZIP anda!</b>\n\n<i>❗️ Klik <b>/skip</b> untuk membuat zip tanpa password.</i>"
        await obj.update_dict(msg, data[1])
    elif data[1] == "extract":
        msg = f"<b>Silahkan masukkan Password untuk extract file anda!</b>\n\n❗️ Klik <b>/skip</b> jika file tidak menggunakan password."
        await obj.update_dict(msg, data[1])
    
    elif data[1] == "ss":
        await obj.set_dict_ss()
    elif data[1] == "sv":
        await obj.set_dict_sv()
        
    elif data[1] == "start_leech":
        await obj.start_leech()

    elif data[1] == "start_mirror":
        await obj.start_mirror()

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
    butt.ibutton("☁️ Mirror", f"auto mirror")
    butt.ibutton("☀️ Leech", f"auto leech")
    butt.ibutton("⛔️ Batal", f"auto cancel")
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
    
    async def main_pesan_custom(self, url, type, gofile=False):
        if type:
            self._type = type
        if gofile:
            self.gofile = True
            self._auto_args["custom_upload"] = "gofile"
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
        mess += f"\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        if self._type == "mirror":
            butt.ibutton("▶️ START MIRROR ", f"auto start_mirror", position="header")
        if self._type == "leech":
            butt.ibutton("▶️ START LEECH ", f"auto start_leech", position="header")

        s = "" if "rename" not in auto_args else "✅"
        butt.ibutton(f"Rename {s}", f"auto rename")

        s = "" if "custom_upload" not in auto_args else "✅"
        butt.ibutton(f"Cstm Upload {s}", f"auto custom_upload")
        
        if not self.gofile:
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

        butt.ibutton("↩️ Kembali", f"auto back")
        butt.ibutton("⛔️ Batal", f"auto cancel")
        butt.ibutton("🗿 Bantuan Singkat", f"auto help", position="footer")
        butts = butt.build_menu(2)
        return mess, butts

    async def send_sub_pesan(self, type):
        self._type = type
        mess, butts = await self.sub_button()
        await editMessage(self._reply_to, mess, butts)
    
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

<b>• Extract:</b> Mengextract file zip.

<b>• Buat Zip:</b> Membuat file anda menjadi arsip ZIP

<b>• Screenshot:</b> Mengambil screenshot random dari video yang anda leech.

<b>• Sample Video:</b> Mengambil sample video random dari video yang anda leech.
        
<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"""
        butt = ButtonMaker()
        butt.ibutton("↩️ Kembali", f"auto {self._type}")
        butt.ibutton("⛔️ Batal", f"auto cancel")
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