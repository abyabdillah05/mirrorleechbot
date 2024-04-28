from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from secrets import token_urlsafe
from asyncio import gather
from json import loads
from time import time

from bot import LOGGER, task_dict, task_dict_lock, bot
from bot.helper.mirror_utils.gdrive_utils.clone import gdClone
from bot.helper.mirror_utils.gdrive_utils.count import gdCount
from bot.helper.ext_utils.help_messages import CLONE_HELP_MESSAGE
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    sendStatusMessage,
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.ext_utils.bot_utils import (
    new_task,
    sync_to_async,
    new_task,
    cmd_exec,
    arg_parser
)
from bot.helper.ext_utils.links_utils import (
    is_gdrive_link,
    is_share_link,
    is_rclone_path,
    is_gdrive_id,
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.mirror_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.mirror_utils.rclone_utils.transfer import RcloneTransferHelper
from bot.helper.mirror_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.listeners.task_listener import TaskListener
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.task_manager import stop_duplicate_check


class Clone(TaskListener):
    def __init__(
        self,
        client,
        message,
        _=None,
        __=None,
        sameDir=None,
        bulk=None,
        multiTag=None,
        auto_url=None,
        options="",
    ):
        if sameDir is None:
            sameDir = {}
        if bulk is None:
            bulk = []
        super().__init__(message)
        self.client = client
        self.multiTag = multiTag
        self.options = options
        self.sameDir = sameDir
        self.bulk = bulk
        self.isClone = True
        self.auto_url = auto_url
        self.extra_details = {'startTime': time()}

    @new_task
    async def newEvent(self):
        text = (
            self.message.text
            or self.message.caption
        ).split("\n")
        
        input_list = text[0].split(" ")

        arg_base = {
            "link": "", 
            "-i": 0, 
            "-b": False, 
            "-up": "", 
            "-rcf": ""
        }

        args = arg_parser(input_list[1:], arg_base)

        try:
            self.multi = int(args["-i"])
        except:
            self.multi = 0

        self.upDest = args["-up"]
        self.rcFlags = args["-rcf"]
        if self.auto_url:
            self.link = self.auto_url
        else:
            self.link = args["link"]

        isBulk = args["-b"]
        bulk_start = 0
        bulk_end = 0

        if not isinstance(isBulk, bool):
            dargs = isBulk.split(":")
            bulk_start = dargs[0] or 0
            if len(dargs) == 2:
                bulk_end = dargs[1] or 0
            isBulk = True

        if isBulk:
            await self.initBulk(input_list, bulk_start, bulk_end, Clone)
            return

        await self.getTag(text)

        if not self.link and (reply_to := self.message.reply_to_message):
            if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()
            if not (
                is_gdrive_link(self.link)
                or is_rclone_path(self.link)
            ) and (reply_caption := reply_to.caption):
                self.link = reply_caption.strip()
            if not (
                is_gdrive_link(self.link)
                or is_rclone_path(self.link)
            ) and (reply_markup := reply_to.reply_markup):
                self.link = (
                    reply_markup.inline_keyboard[0][0].url
                    or ""
                )
            if not (
                is_gdrive_link(self.link)
                or is_rclone_path(self.link)
            ):
                self.link = self.message.text.split("\n", 1)[0].strip()

        LOGGER.info(f"Clone: {self.link}")

        self.run_multi(input_list, "", Clone)

        if len(self.link) == 0:
            user_id = self.message.from_user.id
            buttons = ButtonMaker()
            if self.message.from_user.username:
                user = f"@{self.message.from_user.username}"
            else:
                user = f"{self.message.from_user.first_name}"
            buttons.ibutton('Bantuan Clone', f'pika {user_id} guide other')
            await sendMessage(self.message, f"Hai {user}, Link tidak ditemukan atau perintah anda salah, silahkan klik tombol bantuan dibawah untuk melihat bantuan.", 
                buttons.build_menu(1)
                )
            return

        try:
            await self.beforeStart()
        except Exception as e:
            await sendMessage(self.message, e)
            return
        
        await self._proceedToClone()

    async def _proceedToClone(self):
        if is_share_link(self.link):
            try:
                self.link = await sync_to_async(direct_link_generator, self.link)
                LOGGER.info(f"Generated link: {self.link}")
            except DirectDownloadLinkException as e:
                LOGGER.error(str(e))
                if str(e).startswith("ERROR:"):
                    await sendMessage(self.message, str(e))
                    return
        if is_gdrive_link(self.link) or is_gdrive_id(self.link):
            self.name, mime_type, size, files, _ = await sync_to_async(
                gdCount().count, self.link, self.user_id
            )
            if mime_type is None:
                await sendMessage(self.message, self.name)
                return
            msg, button = await stop_duplicate_check(self)
            if msg:
                await sendMessage(self.message, msg, button)
                return
            await self.onDownloadStart()
            LOGGER.info(f"Clone Started: Name: {self.name} - Source: {self.link}")
            drive = gdClone(self)
            if files <= 10:
                msg = await sendMessage(
                    self.message, f"<b>Mengclone :</b>\n<code>{self.link}</code>"
                )
            else:
                msg = ""
                gid = token_urlsafe(12)
                async with task_dict_lock:
                    task_dict[self.mid] = GdriveStatus(self, drive, size, gid, "cl")
                if self.multi <= 1:
                    await sendStatusMessage(self.message)
            flink, size, mime_type, files, folders, dir_id = await sync_to_async(
                drive.clone
            )
            if msg:
                await deleteMessage(msg)
            if not flink:
                return
            await self.onUploadComplete(
                flink, size, files, folders, mime_type, dir_id=dir_id
            )
            LOGGER.info(f"Cloning Done: {self.name}")
        elif is_rclone_path(self.link):
            if self.link.startswith("mrcc:"):
                self.upDest = self.upDest.lstrip("mrcc:")
                config_path = f"rclone/{self.user_id}.conf"
            else:
                config_path = "rclone.conf"

            remote, src_path = self.link.split(":", 1)
            src_path = src_path.strip("/")

            cmd = f'edge lsjson --fast-list --stat --no-modtime --config {config_path} "{remote}:{src_path}"'
            res = await cmd_exec(cmd, shell=True)
            if res[2] != 0:
                if res[2] != -9:
                    msg = f"<b>Gagal mendapatkan link path Rclone</b>\n<b>Path :</b> <code>{remote}:{src_path}</code>\n\n<b>Stderr :</b>\n<code>{res[1][:4000]}</code>"
                    await sendMessage(self.message, msg)
                return
            rstat = loads(res[0])
            if rstat["IsDir"]:
                self.name = src_path.rsplit("/", 1)[-1] if src_path else remote
                self.upDest += (
                    self.name if self.upDest.endswith(":") else f"/{self.name}"
                )
                mime_type = "Folder"
            else:
                self.name = src_path.rsplit("/", 1)[-1]
                mime_type = rstat["MimeType"]

            await self.onDownloadStart()

            RCTransfer = RcloneTransferHelper(self)
            LOGGER.info(
                f"Clone Started: Name: {self.name} - Source: {self.link} - Destination: {self.upDest}"
            )
            gid = token_urlsafe(12)
            async with task_dict_lock:
                task_dict[self.mid] = RcloneStatus(self, RCTransfer, gid, "cl")
            if self.multi <= 1:
                await sendStatusMessage(self.message)
            flink, destination = await RCTransfer.clone(
                config_path, remote, src_path, mime_type
            )
            if not flink:
                return
            LOGGER.info(f"Cloning Done: {self.name}")
            cmd1 = f'edge lsf --fast-list -R --files-only --config {config_path} "{destination}"'
            cmd2 = f'edge lsf --fast-list -R --dirs-only --config {config_path} "{destination}"'
            cmd3 = (
                f'edge size --fast-list --json --config {config_path} "{destination}"'
            )
            res1, res2, res3 = await gather(
                cmd_exec(cmd1, shell=True),
                cmd_exec(cmd2, shell=True),
                cmd_exec(cmd3, shell=True),
            )
            if res1[2] != res2[2] != res3[2] != 0:
                if res1[2] == -9:
                    return
                files = None
                folders = None
                size = 0
                LOGGER.error(
                    f"Error: While getting rclone stat. Path: {destination}. Stderr: {res1[1][:4000]}"
                )
            else:
                files = len(res1[0].split("\n"))
                folders = len(res2[0].strip().split("\n")) if res2[0] else 0
                rsize = loads(res3[0])
                size = rsize["bytes"]
                await self.onUploadComplete(
                    flink, size, files, folders, mime_type, destination
                )
        else:
            user_id = self.message.from_user.id
            buttons = ButtonMaker()
            if self.message.from_user.username:
                user = f"@{self.message.from_user.username}"
            else:
                user = f"{self.message.from_user.first_name}"
            buttons.ibutton('Tombol Bantuan', f'pika {user_id} guide home')
            await sendMessage(self.message, f"Hai {user}, Perintah clone hanya untuk link google drive, silahkan klik tombol dibawah untuk melihat perintah yang lain.", 
                buttons.build_menu(1)
                )


async def clone(client, message):
    Clone(client, message).newEvent()


bot.add_handler(
    MessageHandler(
        clone,
        filters=command(
            BotCommands.CloneCommand
        ) & CustomFilters.authorized
    )
)
