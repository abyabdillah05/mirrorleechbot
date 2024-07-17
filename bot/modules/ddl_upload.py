import os
import subprocess
import aiohttp
import asyncio
import uuid

from asyncio import create_subprocess_exec
from bot import bot
from time import time, sleep
from datetime import datetime
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      editMessage,
                                                      deleteMessage,)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from pyrogram.filters import command, regex

################################################
#GOFILE_DOWNLOADER
################################################
tasks = {}

async def upload_ddl_main(client, message):
    await ddl_downloader(client, message).upload_ddl()


async def ddl_query(_, query):
        message = query.message
        user_id = query.from_user.id
        data = query.data.split()
        if user_id != int(data[1]):
            return await query.answer(text="Bukan tugas darimu!", show_alert=True)
        elif data[2] == "cancel":
            if data[3] in tasks:
                try:
                    tasks[data[3]].cancel()
                except:
                    return await query.answer(text="Tugas tidak ditemukan!", show_alert=True)

class ddl_downloader():
    def __init__(self, client, message):
        self.message = message
        self.client = client
        self.main_msg = None
        self.token = None
        self._start_time = time()
        self._start_datenow = datetime.now()

    async def download_aria2(self, url, output_dir, headers=None):
        command = ['chrome', url, '-d', output_dir]
        if headers:
            for key, value in headers.items():
                command.extend(['--header', f'{key}: {value}'])
        
        try:
            process = await create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                file_paths = []
                for root, _, files in os.walk(output_dir):
                    for file_name in files:
                        file_paths.append(os.path.join(root, file_name))
                return file_paths
            else:
                raise DirectDownloadLinkException({stderr.decode().strip()})
        except Exception as e:
            return DirectDownloadLinkException(f"ERROR: {e}")

    async def download_telegram(self, uid, file_id, output_dir):
        async def progress(current, total):
            if total == 0:
                total = 1
            butt = ButtonMaker()
            butt.ibutton("⛔️ Batal", f"ddl_cancel {uid} cancel {self.token}")
            butts = butt.build_menu(1)
            sleep(3)
            if current == total:
                return
            current_time = time()
            start_time = self._start_time
            check_time = current_time - start_time
            
            if datetime.now() > self._start_datenow:
                percentage = current * 100 / total
                percentage = str(round(percentage, 2))
                speed = current / check_time
                eta = int((total - current) / speed)
                eta = get_readable_time(eta)
                if not eta:
                    eta = "0 sec"
                total_size = get_readable_file_size(total)
                completed_size = get_readable_file_size(current)
                speed = get_readable_file_size(speed)
                msg = f"""
<b> Mendownload media dari telegram </b>

<b>Ukuruan File:</b> {total_size}
<b>Proses:</b> {completed_size} 
<b>Percentage:</b> {percentage[:5]}%
<b>Speed:</b> {speed}/s
<b>ETA:</b> {eta}"""
            await editMessage(self.main_msg, msg, butts)
        try:
            download = await bot.download_media(file_id, output_dir, progress=progress)
            file_path = [os.path.relpath(download, start=os.getcwd())]
            return file_path
        except Exception as e:
            return (f"ERROR: {e}")

    async def upload_gofile(self, file_path):
        url = 'https://store1.gofile.io/contents/uploadfile'
        headers = {}
        #if token:
        #    headers['Authorization'] = f'Bearer {token}'

        data = aiohttp.FormData()
        data.add_field('file', open(file_path[0], 'rb'))
        #if folder_id:
        #    data.add_field('folderId', folder_id)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    return {"status": "error", "message": f"Gagal upload ke Gofile: {response.status}"}

    async def upload_ddl(self):
        url = None
        file_ = None
        file_name = None
        rply = self.message.reply_to_message
        if rply:
            if rply.text:
                url = rply.text if rply.caption is None else rply.caption
            else:
                file = (rply.photo 
                        or rply.document
                        or rply.video
                        or rply.audio
                        or rply.voice
                        or rply.video_note
                        or rply.sticker
                        or rply.animation
                        )
                if file is not None:
                    file_ = file.file_id
                    try:
                        file_name = file.file_name
                    except:
                        file_name = f"file_{file.file_id}"
        else:
            msg = self.message.text.split(maxsplit=1)
            if len(msg) > 1:
                url = msg[1].strip()
            else:
                await sendMessage (self.message, "Silahkan kirimkan link atau balas sebuah file yang akan diunggah ke Gofile !!.")
                return
        
        # DOWNLOAD
        custom_headers = None
        output_dir = "gofile/"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        uid = self.message.from_user.id
        self.token = uuid.uuid4().hex[:6]
        uname = self.message.from_user.mention
        if uname is None:
            uname = self.message.from_user.first_name
        butt = ButtonMaker()
        butt.ibutton("⛔️ Batal", f"ddl_cancel {uid} cancel {self.token}")
        butts = butt.build_menu(1)
        #if uid in tasks:
        #    await sendMessage(self.message, 'Tugas anda sebelumnya masih diproses, silahkan tunggu atau batalkan terlebih dahulu !')
        #    return
        
        self.main_msg = await sendMessage(self.message, '<b>Sedang mengunduh file anda, silahkan tunggu....</b>', butts)
        if file_ is not None:
            task = asyncio.create_task(self.download_telegram(uid, file_, output_dir))
        else:
            task = asyncio.create_task(self.download_aria2(url, output_dir, custom_headers))
        tasks[self.token] = task
        try:
            file_path = await task
        except asyncio.CancelledError:
            await sendMessage(self.message, f"<b>Hai {uname}, Proses download dibatalkan !</b>")
            try:
                for file in file_path:
                    os.remove(file)
            except:
                pass
            await deleteMessage(self.main_msg)
            tasks.pop(self.token, None)
            return
        except Exception as e:
            await sendMessage(self.message, f"ERROR: <b>Hai {uname}, Terjadi kesalahan saat mendownload file</b> {e.__class__.__name__}")
            await deleteMessage(self.main_msg)
            tasks.pop(self.token, None)
            return

        # Upload
        await editMessage(self.main_msg, 'Sedang mengupload ke Gofile, silahkan tunggu....', butts)
        if file_path:
            task = asyncio.create_task(self.upload_gofile(file_path))
            tasks[self.token] = task
            try:
                r = await task
                if r.get("status") == "ok":
                    data = r["data"]
                    id = data["code"]
                    file_name = data["fileName"]
                    link = data["downloadPage"]
                    md5 = data["md5"]
                    butt = ButtonMaker()
                    butt.ubutton("🔗 Download Link", link)
                    butts = butt.build_menu(1)
                    msg = "<b>✅ File anda berhasil diunggah ke gofile:</b>\n\n"
                    msg +=f"<b>📄 File Name:</b> <code>{file_name}</code>\n"
                    msg +=f"<b>🏷️ File ID:</b> {id}\n"
                    msg +=f"<b>⚙️ MD5:</b> <code>{md5}</code>\n"
                    await sendMessage(self.message, msg, butts)
                else:
                    await sendMessage(self.message, "Gagal mengupload file:", r.get("message"))
                    return
            except asyncio.CancelledError:
                await sendMessage(self.message, f"<b>Hai {uname}, Proses upload ke Gofile dibatalkan !</b>")
            except Exception as e:
                await sendMessage(self.message, f"ERROR: <b>Hai {uname}, Terjadi kesalahan saat mengupload ke Gofile</b> {e.__class__.__name__}")
                return
            finally:
                try:
                    for file in file_path:
                        os.remove(file)
                except:
                    pass
                tasks.pop(self.token, None)
                await deleteMessage(self.main_msg)
        else:
            await sendMessage(self.message, f"Hai {uname}, file yang coba diupload tidak ditemukan !, silahkan coba kembali")
            await deleteMessage(self.main_msg)
            tasks.pop(self.token, None)
            return
            

bot.add_handler(
    MessageHandler(
        upload_ddl_main, 
        filters=command(
            BotCommands.Upload_ddlCommand
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    CallbackQueryHandler(
        ddl_query,
        filters=regex(
            r'^ddl_cancel'
        )
    )
)