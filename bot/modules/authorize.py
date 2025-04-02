from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from asyncio import sleep as asleep

from bot import user_data, DATABASE_URL, bot, LOGGER, OWNER_ID
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.ext_utils.pikachu_utils import create_token


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
            await sendMessage(message, "❌ <b>Format ID tidak valid.</b>")
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
        
    header = "📊 <b>INFORMASI KUOTA PENGGUNA</b>"
    divider = "\n─────────────────────────\n"
    
    standard_quota = 25 * 1024 * 1024 * 1024
    quota_multiples = quota / standard_quota if quota > 0 else 0
    quota_rounded = round(quota_multiples, 2)
    
    base_msg = f"{header}{divider}"
    base_msg += f"<b>Status:</b> <code>{'Guest' if quota == 0 else 'Authorized User'}</code>\n"
    base_msg += f"<b>ID Pengguna:</b> <code>{user_id}</code>\n"
    base_msg += f"<b>Sisa Kuota:</b> <code>{get_readable_file_size(quota)}</code>\n"
    
    if quota > 0:
        base_msg += f"<b>Setara Dengan:</b> <code>{quota_rounded}x</code> paket kuota standard\n"
    
    base_msg += divider
    
    GB_20 = 20 * 1024 * 1024 * 1024
    GB_15 = 15 * 1024 * 1024 * 1024
    GB_10 = 10 * 1024 * 1024 * 1024
    GB_5 = 5 * 1024 * 1024 * 1024
    
    if sudo:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>✅ Hak Istimewa Sudo User:</b>\n"
                f"• Akses tanpa batas ke semua fitur\n"
                f"• Dapat menggunakan bot tanpa batasan kuota\n"
                f"• Kemampuan mengelola pengguna lain\n"
                f"• Akses ke perintah administratif\n\n"
                f"<i>Gunakan hak istimewa ini dengan bijak!</i>"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>⚠️ Informasi:</b> Pengguna ini memiliki hak istimewa Sudo dengan akses kuota tanpa batas."
            )
        
        mess = await sendMessage(message, msg)
        
    elif user_id == OWNER_ID:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>✅ Hak Istimewa Owner:</b>\n"
                f"• Akses penuh ke semua fitur dan pengaturan\n"
                f"• Kuota tak terbatas untuk semua operasi\n"
                f"• Kemampuan mengelola pengguna dan sudo\n"
                f"• Akses ke semua perintah administratif\n\n"
                f"<i>Anda memiliki kontrol penuh atas bot ini!</i>"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>⚠️ Informasi:</b> Pengguna ini adalah Owner bot dengan akses penuh dan kuota tak terbatas."
            )
        
        mess = await sendMessage(message, msg)
        
    else:
        if quota == 0:
            detail_msg = (
                "<b>⚠️ Belum memiliki kuota!</b>\n\n"
                "<i>Untuk menggunakan bot ini, diperlukan kuota yang bisa ditambahkan melalui tombol di bawah. "
                "Kuota digunakan untuk mengunduh dan mengunggah file.</i>\n\n"
                "<b>✅ Keuntungan Memiliki Kuota:</b>\n"
                "• Akses penuh ke semua fitur bot\n"
                "• Dapat mengunduh file tanpa batasan\n"
                "• Kuota tidak akan hangus/expired\n"
                "• Support langsung dari admin\n\n"
            )
        elif quota >= GB_20:
            detail_msg = (
                "<b>✅ Kuota masih banyak!</b>\n\n"
                "<i>Kuota yang tersedia cukup untuk mengunduh banyak file. "
                "Bot dapat digunakan dengan optimal tanpa khawatir kehabisan kuota.</i>\n\n"
                "<b>💡 Tips Menggunakan Kuota:</b>\n"
                "• Hindari mengunduh file yang sama berulang kali\n"
                "• Gunakan fungsi mirror untuk efisiensi kuota\n"
                "• Pastikan link yang diunduh valid\n\n"
            )
        elif quota >= GB_15:
            detail_msg = (
                "<b>✅ Kuota masih mencukupi!</b>\n\n"
                "<i>Dengan kuota saat ini, masih dapat mengunduh banyak file. "
                "Tetapi jika berencana mengunduh file berukuran besar, pertimbangkan untuk menambah kuota.</i>\n\n"
                "<b>💡 Tips Mengoptimalkan Kuota:</b>\n"
                "• Prioritaskan file penting untuk diunduh terlebih dahulu\n"
                "• Gunakan fitur kompresi untuk file besar\n"
                "• Pertimbangkan untuk menambah kuota sebelum habis\n\n"
            )
        elif quota >= GB_10:
            detail_msg = (
                "<b>⚠️ Kuota mulai berkurang!</b>\n\n"
                "<i>Dengan kuota sekitar 10-15GB, masih memiliki ruang yang cukup untuk beberapa file. "
                "Namun, jika berencana mengunduh file besar, sebaiknya tambahkan kuota segera.</i>\n\n"
                "<b>💡 Saran Penggunaan:</b>\n"
                "• Perhatikan ukuran file sebelum mengunduh\n"
                "• Gunakan fitur leech untuk file yang benar-benar penting\n"
                "• Pertimbangkan untuk menambah kuota segera\n\n"
            )
        elif quota >= GB_5:
            detail_msg = (
                "<b>⚠️ Perhatian! Kuota hampir habis!</b>\n\n"
                "<i>Dengan kuota tersisa hanya 5-10GB, perlu berhati-hati dalam menggunakan bot. "
                "File berukuran besar mungkin tidak dapat diunduh tanpa menambah kuota.</i>\n\n"
                "<b>⚡ Tindakan yang Disarankan:</b>\n"
                "• Prioritaskan pengunduhan file penting saja\n"
                "• Cek ukuran file sebelum mengunduh\n"
                "• Tambahkan kuota segera untuk penggunaan lancar\n\n"
            )
        else:
            detail_msg = (
                "<b>🚨 PERINGATAN! KUOTA SANGAT RENDAH!</b>\n\n"
                "<i>Kuota kurang dari 5GB dan akan segera habis! "
                "Tidak akan dapat mengunduh sebagian besar file tanpa menambah kuota.</i>\n\n"
                "<b>🔴 Status Kritis:</b>\n"
                "• Kuota hampir habis\n"
                "• Hanya file kecil yang dapat diunduh\n"
                "• Resiko kegagalan unduhan tinggi\n"
                "• Tambah kuota SEKARANG untuk menghindari gangguan\n\n"
            )
        
        if quota >= GB_20:
            status_indicator = "✅ Status Kuota: Sangat Baik"
        elif quota >= GB_15:
            status_indicator = "✅ Status Kuota: Baik"
        elif quota >= GB_10:
            status_indicator = "⚠️ Status Kuota: Menengah"
        elif quota >= GB_5:
            status_indicator = "⚠️ Status Kuota: Rendah"
        elif quota > 0:
            status_indicator = "🚨 Status Kuota: Kritis"
        else:
            status_indicator = "❌ Status Kuota: Tidak Ada"
            
        detail_msg += f"<b>{status_indicator}</b>\n\n"
        
        if quota < GB_20 or quota == 0:
            if is_reply and user_id != from_user_id:
                detail_msg += f"<i>Tombol tambah kuota hanya dapat digunakan oleh <a href='tg://user?id={user_id}'>pengguna ini</a>.</i>"
            elif not self and not is_reply:
                detail_msg += f"<i>Tombol tambah kuota hanya dapat digunakan oleh pengguna dengan ID: {user_id}.</i>"
            else:
                detail_msg += "<i>Klik tombol di bawah untuk menambah kuota:</i>"
            
            try:
                butt = await create_token(user_id)
                final_msg = base_msg + detail_msg
                mess = await sendMessage(message, final_msg, butt)
            except Exception as e:
                LOGGER.error(f"Error creating token: {str(e)}")
                final_msg = base_msg + detail_msg
                mess = await sendMessage(message, final_msg)
        else:
            detail_msg += "<i>Selamat menggunakan bot! Jika ada pertanyaan, hubungi admin.</i>"
            final_msg = base_msg + detail_msg
            mess = await sendMessage(message, final_msg)
    
    await asleep(120)
    await deleteMessage(mess)

bot.add_handler(
    MessageHandler(
        authorize, 
        filters=command(
            BotCommands.AuthorizeCommand
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        unauthorize,
        filters=command(
            BotCommands.UnAuthorizeCommand
        ) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        addSudo, 
        filters=command(
            BotCommands.AddSudoCommand
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        removeSudo, 
        filters=command(
            BotCommands.RmSudoCommand
        ) & CustomFilters.sudo
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
