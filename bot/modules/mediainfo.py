import re
import os
import json
import httpx
import asyncio
import requests
import subprocess
from async_timeout import timeout 
from urllib.parse import unquote
from pyrogram.handlers import MessageHandler 
from pyrogram.filters import command

from bot import bot
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from pyrogram.types import Message
from bot.helper.ext_utils.mediainfo_utils import *

async def ddl_mediainfo(message, url, isRaw):
    """
    Generates Mediainfo from a Direct Download Link.
    """

    mess = await sendMessage(message,
        "⌛️ Membuat mediainfo dari link anda, silahkan tunggu...")
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<code>{message.from_user.first_name}</code>'
    try:
        filename = re.search(".+/(.+)", url).group(1)
        if len(filename) > 60:
            filename = filename[-60:]

        rand_str = randstr()
        download_path = f"downloads/{rand_str}_{filename}"
        client = httpx.AsyncClient()  
        headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 12; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"
        }
        
        async with timeout(15):
            async with client.stream("GET", url, headers=headers) as response:
                async for chunk in response.aiter_bytes(10000000):
                    with open(download_path, "wb") as file:
                        file.write(chunk)
                    break
                    
        mediainfo = await async_subprocess(f"mediainfo {download_path}")
        mediainfo_json = await async_subprocess(
            f"mediainfo {download_path} --Output=JSON")
        mediainfo_json = json.loads(mediainfo_json)

        filesize = requests.head(url).headers.get("content-length")
        lines = mediainfo.splitlines()

        for i in range(len(lines)):
            if "Complete name" in lines[i]:
                lines[i] = re.sub(r": .+", ": " + unquote(filename), lines[i])

            elif "File size" in lines[i]:
                lines[i] = re.sub(
                    r": .+", ": " + get_readable_bytes(float(filesize)), lines[i])

            elif (
                "Overall bit rate" in lines[i]
                and "Overall bit rate mode" not in lines[i]
            ):
                duration = float(mediainfo_json["media"]["track"][0]["Duration"])
                bitrate = get_readable_bitrate(float(filesize) * 8 / (duration * 1000))
                lines[i] = re.sub(r": .+", ": " + bitrate, lines[i])

            elif "IsTruncated" in lines[i] or "FileExtension_Invalid" in lines[i]:
                lines[i] = ""

        with open(f"{download_path}.txt", "w") as f:
            f.write("\n".join(lines))

        if isRaw:
            await message.reply_document(
                f"{download_path}.txt", caption=f"<b>Nama File: `{filename}`")
            os.remove(f"{download_path}.txt")
            os.remove(f"{download_path}")

        with open(f"{download_path}.txt", "r+") as file:
            content = file.read()

        output = mediainfo_paste(text=content, title=filename)
        buttons = ButtonMaker()
        buttons.ubutton("👁️ Lihat MediaInfo", f"{output}", "footer")
        button = buttons.build_menu(1)
        await sendMessage(message, f"<b>Hai {uname}, Klik tombol dibawah untuk melihat MediaInfo dari file anda.</b>", button)

        os.remove(f"{download_path}.txt")
        os.remove(f"{download_path}")

    except asyncio.TimeoutError:
        return await sendMessage(message,
            f"Hai {uname}, Gagal membuat mediainfo dari link anda, link terlalu lama merespon :(" )
               	
    except Exception as error:
        return await sendMessage(message,
            f"Hai {uname}, Terjadi kesalahan saat mencoba membuat mediainfo dari link yang anda berikan.")
    finally:
        await deleteMessage(mess)

