from signal import signal, SIGINT
from aiofiles.os import path as aiopath, remove
from aiofiles import open as aiopen
from os import execl as osexecl
from time import time
from sys import executable
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from asyncio import gather, create_subprocess_exec
from psutil import (
    disk_usage, 
    cpu_percent, 
    cpu_count, 
    virtual_memory, 
    net_io_counters, 
    boot_time, 
    cpu_freq
)
from subprocess import check_output
from quoters import Quote
from pytz import timezone
from datetime import datetime

from .helper.mirror_utils.rclone_utils.serve import rclone_serve_booter
from .helper.ext_utils.jdownloader_booter import jdownloader
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.files_utils import clean_all, exit_clean_up
from .helper.ext_utils.bot_utils import cmd_exec, sync_to_async, create_help_buttons
from .helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, editMessage, sendFile
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from .helper.listeners.aria2_listener import start_aria2_listener
from bot import (
    bot, 
    botStartTime, 
    LOGGER, 
    Intervals, 
    DATABASE_URL, 
    INCOMPLETE_TASK_NOTIFIER, 
    scheduler, 
    config_dict, 
    Version
)
from .modules import (
    authorize, 
    bot_settings, 
    cancel_task, 
    clone, 
    eval, 
    gd_count, 
    gd_delete, 
    gd_search, 
    gd_rename,
    help, 
    mirror_leech, 
    rss, 
    shell, 
    speedtest,
    status, 
    torrent_search, 
    torrent_select, 
    users_settings, 
    ytdlp,
    bypass,
    query,
    mediainfo
)

def get_quotes():
    try:
        quotez = str(Quote.print_series_quote())
        quote = quotez.split(": ")[1]
        oleh = quotez.split(":")[0]
        quotes = f"{quote}\n=> {oleh}"
    except:
        quotes = "Ngga ada Quote bijak buatmu wahai Tuan yang bijaksana :D"
    return quotes


def progress_bar(percentage):
    if isinstance(percentage, str):
        return "NaN"
    try:
        percentage = int(percentage)
    except:
        percentage = 0
    return "".join(
        "■" if i <= percentage // 10 else "□" for i in range(1, 11)
    )


async def stats(_, message):
    if await aiopath.exists(".git"):
        last_commit = await cmd_exec("git log -1 --date=short --pretty=format:'%cd <b>From</b> %cr'", True)
        last_commit = last_commit[0]
    else:
        last_commit = 'UPSTREAM_REPO tidak ditemukan!'
    currentTime = get_readable_time(time() - botStartTime)
    osUptime = get_readable_time(time() - boot_time())
    total, used, free, disk = disk_usage(config_dict['DOWNLOAD_DIR'])
    try:
        total = get_readable_file_size(total)
    except:
        total = "NaN"
    try:
        used = get_readable_file_size(used)
    except:
        used = "NaN"
    try:
        free = get_readable_file_size(free)
    except:
        free = "NaN"
    # Net Usage
    try:
        sent = get_readable_file_size(net_io_counters().bytes_sent)
    except:
        sent = "NaN"
    try:
        recv = get_readable_file_size(net_io_counters().bytes_recv)
    except:
        recv = "NaN"
    # Cpu
    cpuUsage = cpu_percent(interval=0.5)
    try:
        p_core = cpu_count(logical=False)
    except:
        p_core = "NaN"
    try:
        t_core = cpu_count(logical=True)
    except:
        t_core = "NaN"
    try:
        cpufreq = cpu_freq()
    except:
        cpufreq = "NaN"
    try:
        freqcurrent = round(cpufreq.current)
    except:
        freqcurrent = "NaN"
    memory = virtual_memory()
    mem_p = memory.percent
    try:
        mem_t = get_readable_file_size(memory.total)
    except:
        mem_t = "NaN"
    try:
        mem_a = get_readable_file_size(memory.available)
    except:
        mem_a = "NaN"
    try:
        mem_u = get_readable_file_size(memory.used)
    except:
        mem_u = "NaN"
    # Neofetch
    neofetch = check_output(
        ["neofetch --shell_version off --stdout"], shell=True).decode()
    stats = f'''
<b>𝐏𝐈𝐊𝐀𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐒</b>
<pre languange="python"><code>{neofetch}</code></pre>
<b>┌┤🤖 Status Bot:</b>
<b>├Username     :</b> <code>@{bot.me.username}</code>
<b>├Waktu Bot    :</b> <code>{currentTime}</code>
<b>├Waktu Mesin  :</b> <code>{osUptime}</code>
<b>└Diperbarui   :</b> <code>{last_commit}</code>

<b>┌┤🖥️ CPU:</b>
<b>├Cores        :</b> <code>{p_core}</code>
<b>├Logical      :</b> <code>{t_core}</code>
<b>└┤</b><code>[{progress_bar(cpuUsage)}] {cpuUsage}%</code>

<b>┌┤💽 RAM:</b> 
<b>├Total        :</b> <code>{mem_t}</code>
<b>├Tersedia     :</b> <code>{mem_a}</code>
<b>└┤</b><code>[{progress_bar(mem_p)}] {mem_p}%</code>

<b>┌┤💾 Penyimpanan:</b> 
<b>├Total        :</b> <code>{total}</code>
<b>├Tersedia     :</b> <code>{free}</code>
<b>└┤</b><code>[{progress_bar(disk)}] {disk}%</code>

<b>┌┤🌐 Jaringan:</b>
<b>├Total Unduh  :</b> <code>{recv}</code>
<b>└Total Unggah :</b> <code>{sent}</code>

<b>┌┤📦 Versi Package:</b>
<b>├Aria2c       :</b> <code>v{Version.ar}</code>
<b>├FFMPEG       :</b> <code>v{Version.ff}</code>
<b>├Google Api   :</b> <code>v{Version.ga}</code>
<b>├Java         :</b> <code>v{Version.jv}</code>
<b>├MyJD Api     :</b> <code>v{Version.jd}</code>
<b>├P7Zip        :</b> <code>v{Version.p7}</code>
<b>├Pyro         :</b> <code>v{Version.pr}</code>
<b>├Python       :</b> <code>v{Version.py}</code>
<b>├Rclone       :</b> <code>{Version.rc}</code>
<b>├Qbittorrent  :</b> <code>{Version.qb}</code>
<b>└YT-DLP       :</b> <code>v{Version.yt}</code>

<blockquote><code>{get_quotes()}</code></blockquote>
'''
    await sendMessage(
        message, 
        stats
    )


