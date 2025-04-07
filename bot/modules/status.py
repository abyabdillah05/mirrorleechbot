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
    Intervals,
    bot,
    OWNER_ID,
    user_data
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    auto_delete_message,
    sendStatusMessage,
    update_status_message,
    edit_status,
)
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
    speed_string_to_bytes,
    STATUS_VALUES
)

#############################
## Status Task Manager Bot ##
#############################

@new_task
async def mirror_status(_, message):
    async with task_dict_lock:
        count = len(task_dict)
    
    user_id = message.from_user.id
    is_owner = user_id == OWNER_ID
    
    text = message.text.split()
    cmd_type = text[1].lower() if len(text) > 1 else None
    
    if cmd_type == "help":
        help_text = (
            "<b>📋 BANTUAN PERINTAH STATUS</b>\n\n"
            "<b>Perintah Dasar:</b>\n"
            "• <code>/status</code>: Menampilkan status tugas berdasarkan konteks\n"
            "  - Di grup: Menampilkan tugas grup tersebut\n"
            "  - Di PM: Menampilkan tugas pribadi Anda\n\n"
            "<b>Perintah Khusus:</b>\n"
            "• <code>/status me</code>: Menampilkan hanya tugas Anda (pribadi)\n"
            "• <code>/status all</code>: Menampilkan semua tugas (khusus Owner)\n"
            "• <code>/status help</code>: Menampilkan bantuan ini\n\n"
            "<b>Informasi Tombol:</b>\n"
            "• ⏪ Prev / ⏩ Next: Navigasi antar halaman\n"
            "• 🔄 Refresh: Memperbarui status terbaru\n"
            "• ❓ Help: Menampilkan bantuan singkat\n"
            "• ℹ️ Info: Informasi tentang status saat ini\n"
            "• 🔽 Tutup: Menutup pesan status\n\n"
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
                msg = "<b>⚠️ AKSES DITOLAK</b>\n\n<code>/status all</code> hanya dapat digunakan oleh Owner bot!"
                reply = await sendMessage(message, msg)
                await auto_delete_message(message, reply)
                return
            msg = "<b>📭 TIDAK ADA TUGAS AKTIF (GLOBAL)</b>\n___________________________"
        elif cmd_type == "me":
            msg = "<b>📭 TIDAK ADA TUGAS AKTIF (PRIBADI ANDA)</b>\n___________________________"
        else:
            if message.chat.type in ["private", "bot"]:
                msg = "<b>📭 TIDAK ADA TUGAS AKTIF (PRIBADI ANDA)</b>\n___________________________"
            else:
                msg = "<b>📭 TIDAK ADA TUGAS AKTIF (GRUP INI)</b>\n___________________________"
        
        msg += (
            f"\n<b>CPU :</b> <code>{cpu_percent()}%</code> | <b>FREE :</b> <code>{free}</code>" \
            f"\n<b>RAM :</b> <code>{virtual_memory().percent}%</code> | <b>UPTIME :</b> <code>{currentTime}</code>" \
            f"\n<b>T.Unduh :</b> <code>{recv}</code> | <b>T.Unggah :</b> <code>{sent}</code>" \
            f"\n<b>Powered By {bot.me.first_name}</b>"
        )
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
        return
    
    if cmd_type == "all":
        if not is_owner:
            msg = "<b>⚠️ AKSES DITOLAK</b>\n\n<code>/status all</code> hanya dapat digunakan oleh Owner bot!"
            reply = await sendMessage(message, msg)
            await auto_delete_message(message, reply)
            return
        await sendStatusMessage(message, 0, is_all=True, cmd_user_id=user_id)
        await deleteMessage(message)
        return
    
    if cmd_type == "me":
        await sendStatusMessage(message, message.from_user.id, is_user=True, cmd_user_id=user_id)
        await deleteMessage(message)
        return
    
    if message.chat.type in ["private", "bot"]:
        await sendStatusMessage(message, message.from_user.id, is_user=True, cmd_user_id=user_id)
    else:
        await sendStatusMessage(message, 0, chat_id=message.chat.id, cmd_user_id=user_id)
    
    await deleteMessage(message)

##################
## Status Pages ##
##################

@new_task
async def status_pages(_, query):
    data = query.data.split()
    
    sid = int(data[1])
    action = data[2]
    
    cmd_user_id = int(data[3]) if len(data) > 3 else None
    
    user_id = query.from_user.id
    is_owner = user_id == OWNER_ID
    
    if cmd_user_id and user_id != cmd_user_id and not is_owner:
        await query.answer("⚠️ Tombol ini hanya dapat digunakan oleh pengguna yang meminta status atau Owner!", show_alert=True)
        return
    
    if action == "ref":
        await query.answer("🔄 Menyegarkan status...")
        await update_status_message(sid, force=True)
    
    elif action == "help":
        help_text = (
            "📋 BANTUAN STATUS\n\n"
            "• /status - Status konteks\n"
            "   - Di PM: tugas pribadi\n"
            "   - Di grup: tugas grup\n"
            "• /status me - Status pribadi\n"
            "• /status all - Semua tugas (Owner)\n\n"
            "TIPS:\n"
            "• Gunakan filter untuk melihat status\n"
            "• Batalkan tugas lambat (<20KB/s)"
        )
        await query.answer(help_text, show_alert=True)
    
    elif action in ["nex", "pre"]:
        await query.answer()
        async with task_dict_lock:
            if sid in status_dict:
                if action == "nex":
                    status_dict[sid]["page_no"] += status_dict[sid]["page_step"]
                else:
                    status_dict[sid]["page_no"] -= status_dict[sid]["page_step"]
                await update_status_message(sid, force=True)
    
    elif action == "ps":
        page_step = int(data[3])
        await query.answer(f"🔢 Step diubah menjadi {page_step}")
        async with task_dict_lock:
            if sid in status_dict:
                status_dict[sid]["page_step"] = page_step
                await update_status_message(sid, force=True)
    
    elif action == "st":
        new_status = data[3]
        cmd_user_id = int(data[4]) if len(data) > 4 else None
        
        if cmd_user_id and user_id != cmd_user_id and not is_owner:
            await query.answer("⚠️ Tombol ini hanya dapat digunakan oleh pengguna yang meminta status atau Owner!", show_alert=True)
            return
            
        status_name = next((name for label, name in STATUS_VALUES if name == new_status), new_status)
        await query.answer(f"🔍 Filter: {status_name}")
        async with task_dict_lock:
            if sid in status_dict:
                status_dict[sid]["status"] = new_status
                await update_status_message(sid, force=True)
    
    elif action == 'close':
        await query.answer(f"✅ Status ditutup! Ketik /{BotCommands.StatusCommand[0]} untuk melihat status lagi.")
        await edit_status()
    
    elif action == 'info':
        is_all = status_dict.get(sid, {}).get('is_all', False)
        is_user = status_dict.get(sid, {}).get('is_user', False)
        chat_id = status_dict.get(sid, {}).get('chat_id')
        
        view_type = "Semua Tugas (Global)" if is_all else "Tugas Pribadi" if is_user else "Tugas Grup"
        
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
                tstatus = download.status()
                if (is_all or
                    (is_user and download.listener.user_id == sid) or
                    (chat_id and download.listener.message.chat.id == chat_id)):
                    
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
            f"ℹ️ INFO STATUS\n\n"
            f"Mode: {view_type}\n"
            f"ID: {sid}\n\n"
            f"TUGAS:\n"
            f"• DL: {tasks['Download']} | UP: {tasks['Upload']} | Seed: {tasks['Seed']}\n"
            f"• Arc: {tasks['Archive']} | Ext: {tasks['Extract']}\n"
            f"• QDL: {tasks['QueueDl']} | QUP: {tasks['QueueUp']}\n\n"
            f"KECEPATAN:\n"
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