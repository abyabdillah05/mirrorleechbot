import random
import requests

####################################
## Import Libraries From Pyrogram ##
####################################

from pyrogram.types import InputMediaVideo
from pyrogram.filters import command, regex
from pyrogram.handlers import (CallbackQueryHandler,
                               MessageHandler)

###################################
## Import Variables From Project ##
###################################

from bot import bot
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (sendMessage,
                                                      deleteMessage,
                                                      editMessage)

########################
## Required Variables ##
########################

## You can change this to your own file url ##
## Or you can copy paste teks in file url and make your own json file ##
## https://gist.github.com ##

file_url = "https://gist.githubusercontent.com/abyabdillah05/c0d6facb9d45ca2ed094600c38c23a44/raw/5aec9181633f01dc805546806fc9efef3f78a3d2/asupan.json"

###################################
## Helper Functions For File URL ##
###################################

async def get_url(url):
    try:
        r = requests.get(url).json()
        if r:
            if isinstance(r, list):
                random.shuffle(r)
                video_link = random.choice(r)
                return video_link
    except Exception as e:
        return ("ERROR:", e)

#######################################
## Asupan Feature Credit @aenulrofik ##
#######################################

@new_task
async def asupan(client, message, ganti=None):
    mess = await sendMessage(message, "<b>Tunggu sebentar tuan...</b>")
    uid = message.from_user.id
    try_count = 5
    attempt = 1
    while attempt <= try_count:
        try:
            butt = ButtonMaker()
            butt.ibutton("🔄 Ganti Asupan", f"asupan {uid} ganti" )
            butts = butt.build_menu(1)
            video_link = await get_url(file_url)
            await message.reply_video(video_link, reply_markup=butts)
            break
        except:
            attempt += 1
            if attempt <= try_count:
                await editMessage(mess, f"Gagal mengirim asupan, Mencoba lagi untuk ke-{attempt} kali...")
            else:
                await sendMessage(mess, f"Gagal mengupload asupan setelah 5x percobaan.")
                break
    await deleteMessage(mess)
        

async def asupan_query(_, query):
    message = query.message
    edit_media = query.edit_message_media
    uid = query.from_user.id
    data = query.data.split()
    if uid != int(data[1]):
        return await query.answer(text="Bukan asupan anda tuan !", show_alert=True)
    elif data[2] == "ganti":
        try_count = 5
        attempt = 1
        while attempt <= try_count:
            try:
                butt = ButtonMaker()
                butt.ibutton("🔄 Ganti Asupan", f"asupan {uid} ganti" )
                butts = butt.build_menu(1)
                video_link = await get_url(file_url)
                caption = None
                if video_link.endswith('.mp4'):
                    await edit_media(media=InputMediaVideo(video_link, caption=caption), reply_markup=butts)
                else:
                    await edit_media(video_link, reply_markup=butts)
                break
            except Exception as e:
                attempt += 1
                if attempt == try_count:
                    await sendMessage(message, f"Gagal mengupload asupan setelah 5x percobaan.\n\n{e}")
                    break

######################################
## Command & CallbackQuery Handlers ##
######################################

bot.add_handler(
    MessageHandler(
        asupan, 
        filters=command(
            BotCommands.AsupanCommand
        )
    )
)
bot.add_handler(
    CallbackQueryHandler(
        asupan_query,
        filters=regex(
            r'^asupan'
        )
    )
)

## Thanks to @aenulrofik for this feature ##