async def start(client, message):
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
    buttons = ButtonMaker()
    buttons.ubutton(
        "👤 Owner", "https://t.me/XRofikX")
    buttons.ubutton("🌟 Channel", "https://t.me/pikachukocak")
    reply_markup = buttons.build_menu(2)
    if await CustomFilters.authorized(client, message):
        start_string = f'''
<b>Hai {uname}, Pik4bot disini, saya bisa mirror link atau file anda ke google drive atau leech ke telegram, saya juga bisa membypass beberapa shortlink.</b>

<b>Note :</b>
Segera download atau backup file anda setelah mirror, karena drive akan dihapus secara berkala !

Ketik <code>/{BotCommands.HelpCommand[0]}</code> untuk mendapatkan list perintah yang tersedia!

Enjoy 😉
'''
        await sendMessage(message, start_string, reply_markup)
    else:
        await sendMessage(message, f"Hai {uname}, sayang sekali anda bukan <code>authorized user</code>, anda belum bisa menggunakan bot ini di PM.\n\nSilahkan gunakan bot ini hanya di grup, cek channel yang ada dibawah untuk link grupnya !", reply_markup)

async def donate(_, message):
        path = 'https://telegra.ph/file/e8394bf92c06092433a75.png'
        buttons = ButtonMaker()
        buttons.ubutton(
        "👤 Owner", "https://t.me/XRofikX")
        donate_message = f'''
👋Hai, jika kalian merasa terbantu dengan bot ini, saya akan sangat berterimakasih jika kalian mau memberikan sedikit donasi untuk keperluan server dan google drive. 

Semua donasi saya akan gunakan 100% untuk kebutuhan bot, dan tidak akan mengambil keuntungan sedikitpun dari bot ini.

<u>Kalian bisa memberikan donasi dari link dibawah ya:</u>
• Gopay or Dana: 081237313284
• Saweria: https://saweria.co/peekachu
• Ko-Fi: https://ko-fi.com/pikabot

Jika kalian sudah melakukan donasi, silahkan pm ke owner untuk buktinya ya, nanti kalian bisa tambahkan bot ini ke grup pribadi kalian atau bisa menggunakannya di PM.

<blockquote>♥️ Terimakasih yang sudah Donasi !!</blockquote>
'''
        await message.reply_photo(photo=path, reply_to_message_id=message.id,
                                                 caption=donate_message, reply_markup=buttons.build_menu(1), disable_notification=True)

