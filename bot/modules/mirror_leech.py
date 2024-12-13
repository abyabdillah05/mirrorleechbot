from pyrogram.handlers import MessageHandler
from pyrogram import filters
from pyrogram.filters import command
from base64 import b64encode
from re import match as re_match
from aiofiles.os import path as aiopath
from asyncio import sleep
import re

from bot import bot, DOWNLOAD_DIR, LOGGER
from bot.helper.ext_utils.links_utils import (
    is_url,
    is_magnet,
    is_mega_link,
    is_gdrive_link,
    is_rclone_path,
    is_telegram_link,
    is_gdrive_id,
)
from bot.helper.ext_utils.bot_utils import (
    get_content_type,
    new_task,
    sync_to_async,
    arg_parser,
    COMMAND_USAGE,
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.mirror_utils.download_utils.direct_downloader import add_direct_download
from bot.helper.mirror_utils.download_utils.aria2_download import add_aria2c_download
from bot.helper.mirror_utils.download_utils.gd_download import add_gd_download
from bot.helper.mirror_utils.download_utils.qbit_download import add_qb_torrent
from bot.helper.mirror_utils.download_utils.mega_download import add_mega_download
from bot.helper.mirror_utils.download_utils.rclone_download import add_rclone_download
from bot.helper.mirror_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.mirror_utils.download_utils.telegram_download import (
    TelegramDownloadHelper,
)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage,
    deleteMessage,
    get_tg_link_message
)
from bot.helper.listeners.task_listener import TaskListener
from bot.modules.auto_mirror import AutoMirror
from bot.modules.video_editor import VideEditor
from urllib.parse import urlparse

