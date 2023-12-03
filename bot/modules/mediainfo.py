from aiohttp import ClientSession
from re import search as re_search
from shlex import split as ssplit
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd

from pyrogram.handlers import MessageHandler 
from pyrogram.filters import command

from bot import LOGGER, bot, config_dict
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.telegram_helper.button_build import ButtonMaker


async def gen_mediainfo(message, link=None, media=None, mmsg=None):
    temp_send = await sendMessage(message, '<i>⏳ Membuat media info...</i>')
    try:
        path = "Mediainfo/"
        if not await aiopath.isdir(path):
            await mkdir(path)
        if link:
            filename = re_search(".+/(.+)", link).group(1)
            des_path = ospath.join(path, filename)
            headers = {"user-agent":"Mozilla/5.0 (Linux; Android 12; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"}
            async with ClientSession() as session:
                async with session.get(link, headers=headers) as response:
                    async with aiopen(des_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(10000000):
                            await f.write(chunk)
                            break
        elif media:
            des_path = ospath.join(path, media.file_name)
            if media.file_size <= 50000000:
                await mmsg.download(ospath.join(getcwd(), des_path))
            else:
                async for chunk in bot.stream_media(media, limit=5):
                    async with aiopen(des_path, "ab") as f:
                        await f.write(chunk)
        stdout, _, _ = await cmd_exec(ssplit(f'mediainfo "{des_path}"'))
        tc = f"<h4>ℹ️ {ospath.basename(des_path)}</h4><br><br>"
        if len(stdout) != 0:
            tc += parseinfo(stdout)
    except Exception as e:
        LOGGER.error(e)
        await editMessage(temp_send, f"MediaInfo Stopped due to {str(e)}")
    finally:
        await aioremove(des_path)
    link_id = (await telegraph.create_page(title='Pikabot MediaInfo', content=tc))["path"]
    link_end = f"https://telegra.ph/{link_id}"
    buttons = ButtonMaker()
    buttons.ubutton("👁️ Lihat MediaInfo", f"{link_end}", "footer")
    button = buttons.build_menu(1)
    if message.from_user.username:
        uname = f'@{message.from_user.username}'
    else:
        uname = f'<code>{message.from_user.first_name}</code>'
    await editMessage(temp_send, f"<b>Hai {uname}, Klik tombol dibawah untuk melihat MediaInfo dari file anda.</b>", button)


section_dict = {'General': '🗒️', 'Video': '🎬', 'Audio': '🎵', 'Text': '📝', 'Menu': '📜'}
def parseinfo(out):
    tc = ''
    trigger = False
    for line in out.split('\n'):
        for section, emoji in section_dict.items():
            if line.startswith(section):
                trigger = True
                if not line.startswith('General'):
                    tc += '</pre><br>'
                tc += f"<h4>{emoji} {line.replace('Text', 'Subtitle')}</h4>"
                break
        if trigger:
            tc += '<br><pre>'
            trigger = False
        else:
            tc += line + '\n'
    tc += '</pre><br>'
    return tc


async def mediainfo(_, message):
    rply = message.reply_to_message
    help_msg = "<b>File atau Media tidak ditemukan, silahkan balas ke media yang akan digenerate mediainfo !</b>"
    if len(message.command) > 1 or rply and rply.text:
        link = rply.text if rply else message.command[1]
        return await gen_mediainfo(message, link)
    elif rply:
        if file := next(
            (
                i
                for i in [
                    rply.document,
                    rply.video,
                    rply.audio,
                    rply.voice,
                    rply.animation,
                    rply.video_note,
                ]
                if i is not None
            ),
            None,
        ):
            return await gen_mediainfo(message, None, file, rply)
        else:
            return await sendMessage(message, help_msg)
    else:
        return await sendMessage(message, help_msg)

bot.add_handler(MessageHandler(mediainfo, filters=command(BotCommands.MediaInfoCommand) & CustomFilters.authorized))