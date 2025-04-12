from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from psutil import (
    cpu_percent, 
    virtual_memory, 
    disk_usage, 
    net_io_counters
)
from time import time

from bot import (
    task_dict_lock,
    status_dict,
    task_dict,
    botStartTime,
    DOWNLOAD_DIR,
    Interval,
    bot,
    OWNER_ID,
    SUDO_USERS,
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
    edit_single_status,
)
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    StatusType,
    StatusPermission,
    get_readable_file_size,
    get_readable_time,
    speed_string_to_bytes,
)

@new_task
async def mirror_status(_, message):
    """Handle status command with different arguments"""
    async with task_dict_lock:
        count = len(task_dict)
    
    cmd_args = message.text.split()
    
    # Check if help argument is provided
    if len(cmd_args) > 1 and cmd_args[1].lower() == "help":
        help_msg = """<b>🔍 PANDUAN PENGGUNAAN STATUS</b>

<b>Perintah Dasar:</b>
<code>/{cmd}</code> : Menampilkan status tugas di chat saat ini
<code>/{cmd} me</code> : Menampilkan status tugas pribadi anda
<code>/{cmd} all</code> : Menampilkan status global semua tugas (hanya owner)
<code>/{cmd} [user_id]</code> : Menampilkan status pengguna tertentu (hanya admin)

<b>Fitur Tombol:</b>
• <b>Navigasi</b>: Gunakan tombol Prev/Next untuk berpindah halaman
• <b>Filter</b>: Filter berdasarkan jenis tugas (DL, UP, QU, dll)
• <b>Refresh</b>: Memperbarui status secara manual
• <b>Page Step</b>: Mengatur jumlah langkah saat navigasi halaman

<b>Status Tugas:</b>
• 🟢 <b>Download</b>: Unduhan sedang berlangsung
• 🔵 <b>Upload</b>: Pengunggahan sedang berlangsung
• 🟡 <b>Antrian</b>: Tugas sedang dalam antrian
• 🟠 <b>Arsip</b>: File sedang diarsipkan
• 🟣 <b>Extract</b>: Ekstraksi arsip sedang berlangsung
• ⚪ <b>Cloning</b>: Kloning file dari cloud storage
• 🟤 <b>Seeding</b>: Seeding torrent aktif

<b>Akses & Izin:</b>
• Pengguna biasa hanya dapat melihat tugas mereka sendiri
• Admin dapat melihat tugas semua pengguna
• Owner dapat melihat dan mengelola semua tugas

<b>Tips:</b>
• Gunakan opsi Overview untuk melihat ringkasan semua tugas
• Cancel tugas dengan perintah yang ditampilkan di status
• Status pribadi tidak diperbarui otomatis, gunakan tombol Refresh
""".format(cmd=BotCommands.StatusCommand[0])

        reply_message = await sendMessage(message, help_msg)
        await auto_delete_message(message, reply_message)
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
        msg = "Tidak ada Tugas Aktif!\n___________________________"
        msg += (
            f"\n<b>CPU :</b> <code>{cpu_percent()}%</code> | <b>FREE :</b> <code>{free}</code>" \
            f"\n<b>RAM :</b> <code>{virtual_memory().percent}%</code> | <b>UPTIME :</b> <code>{currentTime}</code>" \
            f"\n<b>T.Unduh :</b> <code>{sent}</code> | <b>T.Unggah :</b> <code>{recv}</code>" 
        )
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
    else:
        # Handle different status modes
        if len(cmd_args) > 1:
            arg = cmd_args[1].lower()
            if arg == "me":
                # User's own status
                await sendStatusMessage(message, message.from_user.id, is_user=True)
            elif arg == "all" and message.from_user.id == OWNER_ID:
                # Global status (owner only)
                await sendStatusMessage(message, is_all=True)
            elif arg.isdigit() and (message.from_user.id == OWNER_ID or message.from_user.id in SUDO_USERS):
                # Specific user's status (admin only)
                await sendStatusMessage(message, int(arg), is_user=True)
            else:
                # Invalid argument
                await sendStatusMessage(message)
        else:
            # Default: show chat-appropriate status
            await sendStatusMessage(message)
            
        # Clean up command message
        await deleteMessage(message)

