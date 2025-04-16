from time import time
from quoters import Quote
from pytz import timezone
from sys import executable
from datetime import datetime
from os import execl as osexecl
from aiofiles import open as aiopen
from subprocess import check_output
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from signal import (
    signal,
    SIGINT,
    )
from psutil import (
    disk_usage,
    cpu_percent,
    cpu_count,
    virtual_memory,
    net_io_counters,
    boot_time,
    cpu_freq,
    )
from asyncio import (
    create_subprocess_exec,
    gather,
    )
from aiofiles.os import (
    path as aiopath,
    remove as aioremove,
    )

###################################
## Import Variables From Project ##
###################################

from bot import (
    bot,
    botStartTime,
    botname,
    botusername,
    config_dict,
    DATABASE_URL,
    INCOMPLETE_TASK_NOTIFIER,
    Interval,
    LOGGER,
    QbInterval,
    scheduler,
    user_data,
    Version,
    )
from bot.modules import (
    asupan,
    authorize,
    auto_mirror,
    bot_settings,
    bypass,
    cancel_task,
    clone,
    eval,
    gd_count,
    gd_delete,
    gd_rename,
    gd_search,
    help,
    mediainfo,
    mirror_leech,
    pickle_generator,
    pikachu_feature,
    query,
    shell,
    speedtest,
    status,
    tiktok,
    torrent_search,
    torrent_select,
    #translate,
    users_settings,
    waifu,
    youtube,
    ytdlp
    )
from bot.helper.ext_utils.bot_utils import (
    cmd_exec,
    sync_to_async,
    create_help_buttons,
    )
from bot.helper.ext_utils.files_utils import (
    clean_all,
    exit_clean_up,
    )
from bot.helper.ext_utils.status_utils import (
    get_readable_file_size,
    get_readable_time,
    ) 
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    editMessage,
    sendFile,
    )
from bot.helper.ext_utils.quota_utils import token_verify
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.listeners.aria2_listener import start_aria2_listener


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
<b>{botname}</b>
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
<b>├MegaSDK      :</b> <code>v{Version.ms}</code>
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


###########
## start ##
###########

