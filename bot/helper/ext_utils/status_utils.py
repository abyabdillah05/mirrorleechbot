from time import time
from html import escape
from psutil import (
    cpu_percent, 
    disk_usage, 
    net_io_counters,
    virtual_memory
)

from bot import task_dict, task_dict_lock, botStartTime, config_dict, LOGGER, bot
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker


SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

class MirrorStatus:
    STATUS_DOWNLOADING = "Download.."
    STATUS_UPLOADING = "Upload.."
    STATUS_QUEUEDL = "Antrian.."
    STATUS_QUEUEUP = "Antrian.."
    STATUS_PAUSED = "Berhenti.."
    STATUS_ARCHIVING = "Arsip.."
    STATUS_EXTRACTING = "Extract.."
    STATUS_CLONING = "Cloning.."
    STATUS_SEEDING = "Seeding.."
    STATUS_SPLITTING = "Split.."
    STATUS_CHECKING = "Mengecek.."
    STATUS_SAMVID = "Sample Video"
    STATUS_DUMPING = "Dumping.."
    STATUS_VIDEDIT = "Video Editor. ."
     
STATUS_VALUES = [
    ("ALL", "All"),
    ("DL", MirrorStatus.STATUS_DOWNLOADING),
    ("UP", MirrorStatus.STATUS_UPLOADING),
    ("QD", MirrorStatus.STATUS_QUEUEDL),
    ("QU", MirrorStatus.STATUS_QUEUEUP),
    ("AR", MirrorStatus.STATUS_ARCHIVING),
    ("EX", MirrorStatus.STATUS_EXTRACTING),
    ("CL", MirrorStatus.STATUS_CLONING),
    ("SD", MirrorStatus.STATUS_SEEDING),
    ("SV", MirrorStatus.STATUS_SAMVID),
    ("DM", MirrorStatus.STATUS_DUMPING),
    ("VE", MirrorStatus.STATUS_VIDEDIT),
]

# Status emoji mapping for visual representation
STATUS_EMOJI = {
    MirrorStatus.STATUS_DOWNLOADING: "🟢",
    MirrorStatus.STATUS_UPLOADING: "🟢",
    MirrorStatus.STATUS_QUEUEDL: "🟡",
    MirrorStatus.STATUS_QUEUEUP: "🟡",
    MirrorStatus.STATUS_PAUSED: "🔴",
    MirrorStatus.STATUS_ARCHIVING: "🟣",
    MirrorStatus.STATUS_EXTRACTING: "🟣",
    MirrorStatus.STATUS_CLONING: "🟢",
    MirrorStatus.STATUS_SEEDING: "🔵",
    MirrorStatus.STATUS_SPLITTING: "🟠",
    MirrorStatus.STATUS_CHECKING: "🟡",
    MirrorStatus.STATUS_SAMVID: "🟠",
    MirrorStatus.STATUS_DUMPING: "🟠",
    MirrorStatus.STATUS_VIDEDIT: "🟠",
}

async def getTaskByGid(gid: str):
    async with task_dict_lock:
        return next((tk for tk in task_dict.values() if tk.gid() == gid), None)

async def getAllTasks(req_status: str):
    async with task_dict_lock:
        if req_status == "all":
            return list(task_dict.values())
        return [tk for tk in task_dict.values() if tk.status() == req_status]

def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes is None:
        return "0B"
    
    is_negative = size_in_bytes < 0
    size_in_bytes = abs(size_in_bytes)

    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1

    formatted_size = f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"
    return f"-{formatted_size}" if is_negative else formatted_size

