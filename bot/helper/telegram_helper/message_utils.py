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
from bot.helper.ext_utils.translator import TranslationManager

## Helper Function For Translation ##

def _get_user_id_from_message(message):
    if hasattr(
        message,
        'from_user'
        ) and message.from_user and hasattr(
            message.from_user,
            'id'
            ):
        return message.from_user.id
    return None             

def _translate_text(text, message=None, user_id=None):
    if user_id is None and message is not None:
        user_id = _get_user_id_from_message(message)
    return TranslationManager.translate_text(
        text,
        user_id=user_id
        )

## Send Message ##

async def sendMessage(message, text, buttons=None, block=True):
    user_id = _get_user_id_from_message(message)
    translated_text = _translate_text(text, user_id=user_id)
    try:
        return await message.reply(
            text=translated_text,
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
    user_id = _get_user_id_from_message(message)
    translated_text = _translate_text(text, user_id=user_id)
    try:
        await message.edit(
            text=translated_text, disable_web_page_preview=True, reply_markup=buttons
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
    user_id = _get_user_id_from_message(message)
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    try:
        return await message.reply_document(
            document=file, 
            quote=True, 
            caption=translated_caption, 
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
    user_id = _get_user_id_from_message(message)
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    try:
        return await message.reply_photo(
            photo=photo, 
            quote=True, 
            caption=translated_caption, 
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
        LOGGER.info("Message already deleted!")

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
                text = f"Status message telah ditutup, silahkan buka kembali dengan perintah /{BotCommands.StatusCommand[0]}"
                translated_text = _translate_text(text, user_id=key)
                await editMessage(data["message"], translated_text)
            except Exception as e:
                LOGGER.error(str(e))

## Edit Status Message ##
## This Function Replaces The Function Above, The Difference Is That It Only Edits One Status In Global | Private | Group ##
# Noted By: Tg @IgnoredProjectXcl #

async def edit_single_status(sid):
    async with task_dict_lock:
        if sid in status_dict:
            try:
                text = f"Status telah ditutup. Gunakan /{BotCommands.StatusCommand[0]} jika anda ingin melihat status lagi."
                translated_text = _translate_text(text, user_id=sid)
                await editMessage(
                    status_dict[sid]["message"], translated_text
                )
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
    # This function doesn't need translation as it doesn't display text to users
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
        error_msg = "USER_SESSION_STRING diperlukan untuk link private!"
        if not user:
            translated_error = _translate_text(error_msg, user_id=uid)
            raise TgLinkException(translated_error)

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
            error_msg = f"Bot tidak punya akses ke chat ini, silahkan tambahkan User_String anda ke bot untuk mirror/leech dari channel Private !\n\n<blockquote>{e}</blockquote>"
            translated_error = _translate_text(error_msg, user_id=uid)
            raise TgLinkException(translated_error) from e
        if not user_message.empty:
            return (links, "user") if links else (user_message, "user")
    else:
        error_msg = "Link private!"
        translated_error = _translate_text(error_msg, user_id=uid)
        raise TgLinkException(translated_error)

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
        text, buttons = await sync_to_async(
            get_readable_message, sid, is_user, page_no, status, page_step
        )
        if text is None:
            del status_dict[sid]
            if obj := Intervals["status"].get(sid):
                obj.cancel()
                del Intervals["status"][sid]
            return
        if text != status_dict[sid]["message"].text:
            translated_text = _translate_text(text, user_id=sid)
            message = await editMessage(
                status_dict[sid]["message"], translated_text, buttons, block=False
            )
            if isinstance(message, str):
                if message.startswith("Telegram says: [400"):
                    del status_dict[sid]
                    if obj := Intervals["status"].get(sid):
                        obj.cancel()
                        del Intervals["status"][sid]
                else:
                    LOGGER.error(
                        f"Status with id: {sid} haven't been updated. Error: {message}"
                    )
                return
            status_dict[sid]["message"].text = text
            status_dict[sid]["time"] = time()

## Enhanced Status All | Private | Group ##
## This Enhanced Different Each User And Group ##
# You Can Modify It Again Or Improve It Again | Noted By: Tg @IgnoredProjectXcl #

async def sendStatusMessage(msg, user_id=0):
    async with task_dict_lock:
        sid = user_id or msg.chat.id
        is_user = bool(user_id)
        if sid in list(status_dict.keys()):
            page_no = status_dict[sid]["page_no"]
            status = status_dict[sid]["status"]
            page_step = status_dict[sid]["page_step"]
            text, buttons = await sync_to_async(
                get_readable_message, sid, is_user, page_no, status, page_step
            )
            if text is None:
                del status_dict[sid]
                if obj := Intervals["status"].get(sid):
                    obj.cancel()
                    del Intervals["status"][sid]
                return
            message = status_dict[sid]["message"]
            await deleteMessage(message)
            translated_text = _translate_text(text, user_id=sid)
            message = await sendMessage(msg, translated_text, buttons, block=False)
            if isinstance(message, str):
                LOGGER.error(
                    f"Status with id: {sid} haven't been sent. Error: {message}"
                )
                return
            message.text = text
            status_dict[sid].update({"message": message, "time": time()})
        else:
            text, buttons = await sync_to_async(get_readable_message, sid, is_user)
            if text is None:
                return
            translated_text = _translate_text(text, user_id=sid)
            message = await sendMessage(msg, translated_text, buttons, block=False)
            if isinstance(message, str):
                LOGGER.error(
                    f"Status with id: {sid} haven't been sent. Error: {message}"
                )
                return
            message.text = text
            status_dict[sid] = {
                "message": message,
                "time": time(),
                "page_no": 1,
                "page_step": 1,
                "status": "All",
                "is_user": is_user,
            }
    if not Intervals["status"].get(sid) and not is_user:
        Intervals["status"][sid] = setInterval(
            config_dict["STATUS_UPDATE_INTERVAL"], update_status_message, sid
        )

## Custom Send Message ##

# NOTE: Custom by Me, if You dont need it, just ignore or delete from this line ^^
async def customSendMessage(client, chat_id:int, text:str, message_thread_id=None, buttons=None):
    translated_text = _translate_text(text, user_id=chat_id)
    try:
        return await client.send_message(
            chat_id=chat_id,
            text=translated_text,
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
        
        if message_thread_id and message_thread_id.isdigit():
            message_thread_id = int(message_thread_id)
    else:
        return "RSS_CHAT_ID tidak ditemukan!"
    
    translated_text = _translate_text(text, user_id=chat_id)
    translated_caption = _translate_text(image_caption, user_id=chat_id) if image_caption else None
    
    try:
        if image:
            if len(translated_text) > 1024:
                reply_photo = await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=f"<code>{translated_caption or ''}</code>",
                    disable_notification=True,
                    message_thread_id=message_thread_id
                )
                return await bot.send_message(
                    chat_id=chat_id,
                    text=translated_text,
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
                    caption=translated_text,
                    disable_notification=True,
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup
                )
        else:
            return await bot.send_message(
                chat_id=chat_id,
                text=translated_text,
                disable_web_page_preview=True,
                disable_notification=True,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup
            )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await customSendRss(text, image, image_caption, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)

## Custom Send Document ##

async def customSendDocument(client, document, thumb, caption, progress):
    user_id = None
    if hasattr(client, 'user_id'):
        user_id = client.user_id
    
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    
    try:
        return await client.reply_document(
            document=document,
            quote=True,
            thumb=thumb,
            caption=translated_caption,
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
    user_id = None
    if hasattr(client, 'user_id'):
        user_id = client.user_id
    
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    
    try:
        return await client.reply_video(
            video=video,
            quote=True,
            caption=translated_caption,
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
    user_id = None
    if hasattr(client, 'user_id'):
        user_id = client.user_id
    
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    translated_title = _translate_text(title, user_id=user_id) if title else None
    translated_performer = _translate_text(performer, user_id=user_id) if performer else None
    
    try:
        return await client.reply_audio(
            audio=audio,
            quote=True,
            caption=translated_caption,
            duration=duration,
            performer=translated_performer,
            title=translated_title,
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
    user_id = None
    if hasattr(client, 'user_id'):
        user_id = client.user_id
    
    translated_caption = _translate_text(caption, user_id=user_id) if caption else None
    
    try:
        return await client.reply_photo(
            photo=photo,
            quote=True,
            caption=translated_caption,
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