async def start(client, message):
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
    
    if len(message.text.split()) > 1:
        data = message.text.split()[1]
        if data.startswith("token_"):
            token = data.split("_")[1]
            user_id = message.from_user.id
            result = await token_verify(user_id, token)
            if isinstance(result, tuple):
                response_text, markup = result
                await sendMessage(message, response_text, markup)
                return
        elif data == "gentoken":
            return await pickle_generator.gen_token(client, message)
        elif data == "gettoken":
            return await pickle_generator.get_token(client, message)
        elif data.startswith("anhdl_"):
            file_id = data.replace("anhdl_", "")
            return await waifu.download_anime_hd(client, message, None, file_id)

    buttons = ButtonMaker()
    buttons.ubutton("👤 Maintainer", "https://t.me/WzdDizzyFlasherr", "header")
    buttons.ubutton("📢 Channel", "https://t.me/IgnoredProjectXcl")
    buttons.ubutton("👥 Group", "https://t.me/TranssionCore5")
    buttons.ubutton("💰 Donate", "https://telegra.ph/Donate-and-Support-Us-03-21")
    buttons.ubutton("➕ Add me to Group", f"https://t.me/{bot.me.username}?startgroup=true", "footer")
    reply_markup = buttons.build_menu(2)

    user_id = message.from_user.id
    is_in_auth_group = message.chat.type.name != "PRIVATE" and await CustomFilters.authorized(client, message)
    
    ################################
    ## Start For Authorized Group ##
    ################################

    if is_in_auth_group:
        start_string = f'''
<b>Selamat Datang di {botname}! 🎉</b>

Halo {uname}, Senang melihat Anda di grup ini!

Bot ini telah dikonfigurasi dan siap membantu Anda dengan berbagai kebutuhan mirror, leech, dan manajemen file. Nikmati semua fitur yang tersedia untuk anggota grup ini.

<b>Cara Menggunakan Bot:</b>
• Gunakan <code>/{BotCommands.HelpCommand[0]}</code> untuk melihat daftar lengkap perintah
• Balas ke file/link dengan perintah mirror/leech untuk memulai tugas
• Pantau progres tugas dengan <code>/{BotCommands.StatusCommand[0]}</code>

<b>Fitur Utama:</b>
• Mirror ke Google Drive
• Leech ke Telegram
• Unduh dari berbagai sumber (Direct Link, Torrent, Mega, dll)
• Pengaturan upload custom
• Fitur pencarian yang kuat

<i>Jika membutuhkan bantuan lebih lanjut, jangan ragu untuk bertanya kepada admin grup!</i>
'''
        
    #####################
    ## Start For Owner ##
    #####################
    elif user_id == config_dict['OWNER_ID']:
        start_string = f'''
<b>Halo Boss {uname}! 👑</b>

Selamat datang kembali di panel kontrol {botname}!

Sebagai pemilik bot, Anda memiliki akses penuh ke semua fitur dan pengaturan. Bot siap menerima perintah Anda dan berfungsi optimal.

<b>Status Bot:</b>
• Bot aktif dan berjalan normal
• Semua sistem dalam keadaan baik
• Siap menerima tugas baru

<b>Pengaturan Cepat:</b>
• <code>/{BotCommands.BotSetCommand[0]}</code> - Konfigurasi bot
• <code>/{BotCommands.StatsCommand[0]}</code> - Cek statistik server
• <code>/{BotCommands.RestartCommand[0]}</code> - Restart bot jika diperlukan

<i>Untuk daftar lengkap perintah, gunakan <code>/{BotCommands.HelpCommand[0]}</code></i>

<b>Semoga harimu menyenangkan, Boss! 🚀</b>
'''

    #########################
    ## Start For Sudo User ##
    #########################

    elif user_id in user_data and user_data[user_id].get('is_sudo', False):
        start_string = f'''
<b>Halo Admin {uname}! ⭐</b>

Selamat datang di panel administrasi {botname}!

Sebagai SUDO user, Anda memiliki akses ke sebagian besar fitur dan pengaturan bot. Bot siap membantu Anda mengelola pengguna dan tugas.

<b>Tugas Admin:</b>
• Mengelola pengguna dengan <code>/{BotCommands.AuthorizeCommand[0]}</code> dan <code>/{BotCommands.UnAuthorizeCommand[0]}</code>
• Memantau kinerja bot dengan <code>/{BotCommands.StatsCommand[0]}</code>
• Restart bot jika diperlukan dengan <code>/{BotCommands.RestartCommand[0]}</code>

<b>Fitur Tambahan:</b>
• Akses ke semua fitur mirror dan leech
• Kemampuan membatalkan tugas semua pengguna
• Melihat dan mengelola status server

<i>Gunakan kekuatan Anda dengan bijak! Untuk daftar lengkap perintah, ketik <code>/{BotCommands.HelpCommand[0]}</code></i>

<b>Terima kasih atas bantuan Anda dalam mengelola bot ini! 👏</b>
'''
        
    ###############################
    ## Start For Authorized User ##
    ###############################

    elif await CustomFilters.authorized(client, message):
        start_string = f'''
<b>Halo {uname}! 🌟</b>

Selamat datang di {botname}! Anda adalah pengguna yang diotorisasi dan memiliki akses ke fitur-fitur bot ini.

<b>Apa yang dapat Anda lakukan:</b>
• Mirror file ke Google Drive dengan <code>/{BotCommands.MirrorCommand[0]}</code>
• Leech file ke Telegram dengan <code>/{BotCommands.LeechCommand[0]}</code>
• Unduh video YouTube dan platform lain dengan <code>/{BotCommands.YtdlCommand[0]}</code>
• Clone file Google Drive dengan <code>/{BotCommands.CloneCommand[0]}</code>
• Cari file di Drive dengan <code>/{BotCommands.ListCommand[0]}</code>

<b>Tips Penggunaan:</b>
• Gunakan <code>/{BotCommands.HelpCommand[0]}</code> untuk panduan lengkap
• Pantau progres dengan <code>/{BotCommands.StatusCommand[0]}</code>
• Batalkan tugas dengan <code>/{BotCommands.CancelTaskCommand[0]}</code>

<i>Jika Anda mengalami masalah atau memiliki pertanyaan, silakan hubungi admin!</i>

<b>Selamat menggunakan! 🚀</b>
'''

    #################################
    ## Start For Unauthorized User ##
    #################################

    else:
        start_string = f'''
<b>Halo {uname}! 👋</b>

Terima kasih telah menyapa {botname}. Saat ini, Anda belum memiliki akses untuk menggunakan bot ini secara pribadi.

<b>Beberapa hal yang perlu Anda ketahui:</b>

• Bot ini adalah alat premium untuk mirror dan leech file
• Akses diberikan oleh admin kepada pengguna tertentu
• Anda dapat menggunakan bot ini di grup resmi kami
• Untuk mendapatkan akses, silakan hubungi admin atau berikan donasi

<b>Cara mendapatkan akses:</b>
• Bergabung dengan grup resmi kami melalui tombol di bawah
• Hubungi maintainer untuk informasi lebih lanjut
• Dukung pengembangan bot dengan donasi

<i>Terima kasih atas pengertian Anda. Kami berharap dapat melayani Anda segera!</i>
'''
    
    await sendMessage(message, start_string, reply_markup)