async def telegram_mediainfo(client, message, isRaw):
    """
    Generates Mediainfo from a Telegram File.
    """
    mess = await sendMessage(message,
        "⌛️ Membuat mediainfo dari media anda, silahkan tunggu...")
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<code>{message.from_user.first_name}</code>'
    try:
        message = message.reply_to_message
        if message.text:
            return await sendMessage(message,
                "Balas ke media yang mau anda generate bukan text, hadeh")

        if message.media.value == "video":
            media = message.video

        elif message.media.value == "audio":
            media = message.audio

        elif message.media.value == "document":
            media = message.document

        elif message.media.value == "voice":
            media = message.voice

        else:
            return await sendMessage(message,
                "Media yang anda coba anda generate, belum disupport.")

        filename = str(media.file_name)
        size = media.file_size

        rand_str = randstr()
        download_path = f"downloads/{rand_str}_{filename}"

        if int(size) <= 50000000:
            await message.download(os.path.join(os.getcwd(), download_path))

        else:
            async for chunk in client.stream_media(message, limit=5):
                with open(download_path, "ab") as f:
                    f.write(chunk)

        mediainfo = await async_subprocess(f"mediainfo '{download_path}'")
        mediainfo_json = await async_subprocess(
            f"mediainfo '{download_path}' --Output=JSON")
        mediainfo_json = json.loads(mediainfo_json)

        readable_size = get_readable_bytes(size)
        lines = mediainfo.splitlines()
        for i in range(len(lines)):
            if "Complete name" in lines[i]:
                lines[i] = re.sub(r": .+", ": " + unquote(filename), lines[i])

            if "File size" in lines[i]:
                lines[i] = re.sub(r": .+", ": " + readable_size, lines[i])

            elif (
                "Overall bit rate" in lines[i]
                and "Overall bit rate mode" not in lines[i]
            ):
                duration = float(mediainfo_json["media"]["track"][0]["Duration"])
                bitrate_kbps = (size * 8) / (duration * 1000)
                bitrate = get_readable_bitrate(bitrate_kbps)
                lines[i] = re.sub(r": .+", ": " + bitrate, lines[i])

            elif "IsTruncated" in lines[i] or "FileExtension_Invalid" in lines[i]:
                lines[i] = ""

        remove_N(lines)
        with open(f"{download_path}.txt", "w") as f:
            f.write("\n".join(lines))

        if isRaw:
            await message.reply_document(
                f"{download_path}.txt", caption=f"<b>Nama File:</b> `{filename}`")
            os.remove(f"{download_path}.txt")
            os.remove(f"{download_path}")

        with open(f"{download_path}.txt", "r+") as file:
            content = file.read()

        output = mediainfo_paste(text=content, title=filename)
        buttons = ButtonMaker()
        buttons.ubutton("👁️ Lihat MediaInfo", f"{output}", "footer")
        button = buttons.build_menu(1)
        await sendMessage(message, f"<b>Hai {uname}, Klik tombol dibawah untuk melihat MediaInfo dari file anda.</b>", button)

        os.remove(f"{download_path}.txt")
        os.remove(download_path)

    except Exception as error:
        return await sendMessage(message,
            f"Hai {uname}, Terjadi kesalahan saat membuat mediainfo dari media anda :(\n\n<code>{error}</code>")
    finally:
        await deleteMessage(mess)

async def mediainfo(client, message: Message):
    mediainfo_usage = f"<b>Generate media info dari media telegram atau dari direct link.</b> \n\nBalas pesan media dengan perintah <code>/{BotCommands.MediaInfoCommand[0]}</code> atau perintah disertai link."

    if message.reply_to_message:
        isRaw = False
        if len(message.command) > 1:
            user_input = message.text.split(None, 1)[1]
            isRaw = bool(re.search(r"(-|--)r", user_input))
        return await telegram_mediainfo(client, message, isRaw)

    if len(message.command) < 2:
        return await sendMessage(message, mediainfo_usage)

    user_input = message.text.split(None, 1)[1]
    isRaw = bool(re.search(r"(-|--)r", user_input))

    if url_match := re.search(
        r"https?://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])",
        user_input,
    ):
        url = url_match.group(0)
        return await ddl_mediainfo(message, url, isRaw)
    return await sendMessage(message, "Link ini tidak disupport, silahkan periksa kembali link anda.")

bot.add_handler(
    MessageHandler(
        mediainfo,
        filters=command(
            BotCommands.MediaInfoCommand)
            & CustomFilters.authorized
        )
    )
