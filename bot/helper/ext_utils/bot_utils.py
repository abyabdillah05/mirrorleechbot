import os
import re

from asyncio import (
    create_subprocess_exec,
    create_subprocess_shell,
    run_coroutine_threadsafe,
    sleep
)
from asyncio.subprocess import PIPE
from functools import partial, wraps
from concurrent.futures import ThreadPoolExecutor
from aiohttp import ClientSession

from bot import user_data, config_dict, bot_loop, active_sessions, TELEGRAM_API, TELEGRAM_HASH, LOGGER
from bot.helper.ext_utils.help_messages import YT_HELP_DICT, MIRROR_HELP_DICT
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.ext_utils.db_handler import DbManger
from pyrogram import Client as tgClient, enums

THREADPOOL = ThreadPoolExecutor(max_workers=1000)

COMMAND_USAGE = {}


class setInterval:
    def __init__(self, interval, action, *args, **kwargs):
        self.interval = interval
        self.action = action
        self.task = bot_loop.create_task(self._set_interval(*args, **kwargs))

    async def _set_interval(self, *args, **kwargs):
        while True:
            await sleep(self.interval)
            await self.action(*args, **kwargs)

    def cancel(self):
        self.task.cancel()


def create_help_buttons():
    buttons = ButtonMaker()
    for name in list(MIRROR_HELP_DICT.keys())[1:]:
        buttons.ibutton(name, f"help m {name}")
    buttons.ibutton("Close", f"help close")
    COMMAND_USAGE["mirror"] = [MIRROR_HELP_DICT["main"], buttons.build_menu(3)]
    buttons.reset()
    for name in list(YT_HELP_DICT.keys())[1:]:
        buttons.ibutton(name, f"help yt {name}")
    buttons.ibutton("Close", f"help close")
    COMMAND_USAGE["yt"] = [YT_HELP_DICT["main"], buttons.build_menu(3)]


def bt_selection_buttons(id_):
    gid = id_[:12] if len(id_) > 20 else id_
    pincode = "".join([n for n in id_ if n.isdigit()][:4])
    buttons = ButtonMaker()
    BASE_URL = config_dict["BASE_URL"]
    if config_dict["WEB_PINCODE"]:
        buttons.ubutton("Pilih File", f"{BASE_URL}/app/files/{id_}")
        buttons.ibutton("Kode Pin", f"btsel pin {gid} {pincode}")
    else:
        buttons.ubutton(
            "Pilih File", f"{BASE_URL}/app/files/{id_}?pin_code={pincode}"
        )
    buttons.ibutton("Selesai Memilih", f"btsel done {gid} {id_}")
    buttons.ibutton("⛔️ 𝙱𝚊𝚝𝚊𝚕", f"btsel cancel {gid}")
    return buttons.build_menu(2)


async def get_telegraph_list(telegraph_content):
    path = [
        (
            await telegraph.create_page(
                title="Pencarian oleh 𝚃𝚛𝚊𝚗𝚜𝚜𝚒𝚘𝚗 𝙲𝚘𝚛𝚎 𝙼𝚒𝚛𝚛𝚘𝚛 - 𝙱𝚘𝚝", content=content
            )
        )["path"]
        for content in telegraph_content
    ]
    if len(path) > 1:
        await telegraph.edit_telegraph(path, telegraph_content)
    buttons = ButtonMaker()
    buttons.ubutton("🔎 Lihat Hasil", f"https://telegra.ph/{path[0]}")
    return buttons.build_menu(1)


def arg_parser(items, arg_base):
    if not items:
        return arg_base
    bool_arg_set = {"-b", "-e", "-z", "-s", "-j", "-d", "-sv", "-ss", "-ct", "-dump", "-ve"}
    t = len(items)
    i = 0
    arg_start = -1

    while i + 1 <= t:
        part = items[i]
        if part in arg_base:
            if arg_start == -1:
                arg_start = i
            if i + 1 == t and part in bool_arg_set or part in ["-s", "-j"]:
                arg_base[part] = True
            else:
                sub_list = []
                for j in range(i + 1, t):
                    item = items[j]
                    if item in arg_base:
                        if part in bool_arg_set and not sub_list:
                            arg_base[part] = True
                        break
                    sub_list.append(item)
                    i += 1
                if sub_list:
                    arg_base[part] = " ".join(sub_list)
        i += 1
    link = []
    if items[0] not in arg_base:
        if arg_start == -1:
            link.extend(iter(items))
        else:
            link.extend(items[r] for r in range(arg_start))
        if link:
            arg_base["link"] = " ".join(link)
    return arg_base


async def get_content_type(url):
    try:
        async with ClientSession(trust_env=True) as session:
            async with session.get(url, verify_ssl=False) as response:
                return response.headers.get("Content-Type")
    except:
        return None


def update_user_ldata(id_, key, value):
    user_data.setdefault(id_, {})
    user_data[id_][key] = value


async def cmd_exec(cmd, shell=False):
    if shell:
        proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    else:
        proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    return stdout, stderr, proc.returncode


def new_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return bot_loop.create_task(func(*args, **kwargs))

    return wrapper


async def sync_to_async(func, *args, wait=True, **kwargs):
    pfunc = partial(func, *args, **kwargs)
    future = bot_loop.run_in_executor(THREADPOOL, pfunc)
    return await future if wait else future


def async_to_sync(func, *args, wait=True, **kwargs):
    future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
    return future.result() if wait else future


def new_thread(func):
    @wraps(func)
    def wrapper(*args, wait=False, **kwargs):
        future = run_coroutine_threadsafe(func(*args, **kwargs), bot_loop)
        return future.result() if wait else future
    return wrapper

def clean_video_name(file_path, compress=False):
    base_name = os.path.basename(file_path)
    final_name = os.path.splitext(base_name)[0]
    if compress:
        final_name = re.sub(r'[-._]?(360|480|540|720|1080)(p)?', '', final_name, flags=re.IGNORECASE)
    return final_name

async def create_session(uid):
    if uid in active_sessions:
        user_ses = active_sessions[uid]
        return user_ses
    else:
        user_dict = user_data.get(uid, {})
        string = user_dict.get("string_session", None)
        if string:
            try:
                user_ses = tgClient(
                    f"user_{uid}", 
                    TELEGRAM_API, 
                    TELEGRAM_HASH, 
                    session_string=string,
                    parse_mode=enums.ParseMode.HTML, 
                    max_concurrent_transmissions=10
                    )
                await user_ses.start()
                active_sessions[uid] = user_ses
                LOGGER.info(f"User_String untuk {uid} ditambahkan.")
                return user_ses
            except Exception as e:
                LOGGER.error(f"Error starting user session: {str(e)}")
                return None