async def restart(_, message):
    restart_message = await sendMessage(
        message, 
        "<b>Restarting...</b>"
    )
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if qb := Intervals["qb"]:
        qb.cancel()
    if jd := Intervals["jd"]:
        jd.cancel()
    if st := Intervals["status"]:
        for intvl in list(st.values()):
            intvl.cancel()
    await sync_to_async(clean_all)
    proc1 = await create_subprocess_exec("pkill", "-9", "-f", "gunicorn|chrome|firefox|opera|edge|safari")
    proc2 = await create_subprocess_exec("python3", "update.py")
    await gather(proc1.wait(), proc2.wait())
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    osexecl(executable, executable, "-m", "bot")


async def ping(_, message):
    start_time = int(round(time() * 1000))
    reply = await sendMessage(
        message, 
        "<b>Mengetest waktu respon bot...</b>"
    )
    end_time = int(round(time() * 1000))
    await editMessage(
        reply, 
        f"🤖 <b>Respon Bot :</b> <code>{end_time - start_time} ms</code>"
    )


async def log(_, message):
    await sendFile(message, "log.txt")

help_string = f"""
<b>Daftar Perintah</b> <code>@{bot.me.username}</code>
<code>/{BotCommands.StartCommand[0]}</code> : Mulai Bot.
<code>/{BotCommands.HelpCommand[0]}</code> atau <code>/{BotCommands.HelpCommand[1]}</code> : Cek semua perintah Bot.
<code>/{BotCommands.MirrorCommand[0]}</code> atau <code>/{BotCommands.MirrorCommand[1]}</code> : Mirror ke Google Drive/Cloud menggunakan Aria2.
<code>/{BotCommands.QbMirrorCommand[0]}</code> atau <code>/{BotCommands.QbMirrorCommand[1]}</code> : Mirror ke Google Drive/Cloud menggunakan qBittorrent.
<code>/{BotCommands.JdMirrorCommand[0]}</code> atau <code>/{BotCommands.JdMirrorCommand[1]}</code> : Mirror ke Google Drive/Cloud menggunakan JDownloader.
<code>/{BotCommands.YtdlCommand[0]}</code> atau <code>/{BotCommands.YtdlCommand[1]}</code> : Mirror ke Google Drive/Cloud menggunakan YT-DLP.
<code>/{BotCommands.LeechCommand[0]}</code> atau <code>/{BotCommands.LeechCommand[1]}</code> : Leech ke Telegram menggunakan Aria2.
<code>/{BotCommands.QbLeechCommand[0]}</code> atau <code>/{BotCommands.QbLeechCommand[1]}</code> : Leech ke Telegram menggunakan qBittorrent.
<code>/{BotCommands.JdLeechCommand[0]}</code> atau <code>/{BotCommands.JdLeechCommand[1]}</code> : Leech ke Telegram menggunakan JDownloader.
<code>/{BotCommands.YtdlLeechCommand[0]}</code> atau <code>/{BotCommands.YtdlLeechCommand[1]}</code> : Leech ke Telegram menggunakan YT-DLP.
<code>/{BotCommands.CloneCommand[0]}</code> atau <code>/{BotCommands.CloneCommand[1]}</code> [gdrive_url] : Menggandakan file/folder Google Drive.
<code>/{BotCommands.CountCommand[0]}</code> atau <code>/{BotCommands.CountCommand[1]}</code> [gdrive_url] : Menghitung file/folder Google Drive.
<code>/{BotCommands.DeleteCommand[0]}</code> atau <code>/{BotCommands.DeleteCommand[1]}</code> [gdrive_url] : Menghapus file/folder Google Drive (Hanya Owner & Sudo).
<code>/{BotCommands.UserSetCommand[0]}</code> atau <code>/{BotCommands.UserSetCommand[1]}</code> : Pengaturan User.
<code>/{BotCommands.BotSetCommand[0]}</code> atau <code>/{BotCommands.BotSetCommand[1]}</code> : Pengaturan Bot (Hanya Owner & Sudo).
<code>/{BotCommands.BtSelectCommand[0]}</code> atau <code>/{BotCommands.BtSelectCommand[1]}</code> : Memilih file dari torrent.
<code>/{BotCommands.CancelTaskCommand[0]}</code> atau <code>/{BotCommands.CancelTaskCommand[1]}</code> : Membatalkan tugas.
<code>/{BotCommands.CancelAllCommand[0]}</code> atau <code>/{BotCommands.CancelAllCommand[1]}</code> : Membatalkan semua tugas (Hanya Owner & Sudo).
<code>/{BotCommands.ListCommand[0]}</code> atau <code>/{BotCommands.ListCommand[1]}</code> [query] : Mencari file/folder di Google Drive.
<code>/{BotCommands.SearchCommand[0]}</code> atau <code>/{BotCommands.SearchCommand[1]}</code> [query] : Mencari torrent menggunakan API.
<code>/{BotCommands.StatusCommand[0]}</code> atau <code>/{BotCommands.StatusCommand[1]}</code> : Menampilkan status dari semua tugas yang sedang berjalan.
<code>/{BotCommands.StatsCommand[0]}</code> atau <code>/{BotCommands.StatsCommand[1]}</code> : Menampilan statistik dari mesin Bot.
<code>/{BotCommands.PingCommand[0]}</code> atau <code>/{BotCommands.PingCommand[1]}</code> : Mengetes kecepatan respon Bot.
<code>/{BotCommands.SpeedCommand[0]}</code> atau <code>/{BotCommands.SpeedCommand[1]}</code> : Mengetes kecepatan koneksi Bot (Hanya Owner & Sudo).
<code>/{BotCommands.AuthorizeCommand[0]}</code> atau <code>/{BotCommands.AuthorizeCommand[1]}</code> : Memberikan izin chat atau user untuk menggunakan Bot (Hanya Owner & Sudo).
<code>/{BotCommands.UnAuthorizeCommand[0]}</code> atau <code>/{BotCommands.UnAuthorizeCommand[1]}</code> : Menghapus izin chat atau user untuk menggunakan Bot (Hanya Owner & Sudo).
<code>/{BotCommands.UsersCommand[0]}</code> atau <code>/{BotCommands.UsersCommand[1]}</code> : Menampilan pengaturan User (Hanya Owner & Sudo).
<code>/{BotCommands.AddSudoCommand[0]}</code> atau <code>/{BotCommands.AddSudoCommand[1]}</code> : Menambahkan User Sudo (Hanya Owner).
<code>/{BotCommands.RmSudoCommand[0]}</code> atau <code>/{BotCommands.RmSudoCommand[1]}</code> : Menghapus User Sudo (Hanya Owner).
<code>/{BotCommands.RestartCommand[0]}</code> atau <code>/{BotCommands.RestartCommand[1]}</code> : Memulai ulang dan memperbarui Bot (Hanya Owner & Sudo).
<code>/{BotCommands.LogCommand[0]}</code> atau <code>/{BotCommands.LogCommand[1]}</code> : Mengambil log file dari Bot (Hanya Owner & Sudo).
<code>/{BotCommands.ShellCommand[0]}</code> atau <code>/{BotCommands.ShellCommand[1]}</code> : Menjalankan perintah Shell (Hanya Owner).
<code>/{BotCommands.EvalCommand[0]}</code> atau <code>/{BotCommands.EvalCommand[1]}</code> : Menjalankan perintah Kode Python (Hanya Owner).
<code>/{BotCommands.ExecCommand[0]}</code> atau <code>/{BotCommands.ExecCommand[1]}</code> : Menjalankan perintah Exec (Hanya Owner).
<code>/{BotCommands.ClearLocalsCommand[0]}</code> atau <code>/{BotCommands.ClearLocalsCommand[1]}</code> : Menghapus penyimpanan lokal (Hanya Owner)
<code>/{BotCommands.RssCommand}</code> : Menu RSS.

<b>NOTE :</b> Kirim perintah tanpa argument untuk melihat perintah secara detail!
"""


