from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from asyncio import sleep as asleep

from bot import user_data, DATABASE_URL, bot, LOGGER, OWNER_ID
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.ext_utils.common_utils import get_readable_file_size
from bot.helper.ext_utils.quota_utils import create_token


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
    
    if id_ not in user_data:
        msg = "🙃 <b>Sudah diunautorisasi!</b>"
    else:
        if id_ in user_data:
            if "quota" in user_data[id_]:
                del user_data[id_]["quota"]
            user_data.pop(id_, None)
        
        msg = "😉 <b>Berhasil diunautorisasi dan dihapus dari database!</b>"
             
        if DATABASE_URL:
            await DbManger().delete_user_data(id_)
            
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
    
    if id_ == "":
        msg = "<b>Berikan ID atau balas pesan dari User yang ingin diturunkan dari Sudo User!</b>"
    elif id_ not in user_data:
        msg = "🙃 <b>Pengguna tidak ditemukan dalam database!</b>"
    elif not user_data[id_].get("is_sudo"):
        msg = "🙃 <b>Pengguna bukan sudo user!</b>"
    else:
        user_data.pop(id_, None)
        msg = "😉 <b>Berhasil diturunkan dari Sudo User dan dihapus dari database!</b>"
            
        if DATABASE_URL:
            await DbManger().delete_user_data(id_)
            
    await sendMessage(message, msg)

