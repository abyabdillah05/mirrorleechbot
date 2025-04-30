import time
from asyncio import sleep as asleep
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.quota_utils import create_token
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.telegram_helper.bot_commands import BotCommands

from bot import (
    user_data,
    DATABASE_URL,
    bot,
    LOGGER,
    OWNER_ID,
    )
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    auto_delete_message
    )


async def authorize(_, message):
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
    else:
        id_ = message.chat.id
    if id_ in user_data and user_data[id_].get("is_auth"):
        msg = "🙃 <b>Sudah diautorisasi!</b>"
    else:
        update_user_ldata(id_, "is_auth", True)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "😉 <b>Berhasil diautorisasi!</b>"
    await sendMessage(message, msg)


async def unauthorize(_, message):
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
    else:
        id_ = message.chat.id
    if id_ not in user_data or user_data[id_].get("is_auth"):
        update_user_ldata(id_, "is_auth", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "😉 <b>Berhasil diunautorisasi!</b>"
    else:
        msg = "🙃 <b>Sudah diunautorisasi!</b>"
    await sendMessage(message, msg)


async def addSudo(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
    if id_:
        if id_ in user_data and user_data[id_].get("is_sudo"):
            msg = "🙃 <b>Sudah menjadi sudo user!</b>"
        else:
            update_user_ldata(id_, "is_sudo", True)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "😉 <b>Berhasil dinaikan menjadi sudo user!</b>"
    else:
        msg = "<b>Berikan ID atau balas pesan dari User yang ingin dinaikan menjadi Sudo User!</b>"
    await sendMessage(message, msg)


async def removeSudo(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
    if id_ and id_ not in user_data or user_data[id_].get("is_sudo"):
        update_user_ldata(id_, "is_sudo", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "😉 <b>Berhasil diturunkan dari Sudo User!</b>"
    else:
        msg = "<b>Berikan ID atau balas pesan dari User yang ingin diturunkan dari Sudo User!</b>"
    await sendMessage(message, msg)

###########################
## Functionn Check Quota ##
###########################

## Credit: @aenulrofik  
## Enhancement by: Tg @IgnoredProjectXcl

async def check_quota(_, message):
    self = False
    sudo = False
    from_user_id = message.from_user.id
    
    is_reply = message.reply_to_message is not None
    replied_user_id = message.reply_to_message.from_user.id if is_reply else None
    
    msg = message.text.split()
    if len(msg) > 1:
        try:
            user_id = int(msg[1].strip())
            self = False
        except ValueError:
            mess = await sendMessage(message, "<b>╔ Format ID tidak valid.</b>")
            await auto_delete_message(message, mess)
            return
    elif is_reply:
        user_id = replied_user_id
        self = False
    else:
        self = True
        user_id = from_user_id
    
    if user_id in user_data and user_data[user_id].get("is_sudo"):
        sudo = True
    if user_id in user_data and user_data[user_id].get("quota", 0):
        quota = user_data[user_id].get("quota", 0)
    else:
        quota = 0
    
    try:
        user_info = await bot.get_users(user_id)
        user_name = user_info.first_name
        username = user_info.username if user_info.username else None
    except Exception as e:
        LOGGER.error(f"Error getting user info: {str(e)}")
        user_name = None
        username = None
    
    GB_20 = 20 * 1024 * 1024 * 1024
    GB_15 = 15 * 1024 * 1024 * 1024
    GB_10 = 10 * 1024 * 1024 * 1024
    GB_5 = 5 * 1024 * 1024 * 1024
    
    header = "<b>╔ INFORMASI KUOTA PENGGUNA</b>"
    divider = "\n——————————————————————\n"
    
    standard_quota = 20 * 1024 * 1024 * 1024
    quota_multiples = quota / standard_quota if quota > 0 else 0
    quota_rounded = round(quota_multiples, 2)
    
    base_msg = f"{header}{divider}"
    
    if user_name:
        base_msg += f"<b>▹ Nama:</b> <code>{user_name}</code>\n"
    if username:
        base_msg += f"<b>▹ Username:</b> <code>@{username}</code>\n"
    
    if sudo:
        base_msg += f"<b>▹ Status:</b> <code>Sudo User</code>\n"
    elif user_id == OWNER_ID:
        base_msg += f"<b>▹ Status:</b> <code>Owner</code>\n"
    else:
        base_msg += f"<b>▹ Status:</b> <code>{'Guest' if quota == 0 else 'Premium User'}</code>\n"
    
    base_msg += f"<b>▹ ID Pengguna:</b> <code>{user_id}</code>\n"
    
    if sudo or user_id == OWNER_ID:
        base_msg += f"<b>▹ Kuota:</b> <code>Unlimited</code>\n"
    else:
        base_msg += f"<b>▹ Kuota:</b> <code>{get_readable_file_size(quota)}</code>\n"
        
        if quota > 0:
            base_msg += f"<b>▹ Setara:</b> <code>{quota_rounded}x</code> paket standard (20GB)\n"
    
    base_msg += divider
    
    if sudo:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>╔ HAK AKSES SUDO USER</b>\n\n"
                f"<i>Sebagai Sudo User, Anda memiliki:</i>\n\n"
                f"▹ Akses tanpa batas ke semua fitur bot\n"
                f"▹ Penggunaan bot tanpa batasan kuota\n"
                f"▹ Kemampuan mengelola pengguna lain\n\n"
                f"<i>Gunakan hak akses ini dengan bijak.</i>"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>╔ INFORMASI PENGGUNA</b>\n\n"
                f"<i>Pengguna ini adalah Sudo User dengan akses khusus:</i>\n\n"
                f"▹ Akses premium ke seluruh fitur bot\n"
                f"▹ Tidak memiliki batasan kuota\n"
                f"▹ Memiliki kemampuan administratif\n\n"
            )
        
        mess = await sendMessage(message, msg)
        await auto_delete_message(message, mess)
        return
        
    elif user_id == OWNER_ID:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>╔ HAK AKSES OWNER</b>\n\n"
                f"<i>Sebagai Owner, Anda memiliki kontrol penuh:</i>\n\n"
                f"▹ Akses penuh ke semua fitur dan pengaturan\n"
                f"▹ Kuota tak terbatas untuk semua operasi\n"
                f"▹ Kemampuan mengelola pengguna dan sudo\n\n"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>╔ INFORMASI PENGGUNA</b>\n\n"
                f"<i>Pengguna ini adalah Owner bot dengan kendali penuh:</i>\n\n"
                f"▹ Akses tak terbatas ke seluruh fitur\n"
                f"▹ Kuota tidak terbatas\n"
                f"▹ Kontrol penuh atas konfigurasi\n\n"
            )
        
        mess = await sendMessage(message, msg)
        await auto_delete_message(message, mess)
        return
    
    butt, hours_remaining = await create_token(user_id)
    has_cooldown = hours_remaining > 0
    
    if has_cooldown and user_id in user_data and user_data[user_id].get("last_quota_add"):
        current_time = int(time.time())
        last_add_time = user_data[user_id]["last_quota_add"]
        time_passed = current_time - last_add_time
        seconds_remaining = 86400 - time_passed
        
        hours = seconds_remaining // 3600
        minutes = (seconds_remaining % 3600) // 60
        seconds = seconds_remaining % 60
        
        cooldown_msg = (
            f"<b>╔ STATUS PENAMBAHAN KUOTA</b>\n"
            f"<b>▹ Status: </b><code>Cooldown</code>\n"
            f"<b>▹ Sisa waktu: </b><code>{hours:02d}:{minutes:02d}:{seconds:02d}</code>\n"
            f"<b>▹ Keterangan: </b><code>Dapat menambah kuota setelah periode cooldown berakhir</code>\n"
            f"{divider}"
        )
        base_msg += cooldown_msg
    
    if quota == 0:
        detail_msg = (
            "<b>╔ BELUM MEMILIKI KUOTA</b>\n\n"
            "<i>Untuk menggunakan bot ini, Anda memerlukan kuota.</i>\n\n"
            "<b>╔ CARA MENDAPATKAN KUOTA</b>\n"
            "▹ Klik tombol \"TAMBAH KUOTA\" di bawah ini\n"
            "▹ Lewati shortlink yang muncul\n"
            "▹ Kuota 15GB akan otomatis ditambahkan\n"
            "▹ Kuota tidak akan pernah kadaluarsa\n\n"
            "<b>╔ KEUNTUNGAN MEMILIKI KUOTA</b>\n"
            "▹ Akses penuh ke semua fitur bot\n"
            "▹ Kemampuan mengunduh file tanpa batasan format\n"
            "▹ Dapat menjalankan tugas berukuran besar\n\n"
        )
    elif quota >= GB_20:
        detail_msg = (
            "<b>╔ INFORMASI KUOTA</b>\n\n"
            "<i>Anda memiliki kuota yang cukup banyak untuk mengunduh berbagai file.</i>\n\n"
            "<b>╔ TIPS PENGGUNAAN</b>\n"
            "▹ Manfaatkan fitur batch download untuk efisiensi\n"
            "▹ Gunakan fitur kompresi untuk menghemat ruang\n"
            "▹ Hindari mengunduh file yang sama berulang kali\n\n"
            "<b>╔ ESTIMASI PENGGUNAAN</b>\n"
            "▹ Kuota Anda cukup untuk mengunduh banyak film HD/4K\n"
            "▹ Ideal untuk penggunaan intensif\n\n"
        )
    elif quota >= GB_15:
        detail_msg = (
            "<b>╔ INFORMASI KUOTA</b>\n\n"
            "<i>Kuota Anda memadai untuk berbagai kebutuhan.</i>\n\n"
            "<b>╔ TIPS PENGGUNAAN</b>\n"
            "▹ Prioritaskan file penting terlebih dahulu\n"
            "▹ Manfaatkan fitur kompresi untuk file besar\n"
            "▹ Periksa ukuran file sebelum mengunduh\n\n"
            "<b>╔ PERKIRAAN KAPASITAS</b>\n"
            "▹ Kuota Anda cukup untuk 7-10 film HD\n"
            "▹ Ideal untuk penggunaan reguler\n\n"
        )
    elif quota >= GB_10:
        detail_msg = (
            "<b>╔ INFORMASI KUOTA</b>\n\n"
            "<i>Kuota Anda cukup untuk beberapa file berukuran sedang.</i>\n\n"
            "<b>╔ SARAN PENGGUNAAN</b>\n"
            "▹ Perhatikan ukuran file sebelum mengunduh\n"
            "▹ Gunakan fitur pemilihan file untuk torrent\n"
            "▹ Prioritaskan konten yang benar-benar Anda butuhkan\n\n"
            "<b>╔ MANAJEMEN KUOTA</b>\n"
            "▹ Hindari mengunduh beberapa file besar sekaligus\n"
            "▹ Pantau penggunaan kuota dengan perintah /cek\n\n"
        )
    elif quota >= GB_5:
        detail_msg = (
            "<b>╔ INFORMASI KUOTA</b>\n\n"
            "<i>Kuota Anda terbatas. Gunakan dengan bijak.</i>\n\n"
            "<b>╔ CATATAN PENGGUNAAN</b>\n"
            "▹ File berukuran besar (>3GB) berisiko gagal diunduh\n"
            "▹ Hindari mengunduh file dalam jumlah banyak\n"
            "▹ Pertimbangkan opsi mirror daripada leech\n\n"
            "<b>╔ REKOMENDASI</b>\n"
            "▹ Tambahkan kuota segera untuk penggunaan optimal\n"
            "▹ Gunakan fitur kompresi untuk file penting\n\n"
        )
    else:
        detail_msg = (
            "<b>╔ INFORMASI KUOTA</b>\n\n"
            "<i>Kuota Anda sangat terbatas (kurang dari 5GB).</i>\n\n"
            "<b>╔ BATASAN</b>\n"
            "▹ Hanya file kecil (<2GB) yang dapat diunduh\n"
            "▹ Risiko tinggi kegagalan unduhan\n"
            "▹ Beberapa fitur mungkin tidak berfungsi optimal\n\n"
            "<b>╔ SARAN TINDAKAN</b>\n"
            "▹ Tambahkan kuota melalui tombol di bawah\n"
            "▹ Hindari memulai tugas baru hingga kuota ditambah\n\n"
        )
    
    detail_msg += f"<b>╔ Status Kuota:</b> <code>{get_readable_file_size(quota)}</code>\n\n"
    
    if user_id != from_user_id:
        if is_reply:
            detail_msg += f"<i>Tombol tambah kuota hanya dapat digunakan oleh <a href='tg://user?id={user_id}'>pengguna ini</a>.</i>"
        else:
            detail_msg += f"<i>Tombol tambah kuota hanya dapat digunakan oleh pengguna dengan ID: {user_id}.</i>"
    else:
        if has_cooldown:
            detail_msg += f"<i>Anda dapat menambah kuota lagi setelah periode cooldown berakhir.</i>"
        else:
            detail_msg += "<i>Klik tombol di bawah untuk menambah kuota.</i>"
    
    try:
        final_msg = base_msg + detail_msg
        mess = await sendMessage(message, final_msg, butt.build_menu(2))
        await auto_delete_message(message, mess)
    except Exception as e:
        LOGGER.error(f"Error creating token: {str(e)}")
        final_msg = base_msg + detail_msg
        mess = await sendMessage(message, final_msg)
        await auto_delete_message(message, mess)

######################
## Commands Handler ##
######################

bot.add_handler(
    MessageHandler(
        authorize, 
        filters=command(
            BotCommands.AuthorizeCommand
        ) & CustomFilters.owner
    )
)
bot.add_handler(
    MessageHandler(
        unauthorize,
        filters=command(
            BotCommands.UnAuthorizeCommand
        ) & CustomFilters.owner
    )
)
bot.add_handler(
    MessageHandler(
        addSudo, 
        filters=command(
            BotCommands.AddSudoCommand
        ) & CustomFilters.owner
    )
)
bot.add_handler(
    MessageHandler(
        removeSudo, 
        filters=command(
            BotCommands.RmSudoCommand
        ) & CustomFilters.owner
    )
)
bot.add_handler(
    MessageHandler(
        check_quota, 
        filters=command(
            BotCommands.CekQuotaCommand
        ) & CustomFilters.authorized
    )
)

