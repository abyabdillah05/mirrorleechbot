from asyncio import sleep
from pyrogram.errors import FloodWait
from time import time
from re import match as re_match

from bot import config_dict, LOGGER, status_dict, task_dict_lock, user_data, Intervals, bot, user as owner_ses
from bot.helper.ext_utils.bot_utils import setInterval, sync_to_async, create_session
from bot.helper.ext_utils.status_utils import get_readable_message
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.exceptions import TgLinkException
from pyrogram import Client as tgClient

## Send Message ##

async def sendMessage(message, text, buttons=None, block=True):
    try:
        return await message.reply(
            text=text,
            quote=True,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if block:
            await sleep(f.value * 1.2)
            return await sendMessage(message, text, buttons)
        return str(f)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Edit Message ##

async def editMessage(message, text, buttons=None, block=True):
    try:
        await message.edit(
            text=text, disable_web_page_preview=True, reply_markup=buttons
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if block:
            await sleep(f.value * 1.2)
            return await editMessage(message, text, buttons)
        return str(f)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)
   
## Copy Message ##

async def copyMessage(chat_id:int, from_chat_id:int, message_id=int, message_thread_id=None, is_media_group=False):
    try:
        if is_media_group:
            await bot.copy_media_group(
                chat_id=chat_id, 
                from_chat_id=from_chat_id, 
                message_id=message_id, 
                message_thread_id=message_thread_id
            )
        else:
            await bot.copy_message(
                chat_id=chat_id, 
                from_chat_id=from_chat_id, 
                message_id=message_id, 
                message_thread_id=message_thread_id
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await copyMessage(chat_id, from_chat_id, message_id, message_thread_id, is_media_group)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Forward Message ##

async def forwardMessage(chat_id:int, from_chat_id:int, message_id=int, message_thread_id=None, unquote=True):
    try:
        await bot.forward_messages(
                chat_id=chat_id, 
                from_chat_id=from_chat_id, 
                message_id=message_id, 
                message_thread_id=message_thread_id,
                drop_author=unquote
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await forwardMessage(chat_id, from_chat_id, message_id, message_thread_id, unquote)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Send Document ##

async def sendFile(message, file, caption=None):
    try:
        return await message.reply_document(
            document=file, 
            quote=True, 
            caption=caption, 
            disable_notification=True
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendFile(message, file, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Send Photo ##

async def sendPhoto(message, photo, caption=None):
    try:
        return await message.reply_photo(
            photo=photo, 
            quote=True, 
            caption=caption, 
            disable_notification=True
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendFile(message, photo, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Send Rss ##
## This Function Is No Longer Used, But You Can Use It If Needed ##
## This Function For Rss ##
# Noted By: Tg @IgnoredProjectXcl #

async def sendRss(text):
    try:
        if owner_ses:
            return await owner_ses.send_message(
                chat_id=config_dict["RSS_CHAT_ID"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
        else:
            return await bot.send_message(
                chat_id=config_dict["RSS_CHAT_ID"],
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendRss(text)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Delete Message ##

async def deleteMessage(message):
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(str(e))

## Auto Delete Message ##
## You Can Change Time Auto Delte Message In config.env ##

async def auto_delete_message(cmd_message=None, bot_message=None):
    if config_dict["AUTO_DELETE_MESSAGE_DURATION"] != -1:
        await sleep(config_dict["AUTO_DELETE_MESSAGE_DURATION"])
        if cmd_message is not None:
            await deleteMessage(cmd_message)
        if bot_message is not None:
            await deleteMessage(bot_message)

## Delete Status Message ##

async def delete_status():
    async with task_dict_lock:
        for key, data in list(status_dict.items()):
            try:
                del status_dict[key]
                await deleteMessage(data["message"])
            except Exception as e:
                LOGGER.error(str(e))

## Edit Status Message ##
## This Function Is No Longer Used, But You Can Use It If Needed ##
# Noted By: Tg @IgnoredProjectXcl #

async def edit_status():
    async with task_dict_lock:
        for key, data in list(status_dict.items()):
            try:
                del status_dict[key]
                await editMessage(data["message"], f"Status message telah ditutup, silahkan buka kembali dengan perintah /{BotCommands.StatusCommand[0]}")
            except Exception as e:
                LOGGER.error(str(e))

## Edit Status Message ##
## This Function Replaces The Function Above, The Difference Is That It Only Edits One Status In Global | Private | Group ##
# Noted By: Tg @IgnoredProjectXcl #

async def edit_single_status(sid):
    async with task_dict_lock:
        if sid in status_dict:
            try:
                await editMessage(status_dict[sid]["message"], f"Status telah ditutup. Gunakan /{BotCommands.StatusCommand[0]} jika anda ingin melihat status lagi.")
                del status_dict[sid]
                if obj := Intervals["status"].get(sid):
                    obj.cancel()
                    del Intervals["status"][sid]
                return True
            except Exception as e:
                LOGGER.error(f"Error saat menutup status {sid}: {str(e)}")
        return False

## Get Telegram Link Message ##

async def get_tg_link_message(link, uid=None):
    user_dict = user_data.get(uid, {})
    string = user_dict.get("string_session", None)
    if uid and string:
        try:
            user = await create_session(uid)
        except:
            pass
    else:
        user = owner_ses
    message = None
    links = []
    if link.startswith("https://t.me/"):
        private = False
        msg = re_match(
            r"https:\/\/t\.me\/(?:c\/)?([^\/]+)(?:\/[^\/]+)?\/([0-9-]+)", link
        )
    else:
        private = True
        msg = re_match(
            r"tg:\/\/openmessage\?user_id=([0-9]+)&message_id=([0-9-]+)", link
        )
        if not user:
            raise TgLinkException("USER_SESSION_STRING diperlukan untuk link private!")

    chat = msg[1]
    msg_id = msg[2]
    if "-" in msg_id:
        start_id, end_id = msg_id.split("-")
        msg_id = start_id = int(start_id)
        end_id = int(end_id)
        btw = end_id - start_id
        if private:
            link = link.split("&message_id=")[0]
            links.append(f"{link}&message_id={start_id}")
            for _ in range(btw):
                start_id += 1
                links.append(f"{link}&message_id={start_id}")
        else:
            link = link.rsplit("/", 1)[0]
            links.append(f"{link}/{start_id}")
            for _ in range(btw):
                start_id += 1
                links.append(f"{link}/{start_id}")
    else:
        msg_id = int(msg_id)

    if chat.isdigit():
        chat = int(chat) if private else int(f"-100{chat}")

    if not private:
        try:
            message = await bot.get_messages(chat_id=chat, message_ids=msg_id)
            if message.empty:
                private = True
        except Exception as e:
            private = True
            if not user:
                raise e

    if not private:
        return (links, "bot") if links else (message, "bot")
    elif user:
        try:
            user_message = await user.get_messages(chat_id=chat, message_ids=msg_id)
        except Exception as e:
            raise TgLinkException(
                f"Bot tidak punya akses ke chat ini, silahkan tambahkan User_String anda ke bot untuk mirror/leech dari channel Private !\n\n<blockquote>{e}</blockquote>"
            ) from e
        if not user_message.empty:
            return (links, "user") if links else (user_message, "user")
    else:
        raise TgLinkException("Link private!")

## Enhanced Status All | Private | Group ##
## This Enhanced Different Each User And Group ##
# You Can Modify It Again Or Improve It Again | Noted By: Tg @IgnoredProjectXcl #

async def update_status_message(sid, force=False):
    async with task_dict_lock:
        if not status_dict.get(sid):
            if obj := Intervals["status"].get(sid):
                obj.cancel()
                del Intervals["status"][sid]
            return
            
        if not force and time() - status_dict[sid]["time"] < 3:
            return
            
        status_dict[sid]["time"] = time()
        
        page_no = status_dict[sid]["page_no"]
        status = status_dict[sid]["status"]
        is_user = status_dict[sid]["is_user"]
        page_step = status_dict[sid]["page_step"]
        is_all = status_dict[sid].get("is_all", False)
        
        chat_id = status_dict[sid].get("chat_id")
        cmd_user_id = status_dict[sid].get("cmd_user_id") or (sid if is_user else None)
        
        text, buttons = await sync_to_async(
            get_readable_message, sid, is_user, page_no, status, page_step, chat_id, is_all, cmd_user_id,
        )
        
        if text is None:
            del status_dict[sid]
            if obj := Intervals["status"].get(sid):
                obj.cancel()
                del Intervals["status"][sid]
            return
            
        if text != status_dict[sid]["message"].text:
            message = await editMessage(
                status_dict[sid]["message"], text, buttons, block=False
            )
            
            if isinstance(message, str):
                if message.startswith("Telegram says: [400"):
                    del status_dict[sid]
                    if obj := Intervals["status"].get(sid):
                        obj.cancel()
                        del Intervals["status"][sid]
                else:
                    LOGGER.error(f"Status dengan ID: {sid} tidak dapat diperbarui. Error: {message}")
                return
                
            status_dict[sid]["message"].text = text
            status_dict[sid]["time"] = time()

## Enhanced Status All | Private | Group ##
## This Enhanced Different Each User And Group ##
# You Can Modify It Again Or Improve It Again | Noted By: Tg @IgnoredProjectXcl #

async def sendStatusMessage(message, user_id=0, is_user=False, chat_id=None, is_all=False, cmd_user_id=None):
    async with task_dict_lock:
        # Determine the status ID and context type
        if is_all:
            sid = 0
            status_type = "global"
        elif is_user:
            sid = user_id
            status_type = "private" 
        elif chat_id and chat_id < 0:
            sid = chat_id
            status_type = "group"
        else:
            if message.chat.type in ["private", "bot"]:
                sid = message.from_user.id
                is_user = True
                status_type = "private"
                chat_id = None
            else:
                sid = message.chat.id
                chat_id = message.chat.id
                status_type = "group"
        
        # Set the requester ID for permission checks
        requester_id = cmd_user_id or message.from_user.id
        
        # Update existing status or create new one
        if sid in list(status_dict.keys()):
            page_no = status_dict[sid]["page_no"]
            status = status_dict[sid]["status"]
            page_step = status_dict[sid]["page_step"]
            
            text, buttons = await sync_to_async(
                get_readable_message, sid, is_user, page_no, status, page_step, chat_id, is_all, requester_id
            )
            
            if text is None:
                del status_dict[sid]
                if obj := Intervals["status"].get(sid):
                    obj.cancel()
                    del Intervals["status"][sid]
                return
                
            message_obj = status_dict[sid]["message"]
            await deleteMessage(message_obj)
            message_obj = await sendMessage(message, text, buttons, block=False)
            
            if isinstance(message_obj, str):
                LOGGER.error(f"Status dengan ID: {sid} tidak dapat dikirim. Error: {message_obj}")
                return
                
            message_obj.text = text
            status_dict[sid].update({
                "message": message_obj, 
                "time": time(),
                "cmd_user_id": requester_id,
                "is_all": is_all,
                "is_user": is_user,
                "chat_id": chat_id,
                "status_type": status_type
            })
        else:
            text, buttons = await sync_to_async(
                get_readable_message, sid, is_user, 1, "All", 1, chat_id, is_all, requester_id
            )
            
            if text is None:
                return
                
            message_obj = await sendMessage(message, text, buttons, block=False)
            
            if isinstance(message_obj, str):
                LOGGER.error(f"Status dengan ID: {sid} tidak dapat dikirim. Error: {message_obj}")
                return
                
            message_obj.text = text
            status_dict[sid] = {
                "message": message_obj,
                "time": time(),
                "page_no": 1,
                "page_step": 1,
                "status": "All",
                "is_user": is_user,
                "cmd_user_id": requester_id,
                "is_all": is_all,
                "chat_id": chat_id,
                "status_type": status_type
            }
            
    # Set up interval for status update
    if not Intervals["status"].get(sid):
        Intervals["status"][sid] = setInterval(
            config_dict["STATUS_UPDATE_INTERVAL"], update_status_message, sid
        )

## Custom Send Message ##

# NOTE: Custom by Me, if You dont need it, just ignore or delete from this line ^^
async def customSendMessage(client, chat_id:int, text:str, message_thread_id=None, buttons=None):
    try:
        return await client.send_message(
            chat_id=chat_id,
            text=text,
            disable_web_page_preview=True,
            disable_notification=True,
            message_thread_id=message_thread_id,
            reply_markup=buttons
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendMessage(client, chat_id, text, message_thread_id, buttons)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Custom Send Rss Message ##
## This Function Is No Longer Used, But You Can Use It If Needed ##
# Noted By: Tg @IgnoredProjectXcl #

async def customSendRss(text, image=None, image_caption=None, reply_markup=None):
    chat_id = None
    message_thread_id = None
    if chat_id := config_dict.get("RSS_CHAT_ID"):
        if not isinstance(chat_id, int):
            if ":" in chat_id:
                message_thread_id = chat_id.split(":")[1]
                chat_id = chat_id.split(":")[0]
        
        if chat_id.isdigit():
            chat_id = int(chat_id)
        
        if message_thread_id.isdigit():
            message_thread_id = int(message_thread_id)
    else:
        return "RSS_CHAT_ID tidak ditemukan!"
        
    try:
        if image:
            if len(text) > 1024:
                reply_photo = await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=f"<code>{image_caption}</code>",
                    disable_notification=True,
                    message_thread_id=message_thread_id
                )
                return await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    disable_web_page_preview=True,
                    disable_notification=True,
                    message_thread_id=message_thread_id,
                    reply_to_message_id=reply_photo.id,
                    reply_markup=reply_markup
                )
            else:
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=text,
                    disable_notification=True,
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup
                )
        else:
            return await bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_web_page_preview=True,
                disable_notification=True,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendRss(text)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Custom Send Document ##

async def customSendDocument(client, document, thumb, caption, progress):
    try:
        return await client.reply_document(
            document=document,
            quote=True,
            thumb=thumb,
            caption=caption,
            force_document=True,
            disable_notification=True,
            progress=progress
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendDocument(client, document, thumb, caption, progress)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Custom Send Video ##

async def customSendVideo(client, video, caption, duration, width, height, thumb, progress):
    try:
        return await client.reply_video(
            video=video,
            quote=True,
            caption=caption,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            supports_streaming=True,
            disable_notification=True,
            progress=progress
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendVideo(client, video, caption, duration, width, height, thumb, progress)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Custom Send Audio ##

async def customSendAudio(client, audio, caption, duration, performer, title, thumb, progress):
    try:
        return await client.reply_audio(
            audio=audio,
            quote=True,
            caption=caption,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=True,
            progress=progress
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendAudio(client, audio, caption, duration, performer, title, thumb, progress)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)

## Custom Send Photo ##

async def customSendPhoto(client, photo, caption, progress):
    try:
        return await client.reply_photo(
            photo=photo,
            quote=True,
            caption=caption,
            disable_notification=True,
            progress=progress
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendPhoto(client, photo, caption, progress)
    except Exception as e:
        LOGGER.error(str(e))
        raise Exception(e)