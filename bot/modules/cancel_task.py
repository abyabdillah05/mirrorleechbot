from asyncio import sleep
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import task_dict, bot, task_dict_lock, OWNER_ID, user_data, multi_tags
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    auto_delete_message,
    deleteMessage,
)
from bot.helper.ext_utils.status_utils import getTaskByGid, getAllTasks, MirrorStatus
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper import button_build


async def cancel_task(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split('_', maxsplit=1)
    if len(msg) > 1:
        cmd_data = msg[1].split('@', maxsplit=1)
        gid = cmd_data[0]
        if len(gid) == 4:
            multi_tags.discard(gid)
            return
        else:
            task = await getTaskByGid(gid)
            if task is None:
                await sendMessage(message, f"<b>Tugas dengan ID</b> <code>{gid}</code> <b>tidak ditemukan!</b>")
                return
    elif reply_to_id := message.reply_to_message_id:
        async with task_dict_lock:
            task = task_dict.get(reply_to_id)
        if task is None:
            await sendMessage(message, "<b>Bukan Tugas Aktif!</b>")
            return
    elif len(msg) == 1:
        msg = (
        "<b>Balas ke pesan perintah saat digunakan untuk memulai Tugas</b>" \
        f" <b>atau kirim</b> <code>/{BotCommands.CancelTaskCommand[0]} atau /{BotCommands.CancelTaskCommand[1]} GID</code> <b>untuk membatalkan Tugas!</b>"
        )
        await sendMessage(message, msg)
        return
    if (
        OWNER_ID != user_id
        and task.listener.user_id != user_id
        and (user_id not in user_data or not user_data[user_id].get("is_sudo"))
    ):
        await sendMessage(message, "<b>Bukan Tugas darimu!</b>")
        return
    obj = task.task()
    await obj.cancel_task()


async def cancel_multi(_, query):
    data = query.data.split()
    user_id = query.from_user.id
    if user_id != int(data[1]) and not await CustomFilters.sudo("", query):
        await query.answer("Bukan Tugas darimu!", show_alert=True)
        return
    tag = int(data[2])
    if tag in multi_tags:
        multi_tags.discard(int(data[2]))
        msg = "Tugas dihentikan!"
    else:
        msg = "Tugas sudah dihentikan/selesai!"
    await query.answer(msg, show_alert=True)
    await deleteMessage(query.message)


async def cancel_all(status):
    matches = await getAllTasks(status)
    if not matches:
        return False
    for task in matches:
        obj = task.task()
        await obj.cancel_task()
        await sleep(2)
    return True


async def cancell_all_buttons(_, message):
    async with task_dict_lock:
        count = len(task_dict)
    if count == 0:
        await sendMessage(message, "<b>Tidak ada tugas aktif!</b>")
        return
    buttons = button_build.ButtonMaker()
    buttons.ibutton("Downloading", f"canall {MirrorStatus.STATUS_DOWNLOADING}")
    buttons.ibutton("Uploading", f"canall {MirrorStatus.STATUS_UPLOADING}")
    buttons.ibutton("Seeding", f"canall {MirrorStatus.STATUS_SEEDING}")
    buttons.ibutton("Splitting", f"canall {MirrorStatus.STATUS_SPLITTING}")
    buttons.ibutton("Cloning", f"canall {MirrorStatus.STATUS_CLONING}")
    buttons.ibutton("Extracting", f"canall {MirrorStatus.STATUS_EXTRACTING}")
    buttons.ibutton("Archiving", f"canall {MirrorStatus.STATUS_ARCHIVING}")
    buttons.ibutton("QueuedDl", f"canall {MirrorStatus.STATUS_QUEUEDL}")
    buttons.ibutton("QueuedUp", f"canall {MirrorStatus.STATUS_QUEUEUP}")
    buttons.ibutton("Paused", f"canall {MirrorStatus.STATUS_PAUSED}")
    buttons.ibutton("All", "canall all")
    buttons.ibutton("Close", "canall close")
    button = buttons.build_menu(2)
    can_msg = await sendMessage(message, "<b>Pilih jenis Tugas yang ingin dibatalkan :</b>", button)
    await auto_delete_message(message, can_msg)


@new_task
async def cancel_all_update(_, query):
    data = query.data.split()
    message = query.message
    reply_to = message.reply_to_message
    await query.answer()
    if data[1] == "close":
        await deleteMessage(reply_to)
        await deleteMessage(message)
    else:
        res = await cancel_all(data[1])
        if not res:
            await sendMessage(reply_to, f"<b>Tugas</b> <code>{data[1]}</code> <b>tidak ditemukan!</b>")


bot.add_handler(
    MessageHandler(
        cancel_task,
        filters=regex(
    rf"^/{BotCommands.CancelTaskCommand[0]}(_\w+)?(?!all)"
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    MessageHandler(
        cancell_all_buttons,
        filters=command(
            BotCommands.CancelAllCommand
        ) & CustomFilters.sudo,
    )
)
bot.add_handler(
    CallbackQueryHandler(
        cancel_all_update, 
        filters=regex(
            "^canall"
        ) & CustomFilters.sudo
    )
)
bot.add_handler(
    CallbackQueryHandler(
        cancel_multi, 
        filters=regex(
            "^stopm"
        )
    )
)
