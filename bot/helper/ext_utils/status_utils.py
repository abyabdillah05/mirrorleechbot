from time import time
from html import escape
from psutil import (
    cpu_percent, 
    disk_usage, 
    net_io_counters,
    virtual_memory
)

from bot.helper.ext_utils.common_utils import (get_readable_file_size,
                                             get_readable_time)
from bot import task_dict, task_dict_lock, botStartTime, config_dict, LOGGER, bot
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.__main__ import botname

bn = botname

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
    tstatus = task.status()
    
    msg = "╔═══════════════════════════╗\n"
    
    if task.listener.isPrivateChat:
        msg += f"╠[ • Nama  : {escape(task.name())}\n"
    else:
        msg += f"╠[ • Nama  : {escape(task.name())}\n"
    
    view_type = "Upload" if tstatus == MirrorStatus.STATUS_UPLOADING else "Download"
    msg += f"╠[ • View Type  : {view_type}\n"
    msg += "╚═══════════════════════════╝\n"
    
    msg += "╔═══════════════════════════╗\n"
    
    status_emoji = STATUS_EMOJI.get(tstatus, "⚪")
    msg += f"╠[ • Status    : {status_emoji} {tstatus}\n"
    
    if tstatus not in [MirrorStatus.STATUS_DUMPING, MirrorStatus.STATUS_VIDEDIT]:
        msg += f"╠[ • Progress  : {get_progress_bar_string(task.progress())} {task.progress()}\n"
    
    time_elapsed = get_readable_time(time() - task.listener.extra_details['startTime'])
    msg += f"╠[ • Time  : {time_elapsed}\n"
    msg += f"╠[ • Size  : {task.size()}\n"
    
    if tstatus not in [
        MirrorStatus.STATUS_SPLITTING,
        MirrorStatus.STATUS_SEEDING,
        MirrorStatus.STATUS_SAMVID,
        MirrorStatus.STATUS_DUMPING,
        MirrorStatus.STATUS_VIDEDIT,
    ]:
        msg += f"╠[ • Diproses  : {task.processed_bytes()}\n"
        msg += f"╠[ • Estimasi  : {task.eta()}\n"
        msg += f"╠[ • Kecepatan : {task.speed()}\n"
    
    if tstatus == MirrorStatus.STATUS_SEEDING:
        msg += f"╠[ • Ratio : {task.ratio()}\n"
        msg += f"╠[ • Waktu : {task.seeding_time()}\n"
        if not is_user:
            msg += f"╠[ • Diupload  : {task.uploaded_bytes()}\n"
        msg += f"╠[ • Kecepatan : {task.seed_speed()}\n"
        
    if hasattr(task, "seeders_num") and tstatus in [MirrorStatus.STATUS_DOWNLOADING]:
        try:
            msg += f"╠[ • Seeders   : {task.seeders_num()}\n"
            msg += f"╠[ • Leechers  : {task.leechers_num()}\n"
        except:
            pass
    
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
        
    msg += f"╠[ • Engine    : {engine}\n"
    msg += f"╠[ • Cancel    : /{BotCommands.CancelTaskCommand[0]}_{task.gid()}\n"
    msg += "╚═══════════════════════════╝\n"
    
    return msg

def build_user_context_info(user_id, username=None, first_name=None, type_status="Private", chat_title=None, is_private_chat=False):
    msg = "╔═════ Info Status ═════╗\n"
    msg += f"╠[ • Tipe     : {type_status}\n"
    
    if type_status == "Private":
        nickname = first_name or "User"
        msg += f"╠[ • Nickname  : {nickname}\n"
        msg += f"╠[ • ID    : {user_id}\n"
        
        if username:
            msg += f"╠[ • Username  : @{username}\n"
        else:
            msg += f"╠[ • Username  : <a href='tg://user?id={user_id}'>User</a>\n"
    else:
        group_name = chat_title or "Group"
        msg += f"╠[ • Grup     : {group_name}\n"
        msg += f"╠[ • ID       : {user_id}\n"
        
        if username:
            msg += f"╠[ • Username  : @{username}\n"
        else:
            if is_private_chat:
                msg += f"╠[ • Username  : Private Group\n"
            else:
                msg += f"╠[ • Username  : <a href='tg://join?invite=Group_{abs(user_id)}'>{group_name}</a>\n"
            
    msg += "╚═══════════════════════════╝\n"
    return msg

def get_system_info():
    free_space = get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)
    uptime = get_readable_time(time() - botStartTime)
    
    ram_used = get_readable_file_size(virtual_memory().used)
    ram_total = get_readable_file_size(virtual_memory().total)
    
    msg = f"Sistem Stats:\n"
    msg += f"CPU: {cpu_percent()}% | RAM: {ram_used} / {ram_total}\n"
    msg += f"FREE: {free_space} | UPT: {uptime}\n"
    
    return msg

