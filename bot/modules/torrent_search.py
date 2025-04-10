from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from aiohttp import ClientSession
from html import escape
from urllib.parse import quote

from bot import bot, LOGGER, config_dict, get_client
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.common_utils import get_readable_file_size

PLUGINS = []
SITES = None
TELEGRAPH_LIMIT = 300
botnname = bot.me.first_name

async def initiate_search_tools():
    qbclient = await sync_to_async(get_client)
    qb_plugins = await sync_to_async(qbclient.search_plugins)
    if SEARCH_PLUGINS := config_dict["SEARCH_PLUGINS"]:
        globals()["PLUGINS"] = []
        src_plugins = eval(SEARCH_PLUGINS)
        if qb_plugins:
            names = [plugin["name"] for plugin in qb_plugins]
            await sync_to_async(qbclient.search_uninstall_plugin, names=names)
        await sync_to_async(qbclient.search_install_plugin, src_plugins)
    elif qb_plugins:
        for plugin in qb_plugins:
            await sync_to_async(qbclient.search_uninstall_plugin, names=plugin["name"])
        globals()["PLUGINS"] = []
    await sync_to_async(qbclient.auth_log_out)

    if SEARCH_API_LINK := config_dict["SEARCH_API_LINK"]:
        global SITES
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(f"{SEARCH_API_LINK}/api/v1/sites") as res:
                    data = await res.json()
            SITES = {
                str(site): str(site).capitalize() for site in data["supported_sites"]
            }
            SITES["all"] = "All"
        except Exception as e:
            LOGGER.error(
                f"{e} Can't fetching sites from SEARCH_API_LINK make sure use latest version of API"
            )
            SITES = None