def get_readable_time(seconds: int):
    periods = [("h", 86400), ("j", 3600), ("m", 60), ("d", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result or "0d"

def speed_string_to_bytes(size_text: str):
    size = 0
    size_text = size_text.lower()
    if "k" in size_text:
        size += float(size_text.split("k")[0]) * 1024
    elif "m" in size_text:
        size += float(size_text.split("m")[0]) * 1048576
    elif "g" in size_text:
        size += float(size_text.split("g")[0]) * 1073741824
    elif "t" in size_text:
        size += float(size_text.split("t")[0]) * 1099511627776
    elif "b" in size_text:
        size += float(size_text.split("b")[0])
    return size

def get_progress_bar_string(pct):
    if isinstance(pct, str):
        pct = float(pct.strip("%"))
    else:
        pct = float(pct)
        
    p = min(max(pct, 0), 100)
    cFull = int(p // 10)
    p_str = "█" * cFull
    p_str += "░" * (10 - cFull)
    return f"[{p_str}]"

def format_status_message(task, is_user=False, is_all=False):
    """Format a single task's status message with the new UI format"""
    tstatus = task.status()
    
    # Tree 1 - File Info Box
    msg = "╔═══════════════════════════╗\n"
    
    if task.listener.isPrivateChat:
        msg += f"╠[ • Nama       : Private Task\n"
    else:
        msg += f"╠[ • Nama       : {escape(task.name())}\n"
    
    view_type = "Upload" if tstatus == MirrorStatus.STATUS_UPLOADING else "Download"
    msg += f"╠[ • View Type  : {view_type}\n"
    msg += "╚═══════════════════════════╝\n\n"
    
    # Tree 2 - Status Process Box
    msg += "╔═══════════════════════════╗\n"
    
    status_emoji = STATUS_EMOJI.get(tstatus, "⚪")
    msg += f"╠[ • Status     : {status_emoji} {tstatus}\n"
    
    if tstatus not in [MirrorStatus.STATUS_DUMPING, MirrorStatus.STATUS_VIDEDIT]:
        msg += f"╠[ • Progress   : {get_progress_bar_string(task.progress())} {task.progress()}\n"
    
    time_elapsed = get_readable_time(time() - task.listener.extra_details['startTime'])
    msg += f"╠[ • Time       : {time_elapsed}\n"
    msg += f"╠[ • Size       : {task.size()}\n"
    
    if tstatus not in [
        MirrorStatus.STATUS_SPLITTING,
        MirrorStatus.STATUS_SEEDING,
        MirrorStatus.STATUS_SAMVID,
        MirrorStatus.STATUS_DUMPING,
        MirrorStatus.STATUS_VIDEDIT,
    ]:
        msg += f"╠[ • Diproses   : {task.processed_bytes()}\n"
        msg += f"╠[ • Estimasi   : {task.eta()}\n"
        msg += f"╠[ • Kecepatan  : {task.speed()}\n"
    
    if tstatus == MirrorStatus.STATUS_SEEDING:
        msg += f"╠[ • Ratio      : {task.ratio()}\n"
        msg += f"╠[ • Waktu      : {task.seeding_time()}\n"
        if not is_user:
            msg += f"╠[ • Diupload   : {task.uploaded_bytes()}\n"
        msg += f"╠[ • Kecepatan  : {task.seed_speed()}\n"
        
    if hasattr(task, "seeders_num") and tstatus in [MirrorStatus.STATUS_DOWNLOADING]:
        try:
            msg += f"╠[ • Seeders    : {task.seeders_num()}\n"
            msg += f"╠[ • Leechers   : {task.leechers_num()}\n"
        except:
            pass
    
    # Set engine information
    engine = ""
    ddl = task.listener
    if hasattr(ddl, 'isGofile') and ddl.isGofile:
        engine = "GofileAPI"
    elif hasattr(ddl, 'isBuzzheavier') and ddl.isBuzzheavier:
        engine = "BuzzheavierAPI"
    elif hasattr(ddl, 'isPixeldrain') and ddl.isPixeldrain:
        engine = "PixeldrainAPI"
    else:
        engine = f"{getattr(task, 'engine', 'Unknown')}"
        
    msg += f"╠[ • Engine     : {engine}\n"
    msg += f"╠[ • Cancel     : /{BotCommands.CancelTaskCommand[0]}_{task.gid()}\n"
    msg += "╚═══════════════════════════╝\n"
    
    return msg

def build_user_context_info(user_id, username=None, first_name=None, type_status="Private"):
    """Build the user context information box"""
    msg = "╔═════ Info Status ═════╗\n"
    msg += f"╠[ • Tipe     : {type_status}\n"
    
    if type_status == "Private":
        nickname = first_name or "User"
        msg += f"╠[ • Nickname : {nickname}\n"
        msg += f"╠[ • ID       : {user_id}\n"
        
        if username:
            msg += f"╠[ • Username : @{username}\n"
        else:
            msg += f"╠[ • Username : (User)[tg{user_id}]\n"
    else:
        # For group context
        group_name = first_name or "Group"
        msg += f"╠[ • Grup     : {group_name}\n"
        msg += f"╠[ • ID       : {user_id}\n"
        
        if username:
            msg += f"╠[ • Username : @{username}\n"
        else:
            msg += f"╠[ • Username : (Group)[tg{user_id}]\n"
            
    msg += "╚═══════════════════════════╝\n"
    return msg

def get_system_info():
    """Get system information in the specified format"""
    free_space = get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)
    uptime = get_readable_time(time() - botStartTime)
    
    ram_used = get_readable_file_size(virtual_memory().used)
    ram_total = get_readable_file_size(virtual_memory().total)
    
    msg = f"💻 Sistem: CPU: {cpu_percent()}% | RAM: {ram_used} / {ram_total}\n"
    msg += f"📦 Free: {free_space} | Uptime: {uptime}\n"
    
    return msg

def get_readable_message(sid, is_user=False, page_no=1, status_filter="All", page_step=1, chat_id=None, is_all=False, cmd_user_id=None):
    """Get readable status message with the new UI format"""
    msg = ""
    button = None

    # Determine the status type and filter tasks accordingly
    if is_all:
        # Get all tasks for owners, sorted by private first then group
        private_tasks = []
        group_tasks = []
        
        for task in task_dict.values():
            if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'chat') and task.listener.message.chat.id < 0:
                group_tasks.append(task)
            else:
                private_tasks.append(task)
        
        # Combine tasks with private first
        tasks = private_tasks + group_tasks
        header_msg = "<b>STATUS GLOBAL</b>\n\n"
        type_status = "Global"
    elif is_user:
        # Get user's tasks
        tasks = [tk for tk in task_dict.values() if tk.listener.user_id == sid]
        header_msg = "<b>STATUS PRIBADI</b>\n\n"
        type_status = "Private"
    elif chat_id and chat_id < 0:
        # Get group's tasks
        tasks = [tk for tk in task_dict.values() if hasattr(tk.listener, 'message') and 
                hasattr(tk.listener.message, 'chat') and tk.listener.message.chat.id == chat_id]
        header_msg = "<b>STATUS GRUP</b>\n\n"
        type_status = "Group"
    else:
        LOGGER.warning(f"Invalid status context: sid={sid}, is_user={is_user}, chat_id={chat_id}")
        return None, None
    
    # Apply status filter if needed
    if status_filter != "All":
        tasks = [tk for tk in tasks if tk.status() == status_filter]
        header_msg = f"<b>STATUS {type_status.upper()} ({status_filter})</b>\n\n"
    
    msg += header_msg
    msg += "─────────────────────────────\n\n"

    # Pagination setup
    STATUS_LIMIT = config_dict["STATUS_LIMIT"]
    tasks_no = len(tasks)
    pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
    
    if page_no > pages:
        page_no = (page_no - 1) % pages + 1
    elif page_no < 1:
        page_no = pages - (abs(page_no) % pages)
        
    start_position = (page_no - 1) * STATUS_LIMIT
    
    # Format each task in the current page
    for index, task in enumerate(tasks[start_position : STATUS_LIMIT + start_position], start=1):
        msg += format_status_message(task, is_user, is_all)
        msg += "\n"
    
    # Add context information based on status type
    if is_user:
        # Find user info from task for Private
        user_info = None
        for task in tasks:
            if hasattr(task.listener, 'user'):
                user = task.listener.user
                user_info = build_user_context_info(
                    user.id, 
                    user.username, 
                    user.first_name, 
                    "Private"
                )
                break
                
        # If no tasks or no user info found
        if not user_info:
            # Try to get user info directly if possible
            try:
                user = bot.get_users(sid)
                user_info = build_user_context_info(
                    sid,
                    user.username,
                    user.first_name,
                    "Private"
                )
            except:
                user_info = build_user_context_info(sid, None, None, "Private")
                
        msg += user_info
        
    elif chat_id and chat_id < 0:
        # Find group info from task for Group
        group_info = None
        for task in tasks:
            if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'chat'):
                chat = task.listener.message.chat
                group_info = build_user_context_info(
                    chat.id,
                    chat.username,
                    chat.title,
                    "Group"
                )
                break
                
        # If no tasks or no group info found
        if not group_info:
            # Try to get group info directly if possible
            try:
                chat = bot.get_chat(chat_id)
                group_info = build_user_context_info(
                    chat_id,
                    chat.username,
                    chat.title,
                    "Group"
                )
            except:
                group_info = build_user_context_info(chat_id, None, None, "Group")
                
        msg += group_info
    
    # No tasks message
    if len(msg) == 0 or tasks_no == 0:
        if is_user:
            context_type = "pribadi Anda"
        elif chat_id:
            context_type = "grup ini"
        else:
            context_type = "global"
            
        if status_filter == "All":
            msg = f"{header_msg}<b>Tidak ada tugas aktif untuk tampilan {context_type}!</b>\n\n"
        else:
            msg = f"{header_msg}<b>Tidak ada tugas {status_filter} untuk tampilan {context_type}!</b>\n\n"
        
        msg += "─────────────────────────────\n\n"

    # Add system information
    msg += get_system_info()
    
    # Add pagination info if needed
    if tasks_no > STATUS_LIMIT:
        msg += f"\nHalaman: {page_no}/{pages} | Step: {page_step} | Total: {tasks_no}\n"
    
    # Add footer
    msg += f"\n⚙️ Powered by: @{bot.me.username or 'TCFBot'}"
    
    # Build buttons
    buttons = ButtonMaker()
    
    if tasks_no > STATUS_LIMIT:
        buttons.ibutton("◀️ Prev", f"status {sid} pre {cmd_user_id}", position="header")
        buttons.ibutton("🔄 Refresh", f"status {sid} ref {cmd_user_id}", position="header")
        buttons.ibutton("Next ▶️", f"status {sid} nex {cmd_user_id}", position="header")
    else:
        buttons.ibutton("🔄 Refresh", f"status {sid} ref {cmd_user_id}", position="header")
    
    buttons.ubutton("Join", "https://t.me/DizzyStuffProject")
    buttons.ibutton("Help", f"status {sid} help {cmd_user_id}")
    buttons.ibutton("Info", f"status {sid} info {cmd_user_id}")
    
    buttons.ibutton("Tutup", f"status {sid} close {cmd_user_id}", position="footer")
    
    # Add status filter buttons
    if status_filter != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status_filter:
                buttons.ibutton(label, f"status {sid} st {status_value} {cmd_user_id}")
    
    # Add page step buttons if needed
    if tasks_no > STATUS_LIMIT and tasks_no > 30:
        for i in [1, 2, 4, 6, 8, 10, 15, 20]:
            buttons.ibutton(i, f"status {sid} ps {i} {cmd_user_id}", position="footer")
    
    button = buttons.build_menu(3)
    return msg, button