from time import time
from html import escape
from psutil import (
    cpu_percent, 
    disk_usage, 
    net_io_counters,
    virtual_memory
)

from bot import task_dict, task_dict_lock, botStartTime, config_dict
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

def get_readable_message(sid, is_user, page_no=1, status="All", page_step=1):
    msg = ""
    button = None

    if status == "All":
        tasks = (
            [tk for tk in task_dict.values() if tk.listener.user_id == sid]
            if is_user
            else list(task_dict.values())
        )
    elif is_user:
        tasks = [
            tk
            for tk in task_dict.values()
            if tk.status() == status and tk.listener.user_id == sid
        ]
    else:
        tasks = [tk for tk in task_dict.values() if tk.status() == status]

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
        if task.listener.isPrivateChat: 
            msg += f"<blockquote><b>📄 Nama :</b> <code>{escape(f'{task.name()}')}</code></b></blockquote>"
        else: 
            msg += f"<blockquote>📄 <b>Nama :</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
        if tstatus not in [
            MirrorStatus.STATUS_DUMPING,
            MirrorStatus.STATUS_VIDEDIT,
        ]:
            msg += f"\n<b>┌ Status : <a href='{task.listener.message.link}'>{tstatus}</a></b> <code>({task.progress()})</code>"
        else:
            msg += f"\n<b>┌ Status : <a href='{task.listener.message.link}'>{tstatus}</a></b>"
        if tstatus not in [
            MirrorStatus.STATUS_DUMPING,
            MirrorStatus.STATUS_VIDEDIT,
        ]:
            msg += f"\n<b>├ </b>{get_progress_bar_string(task.progress())}"
        user = f'<a href="tg://user?id={task.listener.user.id}">{task.listener.user.first_name}</a>'
        msg += f"\n<b>├ Oleh :</b> <code>@{task.listener.user.username}</code>"
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
        elif tstatus == MirrorStatus.STATUS_SEEDING:
            msg += f"\n<b>├ Ratio :</b> <code>{task.ratio()}</code>"
            msg += f"\n<b>├ Waktu :</b> <code>{task.seeding_time()}</code>"
            msg += f"\n<b>├ Ukuran :</b> <code>{task.size()}</code>"
            msg += f"\n<b>├ Diupload :</b> <code>{task.uploaded_bytes()}</code>"
            msg += f"\n<b>├ Kecepatan :</b> <code>{task.seed_speed()}</code>"
        #else:
        #    msg += f"\n<b>├ Ukuran :</b> <code>{task.size()}</code>"
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
        msg += f"\n<b>└⛔️ /{BotCommands.CancelTaskCommand[0]}_{task.gid()}\n\n"

    if len(msg) == 0 and status == "All":
        return None, None
    elif len(msg) == 0:
        msg = f"<b>Tidak ada tugas</b> <code>{status}</code>!\n\n"
    buttons = ButtonMaker()
    if not is_user:
        buttons.ibutton("ℹ️ Overview", "status 0 ov", position="header")
    if len(tasks) > STATUS_LIMIT:
        msg += f"<b>Step :</b> <code>{page_step}</code>"
        msg += f"\n<b>Halaman :</b> <code>{page_no}/{pages}</code>"
        msg += f"\n<b>Total Tugas :</b> <code>{tasks_no}</code>\n\n"
        buttons.ibutton("⏪ Prev", f"status {sid} pre")
        buttons.ibutton("Next ⏩", f"status {sid} nex")
        if tasks_no > 30:
            for i in [1, 2, 4, 6, 8, 10, 15, 20]:
                buttons.ibutton(i, f"status {sid} ps {i}", position="footer")
    if status != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status:
                buttons.ibutton(label, f"status {sid} st {status_value}")
    buttons.ubutton("Join", "https://t.me/pikachukocak2", position="header")
    buttons.ibutton("🔄 Refresh", f"status {sid} ref", position="header")
    buttons.ibutton("🔽 Tutup", f"status {sid} close", position="footer")
    button = buttons.build_menu(3)
    msg += f"<b>──────────────────</b>"
    msg += f"\n<b>CPU :</b> <code>{cpu_percent()}%</code> | <b>RAM :</b> <code>{virtual_memory().percent}%</code>"
    msg += f"\n<b>FREE :</b> <code>{get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}</code> | <b>UPT :</b> <code>{get_readable_time(time() - botStartTime)}</code>"
    return msg, button
