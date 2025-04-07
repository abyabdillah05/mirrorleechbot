from aiohttp import ClientSession
from re import findall
from bs4 import BeautifulSoup
from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.ext_utils.bot_utils import (
    new_task,
    new_thread,
    sync_to_async,
)
from functools import partial
from time import time
from asyncio import wait_for, Event, wrap_future
from bot.helper.ext_utils.status_utils import get_readable_time
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot import bot

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()
    
    if data[1] == "start":
        await obj.start(data[2])
    elif data[1] == "cancel":
        await editMessage(message, "<b>❌ Tugas dibatalkan oleh User!</b>")
        obj.is_cancelled = True
        obj.event.set()
        
@new_task
async def sourceforge_extract(url):
    async with ClientSession() as session:
        try:
            if url.endswith("/download"):
                url = url.split("/download")[0]
                
            try:
                link = findall(r"\bhttps?://sourceforge\.net\S+", url)[0]
            except IndexError:
                raise DirectDownloadLinkException(
                    "⚠️ ERROR: Link SourceForge tidak ditemukan!"
                )
            
            file_id = findall(r"files(.*)", link)[0]
            project = findall(r"projects?/(.*?)/files", link)[0]
            
            async with session.get(
                f"https://sourceforge.net/settings/mirror_choices?projectname={project}&filename={file_id}"
            ) as response:
                content = await response.text()
                
            soup = BeautifulSoup(content, "html.parser")
            mirror_list = soup.find("ul", {"id": "mirrorList"})
            
            if not mirror_list:
                raise DirectDownloadLinkException("⚠️ ERROR: Tidak dapat menemukan daftar mirror server!")
                
            mirror = mirror_list.findAll("li")
            servers = []
            
            for i in mirror:
                servers.append(i['id'])
                
            if servers and servers[0] == "autoselect":
                servers.pop(0)
                
            return servers
        except Exception as e:
            raise DirectDownloadLinkException(f"⚠️ ERROR: {str(e)}")


class sourceforgeExtract:
    def __init__(self, listener):
        self._listener = listener
        self._time = time()
        self._timeout = 160
        self.event = Event()
        self._servers = []
        self._link = ""
        self._final_link = ""
        self._reply_to = None
        self.is_cancelled = False

    @new_thread
    async def _event_handler(self):
        pfunc = partial(main_select, obj=self)
        handler = self._listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^sourceforge") & user(self._listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except:
            await editMessage(self._reply_to, "<b>⏰ Waktu habis, Tugas dibatalkan!</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
            
    async def main(self, link):
        self._link = link
        future = self._event_handler()
        
        try:
            self._servers = await sourceforge_extract(link)
        except DirectDownloadLinkException as e:
            await sendMessage(self._listener.message, str(e))
            self.is_cancelled = True
            self.event.set()
            return
            
        butt = ButtonMaker()
        
        if isinstance(self._servers, list) and self._servers:
            for i in self._servers:
                butt.ibutton(f"🌐{i}", f"sourceforge start {i}")
                
            butt.ibutton("❌ Batal", f"sourceforge cancel", position="footer")
            butts = butt.build_menu(3)
            
            msg = f"<b>📡 Pemilihan Server Mirror Sourceforge</b>\n\n"
            msg += f"<b>📂 Project:</b> <code>{findall(r'projects?/(.*?)/files', self._link)[0]}</code>\n"
            msg += f"<b>🌐 Silahkan pilih salah satu server mirror yang tersedia:</b>\n"
            msg += f"<i>Tip: Pilih server yang terdekat dengan lokasi Anda untuk kecepatan optimal</i>\n\n"
            msg += f"<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
            msg += f"\n\n<b>Powered By {bot.me.first_name}</b>"
            
            self._reply_to = await sendMessage(self._listener.message, msg, butts)
        else:
            await sendMessage(self._listener.message, "⚠️ ERROR: Tidak ada server mirror yang tersedia!")
            self.is_cancelled = True
            self.event.set()
            return
            
        await wrap_future(future)
        
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self._final_link
    
    async def start(self, server):
        try:
            file_id = findall(r"files(.*)", self._link)[0].replace("/download", "")
            project = findall(r"projects?/(.*?)/files", self._link)[0]
            
            self._final_link = f"https://{server}.dl.sourceforge.net/project/{project}{file_id}?viasf=1"
            
            await editMessage(
                self._reply_to, 
                f"<b>✅ Server mirror dipilih:</b> <code>{server}</code>\n<b>🔄 Memproses download...</b>"
            )
            
            self.event.set()
        except Exception as e:
            await editMessage(self._reply_to, f"<b>⚠️ Error memproses server:</b> <code>{str(e)}</code>")
            self.is_cancelled = True
            self.event.set()