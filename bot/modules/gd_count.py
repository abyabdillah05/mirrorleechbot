from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot
from bot.helper.mirror_utils.gdrive_utils.count import gdCount
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task
from bot.helper.ext_utils.links_utils import is_gdrive_link
from .helper.ext_utils.common_utils import get_readable_file_size

@new_task
async def countNode(_, message):
    args = (
        message.text 
        or message.caption
    ).split()
    user = message.from_user or message.sender_chat
    if username := user.username:
        tag = f"@{username}"
    else:
        tag = message.from_user.mention

    link = args[1] if len(args) > 1 else ""
    if len(link) == 0 and (reply_to := message.reply_to_message):
        if reply_to.text:
            link = reply_to.text.split(maxsplit=1)[0].strip()
            if not is_gdrive_link(link) and reply_to.reply_markup:
                link = (
                    reply_to.reply_markup.inline_keyboard[0][0].url
                    or ""
                )
    if is_gdrive_link(link):
        msg = await sendMessage(message, f"<b>Menghitung :</b>\n<code>{link}</code>")
        name, mime_type, size, files, folders = await sync_to_async(
            gdCount().count, 
            link, 
            user.id
        )
        await deleteMessage(msg)
        if mime_type is None:
            await sendMessage(message, f"<b>{name}</b>")
            return
        msg = f"<b>Nama :</b> <code>{name}</code>"
        msg += f"\n\n<b>Ukuran :</b> <code>{get_readable_file_size(size)}</code>"
        msg += f"\n\n<b>Tipe :</b> <code>{mime_type}</code>"
        if mime_type == "Folder":
            msg += f"\n\n<b>Sub Folders :</b> <code>{folders}</code>"
            msg += f"\n\n<b>Files :</b> <code>{files}</code>"
        msg += f"\n\n<b>Oleh :</b> {tag}"
    else:
        msg = "<b>Kirim perintah dengan Link Google Drive atau balas Link Google Drive dengan perintah!</b>"
    await sendMessage(message, msg)


bot.add_handler(
    MessageHandler(
        countNode, filters=command(
            BotCommands.CountCommand
        ) & CustomFilters.authorized
    )
)