urlregex = r"^(?!\/)(rtmps?:\/\/|mms:\/\/|rtsp:\/\/|https?:\/\/|ftp:\/\/)?([^\/:]+:[^\/@]+@)?(www\.)?(?=[^\/:\s]+\.[^\/:\s]+)([^\/:\s]+\.[^\/:\s]+)(:\d+)?(\/[^#\s]*[\s\S]*)?(\?[^#\s]*)?(#.*)?$"
magnetregex = r"magnet:\?xt=urn:(btih|btmh):[a-zA-Z0-9]*\s*"
class Mirror(TaskListener):
    def __init__(
        self,
        client,
        message,
        isQbit=False,
        isLeech=False,
        sameDir=None,
        bulk=None,
        multiTag=None,
        auto_mode=False,
        button_mode=False,
        gofile=False,
        buzzheavier=False,
        pixeldrain=False,
        temp_thumbs=False,
        dump=False,
        ve=False,
        video_editor=None,
        auto_url="",
        options="",
        temp_thumb="",
    ):
        if sameDir is None:
            sameDir = {}
        if bulk is None:
            bulk = []
        super().__init__(message)
        self.client = client
        self.isQbit = isQbit
        self.isLeech = isLeech
        self.multiTag = multiTag
        self.options = options
        self.sameDir = sameDir
        self.bulk = bulk
        self.auto_mode = auto_mode
        self.auto_url = auto_url
        self.button_mode = button_mode
        self.gofile = gofile
        self.buzzheavier = buzzheavier
        self.pixeldrain = pixeldrain
        self.temp_thumbs = temp_thumbs
        self.temp_thumb = temp_thumb
        self.dump = dump
        self.ve = ve
        self.video_editor = video_editor

    @new_task
    async def newEvent(self):
        rply = self.message.reply_to_message
        if rply and len(self.message.text.split()) == 1:
            self.button_mode = True
        elif not rply and len(self.message.text.split()) == 2:
            self.button_mode = True

        if not self.auto_url:
            command_teks = self.message.text.split(maxsplit=1)
            if len(command_teks) > 1:
                self.auto_url = command_teks[1]

        text = (
            self.message.text
            or self.message.caption
        ).split("\n")
        
        input_list = text[0].split(" ")

        arg_base = {
            "-d": False,
            "-j": False,
            "-s": False,
            "-b": False,
            "-e": False,
            "-z": False,
            "-sv": False,
            "-ss": False,
            "-i": 0,
            "-sp": 0,
            "link": "",
            "-n": "",
            "-m": "",
            "-up": "",
            "-rcf": "",
            "-au": "",
            "-ap": "",
            "-h": "",
            "-ct": False,
            "-dump": False,
            "-ve": False
        }

        if self.gofile:
            arg_base["-up"] = "gofile"
        elif self.buzzheavier:
            arg_base["-up"] = "buzzheavier"
        elif self.pixeldrain:
            arg_base["-up"] = "pixeldrain"

        args = arg_parser(input_list[1:], arg_base)

        self.select = args["-s"]
        self.seed = args["-d"]
        self.name = args["-n"]
        self.upDest = args["-up"] 
        self.rcFlags = args["-rcf"]
        self.link = args["link"]
        self.compress = args["-z"]
        self.extract = args["-e"]
        self.join = args["-j"]
        self.splitSize = args["-sp"]
        self.sampleVideo = args["-sv"]
        self.screenShots = args["-ss"]
        self.up_thumb = args["-ct"]
        self.dump = args["-dump"]
        self.ve = args["-ve"]

        headers = args["-h"]
        isBulk = args["-b"]
        folder_name = args["-m"]

        bulk_start = 0
        bulk_end = 0
        ratio = None
        seed_time = None
        reply_to = None
        file_ = None

        if self.ve:
            try:
                self.video_editor = await VideEditor(self).main_pesan()
                if self.video_editor is None:
                    self.removeFromSameDir()
                    return
            except:
                self.removeFromSameDir()
                return

        if self.up_thumb and not self.temp_thumbs:
            self.temp_thumb = await AutoMirror(self).upload_thumbnail()

        if self.auto_mode or self.button_mode:
            _type = None
            self.link = self.auto_url
            if not self.auto_mode:
                _type = "leech" if self.isLeech else "mirror"
                
                reply_to = self.message.reply_to_message
                if reply_to:
                    if reply_text := reply_to.text:
                        self.link = reply_text.split("\n", 1)[0].strip()
                    else:
                        file_ = (
                            reply_to.document
                            or reply_to.photo
                            or reply_to.video
                            or reply_to.audio
                            or reply_to.voice
                            or reply_to.video_note
                            or reply_to.sticker
                            or reply_to.animation
                            or None
                            )
                        if reply_to.document and (
                            file_.mime_type == "application/x-bittorrent"
                            or file_.file_name.endswith(".torrent")
                            ):
                            self.link = await reply_to.download()
                            file_ = None
                        elif file_ is not None:
                            reply_to = reply_to
                        else:
                            reply_to = None

            if (is_url(self.link) or is_magnet(self.link) or reply_to is not None):
                try:
                    if self.gofile:
                        auto_args = await AutoMirror(self).main_pesan_custom(self.link, _type, gofile=True)
                    elif self.buzzheavier:
                        auto_args = await AutoMirror(self).main_pesan_custom(self.link, _type, buzzheavier=True)
                    elif self.pixeldrain:
                        auto_args = await AutoMirror(self).main_pesan_custom(self.link, _type, pixeldrain=True)
                    elif not self.link:
                        if _type:
                            auto_args = await AutoMirror(self).main_pesan_custom("Files", _type)
                        else:
                            auto_args = await AutoMirror(self).main_pesan("Files", _type)
                    else:
                        if _type:
                            auto_args = await AutoMirror(self).main_pesan_custom(self.link, _type)
                        else:
                            auto_args = await AutoMirror(self).main_pesan(self.link, _type)
                        
                    if "rename" in auto_args:
                        self.name = auto_args["rename"]
                    if "custom_upload" in auto_args:
                        self.upDest = auto_args["custom_upload"]
                    if "extract" in auto_args:
                        self.extract = auto_args["extract"]
                    if "zip" in auto_args:
                        self.compress = auto_args["zip"]
                    if "ss" in auto_args:
                        self.screenShots = auto_args["ss"]
                    if "sv" in auto_args:
                        self.sampleVideo = auto_args["sv"]
                    if "leech" in auto_args:
                        self.isLeech = True
                    if "custom_thumb" in auto_args:
                        self.temp_thumb = auto_args["custom_thumb"]

                except:
                    self.removeFromSameDir()
                    return

        try:
            self.multi = int(args["-i"])
        except:
            self.multi = 0

        if not isinstance(self.seed, bool):
            dargs = self.seed.split(":")
            ratio = dargs[0] or None
            if len(dargs) == 2:
                seed_time = dargs[1] or None
            self.seed = True

        if not isinstance(isBulk, bool):
            dargs = isBulk.split(":")
            bulk_start = dargs[0] or 0
            if len(dargs) == 2:
                bulk_end = dargs[1] or 0
            isBulk = True

        if not isBulk:
            if folder_name:
                self.seed = False
                ratio = None
                seed_time = None
                folder_name = f"/{folder_name}"
                if not self.sameDir:
                    self.sameDir = {
                        "total": self.multi,
                        "tasks": set(),
                        "name": folder_name,
                    }
                self.sameDir["tasks"].add(self.mid)
            elif self.sameDir:
                self.sameDir["total"] -= 1

        else:
            await self.initBulk(input_list, bulk_start, bulk_end, Mirror)
            return

        if len(self.bulk) != 0:
            del self.bulk[0]

        if self.gofile:
            self.run_multi(input_list, folder_name, Mirror, gofile=True)
        elif self.buzzheavier:
            self.run_multi(input_list, folder_name, Mirror, buzzheavier=True)
        elif self.pixeldrain:
            self.run_multi(input_list, folder_name, Mirror, pixeldrain=True)
        elif self.temp_thumb:
            self.run_multi(input_list, folder_name, Mirror, temp_thumbs=True, temp_thumb=self.temp_thumb)
        else:
            self.run_multi(input_list, folder_name, Mirror)

        await self.getTag(text)

        path = f"{DOWNLOAD_DIR}{self.mid}{folder_name}"

        if not self.link and (reply_to := self.message.reply_to_message):
            if reply_text := reply_to.text:
                self.link = reply_text.split("\n", 1)[0].strip()
            if not ( 
                is_url(self.link) 
                or is_magnet(self.link)
            ) and (reply_caption := reply_to.caption):
                self.link = reply_caption.strip()
            if not ( 
                is_url(self.link) 
                or is_magnet(self.link)
            ) and (reply_markup := reply_to.reply_markup):
                self.link = (
                    reply_markup.inline_keyboard[0][0].url
                    or ""
                )
            if not ( 
                is_url(self.link) 
                or is_magnet(self.link)
            ):
                self.link = self.message.text.split("\n", 1)[0].strip()
        if is_telegram_link(self.link):
            try:
                reply_to, self.session = await get_tg_link_message(self.link)
            except Exception as e:
                await sendMessage(self.message, f"ERROR: {e}")
                self.removeFromSameDir()
                return

        if isinstance(reply_to, list):
            self.bulk = reply_to
            self.sameDir = {}
            b_msg = input_list[:1]
            self.options = " ".join(input_list[1:])
            b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")
            nextmsg = await sendMessage(self.message, " ".join(b_msg))
            nextmsg = await self.client.get_messages(
                chat_id=self.message.chat.id, message_ids=nextmsg.id
            )
            if self.message.from_user:
                nextmsg.from_user = self.user
            else:
                nextmsg.sender_chat = self.user
            Mirror(
                self.client,
                nextmsg,
                self.isQbit,
                self.isLeech,
                self.sameDir,
                self.bulk,
                self.multiTag,
                self.options,
            ).newEvent()
            return

        if reply_to:
            file_ = (
                reply_to.document
                or reply_to.photo
                or reply_to.video
                or reply_to.audio
                or reply_to.voice
                or reply_to.video_note
                or reply_to.sticker
                or reply_to.animation
                or None
            )

            if file_ is None:
                if reply_text := reply_to.text:
                    self.link = reply_text.split("\n", 1)[0].strip()
                if not ( 
                    is_url(self.link) 
                    or is_magnet(self.link)
                ) and (reply_caption := reply_to.caption):
                    self.link = reply_caption.strip()
                if not (
                    is_url(self.link)
                    or is_magnet(self.link)
                ) and (reply_markup := reply_to.reply_markup):
                    self.link = (
                        reply_markup.inline_keyboard[0][0].url
                        or ""
                    )
                else:
                    reply_to = None
            elif reply_to.document and (
                file_.mime_type == "application/x-bittorrent"
                or file_.file_name.endswith(".torrent")
            ):
                self.link = await reply_to.download()
                file_ = None
                
        if (
            not self.link
            and file_ is None
            or is_telegram_link(self.link)
            and reply_to is None
            or file_ is None
            and not is_url(self.link)
            and not is_magnet(self.link)
            and not await aiopath.exists(self.link)
            and not is_rclone_path(self.link)
            and not is_gdrive_id(self.link)
        ):
            user_id = self.message.from_user.id
            buttons = ButtonMaker()
            if self.message.from_user.username:
                user = f"@{self.message.from_user.username}"
            else:
                user = f"{self.message.from_user.first_name}"
            buttons.ibutton('Bantuan Mirror-Leech', f'pika {user_id} guide home')
            await sendMessage(self.message, f"Hai {user}, Link tidak ditemukan atau perintah anda salah, silahkan klik tombol bantuan dibawah untuk melihat bantuan.", 
                buttons.build_menu(1)
                )
            self.removeFromSameDir()
            return

        if self.link:
            LOGGER.info(self.link)

        try:
            await self.beforeStart()
        except Exception as e:
            await sendMessage(self.message, e)
            self.removeFromSameDir()
            return

        if (
            not is_mega_link(self.link)
            and not self.isQbit
            and not is_magnet(self.link)
            and not is_rclone_path(self.link)
            and not is_gdrive_link(self.link)
            and not self.link.endswith(".torrent")
            and file_ is None
            and not is_gdrive_id(self.link)
        ):
            content_type = await get_content_type(self.link)
            if content_type is None or "application/zip" and "bigota" in self.link or "application/zip" and "hugeota" in self.link or re_match(r"text/html|text/plain", content_type):
                if "uptobox" in self.link:
                    ddl = await sendMessage(
                        self.message,
                        f"<b>Generating Uptobox Direct Link (±30s) :</b>\n<code>{self.link}</code>"
                    )
                elif "bigota" in self.link:
                    ddl = await sendMessage(
                        self.message,
                        f"<b>Mengubah server Bigota :</b>\n<code>{self.link}</code>"
                    )
                else:
                    ddl = await sendMessage(
                        self.message,
                        f"<b>Generating Direct Link :</b>\n<code>{self.link}</code>"
                    )
                try:
                    
                    self.link = await sync_to_async(direct_link_generator, self.link)
                    if isinstance(self.link, tuple):
                        self.link, headers = self.link
                    elif isinstance(self.link, str):
                        LOGGER.info(f"Generated link: {self.link}")
                        await editMessage(ddl, f"<b>Generated Direct Link :</b>\n<code>{self.link}</code>")
                        await sleep(3)
                    await deleteMessage(ddl)
                except DirectDownloadLinkException as e:
                    await sleep(1)
                    await deleteMessage(ddl)
                    e = str(e)
                    if "This link requires a password!" not in e:
                        LOGGER.info(e)
                    if e.startswith("ERROR:"):
                        await sendMessage(self.message, e)
                        self.removeFromSameDir()
                        return

        if file_ is not None:
            await TelegramDownloadHelper(self).add_download(reply_to, f"{path}/")
        elif isinstance(self.link, dict):
            await add_direct_download(self, path)
        elif is_rclone_path(self.link):
            await add_rclone_download(self, f"{path}/")
        elif is_gdrive_link(self.link) or is_gdrive_id(self.link):
            await add_gd_download(self, path)
        elif is_mega_link(self.link):
            await add_mega_download(self, f"{path}/")
        elif self.isQbit:
            await add_qb_torrent(self, path, ratio, seed_time)
        else:
            ussr = args["-au"]
            pssw = args["-ap"]
            if ussr or pssw:
                auth = f"{ussr}:{pssw}"
                headers += (
                    f" authorization: Basic {b64encode(auth.encode()).decode('ascii')}"
                )
            await add_aria2c_download(self, path, headers, ratio, seed_time)

        self.removeFromSameDir()