############
## Donate ##
############

async def donate(_, message):
    buttons = ButtonMaker()
    buttons.ubutton("👤 Maintainer", "https://t.me/WzdDizzyFlasherr", "header")
    buttons.ubutton("📢 Channel", "https://t.me/IgnoredProjectXcl")
    buttons.ubutton("💰 Donate", "https://telegra.ph/Donate-and-Support-Us-03-21", "footer")
    
    donate_message = '''
<b>🎁 Support and Donations</b>

<b>𝐈𝐠𝐧𝐨𝐫𝐞𝐝 𝐏𝐫𝐨𝐣𝐞𝐜𝐭 𝐗𝐜𝐥</b>

Hai! 👋 Terima kasih telah menggunakan layanan kami.

<b>💡 Kenapa Donasi?</b>
Bot ini dikelola dengan penuh dedikasi untuk memberikan pengalaman terbaik bagi pengguna. Semua donasi akan digunakan untuk:
• 🖥️ Biaya server dan infrastruktur
• 💾 Penyimpanan data dan bandwidth
• 🔧 Pengembangan fitur baru
• 🛠️ Pemeliharaan sistem

<b>🎯 Keuntungan Donatur:</b>
• ✅ Akses premium untuk menambahkan bot ke grup pribadi
• ✅ Bebas batasan saat menggunakan bot via PM
• ✅ Dukungan prioritas dan bantuan teknis
• ✅ Fitur eksklusif yang hanya tersedia untuk donatur

<b>💸 100% Transparansi</b>
Semua donasi digunakan sepenuhnya untuk kebutuhan operasional bot - tidak ada keuntungan pribadi yang diambil.

<b>📲 Cara Donasi</b>
Klik tombol "Donate" di bawah untuk melihat berbagai metode pembayaran yang tersedia.

<b>🙏 Dukungan Non-Finansial</b>
Jika belum bisa berdonasi, Anda tetap dapat membantu dengan:
• 🔄 Membagikan bot ini ke teman dan grup
• ⭐ Memberikan feedback untuk pengembangan
• 👥 Bergabung di channel dan grup kami

<i>Setelah donasi, silakan hubungi Maintainer melalui tombol di atas untuk konfirmasi dan mengaktifkan benefit donatur Anda.</i>

<b>❤️ Terima kasih atas dukungan Anda!</b>
'''
    await sendMessage(message, donate_message, buttons.build_menu(2))