#########################
## Check QUota Command ##
#########################

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
            mess = await sendMessage(message, "❌ <b>Format ID tidak valid.</b>")
            await asleep(60)
            await deleteMessage(mess)
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
    
    header = "📊 <b>INFORMASI KUOTA PENGGUNA</b>"
    divider = "\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    standard_quota = 20 * 1024 * 1024 * 1024
    quota_multiples = quota / standard_quota if quota > 0 else 0
    quota_rounded = round(quota_multiples, 2)
    
    base_msg = f"{header}{divider}"
    
    if user_name:
        base_msg += f"<b>👤 Nama:</b> <code>{user_name}</code>\n"
    if username:
        base_msg += f"<b>🔖 Username:</b> <code>@{username}</code>\n"
    
    if sudo:
        base_msg += f"<b>🔰 Status:</b> <code>Sudo User</code>\n"
    elif user_id == OWNER_ID:
        base_msg += f"<b>👑 Status:</b> <code>Owner</code>\n"
    else:
        base_msg += f"<b>🔰 Status:</b> <code>{'Guest' if quota == 0 else 'Premium User'}</code>\n"
    
    base_msg += f"<b>🆔 ID Pengguna:</b> <code>{user_id}</code>\n"
    
    if sudo or user_id == OWNER_ID:
        base_msg += f"<b>💾 Kuota:</b> <code>Unlimited</code>\n"
    else:
        if quota >= GB_20:
            quota_indicator = "🔵"  
        elif quota >= GB_15:
            quota_indicator = "🟢"  
        elif quota >= GB_10:
            quota_indicator = "🟡"  
        elif quota >= GB_5:
            quota_indicator = "🟠"  
        elif quota > 0:
            quota_indicator = "🔴"  
        else:
            quota_indicator = "⚠️"  
        
        base_msg += f"<b>💾 Kuota:</b> <code>{get_readable_file_size(quota)}</code> {quota_indicator}\n"
        
        if quota > 0:
            base_msg += f"<b>📈 Setara:</b> <code>{quota_rounded}x</code> paket standard (20GB)\n"
    
    base_msg += divider
    
    # Initialize mess to None
    mess = None
    
    if sudo:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>✨ HAK ISTIMEWA SUDO USER</b>\n\n"
                f"<i>Sebagai Sudo User, Anda memiliki akses premium:</i>\n\n"
                f"• 🚀 Akses tanpa batas ke semua fitur bot\n"
                f"• 💯 Penggunaan bot tanpa batasan kuota\n"
                f"• 👥 Kemampuan mengelola pengguna lain\n"
                f"• ⚙️ Akses ke semua perintah administratif\n"
                f"• 📊 Monitoring aktivitas dan penggunaan\n\n"
                f"<i>🔍 Gunakan hak istimewa ini dengan bijak dan bertanggung jawab!</i>"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>ℹ️ INFORMASI PENGGUNA</b>\n\n"
                f"<i>Pengguna ini adalah Sudo User dengan hak istimewa khusus:</i>\n\n"
                f"• Memiliki akses premium ke seluruh fitur bot\n"
                f"• Dapat menggunakan bot tanpa batasan kuota\n"
                f"• Memiliki kemampuan administratif dalam sistem\n\n"
                f"<i>Status Sudo User memberikan prioritas dan fitur eksklusif.</i>"
            )
        
        mess = await sendMessage(message, msg)
        await asleep(120)
        await deleteMessage(mess)
        return
        
    elif user_id == OWNER_ID:
        if self:
            msg = (
                f"{base_msg}"
                f"<b>👑 HAK ISTIMEWA OWNER</b>\n\n"
                f"<i>Sebagai Owner, Anda memiliki kontrol penuh atas sistem:</i>\n\n"
                f"• 🔐 Akses penuh ke semua fitur dan pengaturan\n"
                f"• ♾️ Kuota tak terbatas untuk semua operasi\n"
                f"• 👨‍💼 Kemampuan mengelola pengguna dan sudo\n"
                f"• 🛠️ Kontrol penuh atas infrastruktur bot\n"
                f"• 📈 Akses ke statistik dan analitik sistem\n\n"
                f"<i>🌟 Anda memiliki kontrol penuh atas seluruh sistem!</i>"
            )
        else:
            msg = (
                f"{base_msg}"
                f"<b>ℹ️ INFORMASI PENGGUNA</b>\n\n"
                f"<i>Pengguna ini adalah Owner bot dengan kendali penuh atas sistem:</i>\n\n"
                f"• Memiliki akses tak terbatas ke seluruh fitur\n"
                f"• Dapat mengoperasikan bot tanpa batasan kuota\n"
                f"• Memiliki kontrol penuh atas konfigurasi dan pengaturan\n\n"
                f"<i>Status Owner memberikan hak administratif tertinggi dalam sistem.</i>"
            )
        
        mess = await sendMessage(message, msg)
        await asleep(120)
        await deleteMessage(mess)
        return
    
    if quota == 0:
        detail_msg = (
            "<b>⚠️ BELUM MEMILIKI KUOTA!</b>\n\n"
            "<i>Untuk menggunakan layanan bot ini, Anda memerlukan kuota. "
            "Kuota adalah 'kredit' yang diperlukan untuk mengunduh dan mengunggah file.</i>\n\n"
            "<b>📝 CARA MENDAPATKAN KUOTA:</b>\n"
            "• Klik tombol \"TAMBAH KUOTA\" di bawah ini\n"
            "• Lewati shortlink yang muncul (100% gratis)\n"
            "• Kuota 20GB akan otomatis ditambahkan\n"
            "• Kuota tidak akan pernah kadaluarsa\n\n"
            "<b>🌟 KEUNTUNGAN MEMILIKI KUOTA:</b>\n"
            "• Akses penuh ke semua fitur bot premium\n"
            "• Kemampuan mengunduh file tanpa batasan format\n"
            "• Dukungan prioritas dari admin\n"
            "• Kemampuan menjalankan tugas berukuran besar\n\n"
        )
    elif quota >= GB_20:
        detail_msg = (
            "<b>🔵 KUOTA ANDA BERLIMPAH!</b>\n\n"
            "<i>Selamat! Anda memiliki kuota yang sangat banyak. "
            "Anda dapat mengunduh file-file berukuran besar dengan leluasa.</i>\n\n"
            "<b>💡 TIPS PENGGUNAAN OPTIMAL:</b>\n"
            "• Manfaatkan fitur batch download untuk efisiensi\n"
            "• Gunakan fitur pencarian untuk menemukan file berkualitas\n"
            "• Jelajahi fitur kompresi untuk mengoptimalkan ruang\n"
            "• Hindari mengunduh file yang sama berulang kali\n\n"
            "<b>📊 ESTIMASI PENGGUNAAN:</b>\n"
            "• Kuota Anda cukup untuk mengunduh banyak film 4K\n"
            "• Ideal untuk penggunaan intensif jangka panjang\n"
            "• Cocok untuk transfer data dalam jumlah besar\n\n"
        )
    elif quota >= GB_15:
        detail_msg = (
            "<b>🟢 KUOTA ANDA SANGAT BAIK!</b>\n\n"
            "<i>Anda memiliki kuota yang cukup banyak. "
            "Bot dapat digunakan dengan optimal untuk berbagai kebutuhan.</i>\n\n"
            "<b>💡 TIPS MENGOPTIMALKAN KUOTA:</b>\n"
            "• Prioritaskan file penting terlebih dahulu\n"
            "• Manfaatkan fitur kompresi untuk file besar\n"
            "• Hindari mengunduh file berkualitas rendah\n"
            "• Periksa ukuran file sebelum mengunduh\n\n"
            "<b>📊 PERKIRAAN KAPASITAS:</b>\n"
            "• Kuota Anda cukup untuk 7-10 film HD\n"
            "• Ideal untuk penggunaan reguler mingguan\n"
            "• Pertimbangkan menambah kuota jika akan mengunduh file sangat besar\n\n"
        )
    elif quota >= GB_10:
        detail_msg = (
            "<b>🟡 KUOTA ANDA CUKUP!</b>\n\n"
            "<i>Dengan kuota sekitar 10-15GB, Anda masih memiliki ruang yang memadai. "
            "Namun, perlu berhati-hati dengan file berukuran besar.</i>\n\n"
            "<b>💡 SARAN PENGGUNAAN:</b>\n"
            "• Perhatikan ukuran file sebelum mengunduh\n"
            "• Gunakan fitur pemilihan file untuk torrent\n"
            "• Prioritaskan konten yang benar-benar Anda butuhkan\n"
            "• Pertimbangkan untuk menambah kuota dalam waktu dekat\n\n"
            "<b>⚙️ MANAJEMEN KUOTA:</b>\n"
            "• Hindari mengunduh beberapa file besar sekaligus\n"
            "• Gunakan fitur preview untuk mengecek file\n"
            "• Pantau penggunaan kuota dengan perintah /cek\n\n"
        )
    elif quota >= GB_5:
        detail_msg = (
            "<b>🟠 PERHATIAN! KUOTA TERBATAS!</b>\n\n"
            "<i>Kuota Anda sudah mulai terbatas. Dengan sisa 5-10GB, "
            "Anda perlu berhati-hati dalam menggunakan bot.</i>\n\n"
            "<b>⚠️ PERINGATAN PENGGUNAAN:</b>\n"
            "• File berukuran besar (>3GB) berisiko gagal diunduh\n"
            "• Gunakan fitur preview untuk memastikan kualitas\n"
            "• Hindari mengunduh file dalam jumlah banyak\n"
            "• Pertimbangkan opsi mirror daripada leech\n\n"
            "<b>🔄 REKOMENDASI TINDAKAN:</b>\n"
            "• Tambahkan kuota segera untuk menghindari gangguan\n"
            "• Selesaikan unduhan yang sudah berjalan\n"
            "• Gunakan fitur kompresi untuk file penting\n\n"
        )
    else:
        detail_msg = (
            "<b>🔴 PERINGATAN! KUOTA SANGAT RENDAH!</b>\n\n"
            "<i>Kuota Anda hampir habis! Dengan kuota kurang dari 5GB, "
            "kemampuan mengunduh file sangat terbatas.</i>\n\n"
            "<b>🚨 STATUS KRITIS:</b>\n"
            "• Kuota hampir habis dan sangat terbatas\n"
            "• Hanya file kecil (<2GB) yang dapat diunduh\n"
            "• Risiko tinggi kegagalan unduhan\n"
            "• Beberapa fitur mungkin tidak berfungsi optimal\n\n"
            "<b>⚡ TINDAKAN SEGERA:</b>\n"
            "• Tambahkan kuota SEKARANG melalui tombol di bawah\n"
            "• Hentikan semua unduhan yang tidak penting\n"
            "• Hindari memulai tugas baru hingga kuota ditambah\n\n"
        )
    
    if quota >= GB_20:
        status_indicator = "🔵 Status Kuota: Berlimpah"
    elif quota >= GB_15:
        status_indicator = "🟢 Status Kuota: Sangat Baik"
    elif quota >= GB_10:
        status_indicator = "🟡 Status Kuota: Cukup"
    elif quota >= GB_5:
        status_indicator = "🟠 Status Kuota: Terbatas"
    elif quota > 0:
        status_indicator = "🔴 Status Kuota: Kritis"
    else:
        status_indicator = "⚠️ Status Kuota: Tidak Ada"
    
    detail_msg += f"<b>{status_indicator}</b>\n\n"
    
    try:
        butt = await create_token(user_id)
        
        if user_id != from_user_id:
            if is_reply:
                detail_msg += f"<i>ℹ️ Tombol tambah kuota hanya dapat digunakan oleh <a href='tg://user?id={user_id}'>pengguna ini</a>.</i>"
            else:
                detail_msg += f"<i>ℹ️ Tombol tambah kuota hanya dapat digunakan oleh pengguna dengan ID: {user_id}.</i>"
        else:
            detail_msg += "<i>✨ Klik tombol di bawah untuk menambah kuota secara GRATIS:</i>"
        
        final_msg = base_msg + detail_msg
        mess = await sendMessage(message, final_msg, butt.build_menu(2))
    except Exception as e:
        LOGGER.error(f"Error creating token: {str(e)}")
        final_msg = base_msg + detail_msg
        mess = await sendMessage(message, final_msg)
    
    if mess:
        await asleep(120)
        await deleteMessage(mess)

#######################
## Commands Handlers ##
#######################

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
        ) & CustomFilters.owner,
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