async def bot_help(client, message):
    buttons = ButtonMaker()
    user_id = message.from_user.id
    buttons.ibutton('Mirror', f'pika {user_id} guide mirror')
    buttons.ibutton('Leech', f'pika {user_id} guide leech')
    buttons.ibutton('Torrent', f'pika {user_id} guide torrent')
    buttons.ibutton('Ytdlp', f'pika {user_id} guide ytdlp')
    buttons.ibutton('Lainnya', f'pika {user_id} guide other')
    buttons.ibutton('⬇️ Tutup', f'pika {user_id} close', 'footer')
    await sendMessage(message, f"Silahkan pilih jenis bantuan yang anda perlukan !", buttons.build_menu(2))


async def restart_notification():
    if await aiopath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
    else:
        chat_id, msg_id = 0, 0
    
    # Get thread_id from AUTHORIZED_CHATS
    if chat_id == 0:
        chat_id = None
        thread_id = None
        if authorized_chat_id := config_dict.get("AUTHORIZED_CHATS"):
            if not isinstance(authorized_chat_id, int):
                if ":" in authorized_chat_id:
                    chat_id = authorized_chat_id.split(":")[0]
                    thread_id = authorized_chat_id.split(":")[1]

            if (
                chat_id
                and not isinstance(chat_id, int)
                and chat_id.isdigit()
            ):
                chat_id = int(chat_id)

            if (
                thread_id
                and not isinstance(thread_id, int)
                and thread_id.isdigit()
            ):
                thread_id = int(thread_id)

    async def send_incompelete_task_message(cid, msg):
        try:
            if msg.startswith('<b>Bot berhasil dimulai ulang!</b>'):
                await bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=msg_id, 
                    text=msg
                )
                await remove(".restartmsg")
            else:
                await bot.send_message(
                    chat_id=cid, 
                    text=msg, 
                    disable_web_page_preview=True,
                    disable_notification=True,
                    message_thread_id=thread_id,
                )
        except Exception as e:
            LOGGER.error(e)

    now = datetime.now(timezone(f"Asia/Jakarta"))
    if INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        if notifier_dict := await DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                msg = f"""
{'<b>Bot berhasil dimulai ulang!</b>' if cid == chat_id else '<b>Bot dimulai ulang!</b>'}
<pre languange="bash"><b>Hari      :</b> <code>{now.strftime('%A')}</code>
<b>Tanggal   :</b> <code>{now.strftime('%d %B %Y')}</code>
<b>Waktu     :</b> <code>{now.strftime('%H:%M:%S WIB')}</code>
<b>Quotes    :</b>
<code>{get_quotes()}</code>
</pre>           
"""
                if data.items():
                    msg += f"<b>Tugas yang belum selesai :</b>"
                for tag, links in data.items():
                    msg += f"\n{tag} :"
                    for index, link in enumerate(links, start=1):
                        msg += f"\n <a href='{link}'>Tugas ke {index}</a>"
                        if len(msg.encode()) > 4000:
                            await send_incompelete_task_message(cid, msg)
                            msg = ''
                if msg:
                    await send_incompelete_task_message(cid, msg)

    if await aiopath.isfile(".restartmsg"):
        try:
            msg = f"""
<b>Bot berhasil dimulai ulang!</b>
<pre languange="bash"><b>Hari      :</b> <code>{now.strftime('%A')}</code>
<b>Tanggal   :</b> <code>{now.strftime('%d %B %Y')}</code>
<b>Waktu     :</b> <code>{now.strftime('%H:%M:%S WIB')}</code>
<b>Quotes    :</b>
<code>{get_quotes()}</code>
</pre>           
"""
            await bot.edit_message_text(
                chat_id=chat_id, 
                message_id=msg_id, 
                text=msg
            )
        except:
            pass
        await remove(".restartmsg")