async def restart(_, message):
    restart_message = await sendMessage(
        message, 
        "<b>Restarting...</b>"
    )
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if QbInterval:
        QbInterval[0].cancel()
    if Interval:
        for intvl in list(Interval.values()):
            intvl.cancel()
    await clean_all()
    proc1 = await create_subprocess_exec("pkill", "-9", "-f", "gunicorn|chrome|firefox|opera|edge")
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
<code>/{BotCommands.MirrorCommand[0]}</code> atau <code>/{BotCommands.MirrorCommand[1]}</code> : Mirror ke Google Drive/Cloud.
<code>/{BotCommands.QbMirrorCommand[0]}</code> atau <code>/{BotCommands.QbMirrorCommand[1]}</code> : Mirror ke Google Drive/Cloud menggunakan qBittorrent.
<code>/{BotCommands.YtdlCommand[0]}</code> atau <code>/{BotCommands.YtdlCommand[1]}</code> : Mirror link yang disupport YT-DLP.
<code>/{BotCommands.LeechCommand[0]}</code> atau <code>/{BotCommands.LeechCommand[1]}</code> : Leech ke Telegram.
<code>/{BotCommands.QbLeechCommand[0]}</code> atau <code>/{BotCommands.QbLeechCommand[1]}</code> : Leech ke Telegram menggunakan qBittorrent.
<code>/{BotCommands.YtdlLeechCommand[0]}</code> atau <code>/{BotCommands.YtdlLeechCommand[1]}</code> : Leech link yang disupport YT-DLP.
<code>/{BotCommands.CloneCommand[0]}</code> atau <code>/{BotCommands.CloneCommand[1]}</code> [drive_url] : Menggandakan file/folder Google Drive.
<code>/{BotCommands.CountCommand[0]}</code> atau <code>/{BotCommands.CountCommand[1]}</code> [drive_url] : Menghitung file/folder Google Drive.
<code>/{BotCommands.DeleteCommand[0]}</code> atau <code>/{BotCommands.DeleteCommand[1]}</code> [drive_url] : Menghapus file/folder Google Drive (Hanya Owner & Sudo).
<code>/{BotCommands.UserSetCommand[0]}</code> atau <code>/{BotCommands.UserSetCommand[1]}</code> : Pengaturan User.
<code>/{BotCommands.BotSetCommand[0]}</code> atau <code>/{BotCommands.BotSetCommand[1]}</code> : Pengaturan Bot (Hanya Owner & Sudo).
<code>/{BotCommands.BtSelectCommand[0]}</code> atau <code>/{BotCommands.BtSelectCommand[1]}</code> : Memilih file dari torrent.
<code>/{BotCommands.CancelTaskCommand[0]}</code> atau <code>/{BotCommands.CancelTaskCommand[1]}</code> : Membatalkan tugas.
<code>/{BotCommands.CancelAllCommand[0]}</code> atau <code>/{BotCommands.CancelAllCommand[1]}</code> : Membatalkan semua tugas.
<code>/{BotCommands.ListCommand[0]}</code> atau <code>/{BotCommands.ListCommand[1]}</code> [query] : Mencari file/folder di Google Drive.
<code>/{BotCommands.SearchCommand[0]}</code> atau <code>/{BotCommands.SearchCommand[1]}</code> [query] : Mencari torrent menggunakan API.
<code>/{BotCommands.StatusCommand[0]}</code> atau <code>/{BotCommands.StatusCommand[1]}</code> : Menampilkan status dari semua tugas yang sedang berjalan.
<code>/{BotCommands.StatsCommand[0]}</code> atau <code>/{BotCommands.StatsCommand[1]}</code> : Menampilan statistik dari mesin bot.
<code>/{BotCommands.PingCommand[0]}</code> atau <code>/{BotCommands.PingCommand[1]}</code> : Mengetes respon bot (Hanya Owner & Sudo).
<code>/{BotCommands.AuthorizeCommand[0]}</code> atau <code>/{BotCommands.AuthorizeCommand[1]}</code> : Memberikan izin chat atau user untuk menggunakan bot (Hanya Owner & Sudo).
<code>/{BotCommands.UnAuthorizeCommand[0]}</code> atau <code>/{BotCommands.UnAuthorizeCommand[1]}</code> : Menghapus izin chat atau user untuk menggunakan bot (Hanya Owner & Sudo).
<code>/{BotCommands.UsersCommand[0]}</code> atau <code>/{BotCommands.UsersCommand[1]}</code> : Menampilan pengaturan User (Hanya Owner & Sudo).
<code>/{BotCommands.AddSudoCommand[0]}</code> atau <code>/{BotCommands.AddSudoCommand[1]}</code> : Menambahkan User Sudo (Hanya Owner).
<code>/{BotCommands.RmSudoCommand[0]}</code> atau <code>/{BotCommands.RmSudoCommand[1]}</code> : Menghapus User Sudo (Hanya Owner).
<code>/{BotCommands.RestartCommand[0]}</code> atau <code>/{BotCommands.RestartCommand[1]}</code> : Memulai ulang dan memperbarui bot (Hanya Owner & Sudo).
<code>/{BotCommands.LogCommand[0]}</code> atau <code>/{BotCommands.LogCommand[1]}</code> : Mengambil log file dari bot (Hanya Owner & Sudo).
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
                await aioremove(".restartmsg")
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
        await aioremove(".restartmsg")


async def main():
    #jdownloader.initiate()
    await gather(
        clean_all(),
        torrent_search.initiate_search_tools(), 
        restart_notification()
    )
    create_help_buttons()
    await sync_to_async(
        start_aria2_listener, 
        wait=False
    )
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