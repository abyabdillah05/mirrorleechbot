import os
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
from bot.helper.ext_utils.media_utils import storeSubFile, createWM, fonts_dict
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
    if data[1] == "paid":
        await query.answer("⛔ Fitur ini hanya dapat digunakan oleh user premium !!", show_alert=True)
    await query.answer()

    if data[1] == "compress":
        await obj.compress_button()
    elif data[1] == "watermark":
        await obj.watermark_main_button()
    elif data[1] == "hardsub":
        await obj.hardsub_main_button()
    elif data[1] == "softsub":
        await obj.softsub_main_button()
    elif data[1] == "rename":
        await obj.rename_button()
    elif data[1] == "extension":
        await obj.extension_button()
    elif data[1] == "extract":
        await obj.extract_subtitle()
    elif data[1] == "encoding":
        await obj.encoding_main()
    elif data[1] == "mtdta":
        await obj.metadata_main()
    elif data[1] == "merge":
        await obj.merge_stream()
    elif data[1] == "rm_stream":
        await obj.belum_siap()
    elif data[1] == "swap_stream":
        await obj.belum_siap()
    
    elif data[1] == "file_wm":
        await obj.watermark_file_button()
    elif data[1] == "position_wm":
        await obj.watermark_position_button()
    elif data[1] == "size_wm":
        await obj.watermark_size_button()

    elif data[1] in ["1080p", "720p", "540p", "480p", "360p", "144p"]:
        if 'compress' not in obj.video_editor:
            obj.video_editor['compress'] = {}
        obj.video_editor['compress']['resolution'] = data[1]
        await obj.update_pesan()
    
    elif data[1] in ["top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right"]:
        if 'watermark' not in obj.video_editor:
            obj.video_editor['watermark'] = {}
        obj.video_editor['watermark']['position'] = data[1]
        await obj.watermark_main_button()
    
    elif data[1] in ["kecil", "sedang", "besar", "extra", "ultra", "super"]:
        if data[2] == "wm":
            if 'watermark' not in obj.video_editor:
                obj.video_editor['watermark'] = {}
            obj.video_editor['watermark']['size'] = data[1]
            await obj.watermark_main_button()
        elif data[2] == "hs":
            if 'hardsub' not in obj.video_editor:
                obj.video_editor['hardsub'] = {}
            obj.video_editor['hardsub']['size'] = data[1]
            await obj.hardsub_main_button()
    
    elif data[1] == "metadata":
        await obj.metadata_input(data[2])
    
    elif data[1] == "v_encoder":
        await obj.video_encoder_button()
    elif data[1] == "a_encoder":
        await obj.audio_encoder_button()
    elif data[1] == "v_bitrate":
        await obj.video_bitrate_button()
    elif data[1] == "a_bitrate":
        await obj.audio_bitrate_button()
    elif data[1] == "preset_main":
        await obj.preset_button()
    elif data[1] == "crf_main":
        await obj.crf_button()
    elif data[1] == "hs_file":
        await obj.hardsub_file_button()
    elif data[1] == "hs_font":
        await obj.hardsub_font_button()
    elif data[1] == "hs_color":
        await obj.hardsub_color_button()
    elif data[1] == "hs_size":
        await obj.hardsub_size_button()
    elif data[1] == "hs_pos":
        await obj.hardsub_position_button()
    elif data[1] == "hs_bold":
        await obj.hardsub_bold_button()
    elif data[1] == "merge_video":
        await obj.merge_video_video()
    elif data[1] == "merge_audio":
        await obj.merge_video_audio()
    
    elif data[1] == "ss_file":
        await obj.softsub_file_button()
    elif data[1] == "ss_del":
        softsub = obj.video_editor.get("softsub", None)
        if not softsub:
            obj.video_editor['softsub'] = []
        softsub.pop(int(data[2]))
        await obj.softsub_main_button()
            
    elif data[1] == "size_hs":
        if 'hardsub' not in obj.video_editor:
            obj.video_editor['hardsub'] = {}
        obj.video_editor['hardsub']['size'] = data[2]
        await obj.hardsub_main_button()
    elif data[1] == "hs_cs":
        if 'hardsub' not in obj.video_editor:
            obj.video_editor['hardsub'] = {}
        obj.video_editor['hardsub']['color'] = data[2]
        await obj.hardsub_main_button()
    elif data[1] == "hs_fs":
        if 'hardsub' not in obj.video_editor:
            obj.video_editor['hardsub'] = {}
        obj.video_editor['hardsub']['font'] = int(data[2])
        await obj.hardsub_main_button()
    
    elif data[1] == "v_enc":
        obj.video_editor['video_codec'] = data[2]
        await obj.encoding_main()
    
    elif data[1] == "a_enc":
        obj.video_editor['audio_codec'] = data[2]
        await obj.encoding_main()
    
    elif data[1] == "v_br":
        obj.video_editor['video_bitrate'] = data[2]
        await obj.encoding_main()
    
    elif data[1] == "a_br":
        obj.video_editor['audio_bitrate'] = data[2]
        await obj.encoding_main()
    
    elif data[1] == "preset":
        obj.video_editor['preset'] = data[2]
        await obj.encoding_main()
    
    elif data[1] == "crf":
        obj.video_editor['crf'] = data[2]
        await obj.encoding_main()

    elif data[1] == "extract_true":
        obj.video_editor['extract'] = True
        await obj.start()
    
    elif data[1] == "video_start":
        if 'merge_type' not in obj.video_editor:
            obj.video_editor['merge_type'] = "video_video"
            await obj.start()
    
    elif data[1] == "audio_start":
        if 'merge_type' not in obj.video_editor:
            obj.video_editor['merge_type'] = "video_audio"
            await obj.start()

    elif data[1] == "back":
        await obj.back()
    
    elif data[1] == "back_wm":
        await obj.watermark_main_button()

    elif data[1] == "back_hs":
        await obj.hardsub_main_button()
    
    elif data[1] == "encoder_back":
        await obj.encoding_main()

    elif data[1] == "start":
        await obj.start()
    
    elif data[1] == "cancel":
        await editMessage(message, "<b>Tugas dibatalkan !</b>")
        await obj.cancel()
        obj.is_cancelled = True
        obj.event.set()


