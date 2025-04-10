from uuid import uuid4

######################################
## Importing Variabels From Project ##
######################################

from bot import (bot,
                 user_generate_token,
                 user_data,
                 DATABASE_URL,
                 LOGGER,
                 OWNER_ID)
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.safelinku_utils import SafeLinkU
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.telegram_helper.button_build import ButtonMaker
from .helper.ext_utils.common_utils import (get_readable_file_size,
                                            get_readable_time)

######################################
## Quota Check | Credit @aenulrofik ##
######################################

## Modified Notification By Tg @WzdDizzyFlasherr ##

async def quota_check(listener, size):
    id = listener.user_id
    if id in user_data and user_data[id].get("is_sudo") or id == OWNER_ID:
        return
    if id in user_data and user_data[id].get("quota"):
        quota = user_data[id]["quota"]
    else:
        quota = 0
    if quota == 0:
        msg = (
            f"<b>⚠️ KUOTA TIDAK TERSEDIA!</b>\n\n"
            f"<b>Anda belum memiliki kuota untuk menjalankan tugas ini.</b>\n\n"
            f"<i>• Dapatkan kuota GRATIS dengan menekan tombol <b>TAMBAH KUOTA</b> di bawah ini</i>\n"
            f"<i>• Gunakan perintah /cek untuk melihat info kuota lengkap</i>\n\n"
            f"<b>💪 DUKUNG BOT INI:</b>\n"
            f"<i>Dengan menambah kuota melalui shortlink, Anda turut membantu pengembangan dan keberlanjutan bot ini. "
            f"Setiap klik Anda sangat berarti bagi kami!</i>"
        )
        butt = await create_token(id)
        return msg, butt.build_menu(2)
    elif size > quota:
        msg = (
            f"<b>⚠️ KUOTA TIDAK MENCUKUPI!</b>\n\n"
            f"<b>Detail:</b>\n"
            f"• Sisa Kuota Anda: <code>{get_readable_file_size(quota)}</code>\n"
            f"• Ukuran File: <code>{get_readable_file_size(size)}</code>\n\n"
            f"<i>💡 Tambahkan kuota GRATIS dengan menekan tombol di bawah:</i>\n\n"
            f"<b>❤️ DUKUNG BOT INI:</b>\n"
            f"<i>Dengan menambah kuota, Anda membantu kami menjaga server tetap aktif dan mengembangkan fitur baru. "
            f"Terima kasih atas dukungan Anda!</i>"
        )
        butt = await create_token(id)
        return msg, butt.build_menu(2)

#################################################
## Create Token For Quota | Credit @aenulrofik ##
#################################################

async def create_token(id):
    random_id = str(uuid4())
    user_generate_token[id] = random_id
    token_url = f"https://t.me/{bot.me.username}?start=token_{random_id}"
    
    shortened_url = await SafeLinkU.create_short_link(token_url)
    
    butt = ButtonMaker()
    butt.ubutton("➕ TAMBAH KUOTA", shortened_url, "header")
    butt.ubutton("❓ TUTORIAL", "https://t.me/DizzyStuffProject/67")
    butt.ubutton("💰 DONATE", "https://telegra.ph/Donate-and-Support-Us-03-21")
    butt.ubutton("🔧 REPORT", "tg://user?id=7146954165", "footer")
    return butt

#############################################
## Token Verification | Credit @aenulrofik ##
##############################################

## Modified Notification By Tg @WzdDizzyFlasherr ##
## Modify to improve code & add more features & adjusment 25gb to 20gb ##