async def _search(key, site, message, method):
    if method.startswith("api"):
        SEARCH_API_LINK = config_dict["SEARCH_API_LINK"]
        SEARCH_LIMIT = config_dict["SEARCH_LIMIT"]
        if method == "apisearch":
            LOGGER.info(f"API Searching: {key} from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/search?query={key}&limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/search?site={site}&query={key}&limit={SEARCH_LIMIT}"
        elif method == "apitrend":
            LOGGER.info(f"API Trending from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/trending?limit={SEARCH_LIMIT}"
            else:
                api = f"{SEARCH_API_LINK}/api/v1/trending?site={site}&limit={SEARCH_LIMIT}"
        elif method == "apirecent":
            LOGGER.info(f"API Recent from {site}")
            if site == "all":
                api = f"{SEARCH_API_LINK}/api/v1/all/recent?limit={SEARCH_LIMIT}"
            else:
                api = (
                    f"{SEARCH_API_LINK}/api/v1/recent?site={site}&limit={SEARCH_LIMIT}"
                )
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(api) as res:
                    search_results = await res.json()
            if "error" in search_results or search_results["total"] == 0:
                await editMessage(
                    message,
                    f"<b>Pencarian dengan kata kunci</b> <code>{key}</code> <b>tidak ditemukan</b>\n<b>Situs Torrent :</b>\n<code>{SITES.get(site)}</code>",
                )
                return
            msg = f"<b>Found {min(search_results['total'], TELEGRAPH_LIMIT)}</b>"
            if method == "apitrend":
                msg += f" <b>Trending Torrent</b>\n<b>Situs Torrent :</b>\n<code>{SITES.get(site)}</code>"
            elif method == "apirecent":
                msg += (
                    f" <b>Recent Torrent\n<b>Situs Torrent :</b>\n<code>{SITES.get(site)}</code>"
                )
            else:
                msg += f" <b>hasil pencarian kata kunci :</b>/\n<code>{key}</code>\n<b>Situs Torrent :</b>\n<code>{SITES.get(site)}</code>"
            search_results = search_results["data"]
        except Exception as e:
            await editMessage(message, str(e))
            return
    else:
        LOGGER.info(f"PLUGINS Searching: {key} from {site}")
        client = await sync_to_async(get_client)
        search = await sync_to_async(
            client.search_start, pattern=key, plugins=site, category="all"
        )
        search_id = search.id
        while True:
            result_status = await sync_to_async(
                client.search_status, search_id=search_id
            )
            status = result_status[0].status
            if status != "Running":
                break
        dict_search_results = await sync_to_async(
            client.search_results, search_id=search_id, limit=TELEGRAPH_LIMIT
        )
        search_results = dict_search_results.results
        total_results = dict_search_results.total
        if total_results == 0:
            await editMessage(
                message,
                f"<b>Pencarian dengan kata kunci</b> <code>{key}</code> <b>tidak ditemukan</b>\n<b>Situs Torrent :</b>\n<code>{site.capitalize()}</code>",
            )
            return
        msg = f"<b>Menemukan {min(total_results, TELEGRAPH_LIMIT)}</b>"
        msg += f" <b>hasil pencarian dengan kata kunci :</b>\n<code>{key}</code>\n<b>Situs Torrent :</b>\n<code>{site.capitalize()}</code>"
        await sync_to_async(client.search_delete, search_id=search_id)
        await sync_to_async(client.auth_log_out)
    link = await _getResult(search_results, key, message, method)
    buttons = ButtonMaker()
    buttons.ubutton("🔎 Lihat Hasil", link)
    button = buttons.build_menu(1)
    await editMessage(message, msg, button)


async def _getResult(search_results, key, message, method):
    telegraph_content = []
    if method == "apirecent":
        msg = "<h4>API Recent Results</h4>"
    elif method == "apisearch":
        msg = f"<h4>API Search Result(s) For {key}</h4>"
    elif method == "apitrend":
        msg = "<h4>API Trending Results</h4>"
    else:
        msg = f"<h4>PLUGINS Search Result(s) For {key}</h4>"
    for index, result in enumerate(search_results, start=1):
        if method.startswith("api"):
            try:
                if "name" in result.keys():
                    msg += f"<code><a href='{result['url']}'>{escape(result['name'])}</a></code><br>"
                if "torrents" in result.keys():
                    for subres in result["torrents"]:
                        msg += f"<b>Quality: </b>{subres['quality']} | <b>Type: </b>{subres['type']} | "
                        msg += f"<b>Size: </b>{subres['size']}<br>"
                        if "torrent" in subres.keys():
                            msg += f"<a href='{subres['torrent']}'>Direct Link</a><br>"
                        elif "magnet" in subres.keys():
                            msg += "<b>Share Magnet to</b> "
                            msg += f"<a href='http://t.me/share/url?url={subres['magnet']}'>Telegram</a><br>"
                    msg += "<br>"
                else:
                    msg += f"<b>Size: </b>{result['size']}<br>"
                    try:
                        msg += f"<b>Seeders: </b>{result['seeders']} | <b>Leechers: </b>{result['leechers']}<br>"
                    except:
                        pass
                    if "torrent" in result.keys():
                        msg += f"<a href='{result['torrent']}'>Direct Link</a><br><br>"
                    elif "magnet" in result.keys():
                        msg += "<b>Share Magnet to</b> "
                        msg += f"<a href='http://t.me/share/url?url={quote(result['magnet'])}'>Telegram</a><br><br>"
                    else:
                        msg += "<br>"
            except:
                continue
        else:
            msg += f"<a href='{result.descrLink}'>{escape(result.fileName)}</a><br>"
            msg += f"<b>Size: </b>{get_readable_file_size(result.fileSize)}<br>"
            msg += f"<b>Seeders: </b>{result.nbSeeders} | <b>Leechers: </b>{result.nbLeechers}<br>"
            link = result.fileUrl
            if link.startswith("magnet:"):
                msg += f"<b>Share Magnet to</b> <a href='http://t.me/share/url?url={quote(link)}'>Telegram</a><br><br>"
            else:
                msg += f"<a href='{link}'>Direct Link</a><br><br>"

        if len(msg.encode("utf-8")) > 39000:
            telegraph_content.append(msg)
            msg = ""

        if index == TELEGRAPH_LIMIT:
            break

    if msg != "":
        telegraph_content.append(msg)

    await editMessage(
        message, f"<b>Membuat</b> <code>{len(telegraph_content)}</code> <b>Halaman telegraph</b>"
    )
    path = [
        (
            await telegraph.create_page(
                title="Pencarian {botnname}", content=content
            )
        )["path"]
        for content in telegraph_content
    ]
    if len(path) > 1:
        await editMessage(
            message, f"<b>Mengedit</b> <code>{len(telegraph_content)}</code> <b>Halaman telegraph</b>"
        )
        await telegraph.edit_telegraph(path, telegraph_content)
    return f"https://telegra.ph/{path[0]}"


def _api_buttons(user_id, method):
    buttons = ButtonMaker()
    for data, name in SITES.items():
        buttons.ibutton(name, f"torser {user_id} {data} {method}")
    buttons.ibutton("Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


async def _plugin_buttons(user_id):
    buttons = ButtonMaker()
    if not PLUGINS:
        qbclient = await sync_to_async(get_client)
        pl = await sync_to_async(qbclient.search_plugins)
        for name in pl:
            PLUGINS.append(name["name"])
        await sync_to_async(qbclient.auth_log_out)
    for siteName in PLUGINS:
        buttons.ibutton(siteName.capitalize(), f"torser {user_id} {siteName} plugin")
    buttons.ibutton("All", f"torser {user_id} all plugin")
    buttons.ibutton("Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


async def torrentSearch(_, message):
    user_id = message.from_user.id
    buttons = ButtonMaker()
    key = message.text.split()
    SEARCH_PLUGINS = config_dict["SEARCH_PLUGINS"]
    if SITES is None and not SEARCH_PLUGINS:
        await sendMessage(
            message, "<b>Api atau Plugin tidak tersedia!</b>"
        )
    elif len(key) == 1 and SITES is None:
        await sendMessage(message, "<b>Kirim perintah disertai dengan kata kunci!</b>")
    elif len(key) == 1:
        buttons.ibutton("Trending", f"torser {user_id} apitrend")
        buttons.ibutton("Recent", f"torser {user_id} apirecent")
        buttons.ibutton("Cancel", f"torser {user_id} cancel")
        button = buttons.build_menu(2)
        await sendMessage(message, "<b>Kirim perintah disertai dengan kata kunci!</b>", button)
    elif SITES is not None and SEARCH_PLUGINS:
        buttons.ibutton("Api", f"torser {user_id} apisearch")
        buttons.ibutton("Plugins", f"torser {user_id} plugin")
        buttons.ibutton("Cancel", f"torser {user_id} cancel")
        button = buttons.build_menu(2)
        await sendMessage(message, "<b>Pilih alat untuk mencari :</b>", button)
    elif SITES is not None:
        button = _api_buttons(user_id, "apisearch")
        await sendMessage(message, "<b>Pilih situs untuk dicari | API :</b>", button)
    else:
        button = await _plugin_buttons(user_id)
        await sendMessage(message, "<b>Pilih situs untuk dicari | Plugins :</b>", button)


@new_task
async def torrentSearchUpdate(_, query):
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)
    key = key[1].strip() if len(key) > 1 else None
    data = query.data.split()
    if user_id != int(data[1]):
        await query.answer("Bukan tugas darimu!", show_alert=True)
    elif data[2].startswith("api"):
        await query.answer()
        button = _api_buttons(user_id, data[2])
        await editMessage(message, "<b>Pilih situs :</b>", button)
    elif data[2] == "plugin":
        await query.answer()
        button = await _plugin_buttons(user_id)
        await editMessage(message, "<b>Pilih situs :</b>", button)
    elif data[2] != "cancel":
        await query.answer()
        site = data[2]
        method = data[3]
        if method.startswith("api"):
            if key is None:
                if method == "apirecent":
                    endpoint = "Recent"
                elif method == "apitrend":
                    endpoint = "Trending"
                await editMessage(
                    message,
                    f"<b>Mencari {endpoint} Torrent...</b>\n<b>Situs Torrent:</b>\n<code>{SITES.get(site)}</code>",
                )
            else:
                await editMessage(
                    message,
                    f"<b>Mencari torrent dengan kata kunci:\n</b><code>{key}</code>\n<b>Situs Torrent:</b>\n<code>{SITES.get(site)}</code>",
                )
        else:
            await editMessage(
                message,
                f"<b>Mencari torrent dengan kata kunci:\n</b><code>{key}</code>\n<b>Situs Torrent:</b>\n<code>{site.capitalize()}</code>",
            )
        await _search(key, site, message, method)
    else:
        await query.answer()
        await editMessage(message, "<b>Pencarian dibatalkan!</b>")


bot.add_handler(
    MessageHandler(
        torrentSearch,
        filters=command(
            BotCommands.SearchCommand
        ) & CustomFilters.authorized,
    )
)
bot.add_handler(
    CallbackQueryHandler(
        torrentSearchUpdate, 
        filters=regex(
            "^torser"
        )
    )
)
