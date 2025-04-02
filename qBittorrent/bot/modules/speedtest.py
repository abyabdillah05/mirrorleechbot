from speedtest import Speedtest
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot, LOGGER
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import (
    sendMessage, 
    sendPhoto, 
    deleteMessage, 
    editMessage
)
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import get_readable_file_size


@new_task
async def speedtest(_, message):
    msg = await sendMessage(message, "<b>Mengetes kecepatan Unduh & Unggah...</b>")
    test = Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    caption = f"""
<pre languange='bash'>
<b>Hasil SpeedTest</b>
<b>Ping         :</b> <code>{result['ping']} ms</code>
<b>Waktu        :</b> <code>{result['timestamp']}</code>
<b>Unggah       :</b> <code>{get_readable_file_size(result['upload'] / 8)}/s</code>
<b>Upload       :</b> <code>{get_readable_file_size(result['download'] / 8)}/s</code>
<b>Terkirim     :</b> <code>{get_readable_file_size(int(result['bytes_sent']))}</code>
<b>Diterima     :</b> <code>{get_readable_file_size(int(result['bytes_received']))}</code>

<b>Informasi Client</b>
<b>IP           :</b> <code>{result['client']['ip']}</code>
<b>Nama         :</b> <code>{result['client']['isp']}</code>
<b>Rating       :</b> <code>{result['client']['isprating']}</code>
<b>Negara       :</b> <code>{result['client']['country']}</code>
<b>Latitude     :</b> <code>{result['client']['lat']}</code>
<b>Longitude    :</b> <code>{result['client']['lon']}</code>

<b>Informasi Server</b>
<b>Nama         :</b> <code>{result['server']['name']}</code>
<b>Sponsor      :</b> <code>{result['server']['sponsor']}</code>
<b>Latency      :</b> <code>{result['server']['latency']}</code>
<b>Negara       :</b> <code>{result['server']['country']}, {result['server']['cc']}</code>
<b>Latitude     :</b> <code>{result['server']['lat']}</code>
<b>Longitude    :</b> <code>{result['server']['lon']}</code>
</pre>
"""
    try:
        await sendPhoto(
            message, 
            result["share"], 
            caption
        )
        await deleteMessage(msg)
    except Exception as e:
        LOGGER.error(str(e))
        await editMessage(msg, caption)

bot.add_handler(
    MessageHandler(
        speedtest, 
        filters=command(
            BotCommands.SpeedCommand
        ) & CustomFilters.owner
    )
)