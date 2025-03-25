from bot import bot, user_generate_token, user_data, DATABASE_URL, LOGGER, OWNER_ID
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManger
from requests import Session
from bot.helper.ext_utils.status_utils import get_readable_file_size
from uuid import uuid4
from bot.helper.ext_utils.bot_utils import update_user_ldata

async def quota_check(listener, size):
    id = listener.user_id
    if id in user_data and user_data[id].get("is_sudo") or id == OWNER_ID:
        return
    if id in user_data and user_data[id].get("quota"):
        quota = user_data[id]["quota"]
    else:
        quota = 0
    if quota == 0:
        msg = f"<b>⚠️ Untuk mensupport bot ini, silahkan isi kuota dulu (GRATIS) dengan menekan tombol dibawah untuk mulai proses mirror/leech !!</b>\n\n<i>Gunakan perintah /cek untuk melihat sisa kuota anda</i>"
        butt = await create_token(id)
        return msg, butt
    elif size > quota:
        msg = f"<b>Kuota download anda tidak cukup untuk tugas ini.</b>\n\n<b>Sisa kuota anda:</b> <code>{get_readable_file_size(quota)}</code>\n<b>Ukuran tugas ini:</b> <code>{get_readable_file_size(size)}</code>\n\n<i>⚠️ Silahkan tambah kuota anda dengan cara klik tombol di bawah ini :)</i>"
        butt = await create_token(id)
        return msg, butt


async def create_token(id):
    try:
        random_id = str(uuid4())
        user_generate_token[id] = random_id
        token_url = f"https://t.me/{bot.me.username}?start=token_{random_id}"
        safelinku_api = "ed0bb713b96184949787aefd37e0db0d889cb3ed"
        
        try:
            with Session() as session:
                headers = {
                    "Authorization": f"Bearer {safelinku_api}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "url": token_url
                }
                
                response = session.post(
                    "https://safelinku.com/api/v1/links",
                    headers=headers,
                    json=payload,
                    timeout=8
                )
                
                if response.status_code == 201:
                    shortened_url = response.json().get("url")
                    butt = ButtonMaker()
                    butt.ubutton("➕ TAMBAH KUOTA", shortened_url)
                    butt.ubutton("❓ TUTORIAL", "https://t.me/pikachukocak2/106")
                    butt.ubutton("💰 DONATE", "https://telegra.ph/Donate-and-Support-Us-03-21")
                    return butt.build_menu(1)
                else:
                    raise Exception(f"API returned status {response.status_code}")
                    
        except Exception as e:
            LOGGER.error(f"Error shortening URL: {str(e)}")
            butt = ButtonMaker()
            butt.ubutton("❌ GAGAL MENDAPATKAN LINK", "https://www.youtube.com/watch?v=xvFZjo5PgG0&pp=ygUXVklERU8gWU9VVFVCRSBSSUNLIFJPTEw%3D")
            return butt.build_menu(1)
    except Exception as outer_e:
        LOGGER.error(f"Token creation failed: {str(outer_e)}")
        return None

async def token_verify(id, token):
    if id in user_data and user_data[id].get("quota"):
        quota = user_data[id]["quota"]
    else:
        quota = 0
        
    if id in user_generate_token:
        if user_generate_token[id] == token:
            user_generate_token.pop(id)
            new_quota = quota + 25 * 1024 * 1024 * 1024
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
                        f"<b>💰 Notifikasi Pendapatan!</b>\n\n"
                        f"<b>Ada yang berhasil menambah kuota melalui link SafelinkU!</b>\n\n"
                        f"<b>Informasi Pengguna:</b>\n"
                        f"• Nama: <code>{user_name}</code>\n"
                        f"• Username: <code>@{user_username}</code>\n"
                        f"• ID: <code>{id}</code>\n\n"
                        f"<b>Detail Kuota:</b>\n"
                        f"• Kuota Tambahan: <code>25 GB</code>\n"
                        f"• Total Kuota Sekarang: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                        f"<i>💡 Untuk melihat riwayat pesan pengguna, klik tombol di bawah ini:</i>"
                    ),
                    reply_markup=butt.build_menu(1)
                )
            except Exception as e:
                LOGGER.error(f"Failed to send owner notification: {e}")
                
            success_message = (
                f"<b>✅ PENAMBAHAN KUOTA BERHASIL!</b>\n\n"
                f"<b>Detail Kuota:</b>\n"
                f"• Kuota Ditambahkan: <code>25 GB</code>\n"
                f"• Total Kuota Sekarang: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                f"<b>Informasi Penting:</b>\n"
                f"• Kuota anda akan berkurang saat melakukan download\n"
                f"• Kuota tidak akan hangus/expired\n"
                f"• Untuk melihat sisa kuota, gunakan perintah /cek\n\n"
                f"<i>Terima kasih telah mendukung bot ini! Selamat menggunakan layanan kami.</i>"
            )
            
            return success_message
        else:
            error_message = (
                f"<b>❌ TOKEN TIDAK VALID</b>\n\n"
                f"<b>Kemungkinan Penyebab:</b>\n"
                f"• Anda menggunakan link orang lain\n"
                f"• Token sudah kadaluarsa\n"
                f"• Token sudah digunakan sebelumnya\n\n"
                f"<b>Solusi:</b>\n"
                f"• Pastikan anda mengklik tombol \"TAMBAH KUOTA\" yang dikirimkan khusus untuk anda\n"
                f"• Gunakan perintah /cek untuk mendapatkan link baru\n"
                f"• Jangan gunakan link dari pengguna lain\n\n"
                f"<i>Jika masalah berlanjut, silahkan hubungi admin.</i>"
            )
            
            return error_message
    else:
        guidance_message = (
            f"<b>❌ TOKEN TIDAK DITEMUKAN</b>\n\n"
            f"<b>Kemungkinan Penyebab:</b>\n"
            f"• Token telah expired\n"
            f"• Token telah digunakan\n"
            f"• Token tidak valid\n\n"
            f"<b>Cara Mendapatkan Token Baru:</b>\n"
            f"1. Gunakan perintah /cek\n"
            f"2. Klik tombol \"TAMBAH KUOTA\" yang dikirimkan oleh bot\n"
            f"3. Selesaikan proses di link yang disediakan\n\n"
            f"<i>Pastikan untuk menyelesaikan proses dalam waktu 30 menit.</i>"
        )
        
        return guidance_message

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
                            f"<b>📊 Notifikasi Penggunaan Kuota Besar</b>\n\n"
                            f"<b>Pengguna ini menggunakan kuota dalam jumlah besar:</b>\n\n"
                            f"<b>Informasi Pengguna:</b>\n"
                            f"• Nama: <code>{user_name}</code>\n"
                            f"• Username: <code>@{user_username}</code>\n"
                            f"• ID: <code>{id}</code>\n\n"
                            f"<b>Detail Penggunaan:</b>\n"
                            f"• Kuota Terpakai: <code>{get_readable_file_size(size)}</code>\n"
                            f"• Kuota Tersisa: <code>{get_readable_file_size(new_quota)}</code>\n\n"
                            f"<i>💡 Klik tombol di bawah untuk melihat profil pengguna.</i>"
                        ),
                        reply_markup=butt.build_menu(1)
                    )
                except Exception as e:
                    LOGGER.error(f"Failed to send quota usage notification: {e}")
    except Exception as e:
        LOGGER.error(e)
