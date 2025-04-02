import os
from requests import utils as rutils
from aiofiles.os import path as aiopath, listdir, makedirs, remove as aioremove
from html import escape
from aioshutil import move
from asyncio import sleep, Event, gather
from time import time

from bot import (
    bot,
    Interval,
    aria2,
    DOWNLOAD_DIR,
    task_dict,
    task_dict_lock,
    LOGGER,
    DATABASE_URL,
    config_dict,
    non_queued_up,
    non_queued_dl,
    queued_up,
    queued_dl,
    queue_dict_lock,
)
from bot.helper.ext_utils.files_utils import (
    get_path_size,
    clean_download,
    clean_target,
    join_files,
    get_md5,
)
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    delete_status,
    editMessage,
    deleteMessage,
    update_status_message,
    customSendMessage,
)
from bot.helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.links_utils import is_gdrive_id
from bot.helper.ext_utils.task_manager import start_from_queued
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.mirror_utils.status_utils.telegram_status import TelegramStatus
from bot.helper.mirror_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_utils.status_utils.queue_status import QueueStatus
from bot.helper.mirror_utils.status_utils.ddlupload_status import DdlUploadStatus
from bot.helper.mirror_utils.gdrive_utils.upload import gdUpload
from bot.helper.mirror_utils.telegram_uploader import TgUploader
from bot.helper.mirror_utils.rclone_utils.transfer import RcloneTransferHelper
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.common import TaskConfig
from bot.helper.ext_utils.quota_utils import update_quota

from bot.helper.mirror_utils.ddl_uploader import DdlUploader
from bot.helper.ext_utils.files_utils import get_mime_type