async def mirror(client, message):
    Mirror(client, message).newEvent()

async def gofile(client, message):
    Mirror(client, message, gofile=True).newEvent()
    
async def buzz(client, message):
    Mirror(client, message, buzzheavier=True).newEvent()

async def pixeldrain(client, message):
    Mirror(client, message, pixeldrain=True).newEvent()

async def qb_mirror(client, message):
    Mirror(client, message, isQbit=True).newEvent()


async def leech(client, message):
    Mirror(client, message, isLeech=True).newEvent()


async def qb_leech(client, message):
    Mirror(client, message, isQbit=True, isLeech=True).newEvent()

async def auto_mirror(client, message):
    if message.caption is not None:
        text = message.caption
    else:
        text = message.text
    urls = text
    if ' ' in urls.strip() or len(urls.split()) != 1:
        return None
    magnet = re.search(magnetregex, text)
    if magnet:
        pass
    else:
        try:
            domain = urlparse(urls).hostname
            if any(
                x in domain
                for x in [
                    "youtube.com",
                    "youtu.be",
                    "instagram.com",
                    "facebook.com",
                    "tiktok.com",
                    "twitter.com",
                    "x.com",
                ]
            ):
                return None
        except:
            pass
    Mirror(client, message, auto_url=text, auto_mode=True).newEvent()

bot.add_handler(
    MessageHandler(
        mirror, 
        filters=command(
            BotCommands.MirrorCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        leech, 
        filters=command(
            BotCommands.LeechCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        qb_mirror,
        filters=command(
            BotCommands.QbMirrorCommand
        ) & CustomFilters.authorized,
    )
)
bot.add_handler(
    MessageHandler(
        qb_leech, 
        filters=command(
            BotCommands.QbLeechCommand
        ) & CustomFilters.authorized
    )
)   
bot.add_handler(
    MessageHandler(
        auto_mirror,
        filters=CustomFilters.authorized
        & filters.regex(
            f"{urlregex}|{magnetregex}"
        )
    )
)
bot.add_handler(
    MessageHandler(
        gofile, 
        filters=command(
            BotCommands.Upload_gofileCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        buzz, 
        filters=command(
            BotCommands.Upload_buzzCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        pixeldrain, 
        filters=command(
            BotCommands.Upload_pixelCommand
        ) & CustomFilters.authorized
    )
)