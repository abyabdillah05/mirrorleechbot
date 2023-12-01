from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
import re

from bot import bot, LOGGER
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.gdrive_utlis.rename import gdRename
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task
from bot.helper.ext_utils.links_utils import is_gdrive_link


@new_task
async def renamefile(_, message):
    args = message.text.split(maxsplit=2)
    if len(args) > 2:
        link = args[1]
        new_name = args[2]
    elif reply_to := message.reply_to_message:
        link, new_name = re.split(r'\s+', reply_to.text.strip(), maxsplit=1)
    else:
        link, new_name = '', ''
    
    if is_gdrive_link(link):
        LOGGER.info(link)
        msg = await sync_to_async(gdRename().renamefile, link, new_name, message.from_user)
    else:
        msg = '<b>Kirim perintah dengan Link Google Drive dan nama baru untuk filenya!</b>\n\n<b>Contoh:</b> <code>/rename link_gdrive nama_baru.mp4</code> (jangan lupa tambahkan juga ekstensi untuk nama baru, contoh jika rename file zip, tambahkan juga .zip diakhir nama baru, menjadi nama_baru.zip)'
    
    reply_message = await sendMessage(message, msg)
    await auto_delete_message(message, reply_message)


bot.add_handler(MessageHandler(renamefile, filters=command(
    BotCommands.RenameCommand) & CustomFilters.authorized))