@new_task
async def status_pages(_, query):
    data = query.data.split()
    key = int(data[1])
    cmd = data[2]
    user_id = query.from_user.id
    
    # Get status information
    async with task_dict_lock:
        if key not in status_dict:
            await query.answer("Status message no longer exists", show_alert=True)
            return
            
        status_data = status_dict[key]
        status_type = status_data.get("type", StatusType.GROUP)
        cmd_user_id = status_data.get("cmd_user_id", 0)
        status_chat_id = key
        status_owner_id = key if status_data.get("is_user", False) else 0
        
        # Check permissions for button action
        if not StatusPermission.can_use_button(user_id, cmd, status_owner_id, status_type):
            await query.answer("You don't have permission to use this button", show_alert=True)
            return
    
    # Handle different button actions
    if cmd == "ref":
        # Refresh
        await query.answer()
        await update_status_message(key, force=True)
        
    elif cmd in ["nex", "pre"]:
        # Navigation
        await query.answer()
        async with task_dict_lock:
            if cmd == "nex":
                status_dict[key]["page_no"] += status_dict[key]["page_step"]
            else:
                status_dict[key]["page_no"] -= status_dict[key]["page_step"]
        await update_status_message(key)
        
    elif cmd == "ps":
        # Change page step
        await query.answer()
        async with task_dict_lock:
            status_dict[key]["page_step"] = int(data[3])
        await update_status_message(key)
        
    elif cmd == "st":
        # Change status filter
        await query.answer()
        async with task_dict_lock:
            status_dict[key]["status"] = data[3]
        await update_status_message(key, force=True)
        
    elif cmd == 'close':
        # Close status message
        await query.answer(
            f"Anda bisa melihat status message lagi dengan perintah /{BotCommands.StatusCommand[0]}", 
            show_alert=True
        )
        await edit_single_status(key)
        
    elif cmd == 'info':
        # Show info tooltip
        await query.answer(
            "⚠️ Jika speed download anda stuck atau stabil dibawah 20Kbps, "
            "tolong dicancel dan cari link atau torrent lain, karena link itu "
            "kemungkinan sudah limit atau lagi bermasalah.",
            show_alert=True
        )
        
    elif cmd == "ov":
        # Show overview summary
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
        
        async with task_dict_lock:
            # Filter tasks based on status type
            if status_type == StatusType.PRIVATE:
                task_list = [tk for tk in task_dict.values() if tk.listener.user_id == key]
            elif status_type == StatusType.GROUP:
                task_list = [tk for tk in task_dict.values() if tk.listener.message.chat.id == key]
            else:  # Global
                task_list = list(task_dict.values())
            
            # Count tasks by status
            for download in task_list:
                tstatus = download.status()
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

        # Build overview message
        msg = f"""DL : {tasks['Download']} | UP : {tasks['Upload']} | SD : {tasks['Seed']} | AR : {tasks['Archive']}
EX : {tasks['Extract']} | SP : {tasks['Split']} | QD : {tasks['QueueDl']} | QU : {tasks['QueueUp']}
CL : {tasks['Clone']} | CH : {tasks['CheckUp']} | PA : {tasks['Pause']} | SV : {tasks['SamVid']}

Kec. Seed : {get_readable_file_size(seed_speed)}/s
Kec. Unduh : {get_readable_file_size(dl_speed)}/s
Kec. Unggah : {get_readable_file_size(up_speed)}/s

@{bot.me.username}
"""
        await query.answer(msg, show_alert=True)
        
    elif cmd == "help":
        # Show help text
        help_text = (
            "🔄 Refresh - Update status\n"
            "⏪ Prev / ⏩ Next - Navigate pages\n"
            "ALL, DL, UP, etc. - Filter by status\n"
            "Info - Show download troubleshooting\n"
            "Overview - Show task summary\n"
            "Number buttons - Change page step\n"
            "🔽 Tutup - Close status message"
        )
        await query.answer(help_text, show_alert=True)
        
    elif cmd == "cleanall" and user_id == OWNER_ID:
        # Clean all tasks (owner only)
        await query.answer("Cleaning all status messages", show_alert=True)
        await edit_status()


# Register command handlers
bot.add_handler(
    MessageHandler(
        mirror_status,
        filters=command(
            BotCommands.StatusCommand
        ) & CustomFilters.authorized
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