async def token_verify(id, token):
    if id in user_data and user_data[id].get("quota"):
        quota = user_data[id]["quota"]
    else:
        quota = 0
        
    if id in user_generate_token:
        if user_generate_token[id] == token:
            user_generate_token.pop(id)
            added_quota = 20 * 1024 * 1024 * 1024
            new_quota = quota + added_quota
            update_user_ldata(id, "quota", new_quota)
            if DATABASE_URL:
                await DbManger().update_user_data(id)
                
            try:
                user = await bot.get_users(id)
                user_name = user.first_name
                user_username = user.username if user.username else "None"
                
                butt = ButtonMaker()
                butt.ubutton("🔍 Check User", f"tg://user?id={id}")
                
                await bot.send_message(
                    chat_id=OWNER_ID,
                    text=(
                        f"<b>💰 NOTIFIKASI PENDAPATAN!</b>\n\n"
                        f"<b>Ada yang berhasil menambah kuota melalui link SafelinkU!</b>\n\n"
                        f"<b>Informasi Pengguna:</b>\n"
                        f"• Nama: <code>{user_name}</code>\n"
                        f"• Username: <code>@{user_username}</code>\n"
                        f"• ID: <code>{id}</code>\n\n"
                        f"<b>Detail Kuota:</b>\n"
                        f"• Kuota Sebelumnya: <code>{get_readable_file_size(quota)}</code>\n"
                        f"• Kuota Ditambahkan: <code>{get_readable_file_size(added_quota)}</code>\n"
                        f"• Total Kuota Sekarang: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                        f"<i>💡 Untuk melihat riwayat pesan pengguna, klik tombol di bawah ini:</i>"
                    ),
                    reply_markup=butt.build_menu(2)
                )
            except Exception as e:
                LOGGER.error(f"Failed to send owner notification: {e}")
                
            bot_nickname = bot.me.first_name
            
            success_message = (
                f"<b>✅ PENAMBAHAN KUOTA BERHASIL!</b>\n\n"
                f"<b>Detail Penambahan:</b>\n"
                f"• Kuota Sebelumnya: <code>{get_readable_file_size(quota)}</code>\n"
                f"• Kuota Ditambahkan: <code>{get_readable_file_size(added_quota)}</code>\n"
                f"• Total Kuota Sekarang: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                f"<b>Informasi Penting:</b>\n"
                f"• Kuota akan berkurang saat mengunduh file\n"
                f"• Kuota tidak memiliki batas waktu kadaluarsa\n"
                f"• Untuk melihat sisa kuota: gunakan /cek\n\n"
                f"<i>🙏 Terima kasih telah mendukung bot ini! Happy Downloading :v.</i>\n\n"
                f"<code>Powered by {bot_nickname}</code>"
            )
            
            butt = await create_token(id)
            return success_message, butt.build_menu(2)

####################################################################
## Update Quota & Send Notification To Owner | Credit @aenulrofik ##
####################################################################

## Modified Notification By Tg @WzdDizzyFlasherr ##

async def update_quota(id, size):
    try:
        if id in user_data and user_data[id].get("quota"):
            quota = user_data[id]["quota"]
            new_quota = quota - size
            update_user_ldata(id, "quota", new_quota)
            if DATABASE_URL:
                await DbManger().update_user_data(id)
                
            if size > 5 * 1024 * 1024 * 1024:
                try:
                    user = await bot.get_users(id)
                    user_name = user.first_name
                    user_username = user.username if user.username else "None"
                    
                    butt = ButtonMaker()
                    butt.ubutton("🔍 Check User", f"tg://user?id={id}")
                    
                    await bot.send_message(
                        chat_id=OWNER_ID,
                        text=(
                            f"<b>📊 PENGGUNAAN KUOTA BESAR</b>\n\n"
                            f"<b>Pengguna ini menggunakan kuota dalam jumlah signifikan:</b>\n\n"
                            f"<b>Informasi Pengguna:</b>\n"
                            f"• Nama: <code>{user_name}</code>\n"
                            f"• Username: <code>@{user_username}</code>\n"
                            f"• ID: <code>{id}</code>\n\n"
                            f"<b>Detail Penggunaan:</b>\n"
                            f"• Kuota Sebelumnya: <code>{get_readable_file_size(quota)}</code>\n"
                            f"• Kuota Terpakai: <code>{get_readable_file_size(size)}</code>\n"
                            f"• Kuota Tersisa: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                            f"<i>💡 Klik tombol di bawah untuk melihat profil pengguna.</i>"
                        ),
                        reply_markup=butt.build_menu(2)
                    )
                except Exception as e:
                    LOGGER.error(f"Failed to send quota usage notification: {e}")
    except Exception as e:
        LOGGER.error(e)

## Thanks to @aenulrofik for this feature ##