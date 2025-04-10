from time import time
from html import escape
from psutil import (
    cpu_percent, 
    disk_usage, 
    net_io_counters,
    virtual_memory
)

from bot import task_dict, task_dict_lock, botStartTime, config_dict, LOGGER
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
    return result


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
    pct = float(pct.strip("%"))
    p = min(max(pct, 0), 100)
    cFull = int(p // 8)
    p_str = "■" * cFull
    p_str += "□" * (12 - cFull)
    return f"[{p_str}]"


def get_readable_message(sid, is_user=False, page_no=1, status="All", page_step=1, chat_id=None, is_all=False, cmd_user_id=None):
    msg = ""
    button = None

    # Filter tasks based on context
    if is_all:
        # Get all tasks for owners
        tasks = list(task_dict.values())
        header_msg = "<b>STATUS GLOBAL</b>\n\n"
        view_type = "Global"
    elif is_user or (sid > 0 and not chat_id):
        # Get user's tasks
        tasks = [tk for tk in task_dict.values() if tk.listener.user_id == sid]
        header_msg = "<b>STATUS PRIBADI</b>\n\n"
        view_type = "Private"
    elif chat_id and chat_id < 0:
        # Get group's tasks
        tasks = [tk for tk in task_dict.values() if hasattr(tk.listener, 'message') and 
                hasattr(tk.listener.message, 'chat') and tk.listener.message.chat.id == chat_id]
        header_msg = "<b>STATUS GRUP</b>\n\n"
        view_type = "Group"
    else:
        LOGGER.warning(f"Invalid status context: sid={sid}, is_user={is_user}, chat_id={chat_id}")
        return None, None
    
    # Apply status filter if needed
    if status != "All":
        if is_user:
            tasks = [
                tk for tk in tasks
                if tk.status() == status
            ]
            header_msg = f"<b>STATUS PRIBADI ({status})</b>\n\n"
        elif chat_id:
            tasks = [
                tk for tk in tasks
                if tk.status() == status
            ]
            header_msg = f"<b>STATUS GRUP ({status})</b>\n\n"
        elif is_all:
            tasks = [tk for tk in tasks if tk.status() == status]
            header_msg = f"<b>STATUS GLOBAL ({status})</b>\n\n"
    
    msg += header_msg

    STATUS_LIMIT = config_dict["STATUS_LIMIT"]
    tasks_no = len(tasks)
    pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
    
    if page_no > pages:
        page_no = (page_no - 1) % pages + 1
    elif page_no < 1:
        page_no = pages - (abs(page_no) % pages)
        
    start_position = (page_no - 1) * STATUS_LIMIT

    for index, task in enumerate(
        tasks[start_position : STATUS_LIMIT + start_position], start=1
    ):
        tstatus = task.status()
        
        if is_user:
            if task.listener.isPrivateChat: 
                msg += f"<blockquote><b>Nama:</b> <code>Private Task</code></b></blockquote>"
            else:
                msg += f"<blockquote><b>Nama:</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
            
            if tstatus not in [MirrorStatus.STATUS_DUMPING, MirrorStatus.STATUS_VIDEDIT]:
                msg += f"\n<b>Status:</b> <code>{tstatus}</code> <code>({task.progress()})</code>"
                msg += f"\n{get_progress_bar_string(task.progress())}"
            else:
                msg += f"\n<b>Status:</b> <code>{tstatus}</code>"
                
            msg += f"\n<b>Waktu:</b> <code>{get_readable_time(time() - task.listener.extra_details['startTime'])}</code>"
            msg += f"\n<b>Ukuran:</b> {task.size()}"
            
            if tstatus not in [
                MirrorStatus.STATUS_SPLITTING,
                MirrorStatus.STATUS_SEEDING,
                MirrorStatus.STATUS_SAMVID,
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                msg += f"\n<b>Diproses:</b> <code>{task.processed_bytes()}</code>"
                msg += f"\n<b>Estimasi:</b> <code>{task.eta()}</code>"
                msg += f"\n<b>Kecepatan:</b> <code>{task.speed()}</code>"
            
        elif chat_id or is_all:
            task_type_label = "Group" if hasattr(task.listener.message, 'chat') and task.listener.message.chat.id < 0 else "Private"
            
            if is_all:
                msg += f"<blockquote><b>Type:</b> <code>{task_type_label}</code></blockquote>"
                
            if task.listener.isPrivateChat: 
                msg += f"<blockquote><b>Nama:</b> <code>Private Task</code></b></blockquote>"
            else: 
                msg += f"<blockquote><b>Nama:</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
                
            if tstatus not in [
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'link'):
                    msg += f"\n<b>Status:</b> <a href='{task.listener.message.link}'>{tstatus}</a> <code>({task.progress()})</code>"
                else:
                    msg += f"\n<b>Status:</b> <code>{tstatus}</code> <code>({task.progress()})</code>"
                msg += f"\n{get_progress_bar_string(task.progress())}"
            else:
                if hasattr(task.listener, 'message') and hasattr(task.listener.message, 'link'):
                    msg += f"\n<b>Status:</b> <a href='{task.listener.message.link}'>{tstatus}</a>"
                else:
                    msg += f"\n<b>Status:</b> <code>{tstatus}</code>"
                
            # Show user details only for group status or global status
            msg += f"\n<b>User:</b> <code>@{task.listener.user.username or task.listener.user.first_name}</code>"
            msg += f"\n<b>ID:</b> <code>{task.listener.user.id}</code>"
            
            msg += f"\n<b>Waktu:</b> <code>{get_readable_time(time() - task.listener.extra_details['startTime'])}</code>"
            msg += f"\n<b>Ukuran:</b> {task.size()}"
            
            if tstatus not in [
                MirrorStatus.STATUS_SPLITTING,
                MirrorStatus.STATUS_SEEDING,
                MirrorStatus.STATUS_SAMVID,
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                msg += f"\n<b>Diproses:</b> <code>{task.processed_bytes()}</code>"
                msg += f"\n<b>Estimasi:</b> <code>{task.eta()}</code>"
                msg += f"\n<b>Kecepatan:</b> <code>{task.speed()}</code>"
                
                if hasattr(task, "seeders_num"):
                    try:
                        msg += f"\n<b>Seeders:</b> <code>{task.seeders_num()}</code>"
                        msg += f"\n<b>Leechers:</b> <code>{task.leechers_num()}</code>"
                    except:
                        pass
                        
        if tstatus == MirrorStatus.STATUS_SEEDING:
            msg += f"\n<b>Ratio:</b> <code>{task.ratio()}</code>"
            msg += f"\n<b>Waktu:</b> <code>{task.seeding_time()}</code>"
            if not is_user:
                msg += f"\n<b>Ukuran:</b> <code>{task.size()}</code>"
                msg += f"\n<b>Diupload:</b> <code>{task.uploaded_bytes()}</code>"
            msg += f"\n<b>Kecepatan:</b> <code>{task.seed_speed()}</code>"
        
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
        msg += f"\n<b>Engine:</b> <code>{engine}</code>"
        msg += f"\n<b>Cancel:</b> <code>/{BotCommands.CancelTaskCommand[0]}_{task.gid()}</code>\n\n"

    if len(msg) == 0 or tasks_no == 0:
        if is_user:
            context_type = "pribadi Anda"
        elif chat_id:
            context_type = "grup ini"
        else:
            context_type = "global"
            
        if status == "All":
            msg = f"{header_msg}<b>Tidak ada tugas aktif untuk tampilan {context_type}!</b>\n\n"
        else:
            msg = f"{header_msg}<b>Tidak ada tugas {status} untuk tampilan {context_type}!</b>\n\n"
    
    buttons = ButtonMaker()
    
    if len(tasks) > STATUS_LIMIT:
        buttons.ibutton("◀️ Prev", f"status {sid} pre {cmd_user_id}", position="header")
        buttons.ibutton("🔄 Refresh", f"status {sid} ref {cmd_user_id}", position="header")
        buttons.ibutton("Next ▶️", f"status {sid} nex {cmd_user_id}", position="header")
    else:
        buttons.ibutton("🔄 Refresh", f"status {sid} ref {cmd_user_id}", position="header")
    
    buttons.ubutton("Join", "https://t.me/DizzyStuffProject")
    buttons.ibutton("Help", f"status {sid} help {cmd_user_id}")
    buttons.ibutton("Info", f"status {sid} info {cmd_user_id}")
    
    buttons.ibutton("Close", f"status {sid} close {cmd_user_id}", position="footer")
    
    # Add status filter buttons
    if status != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status:
                buttons.ibutton(label, f"status {sid} st {status_value} {cmd_user_id}")
    
    if len(tasks) > STATUS_LIMIT:
        msg += f"<b>Step:</b> <code>{page_step}</code>"
        msg += f"\n<b>Page:</b> <code>{page_no}/{pages}</code>"
        msg += f"\n<b>Total Tasks:</b> <code>{tasks_no}</code>\n\n"
        
        if tasks_no > 30:
            for i in [1, 2, 4, 6, 8, 10, 15, 20]:
                buttons.ibutton(i, f"status {sid} ps {i} {cmd_user_id}", position="footer")
    
    button = buttons.build_menu(3)
    
    msg += f"<b>━━━━━━━━━━━━━━━━━━</b>"
    msg += f"\n<b>Type:</b> <code>{view_type}</code>"
    
    if chat_id and chat_id < 0:
        msg += f"\n<b>Group ID:</b> <code>{chat_id}</code>"
    
    msg += f"\n<b>CPU:</b> <code>{cpu_percent()}%</code> | <b>RAM:</b> <code>{virtual_memory().percent}%</code>"
    msg += f"\n<b>FREE:</b> <code>{get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}</code> | <b>UPTIME:</b> <code>{get_readable_time(time() - botStartTime)}</code>"
    
    return msg, button