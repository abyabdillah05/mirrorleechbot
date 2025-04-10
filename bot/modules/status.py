from time import time

####################################
## Import Libraries From Pyrogram ##
####################################

from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from psutil import (
    cpu_percent, 
    virtual_memory, 
    disk_usage, 
    net_io_counters
)

######################################
## Importing Variabels From Project ##
######################################

from bot import (
    task_dict_lock,
    status_dict,
    task_dict,
    botStartTime,
    DOWNLOAD_DIR,
    bot,
    OWNER_ID,
    LOGGER
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    auto_delete_message,
    sendStatusMessage,
    update_status_message,
    edit_single_status,
)
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    speed_string_to_bytes,
    STATUS_VALUES
)
from bot.helper.ext_utils.common_utils import (get_readable_file_size,
                                            get_readable_time)

#############################
## Status Task Manager Bot ##
#############################

@new_task
async def mirror_status(_, message):
    async with task_dict_lock:
        count = len(task_dict)
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_owner = user_id == OWNER_ID
    
    text = message.text.split()
    cmd_type = text[1].lower() if len(text) > 1 else None
    
    if cmd_type == "help":
        help_text = (
            "<b>📋 BANTUAN PERINTAH STATUS</b>\n\n"
            "<b>Perintah Dasar:</b>\n"
            "• <code>[/status]</code>: Menampilkan status tugas berdasarkan konteks\n"
            "  - Di grup: Menampilkan tugas grup tersebut\n"
            "  - Di PM: Menampilkan tugas pribadi Anda\n\n"
            "<b>Perintah Khusus:</b>\n"
            "• <code>[/status me]</code>: Menampilkan hanya tugas Anda (pribadi)\n"
            "• <code>[/status all]</code>: Menampilkan semua tugas (khusus Owner)\n"
            "• <code>[/status help]</code>: Menampilkan bantuan ini\n\n"
            "<b>Informasi Tombol:</b>\n"
            "• ◀️ Prev / ▶️ Next: Navigasi antar halaman\n"
            "• 🔄 Refresh: Memperbarui status terbaru\n"
            "• Help: Menampilkan bantuan singkat\n"
            "• Info: Informasi tentang status saat ini\n"
            "• Tutup: Menutup pesan status\n\n"
            "<b>Catatan Penting:</b>\n"
            "• Tombol-tombol hanya dapat digunakan oleh pengguna yang meminta status atau Owner\n"
            "• Status diperbarui otomatis setiap beberapa detik\n"
            "• Gunakan filter untuk melihat tugas berdasarkan statusnya"
        )
        reply = await sendMessage(message, help_text)
        await auto_delete_message(message, reply)
        return
    
    if count == 0:
        currentTime = get_readable_time(time() - botStartTime)
        free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
        try:
            sent = get_readable_file_size(net_io_counters().bytes_sent)
        except:
            sent = "NaN"
        try:
            recv = get_readable_file_size(net_io_counters().bytes_recv)
        except:
            recv = "NaN"
        
        if cmd_type == "all":
            if not is_owner:
                msg = "<b>⚠️ Anda Tidak Dapat Menggunakan Perintah Ini!!</b>\n\n<code>[/status all]</code> hanya dapat digunakan oleh Owner bot!"
                reply = await sendMessage(message, msg)
                await auto_delete_message(message, reply)
                return
            context_type = "Global"
        if cmd_type == "me":
            context_type = "Private"
        if user_id:
            context_type = "Private"
        if chat_id:
            context_type = "Group"
            
        msg = f"<b>Tidak ada tugas aktif ({context_type})</b>\n─────────────────────────────"
        
        msg += (
            f"\n<b>Type:</b> <code>{context_type}</code>"
            f"\n<b>CPU:</b> <code>{cpu_percent()}%</code> | <b>FREE:</b> <code>{free}</code>" \
            f"\n<b>RAM:</b> <code>{virtual_memory().percent}%</code> | <b>UPTIME:</b> <code>{currentTime}</code>" \
            f"\n<b>T.Unduh:</b> <code>{recv}</code> | <b>T.Unggah:</b> <code>{sent}</code>"
        )
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
        return
    
    if cmd_type == "all":
        if not is_owner:
            msg = "<b>⚠️ AKSES DITOLAK</b>\n\n<code>[/status all]</code> hanya dapat digunakan oleh Owner bot!"
            reply = await sendMessage(message, msg)
            await auto_delete_message(message, reply)
            return
        await sendStatusMessage(message, 0, is_all=True, cmd_user_id=user_id)
        await deleteMessage(message)
        return
    
    if cmd_type == "me":
        await sendStatusMessage(message, user_id, is_user=True, cmd_user_id=user_id)
        await deleteMessage(message)
        return
    
    if message.chat.type in ["private", "bot"]:
        await sendStatusMessage(message, user_id, is_user=True, cmd_user_id=user_id)
    else:
        await sendStatusMessage(message, 0, chat_id=chat_id, cmd_user_id=user_id)
    
    await deleteMessage(message)

