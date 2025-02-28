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
    if id == OWNER_ID:
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
        inshort_api = "ccc8c7f71df7d79f80decd9e32084158e4c88eb6"
        link = f"https://inshorturl.com/api?api={inshort_api}&url={token_url}&format=text"
        try:
            with Session() as session:
                inshort_url = session.get(link, timeout=5).text
            butt = ButtonMaker()
            butt.ubutton("➕ TAMBAH KUOTA", inshort_url)
            butt.ubutton("❓ TUTORIAL", "https://t.me/pikachukocak2/106")
            return butt.build_menu(1)
        except:
            butt = ButtonMaker()
            butt.ubutton("❌ GAGAL MENDAPATKAN LINK", "https://www.youtube.com/watch?v=xvFZjo5PgG0&pp=ygUXVklERU8gWU9VVFVCRSBSSUNLIFJPTEw%3D")
            return butt.build_menu(1)
    except:
        return

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
            return f"<b>✅ Sukses tambah kuota 25GB, terimakasih :)</b>\n\n<b>Sisa kuota anda:</b> <code>{get_readable_file_size(new_quota)}</code></b>"
        else:
            return f"<b>❌Token salah, silahkan coba kembali.</b>\n\nPastikan anda mengklik tombol tambah kuota yang bot kirim untuk anda, bukan tombol punya orang."
    else:
        return f"<b>❌Token salah, silahkan coba kembali.</b>\n\nCoba gunakan perintah /cek lalu klik tombol tambah kuota yang bot kirim."

async def update_quota(id, size):
    try:
        if id in user_data and user_data[id].get("quota"):
            quota = user_data[id]["quota"]
            new_quota = quota - size
            update_user_ldata(id, "quota", new_quota)
            if DATABASE_URL:
                await DbManger().update_user_data(id)
    except Exception as e:
        LOGGER.error(e)