class TaskListener(TaskConfig):
    def __init__(self, message):
        super().__init__(message)

    async def clean(self):
        try:
            if Interval:
                for intvl in list(Interval.values()):
                    intvl.cancel()
            Interval.clear()
            await gather(sync_to_async(aria2.purge), delete_status())
        except:
            pass

    def removeFromSameDir(self):
        if self.sameDir and self.mid in self.sameDir["tasks"]:
            self.sameDir["tasks"].remove(self.mid)
            self.sameDir["total"] -= 1

    async def onDownloadStart(self):
        if (
            self.isSuperChat
            and config_dict["INCOMPLETE_TASK_NOTIFIER"]
            and DATABASE_URL
        ):
            await DbManger().add_incomplete_task(
                self.message.chat.id, self.message.link, self.tag
            )

    async def onDownloadComplete(self):
        multi_links = False
        if self.sameDir and self.mid in self.sameDir["tasks"]:
            while not (
                self.sameDir["total"] in [1, 0]
                or self.sameDir["total"] > 1
                and len(self.sameDir["tasks"]) > 1
            ):
                await sleep(0.5)

        async with task_dict_lock:
            if (
                self.sameDir
                and self.sameDir["total"] > 1
                and self.mid in self.sameDir["tasks"]
            ):
                self.sameDir["tasks"].remove(self.mid)
                self.sameDir["total"] -= 1
                folder_name = self.sameDir["name"]
                spath = f"{self.dir}{folder_name}"
                des_path = (
                    f"{DOWNLOAD_DIR}{list(self.sameDir['tasks'])[0]}{folder_name}"
                )
                await makedirs(des_path, exist_ok=True)
                for item in await listdir(spath):
                    if item.endswith((".aria2", ".!qB")):
                        continue
                    item_path = f"{self.dir}{folder_name}/{item}"
                    if item in await listdir(des_path):
                        await move(item_path, f"{des_path}/{self.mid}-{item}")
                    else:
                        await move(item_path, f"{des_path}/{item}")
                multi_links = True
            download = task_dict[self.mid]
            self.name = download.name()
            gid = download.gid()
        LOGGER.info(f"Download completed: {self.name}")

        if multi_links:
            await self.onUploadError("Selesai diunduh, Menunggu tugas unduh lain selesai diunduh...")
            return

        if not await aiopath.exists(f"{self.dir}/{self.name}"):
            try:
                files = await listdir(self.dir)
                self.name = files[-1]
                if self.name == "yt-dlp-thumb":
                    self.name = files[0]
            except Exception as e:
                await self.onUploadError(str(e))
                return

        up_path = f"{self.dir}/{self.name}"
        size = await get_path_size(up_path)
        async with queue_dict_lock:
            if self.mid in non_queued_dl:
                non_queued_dl.remove(self.mid)
        await start_from_queued()

        if self.join and await aiopath.isdir(up_path):
            await join_files(up_path)

        if self.extract:
            up_path = await self.proceedExtract(up_path, size, gid)
            if not up_path:
                return
            up_dir, self.name = up_path.rsplit("/", 1)
            size = await get_path_size(up_dir)
        
        if self.dump:
            _, ext = os.path.splitext(up_path)
            if os.path.isdir(up_path) or ext.lower() not in ('.zip', '.tgz', '.7z', '.img'):
                await self.onUploadError("Jenis file tidak didukung untuk proses Dumping !\n\nHanya support file dengan ekstensi <code>.zip, .tgz, .7z, .img</code>")
                return
            up_path = await self.proceedDump(up_path, size, gid)
            if not up_path:
                await self.onUploadError("Proses Dumping gagal, pastikan ROM yang anda berikan berisi <code>payload.bin atau super.img</code> yang valid !")
                return
            up_dir, self.name = up_path.rsplit("/", 1)
            size = await get_path_size(up_dir)

        if self.sampleVideo:
            up_path = await self.generateSampleVideo(up_path, size, gid)
            if not up_path:
                return
            up_dir, self.name = up_path.rsplit("/", 1)
            size = await get_path_size(up_dir)
        
        if self.video_editor:
            up_path = await self.VideoEditor(up_path, size, gid)
            if not up_path:
                return
            up_dir, self.name = up_path.rsplit("/", 1)
            size = await get_path_size(up_dir)

        if self.compress:
            up_path = await self.proceedCompress(up_path, size, gid)
            if not up_path:
                return
            
        if self.upDest in ("pd", "pixeldrain"):
            if os.path.isdir(up_path):
                up_path = await self.proceedCompress(up_path, size, gid)
                if not up_path:
                    return
        
        up_dir, self.name = up_path.rsplit("/", 1)
        size = await get_path_size(up_dir)
        if self.isLeech:
            m_size = []
            o_files = []
            if not self.compress:
                result = await self.proceedSplit(up_dir, m_size, o_files, size, gid)
                if not result:
                    return

        up_limit = config_dict["QUEUE_UPLOAD"]
        all_limit = config_dict["QUEUE_ALL"]
        add_to_queue = False
        async with queue_dict_lock:
            dl = len(non_queued_dl)
            up = len(non_queued_up)
            if (
                all_limit and dl + up >= all_limit and (not up_limit or up >= up_limit)
            ) or (up_limit and up >= up_limit):
                add_to_queue = True
                LOGGER.info(f"Added to Queue/Upload: {self.name}")
                event = Event()
                queued_up[self.mid] = event
        if add_to_queue:
            async with task_dict_lock:
                task_dict[self.mid] = QueueStatus(self, size, gid, "Up")
            await event.wait()
            async with task_dict_lock:
                if self.mid not in task_dict:
                    return
            LOGGER.info(f"Start from Queued/Upload: {self.name}")
        async with queue_dict_lock:
            non_queued_up.add(self.mid)

        if self.isLeech:
            size = await get_path_size(up_dir)
            for s in m_size:
                size -= s
            LOGGER.info(f"Leech Name: {self.name}")
            tg = TgUploader(self, up_dir)
            async with task_dict_lock:
                task_dict[self.mid] = TelegramStatus(self, tg, size, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                tg.upload(o_files, m_size, size),
            )

        elif self.upDest == "gf" or self.upDest == "gofile":
            self.isGofile = True
            size = await get_path_size(up_path)
            LOGGER.info(f"Upload to Gofile, Name: {self.name}")
            gf = DdlUploader(self, up_path)
            async with task_dict_lock:
                task_dict[self.mid] = DdlUploadStatus(self, gf, size, gid)
            if os.path.isdir(up_path):
                await gather(
                    update_status_message(self.message.chat.id),
                    sync_to_async(gf.gf_uploadFolder, size),
                )
            else:
                await gather(
                    update_status_message(self.message.chat.id),
                    sync_to_async(gf.gf_upload),
                )
        
        elif self.upDest == "bh" or self.upDest == "buzzheavier":
            #await self.onUploadError("Upload ke Buzzheavier sementara dinonaktifkan")
            #return
            self.isBuzzheavier = True
            size = await get_path_size(up_path)
            LOGGER.info(f"Upload to Buzzheavier, Name: {self.name}")
            bh = DdlUploader(self, up_path)
            async with task_dict_lock:
                task_dict[self.mid] = DdlUploadStatus(self, bh, size, gid)
            if os.path.isdir(up_path):
                await gather(
                    update_status_message(self.message.chat.id),
                    sync_to_async(bh.bh_upload_folder, size),
                )
            else:
                await gather(
                    update_status_message(self.message.chat.id),
                    sync_to_async(bh.bh_upload),
                )

        elif self.upDest == "pd" or self.upDest == "pixeldrain":
            self.isPixeldrain = True
            if os.path.isdir(up_path):
                await self.onUploadError("Folder anda gagal dicompress dan tidak bisa diupload ke Pixeldrain")
                return
            size = await get_path_size(up_path)
            LOGGER.info(f"Upload to Pixeldrain, Name: {self.name}")
            pd = DdlUploader(self, up_path)
            async with task_dict_lock:
                task_dict[self.mid] = DdlUploadStatus(self, pd, size, gid)
            await gather(
                update_status_message(self.message.chat.id),
                sync_to_async(pd.pd_upload, size),
            )

        elif is_gdrive_id(self.upDest):
            size = await get_path_size(up_path)
            LOGGER.info(f"Gdrive Upload Name: {self.name}")
            drive = gdUpload(self, up_path)
            async with task_dict_lock:
                task_dict[self.mid] = GdriveStatus(self, drive, size, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                sync_to_async(drive.upload, size),
            )
        else:
            size = await get_path_size(up_path)
            LOGGER.info(f"Rclone Upload Name: {self.name}")
            RCTransfer = RcloneTransferHelper(self)
            async with task_dict_lock:
                task_dict[self.mid] = RcloneStatus(self, RCTransfer, gid, "up")
            await gather(
                update_status_message(self.message.chat.id),
                RCTransfer.upload(up_path, size),
            )

    async def onUploadComplete(
        self, link, size, files, folders, mime_type, rclonePath="", dir_id="", server="",
    ):
        try:
            await update_quota(self.user_id, size)
        except:
            pass
        if (
            self.isSuperChat
            and config_dict["INCOMPLETE_TASK_NOTIFIER"]
            and DATABASE_URL
        ):
            await DbManger().rm_complete_task(self.message.link)
        lmsg = f"<b>✅ Tugas leech anda sudah selesai, total ada</b> <code>{folders}</code> <b>file.</b>\n"
        lmsg += f'<b>Waktu:</b> {get_readable_time(time() - self.extra_details["startTime"])}\n<i>Oleh:{self.tag}</i>\n\n'
        msg = f"<blockquote><b>📄 Nama :</b> <code>{escape(self.name)}</code></blockquote>"
        msg += f"\n<b>📦 Ukuran :</b> <code>{get_readable_file_size(size)}</code>"
        LOGGER.info(f"Task Done: {self.name}")
        if self.isLeech:
            msg += f"\n<b>📑 Jumlah File :</b> <code>{folders}</code>"
            msg += f"\n<b>⏱ Waktu</b>: {get_readable_time(time() - self.extra_details['startTime'])}"
            if mime_type != 0:
                lmsg += f"<code>{mime_type}</code> File rusak dan gagal diupload.\n\n"
                msg += f"\n\n<b>❗️ File Rusak :</b> <code>{mime_type}</code>"
            msg += f'\n\n<b>👤 Leech_Oleh :</b> {self.tag}\n\n'
            if not files:
                await sendMessage(self.message, lmsg)
            else:
                fmsg = ""
                buttons = ButtonMaker()
                buttons.ubutton("♻️ Leech Dump Channel", "https://t.me/+bzqjzHqeO8xjM2E1")
                buttons.ubutton("❤️ 𝚂𝚞𝚙𝚙𝚘𝚛𝚝 𝙼𝚎", "https://telegra.ph/Donate-and-Support-Us-03-21", "footer")
                button = buttons.build_menu(1)
                for index, (link, name) in enumerate(files.items(), start=1):
                    fmsg += f"<b>{index:02d}.</b> <a href='{link}'>{name}</a>\n"
                    if len(fmsg.encode() + msg.encode()) > 4000:
                        await sendMessage(self.message, lmsg + fmsg)
                        await sleep(1)
                        fmsg = ""
                if fmsg != "":
                    await sendMessage(self.message, lmsg + fmsg, button)
            if self.seed:
                if self.newDir:
                    await clean_target(self.newDir)
                async with queue_dict_lock:
                    if self.mid in non_queued_up:
                        non_queued_up.remove(self.mid)
                await start_from_queued()
                return
    

        else:
            msg += f"\n<b>🏷️ Tipe :</b> <code>{mime_type}</code>"
            msg += f'\n<b>⏱ Waktu:</b> {get_readable_time(time() - self.extra_details["startTime"])}'
            if mime_type != "Folder" and not self.isClone:
                if self.md5:
                    msg += f"\n<b>🛡️ MD5 Checksum:</b> <code>{self.md5}</code>"
                else:
                    msg += f"\n<b>🛡️ MD5 Checksum:</b> <code>{self.md5}</code>"
            if mime_type == "Folder":
                msg += f"\n<b>📂 Jumlah Folder :</b> <code>{folders}</code>"
                msg += f"\n<b>📄 Jumlah File :</b> <code>{files}</code>"
            if (
                link
                or rclonePath
                and config_dict["RCLONE_SERVE_URL"]
                and not self.privateLink
            ):
                buttons = ButtonMaker()
                if link:
                    if self.isGofile:
                        buttons.ubutton("☁️ 𝙶𝚘𝚏𝚒𝚕𝚎", link, position="header")
                    elif self.isBuzzheavier:
                        buttons.ubutton("☁️ 𝙱𝚞𝚣𝚣𝚑𝚊𝚟𝚒𝚎𝚛", link, position="header")
                    elif self.isPixeldrain:
                        buttons.ubutton("☁️ 𝙿𝚒𝚡𝚎𝚕𝚍𝚛𝚊𝚒𝚗", link, position="header")
                    else:
                        buttons.ubutton("☁️ 𝙲𝚕𝚘𝚞𝚍", link, position="header")
                if rclonePath:
                    msg += f"\n\n<b>📁 Path :</b> <code>{rclonePath}</code>"
                if server:
                    msg += f"\n<b>🖥️ Server :</b> <code>{server}</code>"
                if (
                    rclonePath
                    and (RCLONE_SERVE_URL := config_dict["RCLONE_SERVE_URL"])
                    and not self.privateLink
                ):
                    remote, path = rclonePath.split(":", 1)
                    url_path = rutils.quote(f"{path}")
                    share_url = f"{RCLONE_SERVE_URL}/{remote}/{url_path}"
                    if mime_type == "Folder":
                        share_url += "/"
                    buttons.ubutton("🔗 Rclone", share_url)
                if not rclonePath and dir_id:
                    msg += f"\n\n<code>⚠️ File/Folder ini hanya disimpan sementara di drive, segera download atau copy ke drive anda!</code>"
                    INDEX_URL = ""
                    if self.privateLink or self.upDest.startswith("mtp:"):
                        INDEX_URL = (
                            self.user_dict["index_url"]
                            if self.user_dict.get("index_url")
                            else ""
                        )
                    elif config_dict["INDEX_URL"]:
                        INDEX_URL = config_dict["INDEX_URL"]
                    if INDEX_URL:
                        share_url = f"{INDEX_URL}findpath?id={dir_id}"
                        if mime_type == "Folder":
                            buttons.ubutton("📁 Index", share_url, position="header")
                        else:
                            buttons.ubutton("⚡ Index", share_url, position="header")
                        if mime_type.startswith(("image", "video", "audio")):
                            share_urls = f"{INDEX_URL}findpath?id={dir_id}&view=true"
                            buttons.ubutton("🎬 Stream", share_urls, position="header")
                buttons.ubutton("❤️ 𝚂𝚞𝚙𝚙𝚘𝚛𝚝 𝙼𝚎", "https://telegra.ph/Donate-and-Support-Us-03-21", "footer")
                button = buttons.build_menu(3)
            else:
                msg += f"\n\n<b>📁 Path :</b> <code>{rclonePath}</code>"
                button = None
            msg += f"\n\n<b>👤 Tugas_Oleh :</b> {self.tag}"
            await sendMessage(self.message, msg, button)
            # Log Chat
            LOG_CHAT_ID = None
            LOG_CHAT_THREAD_ID = None
            if LOG_CHAT_ID := config_dict.get("LOG_CHAT_ID"):
                if not isinstance(LOG_CHAT_ID, int):
                    if ":" in LOG_CHAT_ID:
                        LOG_CHAT_THREAD_ID = LOG_CHAT_ID.split(":")[1]
                        LOG_CHAT_ID = LOG_CHAT_ID.split(":")[0]
                        
                if (
                    LOG_CHAT_ID
                    and not isinstance(LOG_CHAT_ID, int)
                    and (
                        LOG_CHAT_ID.isdigit() 
                        or LOG_CHAT_ID.startswith("-")
                    )
                ):
                    LOG_CHAT_ID = int(LOG_CHAT_ID)

                if (
                    LOG_CHAT_THREAD_ID
                    and not isinstance(LOG_CHAT_THREAD_ID, int)
                    and LOG_CHAT_THREAD_ID.isdigit()
                ):
                    LOG_CHAT_THREAD_ID= int(LOG_CHAT_THREAD_ID)
                        
                try:
                    await customSendMessage(
                        client=bot,
                        chat_id=LOG_CHAT_ID,
                        text=msg,
                        message_thread_id=LOG_CHAT_THREAD_ID,
                        buttons=button
                    )
                except Exception as e:
                    LOGGER.error(f"Failed when forward message => {e}")
            if self.seed:
                if self.newDir:
                    await clean_target(self.newDir)
                elif self.compress:
                    await clean_target(f"{self.dir}/{self.name}")
                async with queue_dict_lock:
                    if self.mid in non_queued_up:
                        non_queued_up.remove(self.mid)
                await start_from_queued()
                return

        await clean_download(self.dir)
        async with task_dict_lock:
            if self.mid in task_dict:
                del task_dict[self.mid]
            count = len(task_dict)
        if count == 0:
            if self.temp_thumb and await aiopath.exists(self.temp_thumb):
                await aioremove(self.temp_thumb)
            await self.clean()
        else:
            await update_status_message(self.message.chat.id)

        async with queue_dict_lock:
            if self.mid in non_queued_up:
                non_queued_up.remove(self.mid)
        await start_from_queued()

    async def onDownloadError(self, error, button=None):
        async with task_dict_lock:
            if self.mid in task_dict:
                del task_dict[self.mid]
            count = len(task_dict)
            self.removeFromSameDir()
        msg = f"<b>Hai {self.tag} !</b>\n<b>Tugasmu dihentikan karena :</b>\n\n{error}"
        await sendMessage(self.message, msg, button)
        if count == 0:
            if self.temp_thumb and await aiopath.exists(self.temp_thumb):
                await aioremove(self.temp_thumb)
            await self.clean()
        else:
            await update_status_message(self.message.chat.id)

        if (
            self.isSuperChat
            and config_dict["INCOMPLETE_TASK_NOTIFIER"]
            and DATABASE_URL
        ):
            await DbManger().rm_complete_task(self.message.link)

        async with queue_dict_lock:
            if self.mid in queued_dl:
                queued_dl[self.mid].set()
                del queued_dl[self.mid]
            if self.mid in queued_up:
                queued_up[self.mid].set()
                del queued_up[self.mid]
            if self.mid in non_queued_dl:
                non_queued_dl.remove(self.mid)
            if self.mid in non_queued_up:
                non_queued_up.remove(self.mid)

        await start_from_queued()
        await sleep(3)
        await clean_download(self.dir)
        if self.newDir:
            await clean_download(self.newDir)

    async def onUploadError(self, error):
        async with task_dict_lock:
            if self.mid in task_dict:
                del task_dict[self.mid]
            count = len(task_dict)
        msg = f"<b>Hai {self.tag} !</b>\n<b>Tugasmu dihentikan karena :</b>\n\n{error}"
        await sendMessage(self.message, msg)
        if count == 0:
            if self.temp_thumb and await aiopath.exists(self.temp_thumb):
                await aioremove(self.temp_thumb)
            await self.clean()
        else:
            await update_status_message(self.message.chat.id)

        if (
            self.isSuperChat
            and config_dict["INCOMPLETE_TASK_NOTIFIER"]
            and DATABASE_URL
        ):
            await DbManger().rm_complete_task(self.message.link)

        async with queue_dict_lock:
            if self.mid in queued_dl:
                queued_dl[self.mid].set()
                del queued_dl[self.mid]
            if self.mid in queued_up:
                queued_up[self.mid].set()
                del queued_up[self.mid]
            if self.mid in non_queued_dl:
                non_queued_dl.remove(self.mid)
            if self.mid in non_queued_up:
                non_queued_up.remove(self.mid)

        await start_from_queued()
        await sleep(3)
        await clean_download(self.dir)
        if self.newDir:
            await clean_download(self.newDir)