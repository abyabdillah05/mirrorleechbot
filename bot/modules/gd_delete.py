from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot, LOGGER
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.gdrive_utils.delete import gdDelete
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task
from bot.helper.ext_utils.links_utils import is_gdrive_link


@new_task
async def deletefile(_, message):
    args = (
        message.text 
        or message.caption
    ).split()
    user = message.from_user or message.sender_chat
    if len(args) > 1:
        link = args[1]
    elif reply_to := message.reply_to_message:
        if reply_to.text:
            link = reply_to.text.split(maxsplit=1)[0].strip()
            if not is_gdrive_link(link) and reply_to.reply_markup:
                link = (
                    reply_to.reply_markup.inline_keyboard[0][0].url
                    or ""
                )
    else:
        link = ""
    if is_gdrive_link(link):
        LOGGER.info(link)
        msg = await sync_to_async(
            gdDelete().deletefile, 
            link, 
            user.id
        )
    else:
        msg = "Kirim perintah dengan Link Google Drive atau balas Link Google Drive dengan perintah!"
    reply_message = await sendMessage(message, f"<b>{msg}</b>")
    await auto_delete_message(message, reply_message)


bot.add_handler(
    MessageHandler(
        deletefile,
        filters=command(
            BotCommands.DeleteCommand
        ) & CustomFilters.authorized,
    )
)
