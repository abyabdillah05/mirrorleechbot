from time import time
from asyncio import sleep
from re import match as re_match
from pyrogram.errors import FloodWait
from pyrogram import Client as tgClient

####################################
## Import Variables From Project ##
###################################

from bot.helper.ext_utils.exceptions import TgLinkException
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.status_utils import get_readable_message
from bot.helper.ext_utils.status_utils import (
    StatusType, StatusPermission, StatusButtonManager, 
    StatusContext, StatusRequest,
    format_private_status_message, format_group_status_message, 
    format_global_status_message
)

from bot.helper.ext_utils.bot_utils import (
    setInterval,
    sync_to_async,
    create_session,
)
from bot import (
    config_dict,
    LOGGER,
    status_dict,
    task_dict_lock,
    user_data,
    Intervals,
    bot,
    user as owner_ses,
)

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

## Send File ##

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

## Send RSS ##

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
## You Can Edit Time In config.env ##

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

## Edit Single Status ##

async def edit_single_status(sid):
    """Edit a single status message to closed state"""
    async with task_dict_lock:
        if sid in status_dict:
            try:
                status_data = status_dict[sid]
                await editMessage(
                    status_data["message"], 
                    f"Status message telah ditutup, silahkan buka kembali dengan perintah /{BotCommands.StatusCommand[0]}"
                )
                del status_dict[sid]
                if obj := Intervals["status"].get(sid):
                    obj.cancel()
                    del Intervals["status"][sid]
            except Exception as e:
                LOGGER.error(str(e))

## Edit Status Message ##

async def edit_status():
    """Edit all status messages to closed state"""
    async with task_dict_lock:
        for key, data in list(status_dict.items()):
            try:
                await editMessage(
                    data["message"], 
                    f"Status message telah ditutup, silahkan buka kembali dengan perintah /{BotCommands.StatusCommand[0]}"
                )
                del status_dict[key]
                if obj := Intervals["status"].get(key):
                    obj.cancel()
                    del Intervals["status"][key]
            except Exception as e:
                LOGGER.error(str(e))

## Get Read Link Message ##

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

## Update Status Message ##

async def update_status_message(sid, force=False):
    """Update status message for given status ID"""
    async with task_dict_lock:
        if not status_dict.get(sid):
            if obj := Intervals["status"].get(sid):
                obj.cancel()
                del Intervals["status"][sid]
            return
        if not force and time() - status_dict[sid]["time"] < 3:
            return
            
        # Get status information
        status_data = status_dict[sid]
        page_no = status_data["page_no"]
        status_filter = status_data["status"]
        status_type = status_data["type"]
        cmd_user_id = status_data["cmd_user_id"]
        is_user = status_data["is_user"]
        page_step = status_data["page_step"]
        
        # Create a status request for this update
        request = StatusRequest(
            user_id=sid if is_user else 0,
            chat_id=sid if not is_user else 0,
            status_type=status_type,
            cmd_user_id=cmd_user_id,
            page_no=page_no,
            status_filter=status_filter,
            page_step=page_step
        )
        
        # Get tasks based on context
        tasks = request.get_filtered_tasks()
        
        # If no tasks and filter is All, cleanup
        if len(tasks) == 0 and status_filter == "All":
            del status_dict[sid]
            if obj := Intervals["status"].get(sid):
                obj.cancel()
                del Intervals["status"][sid]
            return
        
        # Ensure page number is valid
        STATUS_LIMIT = config_dict["STATUS_LIMIT"]
        tasks_no = len(tasks)
        
        if status_type == StatusType.GLOBAL:
            pages = max(tasks_no, 1)  # For global, one task per page
        else:
            pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
            
        if page_no > pages:
            page_no = (page_no - 1) % pages + 1
        elif page_no < 1:
            page_no = pages - (abs(page_no) % pages)
            
        status_data["page_no"] = page_no  # Update the page number
        
        # Format message based on context type
        if status_type == StatusType.PRIVATE:
            user = next((tk.listener.user for tk in tasks), None) if tasks else None
            username = getattr(user, 'username', 'Unknown')
            first_name = getattr(user, 'first_name', 'User')
            text = format_private_status_message(tasks, sid, username, first_name, page_no, status_filter, page_step)
        elif status_type == StatusType.GROUP:
            chat_title = getattr(next((tk.listener.message.chat for tk in tasks), None) if tasks else None, 'title', 'Group')
            text = format_group_status_message(tasks, sid, chat_title, page_no, status_filter, page_step)
        else:  # Global
            text = format_global_status_message(tasks, page_no, status_filter, page_step)
            
        # Generate buttons
        button_maker = StatusButtonManager.generate_buttons(
            status_type, sid, cmd_user_id, page_no, pages, tasks_no, status_filter
        )
        buttons = button_maker.build_menu(3)
        
        # Only update if text has changed
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
                    LOGGER.error(
                        f"Status with id: {sid} haven't been updated. Error: {message}"
                    )
                return
            status_dict[sid]["message"].text = text
        
        status_dict[sid]["time"] = time()

## Send Status Message ##