##################
## Status Pages ##
##################

@new_task
async def status_pages(_, query):
    data = query.data.split()
    
    raw_sid = data[1]
    action = data[2]
    
    if raw_sid.startswith("user_"):
        actual_sid = int(raw_sid.split("_")[1])
    elif raw_sid.startswith("group_"):
        actual_sid = int(raw_sid.split("_")[1])
        if actual_sid > 0:
            actual_sid = -abs(actual_sid)
    elif raw_sid == "global_status":
        actual_sid = 0
    else:
        try:
            actual_sid = int(raw_sid)
            if actual_sid > 0:
                raw_sid = f"user_{actual_sid}"
            elif actual_sid < 0:
                raw_sid = f"group_{abs(actual_sid)}"
            else:
                raw_sid = "global_status"
        except:
            await query.answer("Invalid status ID!", show_alert=True)
            return
    
    cmd_user_id = int(data[3]) if len(data) > 3 else None
    
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    is_owner = user_id == OWNER_ID
    
    async with task_dict_lock:
        if raw_sid not in status_dict:
            await query.answer("⚠️ Status message tidak ditemukan atau sudah ditutup!", show_alert=True)
            return
            
        status_type = status_dict[raw_sid].get("status_type", "group")
        status_owner_id = status_dict[raw_sid].get("cmd_user_id")
        is_all = status_dict[raw_sid].get("is_all", False)
        status_chat_id = status_dict[raw_sid].get("chat_id")
    
    has_permission = False
    
    if is_owner:
        has_permission = True
    elif status_owner_id and user_id == status_owner_id:
        has_permission = True
    elif status_type == "Group" and not is_all and status_chat_id and status_chat_id == chat_id:
        has_permission = True
    
    if not has_permission:
        await query.answer("⚠️ Anda tidak memiliki izin untuk mengakses tombol status ini!", show_alert=True)
        return
    
    if action == "ref":
        await query.answer("🔄 Sedang merefresh status...", show_alert=True)
        LOGGER.info(f"Refreshing status {raw_sid}")
        await update_status_message(raw_sid, force=True)
    
    elif action == "help":
        help_text = (
            "STATUS COMMANDS\n"
            "• [/status] - Status konteks\n"
            "• [/status me] - Tugas pribadi\n"
            "• [/status all] - Semua tugas (Owner)\n"
            "• Filter - Gunakan tombol filter\n"
            "• Batalkan tugas lambat (<20KB/s)"
        )
        await query.answer(help_text, show_alert=True)
    
    elif action in ["nex", "pre"]:
        await query.answer()
        async with task_dict_lock:
            if raw_sid in status_dict:
                if action == "nex":
                    status_dict[raw_sid]["page_no"] += status_dict[raw_sid]["page_step"]
                else:
                    status_dict[raw_sid]["page_no"] -= status_dict[raw_sid]["page_step"]
                await update_status_message(raw_sid, force=True)
    
    elif action == "ps":
        page_step = int(data[3])
        await query.answer(f"Step diubah menjadi {page_step}")
        async with task_dict_lock:
            if raw_sid in status_dict:
                status_dict[raw_sid]["page_step"] = page_step
                await update_status_message(raw_sid, force=True)
    
    elif action == "st":
        new_status = data[3]
        await query.answer(f"Filter: {new_status}")
        async with task_dict_lock:
            if raw_sid in status_dict:
                status_dict[raw_sid]["status"] = new_status
                await update_status_message(raw_sid, force=True)
    
    elif action == 'close':
        await query.answer(f"Status ditutup! Ketik [/{BotCommands.StatusCommand[0]}] untuk melihat status lagi.")
        success = await edit_single_status(raw_sid)
        if not success:
            LOGGER.error(f"Gagal menutup status dengan ID: {raw_sid}")
    
    elif action == 'info':
        status_type = status_dict.get(raw_sid, {}).get("status_type", "")
        is_all = status_dict.get(raw_sid, {}).get('is_all', False)
        is_user = status_dict.get(raw_sid, {}).get('is_user', False)
        chat_id = status_dict.get(raw_sid, {}).get('chat_id')
        
        if is_all:
            view_type = "Global"
        elif is_user:
            view_type = "Private" 
        elif chat_id:
            view_type = "Group"
        else:
            await query.answer("Invalid status context", show_alert=True)
            return
        
        async with task_dict_lock:
            tasks = {
                "Download": 0,
                "Upload": 0,
                "Seed": 0,
                "Archive": 0,
                "Extract": 0,
                "Split": 0,
                "QueueDl": 0,
                "QueueUp": 0,
                "Clone": 0,
                "CheckUp": 0,
                "Pause": 0,
                "SamVid": 0,
            }
            dl_speed = 0
            up_speed = 0
            seed_speed = 0
            
            for download in task_dict.values():
                task_matches = False
                tstatus = download.status()
                
                if is_all:
                    task_matches = True
                elif is_user and download.listener.user_id == actual_sid:
                    task_matches = True
                elif chat_id and hasattr(download.listener, 'message') and hasattr(download.listener.message, 'chat') and download.listener.message.chat.id == chat_id:
                    task_matches = True
                
                if task_matches:
                    if tstatus == MirrorStatus.STATUS_DOWNLOADING:
                        tasks["Download"] += 1
                        dl_speed += speed_string_to_bytes(download.speed())
                    elif tstatus == MirrorStatus.STATUS_UPLOADING:
                        tasks["Upload"] += 1
                        up_speed += speed_string_to_bytes(download.speed())
                    elif tstatus == MirrorStatus.STATUS_SEEDING:
                        tasks["Seed"] += 1
                        seed_speed += speed_string_to_bytes(download.seed_speed())
                    elif tstatus == MirrorStatus.STATUS_ARCHIVING:
                        tasks["Archive"] += 1
                    elif tstatus == MirrorStatus.STATUS_EXTRACTING:
                        tasks["Extract"] += 1
                    elif tstatus == MirrorStatus.STATUS_SPLITTING:
                        tasks["Split"] += 1
                    elif tstatus == MirrorStatus.STATUS_QUEUEDL:
                        tasks["QueueDl"] += 1
                    elif tstatus == MirrorStatus.STATUS_QUEUEUP:
                        tasks["QueueUp"] += 1
                    elif tstatus == MirrorStatus.STATUS_CLONING:
                        tasks["Clone"] += 1
                    elif tstatus == MirrorStatus.STATUS_CHECKING:
                        tasks["CheckUp"] += 1
                    elif tstatus == MirrorStatus.STATUS_PAUSED:
                        tasks["Pause"] += 1
                    elif tstatus == MirrorStatus.STATUS_SAMVID:
                        tasks["SamVid"] += 1
        
        info_text = (
            f"STATS INFO\n\n"
            f"Type: {view_type}\n"
            f"ID: {raw_sid}\n\n"
            f"TASKS:\n"
            f"• DL: {tasks['Download']} | UP: {tasks['Upload']} | Seed: {tasks['Seed']}\n"
            f"• Arc: {tasks['Archive']} | Ext: {tasks['Extract']}\n"
            f"• QDL: {tasks['QueueDl']} | QUP: {tasks['QueueUp']}\n\n"
            f"SPEEDS:\n"
            f"• Seed: {get_readable_file_size(seed_speed)}/s\n"
            f"• DL: {get_readable_file_size(dl_speed)}/s\n"
            f"• UP: {get_readable_file_size(up_speed)}/s"
        )
        await query.answer(info_text, show_alert=True)

######################################
## Command & CallbackQuery Handlers ##
######################################

bot.add_handler(
    MessageHandler(
        mirror_status,
        filters=command(
            BotCommands.StatusCommand
        ) & CustomFilters.authorized,
    )
)

bot.add_handler(
    CallbackQueryHandler(
        status_pages, 
        filters=regex(
            "^status"
        )
    )
)