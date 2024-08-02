from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex
from aiofiles import open as aiopen
from bot import bot

from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import editMessage, deleteMessage
from bot.helper.ext_utils.help_messages import MIRROR_HELP, LEECH_HELP, TORRENT_HELP, YTDLP_HELP, OTHER_HELP


async def pikaquery(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    if user_id != int(data[1]):
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)
    elif data[2] == "guide":
        btn = ButtonMaker()
        btn.ibutton('⬅️ Kembali', f'pika {user_id} guide home')
        btn.ibutton('⬇️ Tutup', f'pika {user_id} close')
        if data[3] == "mirror":
            await editMessage(message, MIRROR_HELP, btn.build_menu(2))
        elif data[3] == "leech":
            await editMessage(message, LEECH_HELP, btn.build_menu(2))
        elif data[3] == "torrent":
            await editMessage(message, TORRENT_HELP, btn.build_menu(2))
        elif data[3] == "ytdlp":
            await editMessage(message, YTDLP_HELP, btn.build_menu(2))
        elif data[3] == "other":
            await editMessage(message, OTHER_HELP, btn.build_menu(2))
        else:
            buttons = ButtonMaker()
            buttons.ibutton('Mirror', f'pika {user_id} guide mirror')
            buttons.ibutton('Leech', f'pika {user_id} guide leech')
            buttons.ibutton('Torrent', f'pika {user_id} guide torrent')
            buttons.ibutton('Ytdlp', f'pika {user_id} guide ytdlp')
            buttons.ibutton('Lainnya', f'pika {user_id} guide other')
            buttons.ibutton('⬇️ Tutup', f'pika {user_id} close', 'footer')
            await editMessage(message, f"Silahkan pilih jenis bantuan yang anda perlukan !", buttons.build_menu(2))
        await query.answer()
    else:
        await query.answer()
        await deleteMessage(message)
        if message.reply_to_message:
            await deleteMessage(message.reply_to_message)
            if message.reply_to_message.reply_to_message:
                await deleteMessage(message.reply_to_message.reply_to_message)

bot.add_handler(CallbackQueryHandler(pikaquery, filters=regex(r'^pika')))