async def sendStatusMessage(message, user_id=0, is_user=False, chat_id=None, is_all=False, cmd_user_id=None):
    """Send new status message based on context"""
    # Determine context if not explicitly provided
    if cmd_user_id is None:
        cmd_user_id = message.from_user.id
        
    # Determine context type
    if is_all and StatusPermission.is_owner(cmd_user_id):
        # Global status (owner only)
        status_type = StatusType.GLOBAL
        sid = 0  # Global status always uses 0 as ID
    elif is_user or user_id:
        # Private user status
        status_type = StatusType.PRIVATE
        sid = user_id or message.from_user.id
    elif chat_id:
        # Specific chat status
        status_type = StatusType.GROUP
        sid = chat_id
    else:
        # Default: derive from message context
        cmd_args = message.text.split()[1] if len(message.text.split()) > 1 else None
        status_type, sid, cmd_user_id = StatusContext.determine_context(message, cmd_args)
    
    async with task_dict_lock:
        # Create request object to handle filtering
        request = StatusRequest(
            user_id=sid if status_type == StatusType.PRIVATE else 0,
            chat_id=sid if status_type == StatusType.GROUP else 0,
            status_type=status_type,
            cmd_user_id=cmd_user_id
        )
        
        # Check if a status already exists for this ID
        if sid in status_dict:
            # Use existing status parameters
            page_no = status_dict[sid]["page_no"]
            status_filter = status_dict[sid]["status"]
            page_step = status_dict[sid]["page_step"]
            
            # Update request with existing parameters
            request.page_no = page_no
            request.status_filter = status_filter
            request.page_step = page_step
            
            # Get tasks with these parameters
            tasks = request.get_filtered_tasks()
            
            if len(tasks) == 0 and status_filter == "All":
                del status_dict[sid]
                if obj := Intervals["status"].get(sid):
                    obj.cancel()
                    del Intervals["status"][sid]
                return
                
            # Delete old message
            old_message = status_dict[sid]["message"]
            await deleteMessage(old_message)
            
            # Format new message based on context
            if status_type == StatusType.PRIVATE:
                user = next((tk.listener.user for tk in tasks), None) if tasks else None
                username = getattr(user, 'username', message.from_user.username) 
                first_name = getattr(user, 'first_name', message.from_user.first_name)
                text = format_private_status_message(tasks, sid, username, first_name, page_no, status_filter, page_step)
            elif status_type == StatusType.GROUP:
                chat_title = message.chat.title
                text = format_group_status_message(tasks, sid, chat_title, page_no, status_filter, page_step)
            else:  # Global
                text = format_global_status_message(tasks, page_no, status_filter, page_step)
            
            # Generate buttons
            STATUS_LIMIT = config_dict["STATUS_LIMIT"]
            tasks_no = len(tasks)
            
            if status_type == StatusType.GLOBAL:
                pages = max(tasks_no, 1)  # One task per page for global
            else:
                pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
                
            button_maker = StatusButtonManager.generate_buttons(
                status_type, sid, cmd_user_id, page_no, pages, tasks_no, status_filter
            )
            buttons = button_maker.build_menu(3)
            
            # Send new message
            new_message = await sendMessage(message, text, buttons, block=False)
            if isinstance(new_message, str):
                LOGGER.error(f"Status with id: {sid} hasn't been sent. Error: {new_message}")
                return
                
            new_message.text = text
            
            # Update status_dict
            status_dict[sid].update({
                "message": new_message,
                "time": time(),
                "cmd_user_id": cmd_user_id,
                "type": status_type
            })
        else:
            # Create new status
            tasks = request.get_filtered_tasks()
            
            if len(tasks) == 0 and request.status_filter == "All":
                return
                
            # Format message based on context
            if status_type == StatusType.PRIVATE:
                user = next((tk.listener.user for tk in tasks), None) if tasks else None
                username = getattr(user, 'username', message.from_user.username)
                first_name = getattr(user, 'first_name', message.from_user.first_name)
                text = format_private_status_message(tasks, sid, username, first_name, 1, "All", 1)
            elif status_type == StatusType.GROUP:
                chat_title = message.chat.title
                text = format_group_status_message(tasks, sid, chat_title, 1, "All", 1)
            else:  # Global
                text = format_global_status_message(tasks, 1, "All", 1)
                
            # Generate buttons
            STATUS_LIMIT = config_dict["STATUS_LIMIT"]
            tasks_no = len(tasks)
            
            if status_type == StatusType.GLOBAL:
                pages = max(tasks_no, 1)  # One task per page for global
            else:
                pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
                
            button_maker = StatusButtonManager.generate_buttons(
                status_type, sid, cmd_user_id, 1, pages, tasks_no, "All"
            )
            buttons = button_maker.build_menu(3)
            
            # Send message
            new_message = await sendMessage(message, text, buttons, block=False)
            if isinstance(new_message, str):
                LOGGER.error(f"Status with id: {sid} hasn't been sent. Error: {new_message}")
                return
                
            new_message.text = text
            
            # Create entry in status_dict
            status_dict[sid] = {
                "message": new_message,
                "time": time(),
                "page_no": 1,
                "page_step": 1,
                "status": "All",
                "is_user": status_type == StatusType.PRIVATE,
                "cmd_user_id": cmd_user_id,
                "type": status_type
            }
        
    # Set up interval for auto-refresh (but not for private user status)
    if not Intervals["status"].get(sid) and status_type != StatusType.PRIVATE:
        Intervals["status"][sid] = setInterval(
            config_dict["STATUS_UPDATE_INTERVAL"], update_status_message, sid
        )

## Custom Send Message ##

# NOTE: Custom by @aenulrofik, if You dont need it, just ignore or delete from this line ^^
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

## Custom Send RSS ##

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