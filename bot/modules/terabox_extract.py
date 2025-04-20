from pyrogram.filters import regex, user
from pyrogram.handlers import CallbackQueryHandler
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.ext_utils.bot_utils import (
    new_task,
    new_thread,
)
from functools import partial
from time import time
from asyncio import wait_for, Event, wrap_future
from bot.helper.ext_utils.status_utils import get_readable_time
from random import choice
from bot.helper.ext_utils.terabox_scraper import CariFile, CariLink
from asyncio import gather, Semaphore

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()
    if data[1] =="start":
        await obj.start(data[2])
    if data[1] == "random":
        await obj.random_server()

    elif data[1] == "cancel":
        await editMessage(message, "<b>Tugas dibatalkan oleh User!</b>")
        obj.is_cancelled = True
        obj.event.set()
        
@new_task
async def terabox_extract(url, server):
    details = {"contents": [], "title": "", "total_size": 0}
    async def process_file(file_info):
        if file_info.get('is_dir') == 1 or file_info.get('is_dir') == '1':
            tasks = []
            for sub_item in file_info.get('list', []):
                tasks.append(process_file(sub_item))
            if tasks:
                await gather(*tasks)
        else:
            name = file_info['name']
            Size = file_info['size']
            path = file_info['path']
            terabox_link = CariLink(
                shareid=terabox_file.result['shareid'],
                uk=terabox_file.result['uk'],
                sign=terabox_file.result['sign'],
                timestamp=terabox_file.result['timestamp'],
                fs_id=file_info['fs_id'],
                server_filename=server,
            )
            await terabox_link.generate()
            link = terabox_link.result['download_link'].get('url')
            async with semaphore:
                details["contents"].append(
                    {"url": link, "filename": name, "path": path}
                )
                try:
                    if Size:
                        if isinstance(Size, str):
                            if Size.isdigit():
                                size_value = float(Size)
                                details["total_size"] += size_value
                        else:
                            size_value = float(Size)
                            details["total_size"] += size_value
                except:
                    pass
    
    semaphore = Semaphore(20)
    terabox_file = CariFile()
    await terabox_file.search(url)
    if terabox_file.result['status'] == 'success':
        file_tasks = [process_file(file_info) for file_info in terabox_file.result['list']]
        await gather(*file_tasks)
        
        if terabox_file.result['list']:
            details["title"] = terabox_file.result['list'][0]['name']
    else:
        raise Exception("ERROR: Link File tidak ditemukan!")
    if not details["contents"]:
        raise Exception("ERROR: Link sepertinya tidak valid")
    if len(details["contents"]) == 1:
        return details["contents"][0]["url"]
    return details

class teraboxExtract:
    def __init__(self, listener):
        self._listener = listener
        self._time = time()
        self._timeout = 300
        self.event = Event()
        self._servers = {
            'server_1': 'plain-grass-58b2.comprehensiveaquamarine',
            'server_2':'royal-block-6609.ninnetta7875',
            'server_3':'bold-hall-f23e.7rochelle',
            'server_4':'winter-thunder-0360.belitawhite',
            'server_5':'fragrant-term-0df9.elviraeducational',
            'server_6':'purple-glitter-924b.miguelalocal'
            }
        self._link = ""
        self._final_link = None
        self._reply_to = None
        self.is_cancelled = False

    @new_thread
    async def _event_handler(self):
        pfunc = partial(main_select, obj=self)
        handler = self._listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^terabox") & user(self._listener.user_id)
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
            
    async def main(self, link):
        self._link = link
        future = self._event_handler()
        keys = list(self._servers.keys())
        butt = ButtonMaker()
        for i in keys:
            butt.ibutton(f"{i}", f"terabox start {i}")
        butt.ibutton("🔄️ Random", f"terabox random", position="footer")
        butt.ibutton("⛔ Batal", f"terabox cancel", position="footer")
        butts = butt.build_menu(2)
        msg = f"<b>Silahkan pilih salah satu server mirror Terabox yang tersedia.</b>"
        msg += f"\n\n<b>⏰ Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        self._reply_to = await sendMessage(self._listener.message, msg, butts)
        await wrap_future(future)
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self._final_link
    
    async def start(self, server):
        await editMessage(self._reply_to, f"<b>Mengambil direct link, silahkan tunggu...</b>")
        try:
            self._final_link = await terabox_extract(self._link, self._servers[server])
        except Exception as e:
            await editMessage(self._reply_to, f"<b>{e}</b>")
            self.is_cancelled = True
        self.event.set()
    
    async def random_server(self):
        server = choice(list(self._servers.keys()))
        await self.start(server)