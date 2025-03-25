from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex
from aiofiles import open as aiopen
from bot import bot

from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import editMessage, deleteMessage
from bot.helper.ext_utils.help_messages import MIRROR_HELP, LEECH_HELP, TORRENT_HELP, YTDLP_HELP, OTHER_HELP
from bot.helper.ext_utils.pikachu_utils import token_verify

async def pikaquery(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    if user_id != int(data[1]):
        return await query.answer(text="Bukan Tugas Anda !", show_alert=True)
    elif data[2] == "guide":
        btn = ButtonMaker()
        btn.ibutton('🔙 𝙱𝚊𝚌𝚔', f'pika {user_id} guide home')
        btn.ibutton('🔽 𝚃𝚞𝚝𝚞𝚙', f'pika {user_id} close')
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
            buttons.ibutton('𝙼𝚒𝚛𝚛𝚘𝚛', f'pika {user_id} guide mirror')
            buttons.ibutton('𝙻𝚎𝚎𝚌𝚑', f'pika {user_id} guide leech')
            buttons.ibutton('𝚃𝚘𝚛𝚛𝚎𝚗𝚝', f'pika {user_id} guide torrent')
            buttons.ibutton('𝚈𝚝𝚕𝚍𝚙', f'pika {user_id} guide ytdlp')
            buttons.ibutton('𝙻𝚊𝚒𝚗𝚗𝚢𝚊', f'pika {user_id} guide other')
            buttons.ibutton('🔽 𝚃𝚞𝚝𝚞𝚙', f'pika {user_id} close', 'footer')
            await editMessage(message, f"Silahkan pilih jenis bantuan yang anda perlukan !", buttons.build_menu(2))
        await query.answer()
    else:
        await query.answer()
        await deleteMessage(message)
        if message.reply_to_message:
            await deleteMessage(message.reply_to_message)
            if message.reply_to_message.reply_to_message:
                await deleteMessage(message.reply_to_message.reply_to_message)

async def locked(_, query):
    await query.answer(text="Fitur ini tidak bisa digunakan di bot ini!", show_alert=True)
    await query.answer()

async def paid(_, query):
    await query.answer(text="Fitur ini hanya untuk pengguna premium atau private bot !", show_alert=True)
    await query.answer()

async def token_query(_, query):
    """Handle token verification from inline buttons"""
    user_id = query.from_user.id
    data = query.data.split()
    
    if len(data) < 3:
        return await query.answer("❌ Invalid button data", show_alert=True)
    
    command = data[0]
    token_owner_id = int(data[1])
    token = data[2]
    
    if user_id != token_owner_id:
        return await query.answer("❌ Tombol ini bukan untuk Anda! Gunakan perintah /cek untuk mendapatkan kuota Anda sendiri.", show_alert=True)
    
    result = await token_verify(user_id, token)
    await query.message.reply_text(result)
    await query.answer()

bot.add_handler(CallbackQueryHandler(paid, filters=regex(r'^paid')))
bot.add_handler(CallbackQueryHandler(locked, filters=regex(r'^lock')))
bot.add_handler(CallbackQueryHandler(pikaquery, filters=regex(r'^pika')))
bot.add_handler(CallbackQueryHandler(token_query, filters=regex(r'^token')))