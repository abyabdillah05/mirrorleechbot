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

def get_readable_message(sid, is_user, page_no=1, status="All", page_step=1, chat_id=None, is_all=False, cmd_user_id=None):
    msg = ""
    button = None

    if is_all:
        tasks = list(task_dict.values())
        header_msg = "<b>🌐 STATUS SEMUA TUGAS (GLOBAL)</b>\n\n"
    elif is_user or (sid > 0 and not chat_id):
        tasks = [tk for tk in task_dict.values() if tk.listener.user_id == sid]
        header_msg = "<b>🔹 STATUS TUGAS PRIBADI ANDA</b>\n\n"
    elif chat_id and chat_id < 0:
        tasks = [tk for tk in task_dict.values() if hasattr(tk.listener, 'message') and 
                hasattr(tk.listener.message, 'chat') and tk.listener.message.chat.id == chat_id]
        header_msg = "<b>📊 STATUS TUGAS GRUP INI</b>\n\n"
    else:
        LOGGER.warning(f"Invalid status context: sid={sid}, is_user={is_user}, chat_id={chat_id}")
        return None, None
    
    if status != "All":
        if is_user:
            tasks = [
                tk for tk in tasks
                if tk.status() == status
            ]
            header_msg = f"<b>🔹 STATUS TUGAS PRIBADI ({status})</b>\n\n"
        elif chat_id:
            tasks = [
                tk for tk in tasks
                if tk.status() == status
            ]
            header_msg = f"<b>📊 STATUS TUGAS GRUP ({status})</b>\n\n"
        elif is_all:
            tasks = [tk for tk in tasks if tk.status() == status]
            header_msg = f"<b>🌐 STATUS SEMUA TUGAS ({status})</b>\n\n"
    
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
                msg += f"<blockquote><b>🔐 Nama :</b> <code>Private Task</code></b></blockquote>"
            else:
                msg += f"<blockquote>📄 <b>Nama :</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
            
            if tstatus not in [MirrorStatus.STATUS_DUMPING, MirrorStatus.STATUS_VIDEDIT]:
                msg += f"\n<b>┌ Status :</b> <code>{tstatus}</code> <code>({task.progress()})</code>"
                msg += f"\n<b>├ </b>{get_progress_bar_string(task.progress())}"
            else:
                msg += f"\n<b>┌ Status :</b> <code>{tstatus}</code>"
                
            msg += f"\n<b>├ Waktu :</b> <code>{get_readable_time(time() - task.listener.extra_details['startTime'])}</code>"
            msg += f"\n<b>├ Ukuran :</b> {task.size()}"
            
            if tstatus not in [
                MirrorStatus.STATUS_SPLITTING,
                MirrorStatus.STATUS_SEEDING,
                MirrorStatus.STATUS_SAMVID,
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                msg += f"\n<b>├ Diproses :</b> <code>{task.processed_bytes()}</code>"
                msg += f"\n<b>├ Estimasi :</b> <code>{task.eta()}</code>"
                msg += f"\n<b>├ Kecepatan :</b> <code>{task.speed()}</code>"
            
        elif chat_id or is_all:
            if task.listener.isPrivateChat: 
                msg += f"<blockquote><b>🔐 Nama :</b> <code>Private Task</code></b></blockquote>"
            else: 
                msg += f"<blockquote>📄 <b>Nama :</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
                
            if tstatus not in [
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                msg += f"\n<b>┌ Status : <a href='{task.listener.message.link}'>{tstatus}</a></b> <code>({task.progress()})</code>"
                msg += f"\n<b>├ </b>{get_progress_bar_string(task.progress())}"
            else:
                msg += f"\n<b>┌ Status : <a href='{task.listener.message.link}'>{tstatus}</a></b>"
                
            user_mention = f'<a href="tg://user?id={task.listener.user.id}">{task.listener.user.first_name}</a>'
            msg += f"\n<b>├ Oleh :</b> <code>@{task.listener.user.username or task.listener.user.first_name}</code>"
            msg += f"\n<b>├ UserID :</b> [<code>{task.listener.user.id}</code>]"
            
            msg += f"\n<b>├ Waktu :</b> <code>{get_readable_time(time() - task.listener.extra_details['startTime'])}</code>"
            msg += f"\n<b>├ Ukuran :</b> {task.size()}"
            
            if tstatus not in [
                MirrorStatus.STATUS_SPLITTING,
                MirrorStatus.STATUS_SEEDING,
                MirrorStatus.STATUS_SAMVID,
                MirrorStatus.STATUS_DUMPING,
                MirrorStatus.STATUS_VIDEDIT,
            ]:
                msg += f"\n<b>├ Diproses :</b> <code>{task.processed_bytes()}</code>"
                msg += f"\n<b>├ Estimasi :</b> <code>{task.eta()}</code>"
                msg += f"\n<b>├ Kecepatan :</b> <code>{task.speed()}</code>"
                
                if hasattr(task, "seeders_num"):
                    try:
                        msg += f"\n<b>├ Seeders :</b> <code>{task.seeders_num()}</code>"
                        msg += f"\n<b>├ Leechers :</b> <code>{task.leechers_num()}</code>"
                    except:
                        pass
                        
        if tstatus == MirrorStatus.STATUS_SEEDING:
            msg += f"\n<b>├ Ratio :</b> <code>{task.ratio()}</code>"
            msg += f"\n<b>├ Waktu :</b> <code>{task.seeding_time()}</code>"
            if not is_user:
                msg += f"\n<b>├ Ukuran :</b> <code>{task.size()}</code>"
                msg += f"\n<b>├ Diupload :</b> <code>{task.uploaded_bytes()}</code>"
            msg += f"\n<b>├ Kecepatan :</b> <code>{task.seed_speed()}</code>"
        
        engine = ""
        ddl = task.listener
        if ddl.isGofile:
            engine = "GofileAPI"
        elif ddl.isBuzzheavier:
            engine = "BuzzheavierAPI"
        elif ddl.isPixeldrain:
            engine = "PixeldrainAPI"
        else:
            engine = f"{task.engine}"
        msg += f"\n<b>├ Engine :</b> <code>{engine}</code>"
        msg += f"\n<b>└⛔️ /{BotCommands.CancelTaskCommand[0]}_{task.gid()}</b>\n\n"

    if len(msg) == 0 or tasks_no == 0:
        if is_user:
            view_type = "pribadi Anda"
        elif chat_id:
            view_type = "grup ini"
        else:
            view_type = "global"
            
        if status == "All":
            msg = f"{header_msg}<b>📭 Tidak ada tugas aktif untuk tampilan {view_type}!</b>\n\n"
        else:
            msg = f"{header_msg}<b>📭 Tidak ada tugas {status} untuk tampilan {view_type}!</b>\n\n"
    
    buttons = ButtonMaker()
    
    if len(tasks) > STATUS_LIMIT:
        buttons.ibutton("◀️ 𝙿𝚛𝚎𝚟", f"status {sid} pre {cmd_user_id}", position="header")
        buttons.ibutton("🔄 𝚁𝚎𝚏𝚛𝚎𝚜𝚑", f"status {sid} ref {cmd_user_id}", position="header")
        buttons.ibutton("𝙽𝚎𝚡𝚝 ▶️", f"status {sid} nex {cmd_user_id}", position="header")
    else:
        buttons.ibutton("🔄 Refresh", f"status {sid} ref {cmd_user_id}", position="header")
    
    buttons.ubutton("✨ 𝚓𝚘𝚒𝚗", "https://t.me/DizzyStuffProject")
    buttons.ibutton("❓ Help", f"status {sid} help {cmd_user_id}")
    buttons.ibutton("ℹ️ 𝙸𝚗𝚏𝚘", f"status {sid} info {cmd_user_id}")
    
    buttons.ibutton("🔽 𝚃𝚞𝚝𝚞𝚙", f"status {sid} close {cmd_user_id}", position="footer")
    
    if status != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status:
                buttons.ibutton(label, f"status {sid} st {status_value} {cmd_user_id}")
    
    if len(tasks) > STATUS_LIMIT:
        msg += f"<b>Step :</b> <code>{page_step}</code>"
        msg += f"\n<b>Halaman :</b> <code>{page_no}/{pages}</code>"
        msg += f"\n<b>Total Tugas :</b> <code>{tasks_no}</code>\n\n"
        
        if tasks_no > 30:
            for i in [1, 2, 4, 6, 8, 10, 15, 20]:
                buttons.ibutton(i, f"status {sid} ps {i} {cmd_user_id}", position="footer")
    
    button = buttons.build_menu(3)
    
    view_type = "Pribadi" if is_user else "Grup" if chat_id else "Global"
    msg += f"<b>──────────────────</b>"
    msg += f"\n<b>Mode Tampilan:</b> <code>{view_type}</code>"
    msg += f"\n<b>CPU :</b> <code>{cpu_percent()}%</code> | <b>RAM :</b> <code>{virtual_memory().percent}%</code>"
    msg += f"\n<b>FREE :</b> <code>{get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}</code> | <b>UPT :</b> <code>{get_readable_time(time() - botStartTime)}</code>"
    
    return msg, button