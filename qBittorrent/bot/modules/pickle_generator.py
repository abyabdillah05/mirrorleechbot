import os
import pickle

from asyncio import sleep as asleep
from aiofiles.os import remove as aioremove, path as aiopath, mkdir, makedirs

######################################################
## Import Main Libraries From Pyrogram & Google API ##
######################################################

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from pyrogram import (filters)
from pyrogram.enums import ChatType
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

####################################
## Imports Variables From Project ##
####################################

from bot import LOGGER, DATABASE_URL, bot
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata, new_task
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      deleteMessage,
                                                      editMessage)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.safelinku_utils import SafeLinkU

########################
## Required Variables ##
########################

## You can change client_id and client_secret to your own ##
## You can get client_id and client_secret from https://console.cloud.google.com/apis/credentials?project=drive-api-quickstart ##
## Make sure to enable Google Drive API in your project ##

OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
client_id = "281074057431-i80g6t8u4mce5khh1bhlqjd0b3sssfvg.apps.googleusercontent.com"
client_secret = "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"

#######################################
## Get Token | Credit By @aenulrofik ##
#######################################

## Modified By Tg @WzdDizzyFlasherr ##
## This is a modified version of the original code to improve readability and maintainability. ##

@new_task
async def get_token(client, message):
    private = bool(message.chat.type == ChatType.PRIVATE)
    if not private:
        butt = ButtonMaker()
        butt.ubutton("💬 CHAT PRIBADI", f"https://t.me/{bot.me.username}?start=gettoken")
        await sendMessage(message, "⚠️ <b>PERHATIAN!</b>\n\nPerintah ini hanya bisa digunakan dalam chat pribadi untuk alasan keamanan. Silakan klik tombol di bawah untuk melanjutkan di chat pribadi dengan bot.", butt.build_menu(1))
        return
    uid = message.from_user.id
    path = f"tokens/{uid}/"
    pickle_path = f"{path}/token.pickle"
    await makedirs(path, exist_ok=True)
    try:
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost:1"],
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            OAUTH_SCOPE,
            redirect_uri='http://localhost:1'
        )
        
        auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        
        shortened_auth_url = await SafeLinkU.create_short_link(auth_url)
        
        msg = f"<b>🌟 BUAT TOKEN GOOGLE DRIVE</b>\n\n"
        msg += f"<b>Halo! Ikuti panduan berikut untuk mendapatkan token Google Drive Anda:</b>\n\n"
        msg += f"1️⃣ <b>Klik tombol</b> \"<b>MULAI OTORISASI</b>\" di bawah\n"
        msg += f"2️⃣ <b>Masuk</b> ke akun Google Drive yang ingin Anda gunakan\n"
        msg += f"3️⃣ <b>Centang semua izin</b> yang diminta dan klik \"<b>Lanjutkan</b>\"\n"
        msg += f"4️⃣ Anda akan dialihkan ke halaman dengan tulisan \"<b>This site can't be reached</b>\"\n"
        msg += f"5️⃣ <b>Salin seluruh URL</b> dari browser Anda (mulai dari https://)\n"
        msg += f"6️⃣ <b>Kembali ke chat ini</b> dan kirim URL tersebut\n\n"
        msg += f"<i>⏱️ Sesi otorisasi ini akan berakhir dalam 5 menit</i>"
        
        butt = ButtonMaker()
        butt.ubutton("🔑 MULAI OTORISASI", shortened_auth_url)
        butt.ubutton("📝 TUTORIAL LENGKAP", "https://t.me/DizzyStuffProject")
        butts = butt.build_menu(1)
        
        try:
            ask = await sendMessage(message, msg, butts)
            respon = await bot.listen(
                filters=filters.text & filters.user(uid), timeout=300
            )
        except:
            await deleteMessage(ask)
            raise Exception("⌛ Waktu habis! Silakan coba lagi dengan perintah /gettoken")
        try:
            code = respon.text.split('code=')[1].split('&')[0]
        except IndexError:
            await deleteMessage(ask)
            raise Exception("❌ Format URL tidak valid! Pastikan Anda menyalin URL lengkap dari browser. URL harus mengandung 'code='")
        await respon.delete()
        await editMessage(ask, f"🔄 <b>Memproses token Anda...</b>\n\n<i>Mohon tunggu sebentar, sistem sedang memverifikasi kode otorisasi.</i>")
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            with open(pickle_path, "wb") as token:
                pickle.dump(credentials, token)
            caption = "✅ <b>TOKEN GOOGLE DRIVE BERHASIL DIBUAT!</b>\n\n"
            caption += f"<b>📋 DETAIL TOKEN:</b>\n\n"
            caption += f"<b>🆔 Client ID:</b>\n<code>{client_id}</code>\n\n"
            caption += f"<b>🔐 Client Secret:</b>\n<code>{client_secret}</code>\n\n"
            caption += f"<b>🔄 Refresh Token:</b>\n<code>{credentials.refresh_token}</code>\n\n"
            caption += f"<b>⚠️ PENTING:</b> Jangan bagikan token ini dengan siapapun! Token ini memberikan akses ke Google Drive Anda."
            await message.reply_document(
                document=pickle_path,
                caption=caption,
                )
        except Exception as e:
            raise Exception(f"❌ Gagal memverifikasi kode: {str(e)}")
        await deleteMessage(ask)
    except Exception as e:
        await sendMessage(message, f"<b>❌ ERROR:</b> {e}")
    finally:
        if os.path.exists(pickle_path):
            os.remove(pickle_path)