def get_readable_message(sid, is_user=False, page_no=1, status_filter="All", page_step=1, chat_id=None, is_all=False, cmd_user_id=None):
    msg = ""
    button = None

    if is_all:
        private_tasks = []
        group_tasks = []
        
        for task in task_dict.values():
            if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'chat') and task.listener.message.chat.id < 0:
                group_tasks.append(task)
            else:
                private_tasks.append(task)
        
        tasks = private_tasks + group_tasks
        header_msg = "<b>Status Global</b>\n\n"
        type_status = "Global"
    elif is_user:
        tasks = [tk for tk in task_dict.values() if hasattr(tk.listener, 'user_id') and tk.listener.user_id == sid]
        header_msg = "<b>Status Pribadi</b>\n\n"
        type_status = "Private"
    elif chat_id and chat_id < 0:
        tasks = [tk for tk in task_dict.values() if hasattr(tk.listener, 'message') and 
                hasattr(tk.listener.message, 'chat') and tk.listener.message.chat.id == chat_id]
        header_msg = "<b>Status Group</b>\n\n"
        type_status = "Group"
    else:
        LOGGER.warning(f"Invalid status context: sid={sid}, is_user={is_user}, chat_id={chat_id}")
        return None, None
    
    if status_filter != "All":
        tasks = [tk for tk in tasks if tk.status() == status_filter]
        header_msg = f"<b>STATUS {type_status.upper()} ({status_filter})</b>\n"
    
    msg += header_msg
    msg += "─────────────────────────────\n\n"

    STATUS_LIMIT = config_dict["STATUS_LIMIT"]
    tasks_no = len(tasks)
    pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
    
    if page_no > pages:
        page_no = (page_no - 1) % pages + 1
    elif page_no < 1:
        page_no = pages - (abs(page_no) % pages)
        
    start_position = (page_no - 1) * STATUS_LIMIT
    
    displayed_tasks = tasks[start_position : start_position + STATUS_LIMIT]
    for index, task in enumerate(displayed_tasks, start=1):
        msg += format_status_message(task, is_user, is_all)
        msg += "\n"
    
    if is_all:
        if cmd_user_id:
            try:
                user = bot.get_users(cmd_user_id)
                user_info = build_user_context_info(
                    cmd_user_id,
                    user.username,
                    user.first_name,
                    "Global Request"
                )
                msg += user_info
            except:
                pass
    elif is_user:
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
                
        if not user_info:
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
        group_info = None
        is_private_group = False
        
        for task in tasks:
            if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'chat'):
                chat = task.listener.message.chat
                is_private_group = chat.type == "private" or not chat.username
                group_info = build_user_context_info(
                    chat.id,
                    chat.username,
                    chat.title,
                    "Group",
                    None,
                    is_private_group
                )
                break
                
        if not group_info:
            try:
                chat = bot.get_chat(chat_id)
                is_private_group = chat.type == "private" or not chat.username
                group_info = build_user_context_info(
                    chat_id,
                    chat.username,
                    chat.title,
                    None,
                    is_private_group
                )
            except:
                group_info = build_user_context_info(chat_id, None, None, None, True)
                
        msg += group_info
    
    if len(msg) == 0 or tasks_no == 0:
        if is_user:
            context_type = "Status Private"
        elif chat_id:
            context_type = "Status Group"
        else:
            context_type = "Status Global"
            
        if status_filter == "All":
            msg = f"{header_msg}<b>Tidak ada tugas aktif untuk tampilan {context_type}!</b>\n"
        else:
            msg = f"{header_msg}<b>Tidak ada tugas {status_filter} untuk tampilan {context_type}!</b>\n"
        
        msg += "─────────────────────────────\n"
        
        if is_user:
            try:
                user = bot.get_users(sid)
                user_info = build_user_context_info(
                    sid,
                    user.username,
                    user.first_name,
                    "Private"
                )
                msg += user_info
            except:
                user_info = build_user_context_info(sid, None, None, "Private")
                msg += user_info
        elif chat_id and chat_id < 0:
            try:
                chat = bot.get_chat(chat_id)
                is_private_group = chat.type == "private" or not chat.username
                group_info = build_user_context_info(
                    chat_id,
                    chat.username,
                    chat.title,
                    "Group",
                    None,
                    is_private_group
                )
                msg += group_info
            except:
                group_info = build_user_context_info(chat_id, None, None, "Group", None, True)
                msg += group_info
        elif is_all and cmd_user_id:
            try:
                user = bot.get_users(cmd_user_id)
                user_info = build_user_context_info(
                    cmd_user_id,
                    user.username,
                    user.first_name,
                    "Global Request"
                )
                msg += user_info
            except:
                pass

    msg += get_system_info()
    
    if tasks_no > STATUS_LIMIT:
        msg += f"Halaman: {page_no}/{pages} | Step: {page_step} | Total: {tasks_no}\n"
    
    msg += f"Powered by: {bn}"
    
    if is_all:
        sid_str = "global_status"
    elif is_user:
        sid_str = f"user_{sid}"
    elif chat_id:
        sid_str = f"group_{chat_id}"
    else:
        sid_str = str(sid)
    
    buttons = ButtonMaker()
    
    if tasks_no > STATUS_LIMIT:
        buttons.ibutton("◀️ Prev", f"status {sid_str} pre {cmd_user_id}", position="header")
        buttons.ibutton("🔄 Refresh", f"status {sid_str} ref {cmd_user_id}", position="header")
        buttons.ibutton("Next ▶️", f"status {sid_str} nex {cmd_user_id}", position="header")
    else:
        buttons.ibutton("🔄 Refresh", f"status {sid_str} ref {cmd_user_id}", position="header")
    
    buttons.ibutton("Help", f"status {sid_str} help {cmd_user_id}")
    buttons.ubutton("Join", "https://t.me/DizzyStuffProject")
    buttons.ibutton("Info", f"status {sid_str} info {cmd_user_id}")
    
    buttons.ibutton("Tutup", f"status {sid_str} close {cmd_user_id}", position="footer")
    
    if status_filter != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status_filter:
                buttons.ibutton(label, f"status {sid_str} st {status_value} {cmd_user_id}")
    
    if tasks_no > STATUS_LIMIT and tasks_no > 30:
        for i in [1, 2, 4, 6, 8, 10, 15, 20]:
            buttons.ibutton(i, f"status {sid_str} ps {i} {cmd_user_id}")
    
    button = buttons.build_menu(3)
    return msg, button