class VideEditor:
    def __init__(self, listener):
        self._listener = listener
        self.video_editor = {}
        self.video_editor["extension"] = "mkv"
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
        if watermark:
            watermark = watermark.get("file", None)
        hardsub = video_editor.get("hardsub", None)
        if hardsub:
            hardsub = hardsub.get("file", None)
        softsub = video_editor.get("softsub", None)
        rename = video_editor.get("rename", None)
        try:
            metadata = video_editor.get("metadata")
        except:
            metadata = None
        extension = video_editor.get("extension", "mkv")
        butt = ButtonMaker()
        msg = "𝐕𝐢𝐝𝐞𝐨𝐄𝐝𝐢𝐭𝐨𝐫 𝐯𝟐.𝟎 𝐁𝐞𝐭𝐚\n___________________________\n<b>Silahkan pilih menu video editor dibawah:</b>\n\n"
        butt.ibutton(f"▶️ Start Video Editor", f"ve start", position="header")
        video_encoder = self.video_editor.get("video_codec", "default")
        audio_encoder = self.video_editor.get("audio_codec", "default")
        video_bitrate = self.video_editor.get("video_bitrate", "default")
        audio_bitrate = self.video_editor.get("audio_bitrate", "default")
        crf = self.video_editor.get("crf", 23)
        preset = self.video_editor.get("preset", "veryfast")
        msg += f"<b>▪️ Encoding:</b>\n"
        msg += f"<b>• Video Encoder:</b> <code>{video_encoder}</code>\n"
        msg += f"<b>• Video Bitrate:</b> <code>{video_bitrate}</code>\n"
        msg += f"<b>• Audio Encoder:</b> <code>{audio_encoder}</code>\n"
        msg += f"<b>• Audio Bitrate:</b> <code>{audio_bitrate}</code>\n"
        msg += f"<b>• CRF:</b> <code>{crf}</code>\n"
        msg += f"<b>• Preset:</b> <code>{preset}</code>\n\n"
        metadata_exists = False
        metadata = self.video_editor.get("metadata", {})
        metadata_fields = {
            "title": "title",
            "description": "description",
            "artist": "artist",
            "comment": "comment",
            "genre": "genre",
            "album": "album",
            "date": "date",
            "copyright": "copyright",
        }
        for key, value in metadata_fields.items():
            if metadata.get(key):
                metadata_exists = True
        if compress:
            reso = compress['resolution']
            msg += f"<b>▪️ Kompres ke resolusi:</b> <code>{reso}</code>\n"
        if rename:
            msg += f"<b>▪️ Rename ke:</b> <code>{rename}</code>\n"
        if metadata_exists:
            msg += f"<b>▪️ Metadata:</b> <code>Metadata ditambahkan</code>\n"
        if watermark:
            msg += f"<b>▪️ Watermark:</b> <code>Watermark ditambahkan</code>\n"
        if hardsub:
            msg += f"<b>▪️ Hardsub:</b> <code>Hardsub ditambahkan</code>\n"
        if softsub:
            msg += f"<b>▪️ Softsub:</b> <code>Softsub ditambahkan</code>\n"
        msg += f"<b>▪️ Format video:</b> <code>{extension}</code>\n"
        s = "" if not compress else "✅"
        butt.ibutton(f"{s} Kompres ⭐️", f"paid")
        s = "" if not rename else "✅"
        butt.ibutton(f"{s} Rename", f"ve rename")
        s = "" if not hardsub else "✅"
        butt.ibutton(f"{s} Hardsub ⭐️", f"paid")
        s = "" if not softsub else "✅"
        butt.ibutton(f"{s} Softsub", f"ve softsub")
        s = "" if not watermark else "✅"
        butt.ibutton(f"{s} Watermark ⭐️", f"paid")
        butt.ibutton(f"Convert: {extension}", f"ve extension")
        butt.ibutton(f"Extract", f"ve extract")
        butt.ibutton(f"Encoding ⭐️", f"paid")
        s = "" if not metadata_exists else "✅"
        butt.ibutton(f"Metadata", f"ve mtdta")
        butt.ibutton(f"Merge", f"ve merge")
        butt.ibutton(f"Hapus Stream (soon)", f"ve rm_stream")
        butt.ibutton(f"Swap Stream (soon)", f"ve swap_stream")
        butt.ibutton(f"⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
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
        s = "✅" if "1080p" in resolution else ""
        butt.ibutton(f"1080p {s}", f"ve 1080p")
        s = "✅" if "720p" in resolution else ""
        butt.ibutton(f"720p {s}", f"ve 720p")
        s = "✅" if "540p" in resolution else ""
        butt.ibutton(f"540p {s}", f"ve 540p")
        s = "✅" if "480p" in resolution else ""
        butt.ibutton(f"480p {s}", f"ve 480p")
        s = "✅" if "360p" in resolution else ""
        butt.ibutton(f"360p {s}", f"ve 360p")
        s = "✅" if "144p" in resolution else ""
        butt.ibutton(f"144p {s}", f"ve 144p")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel")
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
    
    async def metadata_main_button(self):
        msg = "<b>📌 Pilih metadata untuk video anda </b>\n\n"
        metadata = self.video_editor.get("metadata", {})
        title = metadata.get("title", "") if metadata else ""
        description = metadata.get("description", "") if metadata else ""
        artist = metadata.get("artist", "") if metadata else ""
        comment = metadata.get("comment", "") if metadata else ""
        genre = metadata.get("genre", "") if metadata else ""
        album = metadata.get("album", "") if metadata else ""
        date = metadata.get("date", "") if metadata else ""
        copyright = metadata.get("copyright", "") if metadata else ""
        msg += f"<b>▪️ Judul:</b> <code>{title}</code>\n"
        msg += f"<b>▪️ Deskripsi:</b> <code>{description}</code>\n"
        msg += f"<b>▪️ Artis:</b> <code>{artist}</code>\n"
        msg += f"<b>▪️ Komentar:</b> <code>{comment}</code>\n"
        msg += f"<b>▪️ Genre:</b> <code>{genre}</code>\n"
        msg += f"<b>▪️ Album:</b> <code>{album}</code>\n"
        msg += f"<b>▪️ Tanggal:</b> <code>{date}</code>\n"
        msg += f"<b>▪️ Hak Cipta:</b> <code>{copyright}</code>\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        s = "" if not title else "✅"
        butt.ibutton(f"Judul {s}", f"ve metadata title")
        s = "" if not description else "✅"
        butt.ibutton(f"Deskripsi {s}", f"ve metadata description")
        s = "" if not artist else "✅"
        butt.ibutton(f"Artis {s}", f"ve metadata artist")
        s = "" if not comment else "✅"
        butt.ibutton(f"Komentar {s}", f"ve metadata comment")
        s = "" if not genre else "✅"
        butt.ibutton(f"Genre {s}", f"ve metadata genre")
        s = "" if not album else "✅"
        butt.ibutton(f"Album {s}", f"ve metadata album")
        s = "" if not date else "✅"
        butt.ibutton(f"Tanggal {s}", f"ve metadata date")
        s = "" if not copyright else "✅"
        butt.ibutton(f"Hak Cipta {s}", f"ve metadata copyright")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back")
        butts = butt.build_menu(2)
        return msg, butts

    async def metadata_main(self):
        msg, butts = await self.metadata_main_button()
        await editMessage(self._reply_to, msg, butts)

    async def metadata_input(self, option=""):
        if "metadata" not in self.video_editor:
            self.video_editor["metadata"] = {}
        msg = f"<b>📌 Silahkan masukan {option} metadata ! </b>\n\nKlik /batal untuk membatalkan"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        metadata = self.video_editor.get("metadata", {})
        if option not in metadata:
            try:
                ask = await sendMessage(self._listener.message, msg)
                respon = await bot.listen(
                    filters=filters.text & filters.user(self._listener.user_id), timeout=30
                    )
                if respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    data = respon.text
                    upd = {f"{option}": data}
                    self.video_editor["metadata"].update(upd)
                await respon.delete()
                await deleteMessage(ask)
                await self.metadata_main()
            except:
                await self.umetadata_main()
        else:
            del self.video_editor["metadata"][option]
            await self.metadata_main()

    async def update_pesan(self):
        msg, buttons = await self.home_button()
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        await editMessage(self._reply_to, msg, buttons)
    
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
        s = "🔒" if not path else "✅"
        if path:
            butt.ibutton(f"Hapus Watermark {s}", f"ve paid", position="header")
        else:
            butt.ibutton(f"Tambah Watermark {s}", f"ve paid", position="header")
        butt.ibutton(f"Ukuran", f"ve size_wm")
        butt.ibutton(f"Posisi", f"ve position_wm")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
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
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_wm")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel")
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
        butt.ibutton(f"Kecil {s}", f"ve kecil wm")
        s = "" if not size == "sedang" else "✅"
        butt.ibutton(f"Sedang {s}", f"ve sedang wm")
        s = "" if not size == "besar" else "✅"
        butt.ibutton(f"Besar {s}", f"ve besar wm")
        s = "" if not size == "extra" else "✅"
        butt.ibutton(f"Extra {s}", f"ve extra wm")
        s = "" if not size == "ultra" else "✅"
        butt.ibutton(f"Ultra {s}", f"ve ultra wm")
        s = "" if not size == "super" else "✅"
        butt.ibutton(f"Super {s}", f"ve super wm")

        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_wm", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
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
        else:
            self.video_editor["watermark"].pop("file", None)
            await self.watermark_main_button()

    async def hardsub_main_button(self):
        msg = "<b>📌 Pilih format hardsub anda </b>\n\n"
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        hardsub_file = hardsub.get("file", None)
        font_size = hardsub.get("size", "sedang")
        font_color = hardsub.get("color", "putih")
        font_style = hardsub.get("font", 5)
        hardsub_position = hardsub.get("position", "bawah")
        bold = hardsub.get("bold", False)
        if hardsub_file:
            msg += f"<b>▪️ File Subtitle:</b> <code>✅Sudah Ditambahkan</code>\n"
        else:
            msg += f"<b>▪️ File Subtitle:</b> <code>Belum Ditambahkan !!</code>\n"
        msg += f"<b>▪️ Ukuran Teks:</b> <code>{font_size}</code>\n"
        msg += f"<b>▪️ Warna Teks:</b> <code>{font_color}</code>\n"
        if font_color == "hitam":
            msg += f"<b>(Orang gila mana pake subs hitam njir.)</b>\n"
        msg += f"<b>▪️ Jenis Font:</b> <code>{fonts_dict[int(font_style)]}</code>\n"
        msg += f"<b>▪️ Posisi Hardsub:</b> <code>{hardsub_position}</code>\n"
        if bold:
            msg += f"<b>▪️ Bold:</b> <code>Hidup</code>\n"
        else:
            msg += f"<b>▪️ Bold:</b> <code>Mati</code>\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        s = "🔒" if not hardsub_file else "✅"
        if hardsub_file:
            butt.ibutton(f"Hapus Subtitle {s}", f"ve paid", position="header")
        else:
            butt.ibutton(f"Tambahkan Subtitle {s}", f"ve paid", position="header")
        butt.ibutton(f"Ukuran Teks", f"ve hs_size")
        butt.ibutton(f"Warna Teks", f"ve hs_color")
        butt.ibutton(f"Jenis Font", f"ve hs_font")
        s = "" if not bold else "✅"
        butt.ibutton(f"Bold {s}", f"ve hs_bold")
        butt.ibutton(f"Posisi Hardsub: {hardsub_position}", f"ve hs_pos")

        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)

    async def hardsub_file_button(self):
        msg = "<b>📌 Silahkan kirimkan file subtitle anda, support jenis subtitle .srt, .ass, .ssa, .vtt\n\n"
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        hardsub_path = hardsub.get("file", "") if hardsub else ""
        if not hardsub_path:
            try:
                ask = await sendMessage(self._listener.message, f"{msg}\n\nKlik /batal untuk membatalkan")
                respon = await bot.listen(
                    filters= filters.user(self._listener.user_id), timeout=30
                    )
                if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                    try:
                        msg = respon
                        uid = self._listener.user_id
                        hs = await storeSubFile(msg, uid)
                        hardsub = self.video_editor["hardsub"]
                        hardsub["file"] = hs
                    except: 
                        pass
                await respon.delete()
                await deleteMessage(ask)
                await self.hardsub_main_button()
            except:
                await deleteMessage(ask)
                await self.hardsub_main_button()
        else:
            self.video_editor["hardsub"].pop("file", None)
            await self.hardsub_main_button()
    
    async def belum_siap(self):
        msg = "<b>Fitur ini belum bisa digunakan hehe 👻 </b>\n\n"
        butt = ButtonMaker()
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def hardsub_size_button(self):
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        size = hardsub.get("size", "sedang")
        msg = "<b>📌 Silahkan pilih ukuran hardsub anda !</b>\n\n"
        msg += f"<b>Sekedar Saran:\n▪️ Gunakan size kecil sampai sedang untuk resolusi video 480p\n▪️ Gunakan sedang sampai besar untuk resolusi video 720p\n▪️ Gunakan besar besar sampai extra untuk resolusi video 1080p\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"

        butt = ButtonMaker()
        s = "" if not size == "kecil" else "✅"
        butt.ibutton(f"Kecil {s}", f"ve kecil hs")
        s = "" if not size == "sedang" else "✅"
        butt.ibutton(f"Sedang {s}", f"ve sedang hs")
        s = "" if not size == "besar" else "✅"
        butt.ibutton(f"Besar {s}", f"ve besar hs")
        s = "" if not size == "extra" else "✅"
        butt.ibutton(f"Extra {s}", f"ve extra hs")
        s = "" if not size == "ultra" else "✅"
        butt.ibutton(f"Ultra {s}", f"ve ultra hs")
        s = "" if not size == "super" else "✅"
        butt.ibutton(f"Super {s}", f"ve super hs")

        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_hs", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(3)
        await editMessage(self._reply_to, msg, buttons)
    
    async def hardsub_color_button(self):
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        color = hardsub.get("color", "putih")
        msg = "<b>📌 Silahkan pilih warna hardsub anda !</b>\n\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"

        butt = ButtonMaker()
        s = "" if not color == "putih" else "✅"
        butt.ibutton(f"Putih {s}", f"ve hs_cs putih")
        s = "" if not color == "merah" else "✅"
        butt.ibutton(f"Merah {s}", f"ve hs_cs merah")
        s = "" if not color == "hijau" else "✅"
        butt.ibutton(f"Hijau {s}", f"ve hs_cs hijau")
        s = "" if not color == "biru" else "✅"
        butt.ibutton(f"Biru {s}", f"ve hs_cs biru")
        s = "" if not color == "kuning" else "✅"
        butt.ibutton(f"Kuning {s}", f"ve hs_cs kuning")
        s = "" if not color == "cyan" else "✅"
        butt.ibutton(f"Cyan {s}", f"ve hs_cs cyan")
        s = "" if not color == "magenta" else "✅"
        butt.ibutton(f"Magenta {s}", f"ve hs_cs magenta")
        s = "" if not color == "purple" else "✅"
        butt.ibutton(f"Purple {s}", f"ve hs_cs purple")
        s = "" if not color == "hitam" else "✅"
        butt.ibutton(f"Hitam {s}", f"ve hs_cs hitam")

        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_hs", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(3)
        await editMessage(self._reply_to, msg, buttons)
    
    async def hardsub_font_button(self):
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        font = hardsub.get("font", 5)
        
        msg = "<b>📌 Silahkan pilih jenis font hardsub anda !</b>\n\n"
        msg += """<b>1.</b> Standard Symbols PS
<b>2.</b> Century Schoolbook L
<b>3.</b> URW Gothic
<b>4.</b> Nimbus Roman
<b>5.</b> DejaVu Sans Mono
<b>6.</b> URW Palladio L
<b>7.</b> Nimbus Sans
<b>8.</b> URW Gothic L
<b>9.</b> Dingbats
<b>10.</b> URW Chancery L
<b>11.</b> Nimbus Mono PS
<b>12.</b> Nimbus Sans Narrow
<b>13.</b> URW Bookman
<b>14.</b> DejaVu Sans
<b>15.</b> Noto Sans Mono
<b>16.</b> C059
<b>17.</b> Nimbus Sans L
<b>18.</b> Droid Sans Fallback
<b>19.</b> Z003
<b>20.</b> Standard Symbols L
<b>21.</b> D050000L
<b>22.</b> Nimbus Mono L
<b>23.</b> Nimbus Roman No9 L
<b>24.</b> Noto Mono
<b>25.</b> P052
<b>26.</b> DejaVu Serif
<b>27.</b> URW Bookman L"""
    
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        for i in range(1, 28):
            s = "✅" if font == i else ""
            butt.ibutton(f"{i} {s}", f"ve hs_fs {i}")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_hs", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(5)
        await editMessage(self._reply_to, msg, buttons)
    
    async def hardsub_bold_button(self):
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        bold = hardsub.get("bold", False)
        if bold == True:
            bold = False
        else:
            bold = True
        hardsub["bold"] = bold
        await self.hardsub_main_button()
    
    async def hardsub_position_button(self):
        hardsub = self.video_editor.get("hardsub", None)
        if not hardsub:
            hardsub = self.video_editor["hardsub"] = {}
        position = hardsub.get("position", "bawah")
        if position == "atas":
            position = "bawah"
        else:
            position = "atas"
        hardsub["position"] = position
        await self.hardsub_main_button()
    
    async def softsub_main_button(self):
        msg = "<b>📌 Silahkan masukkan subtitle anda (Support multi subtitle) </b>\n\n"
        softsub = self.video_editor.get("softsub", None)
        if not softsub:
            softsub = self.video_editor["softsub"] = []
        for index, sub in enumerate(softsub):
            sub_name = os.path.basename(sub['file'])
            msg += f"<b>{index+1}.</b>{sub_name} (<code>{sub['language']}</code>)\n"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        s = "➕" if softsub else ""
        if softsub:
            butt.ibutton(f"{s} Tambah Subtitle", f"ve ss_file", position="header")
        else:
            butt.ibutton(f"Masukkan Subtitle", f"ve ss_file", position="header")
        for i in range(0, len(softsub)):
            butt.ibutton(f"Hapus Subtitle {i+1}", f"ve ss_del {i}")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def softsub_file_button(self):
        msg = "<b>📌 Silahkan kirimkan file subtitle anda, support jenis subtitle .srt, .ass, .ssa, .vtt\n\n"
        softsub = self.video_editor.get("softsub", None)
        file = ""
        language = ""
        if not softsub:
            softsub = self.video_editor["softsub"] = []
        try:
            ask = await sendMessage(self._listener.message, f"{msg}\n\nKlik /batal untuk membatalkan")
            respon = await bot.listen(
                filters= filters.user(self._listener.user_id), timeout=30
                )
            if respon and respon.text != "/batal" and respon.text != f"/batal@{bot.me.username}":
                try:
                    msg = respon
                    uid = self._listener.user_id
                    file += await storeSubFile(msg, uid, soft=True)
                except: 
                    pass
            await respon.delete()
            await deleteMessage(ask)
            ask = await sendMessage(self._listener.message, "<b>📌 Silahkan masukkan keterangan bahasa untuk subtitle ini, contoh <code>Indonesia, English, Malaysia, China dll.</code></b>\n\nKlik /skip jika tidak tahu")
            respon = await bot.listen(
                filters= filters.user(self._listener.user_id), timeout=30
            )
            if respon and respon.text != "/skip" and respon.text != f"/skip@{bot.me.username}":
                language = respon.text
            else:
                language = "Tidak Diketahui"
            softsub.append({"file": file, "language": language})
            self.video_editor["softsub"] = softsub
            await respon.delete()
            await deleteMessage(ask)
            await self.softsub_main_button()
        except:
            await deleteMessage(ask)
            await self.softsub_main_button()
    
    async def extract_subtitle(self):
        msg = "<b>📌 Anda akan mengextract semua stream dari video ini, seperti video,audio,subtitle,cover dll !!</b>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("👀 Mulai Extract Stream", f"ve extract_true")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def merge_stream(self):
        msg = "<b>📌 Silahkan pilih type merge anda!</b>"
        msg += "\n\n<b>⚠️ Note:</b> Gunakan fitur multi mirror dan samedir untuk menggunakan fitur ini, atau gunakan link folder yang berisi multi video atau audio.\n"
        msg += f"<i>Klik <a href='https://t.me/pikachukocak2/113'><b>DISINI</b></a> untuk melihat cara penggunaan fitur ini dengan samedir.</i>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("🎞️ Merge Video+Video", f"ve merge_video")
        butt.ibutton("🎥 Merge Video+Audio", f"ve merge_audio")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(1)
        await editMessage(self._reply_to, msg, buttons)

    async def merge_video_video(self):
        msg = "<b>📌 Anda akan menggabungkan semua video yang ada didalam folder menjadi satu video !</b>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("▶️ Start Merge Video+Video", f"ve video_start")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_merge", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(1)
        await editMessage(self._reply_to, msg, buttons)
    
    async def merge_video_audio(self):
        msg = "<b>📌 Anda akan menggabungkan video dengan semua audio yang ada didalam folder !</b>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("▶️ Start Merge Video+Audio", f"ve audio_start")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back_merge", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(1)
        await editMessage(self._reply_to, msg, buttons)
    
    async def encoding_main(self):
        msg = "<b>📌 Silahkan pilih menu encoding anda !</b>\n\n"
        video_encoder = self.video_editor.get("video_codec", "default")
        audio_encoder = self.video_editor.get("audio_codec", "default")
        video_bitrate = self.video_editor.get("video_bitrate", "default")
        audio_bitrate = self.video_editor.get("audio_bitrate", "default")
        crf = self.video_editor.get("crf", 23)
        preset = self.video_editor.get("preset", "veryfast")
        msg += f"<b>• Video Encoder:</b> <code>{video_encoder}</code>\n"
        msg += f"<b>• Video Bitrate:</b> <code>{video_bitrate}</code>\n"
        msg += f"<b>• Audio Encoder:</b> <code>{audio_encoder}</code>\n"
        msg += f"<b>• Audio Bitrate:</b> <code>{audio_bitrate}</code>\n"
        msg += f"<b>• CRF:</b> <code>{crf}</code>\n"
        msg += f"<b>• Preset:</b> <code>{preset}</code>\n"
        msg += f"<b>\n⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Video Encoder", f"ve v_encoder")
        butt.ibutton("Video Bitrate", f"ve v_bitrate")
        butt.ibutton("Audio Encoder", f"ve a_encoder")
        butt.ibutton("Audio Bitrate", f"ve a_bitrate")
        butt.ibutton("Preset", f"ve preset_main")
        butt.ibutton("CRF", f"ve crf_main")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve back", position="footer")
        butt.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"ve cancel", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def video_encoder_button(self):
        msg = "<b>📌 Silahkan pilih video encoder anda !</b>\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Default", f"ve v_enc default", position="header")
        butt.ibutton("H.264", f"ve v_enc libx264")
        butt.ibutton("H.265", f"ve v_enc libx265")
        butt.ibutton("VP8", f"ve v_enc libvpx")
        butt.ibutton("VP9", f"ve v_enc libvpx-vp9")
        butt.ibutton("AV1", f"ve v_enc libaom-av1")
        butt.ibutton("Theora", f"ve v_enc libtheora")
        butt.ibutton("MPEG4", f"ve v_enc mpeg4")
        butt.ibutton("MPEG2", f"ve v_enc mpeg2video")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def video_bitrate_button(self):
        msg = "<b>📌 Silahkan pilih video bitrate anda !</b>\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Default", f"ve v_br default", position="header")
        butt.ibutton("0.5 Mbps", f"ve v_br 500k")
        butt.ibutton("1.2 Mbps", f"ve v_br 1200k")
        butt.ibutton("2 Mbps", f"ve v_br 2000k")
        butt.ibutton("3 Mbps", f"ve v_br 3000k")
        butt.ibutton("4 Mbps", f"ve v_br 4000k")
        butt.ibutton("5 Mbps", f"ve v_br 5000k")
        butt.ibutton("6 Mbps", f"ve v_br 6000k")
        butt.ibutton("7 Mbps", f"ve v_br 7000k")
        butt.ibutton("8 Mbps", f"ve v_br 8000k")
        butt.ibutton("9 Mbps", f"ve v_br 9000k")
        butt.ibutton("10 Mbps", f"ve v_br 10000k")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def audio_encoder_button(self):
        msg = "<b>📌 Silahkan pilih audio encoder anda !</b>\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Default", f"ve a_enc default", position="header")
        butt.ibutton("AAC", f"ve a_enc aac")
        butt.ibutton("MP3", f"ve a_enc libmp3lame")
        butt.ibutton("Opus", f"ve a_enc libopus")
        butt.ibutton("Vorbis", f"ve a_enc libvorbis")
        butt.ibutton("WAV", f"ve a_enc pcm_s16le")
        butt.ibutton("MPEG", f"ve a_enc mpeg")
        butt.ibutton("FLAC", f"ve a_enc flac")
        butt.ibutton("ALAC", f"ve a_enc alac")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def audio_bitrate_button(self):
        msg = "<b>📌 Silahkan pilih audio bitrate anda !</b>\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Default", f"ve a_br default", position="header")
        butt.ibutton("32 kbps", f"ve a_br 32k")
        butt.ibutton("64 kbps", f"ve a_br 64k")
        butt.ibutton("96 kbps", f"ve a_br 96k")
        butt.ibutton("128 kbps", f"ve a_br 128k")
        butt.ibutton("192 kbps", f"ve a_br 192k")
        butt.ibutton("256 kbps", f"ve a_br 256k")
        butt.ibutton("320 kbps", f"ve a_br 320k")
        butt.ibutton("512 kbps", f"ve a_br 512k")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def preset_button(self):
        msg = "<b>📌 Silahkan pilih preset anda !</b>\n\n"
        msg += "<b>⚠️ Note:</b> Semakin cepat proses kompresi, semakin besar ukuran file video\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        butt.ibutton("Ultrafast", f"ve preset ultrafast")
        butt.ibutton("Superfast", f"ve preset superfast")
        butt.ibutton("Veryfast", f"ve preset veryfast")
        butt.ibutton("Faster", f"ve preset faster")
        butt.ibutton("Fast", f"ve preset fast")
        butt.ibutton("Medium", f"ve preset medium")
        butt.ibutton("Slow", f"ve preset slow")
        butt.ibutton("Slower", f"ve preset slower")
        butt.ibutton("Veryslow", f"ve preset veryslow")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(2)
        await editMessage(self._reply_to, msg, buttons)
    
    async def crf_button(self):
        msg = "<b>📌 Silahkan pilih crf anda !</b>\n\n"
        msg += "<b>⚠️ Note:</b> Semakin kecil crf, semakin bagus kualitas video tapi proses kompresi semakin lama\n\n"
        msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        butt = ButtonMaker()
        for i in range(18, 29):
            butt.ibutton(str(i), f"ve crf {i}")
        butt.ibutton("🔙 𝙺𝚎𝚖𝚋𝚊𝚕𝚒", f"ve encoder_back", position="footer")
        buttons = butt.build_menu(5)
        await editMessage(self._reply_to, msg, buttons)
            
    async def start(self):
        self.event.set()

    async def back(self):      
        msg, buttons = await self.home_button()
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        await editMessage(self._reply_to, msg, buttons)
    
    async def cancel(self):
        watermark = self.video_editor.get("watermark", {})
        hardsub = self.video_editor.get("hardsub", {})
        softsub = self.video_editor.get("softsub", [])
        if watermark:
            try:
                await aioremove(watermark["file"])
            except:
                pass
        if hardsub:
            try:
                await aioremove(hardsub["file"])
            except:
                pass
        if softsub:
            for sub in softsub:
                try:
                    await aioremove(sub["file"])
                except:
                    continue