async def main():
    await gather(
        sync_to_async(clean_all),
        torrent_search.initiate_search_tools(), 
        restart_notification(),
        telegraph.create_account(),
        rclone_serve_booter(),
        jdownloader.intiate(),
        sync_to_async(start_aria2_listener, wait=False),
    )
    create_help_buttons()
    
    bot.add_handler(
        MessageHandler(
            start, 
            filters=command(
                BotCommands.StartCommand
            )
        )
    )
    bot.add_handler(
        MessageHandler(
            donate, 
            filters=command(
                BotCommands.DonateCommand
            )
        )
    )
    bot.add_handler(
        MessageHandler(
            log, 
            filters=command(
                BotCommands.LogCommand
            ) & CustomFilters.sudo
        )
    )
    bot.add_handler(
        MessageHandler(
            restart, 
            filters=command(
                BotCommands.RestartCommand
            ) & CustomFilters.sudo
        )
    )
    bot.add_handler(
        MessageHandler(
            ping, 
            filters=command(
                BotCommands.PingCommand
            ) & CustomFilters.authorized
        )
    )
    bot.add_handler(
        MessageHandler(
            bot_help, 
            filters=command(
                BotCommands.HelpCommand
            ) & CustomFilters.authorized
        )
    )
    bot.add_handler(
        MessageHandler(
            stats, 
            filters=command(
                BotCommands.StatsCommand
            ) & CustomFilters.authorized
        )
    )
    
    LOGGER.info(f"Bot Started! => @{bot.me.username}")
    signal(SIGINT, exit_clean_up)

bot.loop.run_until_complete(main())
bot.loop.run_forever()
