from logging import getLogger
from aiofiles.os import (
    remove,
    path as aiopath,
    rename,
    makedirs,
)
from os import walk, path as ospath
from time import time
from PIL import Image
from pyrogram.types import InputMediaVideo, InputMediaDocument, InputMediaPhoto
from pyrogram.errors import FloodWait, RPCError
from asyncio import sleep
from re import match as re_match, sub as re_sub
from natsort import natsorted
from aioshutil import copy
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    RetryError,
)

from bot import config_dict, bot, user
from bot.helper.ext_utils.files_utils import clean_unwanted, is_archive, get_base_name
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.telegram_helper.message_utils import (
    deleteMessage, 
    copyMessage, 
    customSendMessage, 
    customSendDocument, 
    customSendVideo, 
    customSendAudio, 
    customSendPhoto,
    sendMessage
)
from bot.helper.ext_utils.media_utils import (  
    get_media_info,
    get_document_type,
    create_thumbnail,
    get_audio_thumb,
    take_ss,
)


LOGGER = getLogger(__name__)


class TgUploader:
    def __init__(self, listener, path):
        self._last_uploaded = 0
        self._processed_bytes = 0
        self._listener = listener
        self._path = path
        self._start_time = time()
        self._total_files = 0
        self._is_cancelled = False
        self._thumb = self._listener.thumb or f"Thumbnails/{listener.user_id}.jpg"
        self._temp_thumb = self._listener.temp_thumb
        self._msgs_dict = {}
        self._corrupted = 0
        self._is_corrupted = False
        self._media_dict = {"videos": {}, "documents": {}}
        self._last_msg_in_group = False
        self._up_path = ""
        self._lprefix = ""
        self._lsuffix = ""
        self._media_group = False
        self._forwardChatId = None
        self._forwardThreadId = None
        self._caption = self._listener.caption

    async def _upload_progress(self, current, _):
        if self._is_cancelled:
            if (
                self._listener.userTransmission
                or self._listener.session == "user"
            ):
                user.stop_transmission()
            else:
                self._listener.client.stop_transmission()
        chunk_size = current - self._last_uploaded
        self._last_uploaded = current
        self._processed_bytes += chunk_size

    async def _user_settings(self):
        self._media_group = self._listener.user_dict.get("media_group") or (
            config_dict["MEDIA_GROUP"]
            if "media_group" not in self._listener.user_dict
            else False
        )
        
        self._lprefix = self._listener.user_dict.get("lprefix") or (
            config_dict["LEECH_FILENAME_PREFIX"]
            if "lprefix" not in self._listener.user_dict
            else ""
        )
        
        self._lsuffix = self._listener.user_dict.get("lsuffix", "")
        
        self._forwardChatId = self._listener.user_dict.get("leech_dest")
        if not self._forwardChatId:
            self._forwardChatId = self._listener.message.chat.id
            self._forwardThreadId = (
                self._listener.message.message_thread_id
                if self._listener.message.chat.is_forum
                else None
            )
            
        if not isinstance(self._forwardChatId, int):
            if ":" in self._forwardChatId:
                self._forwardThreadId = self._forwardChatId.split(":")[1]
                self._forwardChatId = self._forwardChatId.split(":")[0]
                
        if (
            self._forwardChatId
            and not isinstance(self._forwardChatId, int)
            and self._forwardChatId.isdigit()
        ):
            self._forwardChatId = int(self._forwardChatId)
                
        if (
            self._forwardThreadId
            and not isinstance(self._forwardThreadId, int)
            and self._forwardThreadId.isdigit()
        ):
            self._forwardThreadId = int(self._forwardThreadId)
        
        if not await aiopath.exists(self._thumb):
            self._thumb = None

    async def _msg_to_reply(self):
        if self._listener.upDest:
            msg = (
                self._listener.message.link
                if self._listener.isSuperChat
                else self._listener.message.text.lstrip("/")
            )
            try:
                if (
                    self._listener.userTransmission
                    and self._listener.session == "user"
                ):
                    client = user
                else:
                    client = self._listener.client
                    
                self._sent_msg = await customSendMessage(
                    client=client,
                    chat_id=self._listener.upDest,
                    text=msg,
                    message_thread_id=self._listener.threadId
                )
            except Exception as e:
                await self._listener.onUploadError(str(e))
                return False
        elif (
            self._listener.userTransmission
            and self._listener.session == "user"
        ):
            self._sent_msg = await user.get_messages(
                chat_id=self._listener.message.chat.id, 
                message_ids=self._listener.mid
            )
            if self._sent_msg is None:
                self._sent_msg = await bot.send_message(
                        chat_id=self._listener.message.chat.id,
                        text="<b>Pesan Cmd terhapus!</b>\nJangan menghapus pesan Cmd agar tidak terjadi error!",
                        disable_web_page_preview=True,
                        disable_notification=True,
                    )
        else:
            self._sent_msg = self._listener.message
        return True

    async def _prepare_file(self, file_, dirpath):
        if self._caption == "Monospace":
            capt = f"<code>{file_}</code>"
        elif self._caption == "Bold":
            capt = f"<b>{file_}</b>"
        elif self._caption == "Italic":
            capt = f"<i>{file_}</i>"
        elif self._caption == "Normal":
            capt = f"{file_}"
        else:
            capt = f"<code>{file_}</code>"

        if self._lprefix and self._lsuffix:
            cap_mono = f"{self._lprefix} {capt}\n\n{self._lsuffix}"
            self._lprefix = re_sub("<.*?>", "", self._lprefix)
            self._lsuffix = re_sub("<.*?>", "", self._lsuffix)
            if (
                self._listener.seed
                and not self._listener.newDir
                and not dirpath.endswith("/splited_files_mltb")
            ):
                dirpath = f"{dirpath}/copied_mltb"
                await makedirs(dirpath, exist_ok=True)
                new_path = ospath.join(dirpath, f"{self._lprefix} {file_} {self._lsuffix}")
                self._up_path = await copy(self._up_path, new_path)
            else:
                new_path = ospath.join(dirpath, f"{self._lprefix} {file_} {self._lsuffix}")
                await rename(self._up_path, new_path)
                self._up_path = new_path
        elif self._lprefix:
            cap_mono = f"{self._lprefix} {capt}"
            self._lprefix = re_sub("<.*?>", "", self._lprefix)
            if (
                self._listener.seed
                and not self._listener.newDir
                and not dirpath.endswith("/splited_files_mltb")
            ):
                dirpath = f"{dirpath}/copied_mltb"
                await makedirs(dirpath, exist_ok=True)
                new_path = ospath.join(dirpath, f"{self._lprefix} {file_}")
                self._up_path = await copy(self._up_path, new_path)
            else:
                new_path = ospath.join(dirpath, f"{self._lprefix} {file_}")
                await rename(self._up_path, new_path)
                self._up_path = new_path
        elif self._lsuffix:
            cap_mono = f"{capt}\n\n{self._lsuffix}"
            self._lsuffix = re_sub("<.*?>", "", self._lsuffix)
            if (
                self._listener.seed
                and not self._listener.newDir
                and not dirpath.endswith("/splited_files_mltb")
            ):
                dirpath = f"{dirpath}/copied_mltb"
                await makedirs(dirpath, exist_ok=True)
                new_path = ospath.join(dirpath, f"{file_} {self._lsuffix}")
                self._up_path = await copy(self._up_path, new_path)
            else:
                new_path = ospath.join(dirpath, f"{file_} {self._lsuffix}")
                await rename(self._up_path, new_path)
                self._up_path = new_path
        else:
            cap_mono = f"{capt}"
        if len(file_) > 54:
            if is_archive(file_):
                name = get_base_name(file_)
                ext = file_.split(name, 1)[1]
            elif match := re_match(r".+(?=\..+\.0*\d+$)|.+(?=\.part\d+\..+$)", file_):
                name = match.group(0)
                ext = file_.split(name, 1)[1]
            elif len(fsplit := ospath.splitext(file_)) > 1:
                name = fsplit[0]
                ext = fsplit[1]
            else:
                name = file_
                ext = ""
            extn = len(ext)
            remain = 54 - extn
            name = name[:remain]
            if (
                self._listener.seed
                and not self._listener.newDir
                and not dirpath.endswith("/splited_files_mltb")
            ):
                dirpath = f"{dirpath}/copied_mltb"
                await makedirs(dirpath, exist_ok=True)
                new_path = ospath.join(dirpath, f"{name}{ext}")
                self._up_path = await copy(self._up_path, new_path)
            else:
                new_path = ospath.join(dirpath, f"{name}{ext}")
                await rename(self._up_path, new_path)
                self._up_path = new_path
        return cap_mono

    def _get_input_media(self, subkey, key):
        rlist = []
        for msg in self._media_dict[key][subkey]:
            if key == "videos":
                input_media = InputMediaVideo(
                    media=msg.video.file_id, caption=msg.caption
                )
            else:
                input_media = InputMediaDocument(
                    media=msg.document.file_id, caption=msg.caption
                )
            rlist.append(input_media)
        return rlist

    async def _send_screenshots(self):
        if isinstance(self._listener.screenShots, str):
            ss_nb = int(self._listener.screenShots)
        else:
            ss_nb = 10
        outputs = await take_ss(self._up_path, ss_nb)
        inputs = []
        if outputs:
            for m in outputs:
                if await aiopath.exists(m):
                    cap = m.rsplit("/", 1)[-1]
                    inputs.append(InputMediaPhoto(m, cap))
                else:
                    outputs.remove(m)
            if outputs:
                self._sent_msg = (
                    await self._sent_msg.reply_media_group(
                        media=inputs,
                        quote=True,
                        disable_notification=True,
                    )
                )[-1]
                # Send ScreenShots to ForwardChatId
                try:
                    if self._forwardChatId != "":
                        await bot.send_media_group(
                            chat_id=self._forwardChatId,
                            media=inputs,
                            disable_notification=True,
                            message_thread_id=self._forwardThreadId,
                            reply_to_message_id=self._listener.mid
                        )
                except Exception as e:
                    LOGGER.error(f"Failed when forward message => {e}")
                for m in outputs:
                    await remove(m)

    async def _send_media_group(self, subkey, key, msgs):
        msgs_list = await msgs[0].reply_to_message.reply_media_group(
            media=self._get_input_media(subkey, key),
            quote=True,
            disable_notification=True,
        )
        for msg in msgs:
            if msg.link in self._msgs_dict:
                del self._msgs_dict[msg.link]
            await deleteMessage(msg)
        del self._media_dict[key][subkey]
        if self._listener.isSuperChat or self._listener.upDest:
            for m in msgs_list:
                self._msgs_dict[m.link] = m.caption
        self._sent_msg = msgs_list[-1]

    async def upload(self, o_files, m_size, size):
        await self._user_settings()
        # res = await self._msg_to_reply()
        # if not res:
        #     return
        for dirpath, _, files in sorted(await sync_to_async(walk, self._path)):
            if dirpath.endswith("/yt-dlp-thumb"):
                continue
            for file_ in natsorted(files):
                self._up_path = ospath.join(dirpath, file_)
                if file_.lower().endswith(tuple(self._listener.extension_filter)):
                    if not self._listener.seed or self._listener.newDir:
                        await remove(self._up_path)
                    continue
                try:
                    f_size = await aiopath.getsize(self._up_path)
                    # Force uploads below 2GB using Bot session and above 2GB using User session
                    if f_size < 2097152000:
                        self._listener.session = "bot"
                    else:
                        self._listener.session = "user"
                    res = await self._msg_to_reply()
                    if not res:
                        return
                    if self._listener.seed and file_ in o_files and f_size in m_size:
                        continue
                    self._total_files += 1
                    if f_size == 0:
                        LOGGER.error(
                            f"{self._up_path} size is zero, telegram don't upload zero size files"
                        )
                        self._corrupted += 1
                        continue
                    if self._is_cancelled:
                        return
                    cap_mono = await self._prepare_file(file_, dirpath)
                    if self._last_msg_in_group:
                        group_lists = [
                            x for v in self._media_dict.values() for x in v.keys()
                        ]
                        match = re_match(
                            r".+(?=\.0*\d+$)|.+(?=\.part\d+\..+$)", self._up_path
                        )
                        if not match or match and match.group(0) not in group_lists:
                            for key, value in list(self._media_dict.items()):
                                for subkey, msgs in list(value.items()):
                                    if len(msgs) > 1:
                                        await self._send_media_group(subkey, key, msgs)
                    self._last_msg_in_group = False
                    self._last_uploaded = 0
                    LOGGER.info(f"Leech Started: {self._listener.name} | Using: {self._listener.session.upper()} Session")
                    await self._upload_file(cap_mono, file_)
                    if self._is_cancelled:
                        return
                    if not self._is_corrupted and (
                        self._listener.isSuperChat or self._listener.upDest
                    ):
                        self._msgs_dict[self._sent_msg.link] = file_
                    await sleep(1)
                except Exception as err:
                    if isinstance(err, RetryError):
                        LOGGER.info(
                            f"Total Attempts: {err.last_attempt.attempt_number}"
                        )
                        err = err.last_attempt.exception()
                    LOGGER.error(f"{err}. Path: {self._up_path}")
                    self._corrupted += 1
                    if self._is_cancelled:
                        return
                    continue
                finally:
                    if (
                        not self._is_cancelled
                        and await aiopath.exists(self._up_path)
                        and (
                            not self._listener.seed
                            or self._listener.newDir
                            or dirpath.endswith("/splited_files_mltb")
                            or "/copied_mltb/" in self._up_path
                        )
                    ):
                        await remove(self._up_path)
        for key, value in list(self._media_dict.items()):
            for subkey, msgs in list(value.items()):
                if len(msgs) > 1:
                    try:
                        await self._send_media_group(subkey, key, msgs)
                    except Exception as e:
                        LOGGER.info(
                            f"While sending media group at the end of task. Error: {e}"
                        )
        if self._is_cancelled:
            return
        if self._listener.seed and not self._listener.newDir:
            await clean_unwanted(self._path)
        if self._total_files == 0:
            await self._listener.onUploadError(
                "Tidak ada file untuk diunggah ke telegram!"
            )
            return
        if self._total_files <= self._corrupted:
            await self._listener.onUploadError(
                "Ekstensi file ini diblokir oleh bot!"
            )
            return
        LOGGER.info(f"Leech Completed: {self._listener.name}")
        await self._listener.onUploadComplete(
            None, size, self._msgs_dict, self._total_files, self._corrupted
        )

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def _upload_file(self, cap_mono, file, force_document=False):
        if self._thumb is not None and not await aiopath.exists(self._thumb):
            self._thumb = None
        thumb = self._thumb
        if self._temp_thumb:
            thumb = self._temp_thumb
        self._is_corrupted = False
        try:
            is_video, is_audio, is_image = await get_document_type(self._up_path)

            if not is_image and thumb is None:
                file_name = ospath.splitext(file)[0]
                thumb_path = f"{self._path}/yt-dlp-thumb/{file_name}.jpg"
                if await aiopath.isfile(thumb_path):
                    thumb = thumb_path
                elif is_audio and not is_video:
                    thumb = await get_audio_thumb(self._up_path)

            if (
                self._listener.as_doc
                or force_document
                or (not is_video and not is_audio and not is_image)
            ):
                key = "documents"
                if is_video:
                    if self._listener.screenShots:
                        await self._send_screenshots()
                    if thumb is None:
                        thumb = await create_thumbnail(self._up_path, None)

                if self._is_cancelled:
                    return
                
                # self._sent_msg = await self._sent_msg.reply_document(
                #     document=self._up_path,
                #     quote=True,
                #     thumb=thumb,
                #     caption=cap_mono,
                #     force_document=True,
                #     disable_notification=True,
                #     progress=self._upload_progress,
                # )
                
                self._sent_msg = await customSendDocument(
                    client=self._sent_msg,
                    document=self._up_path,
                    thumb=thumb,
                    caption=cap_mono,
                    progress=self._upload_progress
                )
                
            elif is_video:
                if self._listener.screenShots:
                    await self._send_screenshots()
                key = "videos"
                duration = (await get_media_info(self._up_path))[0]
                if thumb is None:
                    thumb = await create_thumbnail(self._up_path, duration)
                if thumb is not None:
                    with Image.open(thumb) as img:
                        width, height = img.size
                else:
                    width = 480
                    height = 320
                if not self._up_path.upper().endswith(("MP4", "MKV")):
                    dirpath, file_ = self._up_path.rsplit("/", 1)
                    if (
                        self._listener.seed
                        and not self._listener.newDir
                        and not dirpath.endswith("/splited_files_mltb")
                    ):
                        dirpath = f"{dirpath}/copied_mltb"
                        await makedirs(dirpath, exist_ok=True)
                        new_path = ospath.join(
                            dirpath, f"{ospath.splitext(file_)[0]}.mp4"
                        )
                        self._up_path = await copy(self._up_path, new_path)
                    else:
                        new_path = f"{ospath.splitext(self._up_path)[0]}.mp4"
                        await rename(self._up_path, new_path)
                        self._up_path = new_path
                        
                if self._is_cancelled:
                    return
                
                # self._sent_msg = await self._sent_msg.reply_video(
                #     video=self._up_path,
                #     quote=True,
                #     caption=cap_mono,
                #     duration=duration,
                #     width=width,
                #     height=height,
                #     thumb=thumb,
                #     supports_streaming=True,
                #     disable_notification=True,
                #     progress=self._upload_progress,
                # )
                
                self._sent_msg = await customSendVideo(
                    client=self._sent_msg,
                    video=self._up_path,
                    caption=cap_mono,
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    progress=self._upload_progress
                )
                
            elif is_audio:
                key = "audios"
                duration, artist, title = await get_media_info(self._up_path)
                
                if self._is_cancelled:
                    return
                
                # self._sent_msg = await self._sent_msg.reply_audio(
                #     audio=self._up_path,
                #     quote=True,
                #     caption=cap_mono,
                #     duration=duration,
                #     performer=artist,
                #     title=title,
                #     thumb=thumb,
                #     disable_notification=True,
                #     progress=self._upload_progress,
                # )

                self._sent_msg = await customSendAudio(
                    client=self._sent_msg,
                    audio=self._up_path,
                    caption=cap_mono,
                    duration=duration,
                    performer=artist,
                    title=title,
                    thumb=thumb,
                    progress=self._upload_progress
                )

            else:
                key = "photos"
                
                if self._is_cancelled:
                    return
                
                # self._sent_msg = await self._sent_msg.reply_photo(
                #     photo=self._up_path,
                #     quote=True,
                #     caption=cap_mono,
                #     disable_notification=True,
                #     progress=self._upload_progress,
                # )

                self._sent_msg = await customSendPhoto(
                    client=self._sent_msg,
                    photo=self._up_path,
                    caption=cap_mono,
                    progress=self._upload_progress
                )

            if (
                not self._is_cancelled
                and self._media_group
                and (self._sent_msg.video or self._sent_msg.document)
            ):
                key = "documents" if self._sent_msg.document else "videos"
                if match := re_match(
                    r".+(?=\.0*\d+$)|.+(?=\.part\d+\..+$)", self._up_path
                ):
                    pname = match.group(0)
                    if pname in self._media_dict[key].keys():
                        self._media_dict[key][pname].append(self._sent_msg)
                    else:
                        self._media_dict[key][pname] = [self._sent_msg]
                    msgs = self._media_dict[key][pname]
                    if len(msgs) == 10:
                        await self._send_media_group(pname, key, msgs)
                    else:
                        self._last_msg_in_group = True

            if (
                self._thumb is None
                and thumb is not None
                and await aiopath.exists(thumb)
                and self._temp_thumb is None
            ):
                await remove(thumb)
            if (
                not self._is_cancelled
                and not self._is_corrupted
            ):
                await self.copy_message()
        except FloodWait as f:
            LOGGER.warning(str(f))
            await sleep(f.value)
        except Exception as err:
            if (
                self._thumb is None
                and thumb is not None
                and await aiopath.exists(thumb)
                and self._temp_thumb is None
            ):
                await remove(thumb)
            err_type = "RPCError: " if isinstance(err, RPCError) else ""
            LOGGER.error(f"{err_type}{err}. Path: {self._up_path}")
            if "Telegram says: [400" in str(err) and key != "documents":
                LOGGER.error(f"Retrying As Document. Path: {self._up_path}")
                return await self._upload_file(cap_mono, file, True)
            raise err
    
    async def copy_message(self):
        max_retries = 2
        for attempt in range(max_retries):
            LOGGER.info(f"Forwarding message (attempt {attempt + 1}/{max_retries})")
            try:
                if self._forwardChatId != "":
                    await copyMessage(
                        chat_id=self._forwardChatId, 
                        from_chat_id=self._sent_msg.chat.id, 
                        message_id=self._sent_msg.id, 
                        message_thread_id=self._forwardThreadId
                    )
                break
            except Exception as e:
                LOGGER.error(f"Failed when forward message (attempt {attempt + 1}/{max_retries}) => {e}")
                if attempt == max_retries - 1:
                    #await sendMessage(self._listener.message, f"Hai {self._listener.tag}, Terjadi kesalahan saat forward hasil leech anda.\n\n<code>{e}</code>")
                    LOGGER.error(f"Failed to forward message after {max_retries} attempts. Path: {self._up_path}")
                await sleep(1)

    @property
    def speed(self):
        try:
            return self._processed_bytes / (time() - self._start_time)
        except:
            return 0

    @property
    def processed_bytes(self):
        return self._processed_bytes

    async def cancel_task(self):
        self._is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self._listener.name}")
        await self._listener.onUploadError("Unggahan dibatalkan oleh User!")