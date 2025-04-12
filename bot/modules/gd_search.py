from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from asyncio import Lock
from math import ceil

from bot import LOGGER, bot, user_data
from bot.helper.mirror_utils.gdrive_utils.search import gdSearch
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task

msg_dict = {}
max_total = 5
list_lock = Lock()

async def list_buttons(user_id, isRecursive=True, user_token=False):
    buttons = ButtonMaker()
    buttons.ibutton(
        "Folders", f"list_types {user_id} folders {isRecursive} {user_token}"
    )
    buttons.ibutton("Files", f"list_types {user_id} files {isRecursive} {user_token}")
    buttons.ibutton("Keduanya", f"list_types {user_id} both {isRecursive} {user_token}")
    buttons.ibutton(
        f"Recursive : {isRecursive}",
        f"list_types {user_id} rec {isRecursive} {user_token}",
    )
    buttons.ibutton(
        f"User Token : {user_token}",
        f"list_types {user_id} ut {isRecursive} {user_token}",
    )
    buttons.ibutton("Batalkan", f"list_types {user_id} cancel")
    return buttons.build_menu(2)

async def _list_drive(key, message, item_type, isRecursive, user_token, user_id):
    LOGGER.info(f"listing: {key}")
    if user_token:
        user_dict = user_data.get(user_id, {})
        target_id = user_dict.get("gdrive_id", "") or ""
        LOGGER.info(target_id)
    else:
        target_id = ""

## GD List sent to telegram
    LOGGER.info(f"listing: {key}")
    msgid, userid = message.reply_to_message.id, message.reply_to_message.from_user.id
    
    msg, _ = await sync_to_async(
        gdSearch(
            isRecursive=isRecursive,
            itemType=item_type
        ).drive_list,
        key,
        target_id,
        user_id
    )

    if msg:
        count, page_no, cur_page = 0, 1, None
        msg_dict[msgid] = [count, page_no, msg, cur_page, key, msgid, message.reply_to_message]
        async with list_lock:
            result_msg = ""
            cur_page = ceil(len(msg) / max_total)
            msg_dict[msgid][3] = cur_page

            if page_no > cur_page and cur_page != 0:
                count -= max_total
                page_no -= 1

            buttons = ButtonMaker()

            for no, data in enumerate(msg[count:], start=1):
                result_msg += data
                if no == max_total:
                    break

            if len(msg) > max_total:
                buttons.ibutton("⫷", f"list pre {userid} {msgid}")
                buttons.ibutton(f"{page_no}/{cur_page}", f"list {page_no} {userid} {msgid}")
                buttons.ibutton("⫸", f"list next {userid} {msgid}")

            if len(msg) <= max_total:
                buttons.ibutton(f"{page_no}/{cur_page}", f"list {page_no} {userid} {msgid}")

        buttons.ibutton("Close", f"list closelist {userid} {msgid}", "footer")
        await message.delete()
        await sendMessage(msg_dict[msgid][6], result_msg, buttons.build_menu(3))
    else:
        await editMessage(message, f"<b>Pencarian untuk: <code>{key}</code> Tidak ditemukan</b>")    


@new_task
async def select_type(_, query):
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)[1].strip()
    data = query.data.split()
    if user_id != int(data[1]):
        return await query.answer(text="Bukan tugas darimu!", show_alert=True)
    elif data[2] == "rec":
        await query.answer()
        isRecursive = not bool(eval(data[3]))
        buttons = await list_buttons(user_id, isRecursive, eval(data[4]))
        return await editMessage(message, "<b>Pilih opsi :</b>", buttons)
    elif data[2] == "ut":
        await query.answer()
        user_token = not bool(eval(data[4]))
        buttons = await list_buttons(user_id, eval(data[3]), user_token)
        return await editMessage(message, "<b>Pilih tipe yang mau dicari :</b>", buttons)
    elif data[2] == "cancel":
        await query.answer()
        return await editMessage(message, "<b>Pencarian dibatalkan!</b>")
    await query.answer()
    item_type = data[2]
    isRecursive = eval(data[3])
    user_token = eval(data[4])
    await editMessage(message, f"<b>Mencari file dengan kata kunci</b> <code>{key}</code>...")
    await _list_drive(key, message, item_type, isRecursive, user_token, user_id)