#######################################
## Gen Token | Credit By @aenulrofik ##
#######################################

## Modified By Tg @WzdDizzyFlasherr ##
## This is a modified version of the original code to improve readability and maintainability. ##

async def gen_token(client, message):
    uid = message.from_user.id
    
    private = bool(message.chat.type == ChatType.PRIVATE)
    if not private:
        butt = ButtonMaker()
        butt.ubutton("💬 CHAT PRIBADI", f"https://t.me/{bot.me.username}?start=gentoken")
        await sendMessage(message, "⚠️ <b>PERHATIAN!</b>\n\nPerintah ini hanya bisa digunakan dalam chat pribadi untuk alasan keamanan. Silakan klik tombol di bawah untuk melanjutkan di chat pribadi dengan bot.", butt.build_menu(1))
        return
    
    path = f"tokens/"
    pickle_path = f"{path}{uid}.pickle"
    await makedirs(path, exist_ok=True)
    async def generate_token(message):
        if os.path.exists(pickle_path):
            with open(pickle_path, "rb") as f:
                credentials = pickle.load(f)
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                return None, "Token google drive anda sudah ada dan sudah diperbaharui. \n\nUntuk hapus token yang ada, silahkan gunakan Usetting - Gdrive Tools - token.pickle"
        else:
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost:1"],
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                OAUTH_SCOPE,
                redirect_uri='http://localhost:1'
            )
            auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true')
            
            shortened_auth_url = await SafeLinkU.create_short_link(auth_url)
            
            msg = f"<b>Ikuti langkah dibawah untuk generate token google drive:</b>\n\n• Klik link dibawah untuk autorisasi google drive\n"
            msg += f"• Pilih akun googledrive yang akan digunakan untuk mirroring.\n"
            msg += f"• Klik Lanjutkan dan anda akan dibawa ke halaman error.\n"
            msg += f"• Silahkan salin semua alamat url di halaman error tersebut dan kirim ke bot.\n"
            msg += f"\n<i>⏰ Timeout 5 menit</i>\n"
            butt = ButtonMaker()
            butt.ubutton("Autorisasi Google Drive", shortened_auth_url)
            butts = butt.build_menu(1)
            try:
                ask = await sendMessage(message, msg, butts)
                respon = await bot.listen(
                        filters=filters.text & filters.user(uid), timeout=300
                        )
            except:
                await deleteMessage(ask)
                return None, "Waktu habis, tidak ada respon dari pengguna, silahkan coba lagi."
            try:
                code = respon.text.split('code=')[1].split('&')[0]
            except IndexError:
                await deleteMessage(ask)
                return None, "Format URL tidak valid. Pastikan Anda menyalin seluruh URL."
            await respon.delete()
            await editMessage(ask, f"Memferifikasi kode anda...")
            try:
                flow.fetch_token(code=code)
                credentials = flow.credentials
                with open(pickle_path, "wb") as token:
                    pickle.dump(credentials, token)
                await deleteMessage(ask)
                return credentials, None
            except Exception as e:
                await deleteMessage(ask)
                return None, f"Gagal saat memverifikasi kode: {str(e)}"
    try:
        credentials, error_message = await generate_token(message)
        
        if error_message:
            await sendMessage(message, f"<b>⛔ ERROR:</b> {error_message}")
            return
            
        if credentials and os.path.exists(pickle_path):
            wait = await sendMessage(message, "<b>⌛ Proses setup google drive anda...</b>")
            def create_folder():
                try:
                    auth = build("drive", "v3", credentials=credentials, cache_discovery=False)
                    file_metadata = {
                        "name": f"MirrorFolder oleh {bot.me.username}",
                        "description": f"Uploaded by {bot.me.username}",
                        "mimeType": "application/vnd.google-apps.folder",
                    }
                    file = (
                        auth.files()
                        .create(body=file_metadata, supportsAllDrives=True)
                        .execute()
                    )
                    folder_id = file.get("id")
                    LOGGER.info(f"Sukses membuat Folder id: {folder_id}")
                    permissions = {
                        "role": "reader",
                        "type": "anyone",
                        "value": None,
                        "withLink": True,
                    }
                    (auth.permissions()
                    .create(fileId=folder_id, body=permissions, supportsAllDrives=True)
                    .execute())
                    LOGGER.info(f"Sukses membuat Permission id: {folder_id}")
                    return folder_id
                except Exception as e:
                    LOGGER.error(f"Error membuat folder: {str(e)}")
                    return
            update_user_ldata(uid, "token_pickle", f"tokens/{uid}.pickle")
            if DATABASE_URL:
                await DbManger().update_user_doc(uid, "token_pickle", pickle_path)
            if folder_id := create_folder():
                update_user_ldata(uid, "gdrive_id", f"mtp:{folder_id}")
                update_user_ldata(uid, "default_upload", "gd")
                if DATABASE_URL:
                    await DbManger().update_user_data(uid)
            msg = f"✅ <b>Token google drive anda berhasil dibuat dan dimasukkan ke usetting</b>\n\n"
            if folder_id:
                msg += f"• <b>Nama Folder:</b> <code>MirrorFolder oleh {bot.me.username}</code>\n"
                msg += f"• <b>Gdrive_Id:</b> <code>{folder_id}</code>\n"
                msg += f"• <b>Default Upload:</b> <code>Google Drive</code>\n\n"
                msg += f"✅ <b>Semua proses selesai, gunakan perintah /{BotCommands.MirrorCommand[0]} untuk memulai proses mirror ke google drive anda.</b> !"
            else:
                msg += f"❌ <b>Terjadi kesalahan, saat setup folder di akun anda, silahkan setup manual dengan mengisi gdrive_id di usetting dengan format:<blockquote><code>mtp:gdrive_id</code></blockquote> !</b>"
            await editMessage(wait, msg)
        else:
            await sendMessage(message, f"❌ <b>Token google drive anda gagal dibuat, silahkan coba lagi</b>")
    except Exception as e:
        await sendMessage(message, f"<b>⛔ ERROR:</b> {e}")

##########################
## Handler for commands ##
##############################

bot.add_handler(
    MessageHandler(
        get_token, 
        filters=command(
            BotCommands.GetTokenCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        gen_token, 
        filters=command(
            BotCommands.GenTokenCommand
        ) & CustomFilters.authorized
    )
)