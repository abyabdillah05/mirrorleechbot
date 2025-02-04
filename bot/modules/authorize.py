from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import user_data, DATABASE_URL, bot, LOGGER
from bot.helper.telegram_helper.message_utils import sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.ext_utils.pikachu_utils import create_token


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
    if id_ not in user_data or user_data[id_].get("is_auth"):
        update_user_ldata(id_, "is_auth", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "😉 <b>Berhasil diunautorisasi!</b>"
    else:
        msg = "🙃 <b>Sudah diunautorisasi!</b>"
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
    if id_ and id_ not in user_data or user_data[id_].get("is_sudo"):
        update_user_ldata(id_, "is_sudo", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "😉 <b>Berhasil diturunkan dari Sudo User!</b>"
    else:
        msg = "<b>Berikan ID atau balas pesan dari User yang ingin diturunkan dari Sudo User!</b>"
    await sendMessage(message, msg)

async def check_quota(_, message):
    self = False
    msg = message.text.split()
    if len(msg) > 1:
        try:
            user_id = int(msg[1].strip())
        except ValueError:
            await sendMessage(message, "❌ <b>Format ID tidak valid.</b>")
            return
    else:
        self = True
        user_id = message.from_user.id
    
    if user_id in user_data and user_data[user_id].get("quota", 0):
        quota = user_data[user_id].get("quota", 0)
    else:
        quota = 0
    if self:
        butt = None
        msg = f"📊 <b>Kuota Mirror/Leech anda saat ini:</b><code> {get_readable_file_size(quota)}</code>\n\n"
        
        if quota < 20 * 1024:
            msg += "<i>Silahkan tambah kuota anda dengan cara klik tombol di bawah ini :)</i>"
            try:
                butt = await create_token(user_id)
            except Exception as e:
                LOGGER.error(str(e))
        else:
            msg += "<i>Kuota anda masih tersisa banyak, semoga harimu senin terus :)</i>"
        
        await sendMessage(message, msg, butt)
    else:
        await sendMessage(
            message, 
            f"📊 <b>Kuota Mirror/Leech user {user_id} saat ini:</b><code> {get_readable_file_size(quota)}</code>\n\n"
            "<i>Jangan lupa bahagia :)</i>"
        )
bot.add_handler(
    MessageHandler(
        authorize, 
        filters=command(
            BotCommands.AuthorizeCommand
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        unauthorize,
        filters=command(
            BotCommands.UnAuthorizeCommand
        ) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        addSudo, 
        filters=command(
            BotCommands.AddSudoCommand
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        removeSudo, 
        filters=command(
            BotCommands.RmSudoCommand
        ) & CustomFilters.sudo
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