async def gdrive_search(_, message):
    if len(message.text.split()) == 1:
        return await sendMessage(message, "<b>Kirim perintah disertai dengan kata kunci!</b>")
    user_id = message.from_user.id
    buttons = await list_buttons(user_id)
    await sendMessage(message, "<b>Pilih tipe yang mau dicari :</b>", buttons)

@new_task
async def list_query(client, query):
    data = query.data.split()
    try:
        msgs = msg_dict[int(data[3])]
    except:
        await query.message.delete()
        await query.message.reply_to_message.delete()
        return await query.answer("Query pencarian sudah expired", True)
    userid = int(data[2])
    buttons = ButtonMaker()
    if data[1] == "pre":
        if msgs[1] == 1:
            msgs[0] = max_total * (msgs[3] - 1)
            msgs[1] = msgs[3]
        else:
            msgs[0] -= max_total
            msgs[1] -= 1
        msg = ""
        cur_page = ceil(len(msgs[2]) / max_total)
        if cur_page != 0 and msgs[1] > cur_page:
            msgs[0] -= max_total
            msgs[1] -= 1
        for no, data in enumerate(msgs[2][msgs[0] :], start=1):
            msg += data
            if no == max_total:
                break
        if len(msgs[2]) > max_total:
            buttons.ibutton("⫷", f"list pre {userid} {msgs[5]}")
            buttons.ibutton(f"{msgs[1]}/{cur_page}", f"list {msgs[1]} {userid} {msgs[5]}")
            buttons.ibutton("⫸", f"list next {userid} {msgs[5]}")
        if len(msgs[2]) <= max_total:
            buttons.ibutton(f"{msgs[1]}/{cur_page}", f"list {msgs[1]} {userid} {msgs[5]}")
        buttons.ibutton("Close", f"list closelist {userid} {msgs[5]}", "footer")
        await query.answer()
        await editMessage(query.message, msg, buttons.build_menu(3))
    elif data[1] == "next":
        if msgs[1] == msgs[3]:
            msgs[0] = 0
            msgs[1] = 1
        else:
            msgs[0] += max_total
            msgs[1] += 1
        msg = ""
        cur_page = ceil(len(msgs[2]) / max_total)
        if cur_page != 0 and msgs[1] > cur_page:
            msgs[0] -= max_total
            msgs[1] -= 1
        for no, data in enumerate(msgs[2][msgs[0] :], start=1):
            msg += data
            if no == max_total:
                break
        if len(msgs[2]) > max_total:
            buttons.ibutton("⫷", f"list pre {userid} {msgs[5]}")
            buttons.ibutton(f"{msgs[1]}/{cur_page}", f"list {msgs[1]} {userid} {msgs[5]}")
            buttons.ibutton("⫸", f"list next {userid} {msgs[5]}")
        if len(msgs[2]) <= max_total:
            buttons.ibutton(f"{msgs[1]}/{cur_page}", f"list {msgs[1]} {userid} {msgs[5]}")
        buttons.ibutton("Close", f"list closelist {userid} {msgs[5]}", "footer")
        await query.answer()
        await editMessage(query.message, msg, buttons.build_menu(3))
    elif data[1] == "closelist":
        await query.message.delete()
        await query.message.reply_to_message.delete()
        try:
            del msgs[5]
        except:
            pass
    else:
        for no, _ in enumerate(msgs[2], start=1):
            if no == max_total:
                break

bot.add_handler(
    MessageHandler(
        gdrive_search,
        filters=command(
            BotCommands.ListCommand
        ) & CustomFilters.authorized
    )
)
bot.add_handler(
    CallbackQueryHandler(
        select_type, 
        filters=regex(
            "^list_types"
        )
    )
)
bot.add_handler(
    CallbackQueryHandler(
        list_query, 
        filters=regex(
            "^list")
    )
)