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
    STATUS_DOWNLOADING = "📥 Mengunduh..."
    STATUS_UPLOADING = "📤 Mengunggah..."
    STATUS_QUEUEDL = "⌛️ Antrian Download..."
    STATUS_QUEUEUP = "⏳ Antrian Upload..."
    STATUS_PAUSED = "⛔️Dihentikan."
    STATUS_ARCHIVING = "📦 Mengarsip..."
    STATUS_EXTRACTING = "🗂️ Mengekstrak..."
    STATUS_CLONING = "📑 Mengclone..."
    STATUS_SEEDING = "🧲 Mengeseed..."
    STATUS_SPLITTING = "📚 Membagi..."
    STATUS_CHECKING = "📝 Mengecek..."
    STATUS_SAMVID = "🎞️ SampleVideo"
     
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
    ("SV", MirrorStatus.STATUS_SAMVID)
]


async def getTaskByGid(gid: str):
    async with task_dict_lock:
        return next((tk for tk in task_dict.values() if tk.gid() == gid), None)


async def getAllTasks(req_status: str):
    async with task_dict_lock:
        if req_status == "all":
            return list(task_dict.values())
        return [tk for tk in task_dict.values() if tk.status() == req_status]


def get_readable_file_size(size_in_bytes: int):
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1
    return (
        f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"
        if index > 0
        else f"{size_in_bytes:.2f}B"
    )

def get_readable_time(seconds: int):
    periods = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
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
            msg += f"<blockquote><b>🔐 Nama :</b> <code>Private Task</code></b></blockquote>"
        else: 
            msg += f"<blockquote><b>📄 Nama :</b> <code>{escape(f'{task.name()}')}</code></blockquote>"
        msg += f"\n<b>┌┤{get_progress_bar_string(task.progress())}<code>{task.progress()}</code></b>"
        if task.listener.isSuperChat:
            msg += f"\n<b>├⌛️ Status :</b> <a href='{task.listener.message.link}'><b>{tstatus}</b></a>"
        else:
            msg += f"\n<b>├⌛️ Status : {tstatus}</b>"
        if tstatus not in [
            MirrorStatus.STATUS_SPLITTING,
            MirrorStatus.STATUS_SEEDING,
            MirrorStatus.STATUS_SAMVID,
        ]:
            msg += f"\n<b>├📦 Ukuran :</b> {task.size()}"
            msg += f"\n<b>├🪫 Diproses :</b> <code>{task.processed_bytes()}</code>"
            msg += f"\n<b>├⏰ Estimasi :</b> <code>{task.eta()}</code>"
            msg += f"\n<b>├⚡️ Kecepatan :</b> <code>{task.speed()}</code>"
            if hasattr(task, "seeders_num"):
                try:
                    msg += f"\n<b>├🌱 Seeders :</b> <code>{task.seeders_num()}</code>"
                    msg += f"\n<b>├🐌 Leechers :</b> <code>{task.leechers_num()}</code>"
                except:
                    pass
        elif tstatus == MirrorStatus.STATUS_SEEDING:
            msg += f"\n<b>├🧲 Ratio :</b> <code>{task.ratio()}</code>"
            msg += f"\n<b>├⏲ Waktu :</b> <code>{task.seeding_time()}</code>"
            msg += f"\n<b>├📦 Ukuran :</b> <code>{task.size()}</code>"
            msg += f"\n<b>├🆙 Diupload :</b> <code>{task.uploaded_bytes()}</code>"
            msg += f"\n<b>├⚡️ Kecepatan :</b> <code>{task.seed_speed()}</code>"
        else:
            msg += f"\n<b>├📦 Ukuran :</b> <code>{task.size()}</code>"
        #if task.listener.isPrivateChat: 
            #msg += f"\n<b>├ ID :</b> <code>PRIVATE</code>"
            #msg += f"\n<b>├👨‍💻 User : <b>Anonymous 👻</b>" 
        #else:
            #msg += f"\n<b>├ ID :</b> <code>{task.listener.user_id}</code>"
        user = f'<a href="tg://user?id={task.listener.user.id}">{task.listener.user.first_name}</a>'
        msg += f"\n<b>├👨‍💻 User :</b> <b>{user}</b>"
        msg += f"\n<b>└🚫 Stop :</b> <code>/{BotCommands.CancelTaskCommand[1]} {task.gid()}</code>\n"

    if len(msg) == 0 and status == "All":
        return None, None
    elif len(msg) == 0:
        msg = f"<b>Tidak ada tugas</b> <code>{status}</code>!\n\n"
    buttons = ButtonMaker()
    if not is_user:
        buttons.ibutton("🤖", "status 0 ov", position="header")
    if len(tasks) > STATUS_LIMIT:
        msg += f"<b>Step :</b> <code>{page_step}</code>"
        msg += f"\n<b>Halaman :</b> <code>{page_no}/{pages}</code>"
        msg += f"\n<b>Total Tugas :</b> <code>{tasks_no}</code>\n"
        buttons.ibutton("⏪", f"status {sid} pre", position="header")
        buttons.ibutton("⏩", f"status {sid} nex", position="header")
        if tasks_no > 30:
            for i in [1, 2, 4, 6, 8, 10, 15, 20]:
                buttons.ibutton(i, f"status {sid} ps {i}", position="footer")
    if status != "All" or tasks_no > 20:
        for label, status_value in STATUS_VALUES:
            if status_value != status:
                buttons.ibutton(label, f"status {sid} st {status_value}")
    buttons.ibutton("♻️", f"status {sid} ref", position="header")
    button = buttons.build_menu(8)
    msg += f"\n<b><b>──────❪ 𝑷𝒊𝒌𝒂𝒃𝒐𝒕 ❫──────</b>"
    msg += f"\n<b>CPU :</b> <code>{cpu_percent()}%</code> | <b>RAM :</b> <code>{virtual_memory().percent}%</code>"
    #msg += f"\n<b>🆃🅳🅻 :</b> <code>{get_readable_file_size(net_io_counters().bytes_recv)}</code> | <b>🆃🆄🅻 :</b> <code>{get_readable_file_size(net_io_counters().bytes_sent)}</code>"
    msg += f"\n<b>FREE :</b> <code>{get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)}</code> | <b>UPT :</b> <code>{get_readable_time(time() - botStartTime)}</code>"
    return msg, button
