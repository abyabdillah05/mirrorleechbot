#!/usr/bin/env python3
# Poweered by RKMBot and Rozakul Halim
# https://t.me/MRojeck_Lim
# mod by pikachu
# Enhanced version

from datetime import datetime
from http.cookies import SimpleCookie
from random import choice
from time import time

from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from urllib.parse import urlparse, unquote

from bot import bot
import time
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from asyncio import sleep as asleep

import cloudscraper
from cloudscraper import create_scraper

import requests as requestsx
import httpx
from aiohttp import ClientSession
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
from re import match
from requests import get as rget

# Aiohttp Async Client
#session = ClientSession()

# HTTPx Async Client
http = httpx.AsyncClient(
    http2=True,
    verify=False,
    timeout=httpx.Timeout(40),
)

class BypassException(Exception):
    def __init__(self, message, service_name=None, suggestion=None):
        self.service_name = service_name
        self.suggestion = suggestion
        super().__init__(message)
    
    def __str__(self):
        msg = super().__str__()
        if self.service_name:
            msg = f"[{self.service_name}] {msg}"
        if self.suggestion:
            msg = f"{msg}\n\nSaran: {self.suggestion}"
        return msg

class DDLException(Exception):
    """Tidak ada metode untuk extract link ini"""
    pass

# Helper Functions
async def get(url: str, *args, **kwargs):
    async with ClientSession() as session:
        async with session.get(url, *args, **kwargs) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = await resp.text()
        return data


async def head(url: str, *args, **kwargs):
    async with ClientSession() as session:
        async with session.head(url, *args, **kwargs) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = await resp.text()
        return data


async def post(url: str, *args, **kwargs):
    async with ClientSession() as session:
        async with session.post(url, *args, **kwargs) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = await resp.text()
        return data


async def show_progress_message(message, step, total_steps, title):
    progress = min(100, int((step / total_steps) * 100))
    progress_bar = "".join(["■" for _ in range(progress // 5)]) + "".join(["□" for _ in range(20 - (progress // 5))])
    
    text = f"<b>{title}</b>\n" \
           f"<code>{progress_bar}</code> {progress}%\n" \
           f"<i>Tahap {step}/{total_steps} - Mohon tunggu...</i>"
    
    await editMessage(message, text)


def format_bypass_result(url, result):
    host = urlparse(url).hostname
    
    if "<b>" in result or "<code>" in result:
        return result
        
    if "gdrive" in result.lower() or "drive.google.com" in result:
        return f"<b>🔗 Google Drive:</b>\n<code>{result}</code>"
    elif "mediafire" in host:
        return f"<b>🔗 MediaFire Direct Link:</b>\n<code>{result}</code>"
    elif any(x in host for x in ["mega.nz", "mega.co.nz"]):
        return f"<b>🔗 MEGA Link:</b>\n<code>{result}</code>"
    elif "dropbox" in host:
        return f"<b>🔗 Dropbox Direct Link:</b>\n<code>{result}</code>"
    elif "pixeldrain" in host:
        return f"<b>🔗 Pixeldrain Direct Link:</b>\n<code>{result}</code>"
    
    return f"<code>{result}</code>"


async def rentry(teks):
    start_message = "<b>📄 Hasil bypass sangat panjang! Menyiapkan halaman Rentry...</b>"
    
    cookie = SimpleCookie()
    kuki = (await http.get("https://rentry.co")).cookies
    cookie.load(kuki)
    kukidict = {key: value.value for key, value in cookie.items()}
    header = {"Referer": "https://rentry.co"}
    payload = {"csrfmiddlewaretoken": kukidict["csrftoken"], "text": teks}
    
    response = await http.post(
        "https://rentry.co/api/new",
        data=payload,
        headers=header,
        cookies=kukidict,
    )
    
    # Dapatkan URL dari respons JSON
    result_url = response.json().get("url")
    
    additional_text = "<i>• Hasil bypass sangat panjang dan telah dikirim ke Rentry untuk kemudahan pembacaan.</i>"
    final_result = f"\n<b>🔗 Link Rentry:</b> <a href='{result_url}'>{result_url}</a>\n\n{additional_text}"
    
    return final_result


def RecaptchaV3():
    import requests
    ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=ahgyd1gkfkhe'
    url_base = 'https://www.google.com/recaptcha/'
    post_data = "v={}&reason=q&c={}&k={}&co={}"
    client = requests.Session()
    client.headers.update({
        'content-type': 'application/x-www-form-urlencoded'
    })
    matches = re.findall(r'([api2|enterprise]+)\/anchor\?(.*)', ANCHOR_URL)[0]
    url_base += matches[0]+'/'
    params = matches[1]
    res = client.get(url_base+'anchor', params=params)
    token = re.findall(r'"recaptcha-token" value="(.*?)"', res.text)[0]
    params = dict(pair.split('=') for pair in params.split('&'))
    post_data = post_data.format(params["v"], token, params["k"], params["co"])
    res = client.post(url_base+'reload', params=f'k={params["k"]}', data=post_data)
    answer = re.findall(r'"rresp","(.*?)"', res.text)[0]    
    return answer


client = requests.Session()
client.headers.update({
    'authority': 'ouo.io',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'referer': 'http://www.google.com/ig/adde?moduleurl=',
    'upgrade-insecure-requests': '1',
})


def ouo_bypass(url: str) -> str:
    tempurl = url.replace("ouo.press", "ouo.io")
    p = urlparse(tempurl)
    id = tempurl.split('/')[-1]
    res = client.get(tempurl, impersonate="chrome110")
    next_url = f"{p.scheme}://{p.hostname}/go/{id}"

    for _ in range(2):
        if res.headers.get('Location'): break

        bs4 = BeautifulSoup(res.content, 'lxml')
        inputs = bs4.form.findAll("input", {"name": re.compile(r"token$")})
        data = { input.get('name'): input.get('value') for input in inputs }
        data['x-token'] = RecaptchaV3()
        
        h = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        
        res = client.post(next_url, data=data, headers=h, 
            allow_redirects=False, impersonate="chrome110")
        next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id}"
        url = res.headers.get('Location')

    return url


async def transcript(url: str, DOMAIN: str, ref: str, sltime) -> str:
    code = url.rstrip("/").split("/")[-1]
    try:
        cget = create_scraper(allow_brotli=False).request
        resp = cget("GET", f"{DOMAIN}/{code}", headers={"referer": ref})
        soup = BeautifulSoup(resp.content, "html.parser")
        data = { inp.get('name'): inp.get('value') for inp in soup.find_all("input") }
        
        await asleep(sltime)
        resp = cget("POST", f"{DOMAIN}/links/go", data=data, headers={ "x-requested-with": "XMLHttpRequest" })
        try: 
            return resp.json()['url']
        except: 
            return "❌ Gagal membypass link: API tidak memberikan respons yang valid."
    except Exception as e:
        return f"❌ Gagal membypass link: {str(e)}"


async def try2link(url: str) -> str:
    cget = create_scraper(allow_brotli=False).request
    url = url.rstrip("/")
    try:
        res = cget("GET", url, params=(('d', int(time()) + (60 * 4)),), headers={'Referer': 'https://fx-gd.net/'})
        soup = BeautifulSoup(res.text, 'html.parser')
        inputs = soup.find(id="go-link").find_all(name="input")
        data = { inp.get('name'): inp.get('value') for inp in inputs }    
        await asleep(7)
        headers = {'Host': 'try2link.com', 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://try2link.com', 'Referer': url}
        resp = cget('POST', 'https://try2link.com/links/go', headers=headers, data=data)
        try:
            return resp.json()["url"]
        except:
            raise BypassException("Gagal mengekstrak link", "Try2Link", "Coba lagi nanti atau gunakan layanan lain")
    except Exception as e:
        raise BypassException(f"Error: {str(e)}", "Try2Link")


async def gyanilinks(url: str) -> str:
    DOMAIN = "https://go.hipsonyc.com/"
    cget = create_scraper(allow_brotli=False).request
    code = url.rstrip("/").split("/")[-1]
    try:
        soup = BeautifulSoup(cget("GET", f"{DOMAIN}/{code}").content, "html.parser")
        inputs = soup.find(id="go-link").find_all(name="input")
        await asleep(5)
        resp = cget("POST", f"{DOMAIN}/links/go", data={ input.get('name'): input.get('value') for input in inputs }, headers={ "x-requested-with": "XMLHttpRequest" })
        try: 
            return resp.json()['url']
        except:
            return "❌ Gagal membypass link"
    except:
        return "❌ Gagal membypass link"


async def mdisk(url: str) -> str: # Depreciated ( Code Preserved )
    header = {'Accept': '*/*', 
         'Accept-Language': 'en-US,en;q=0.5', 
         'Accept-Encoding': 'gzip, deflate, br', 
         'Referer': 'https://mdisk.me/', 
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36' }
    URL = f'https://diskuploader.entertainvideo.com/v1/file/cdnurl?param={url.rstrip("/").split("/")[-1]}'
    res = rget(url=URL, headers=header).json() 
    return res['download'] + '\n\n' + res['source']


async def shareus(url: str) -> str: 
    DOMAIN = "https://api.shrslink.xyz" 
    cget = create_scraper().request
    try:
        params = {'shortid': url.rstrip('/').split("/")[-1] , 'initial': 'true', 'referrer': 'https://shareus.io/'}
        headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        resp = cget("GET", f'{DOMAIN}/v', params=params, headers=headers)
        for page in range(1, 4): 
            resp = cget("POST", f'{DOMAIN}/v', headers=headers, json={'current_page': page}) 
        try:
            return (cget('GET', f'{DOMAIN}/get_link', headers=headers).json())["link_info"]["destination"]
        except:
            return "❌ Gagal membypass link"
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
    
async def linkvertise(url: str) -> str:
    try:
        resp = rget('https://bypass.pm/bypass2', params={'url': url}).json()
        if resp["success"]: 
            return resp["destination"]
        else: 
            return "❌ Gagal membypass link"
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def rslinks(url: str) -> str:
    try:
        resp = rget(url, stream=True, allow_redirects=False)
        code = resp.headers["location"].split('ms9')[-1]
        try:
            return f"http://techyproio.blogspot.com/p/short.html?{code}=="
        except:
            return "❌ Gagal membypass link"
    except Exception as e:
        return f"❌ Error: {str(e)}"
      

async def shorter(url: str) -> str:
    try:
        cget = create_scraper().request 
        resp = cget("GET", url, allow_redirects=False)
        return resp.headers['Location']
    except: 
        return "❌ Gagal membypass link"


async def appurl(url: str):
    try:
        cget = create_scraper().request 
        resp = cget("GET", url, allow_redirects=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.select('meta[property="og:url"]')[0]['content']
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
    
async def surl(url: str):
    try:
        cget = create_scraper().request
        resp = cget("GET", f"{url}+")
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.select('p[class="long-url"]')[0].string.split()[1]
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def shrtco(url: str) -> str:
    try:
        code = url.rstrip("/").split("/")[-1]
        return rget(f'https://api.shrtco.de/v2/info?code={code}').json()['result']['url']
    except: 
        return "❌ Gagal membypass link"
    

async def thinfi(url: str) -> str:
    try: 
        return BeautifulSoup(rget(url).content, "html.parser").p.a.get("href")
    except: 
        return "❌ Gagal membypass link"


def pling_bypass(url):
    try:
        id_url = re.search(r"https?://(store.kde.org|www.pling.com)\/p\/(\d+)", url)[2]
        link = f"https://www.pling.com/p/{id_url}/loadFiles"
        res = requestsx.get(link)
        json_dic_files = res.json().pop("files")
        msg = f"**Source Link** :\n`{url}`\n**Direct Link :**\n"
        mss = "<b>Pling Direct Link :</b>\n"
        
        for i in json_dic_files:
            file_name = i["name"]
            file_url = unquote(i["url"])
            file_size = get_readable_file_size(int(i["size"]))
            
            msg_line = f'**→ [{file_name}]({file_url}) ({file_size})**'
            mss_line = f"📄 <a href='{file_url}'>{file_name}</a> ({file_size})\n"
            
            msg += "\n" + msg_line
            mss += "<br>" + mss_line
            err = f"Link Pling yang anda coba mirror salah, silahkan bypass terlebih dahulu dengan command <code>/bypass</code> dan pastikan linknya tidak mengarah ke sourceforge atau hosting yang lain."
        
        if len(mss) > 4000:
            return msg
        else:
            return mss
    except Exception:
        return err


async def direct(_, message):
    if message.caption is not None:
        args = message.caption.split()
    else:
        args = message.text.split()
    link = ''
    if len(args) > 1:
        link = args[1]
    elif reply_to := message.reply_to_message:
        if reply_to.caption is not None:
            link = reply_to.caption
        else:
            link = reply_to.text
    else:
        link = ''

    if is_url(link):
        s = datetime.now()
        loading_messages = [
            "🔄 <b>Memulai proses bypass...</b>",
            "🔎 <b>Mencari jalur bypass...</b>",
            "⚡ <b>Menyiapkan metode ekstraksi...</b>",
            "🔓 <b>Membuka blokir link...</b>",
            "🔍 <b>Menganalisis struktur URL...</b>"
        ]
        loading_msg = choice(loading_messages)
        mess = f"{loading_msg}\n\n<code>{link}</code>"
        ray = await sendMessage(message, mess)
        try:
            await asleep(1)
            if 'ouo.io' in link or 'ouo.press' in link:
                await editMessage(ray, f"⏳ <b>Memproses link OUO</b>\n<i>Mohon tunggu, ini bisa memakan waktu...</i>\n\n<code>{link}</code>")
                res = await sync_to_async(ouo_bypass, link)
            elif 'uptobox.com' in link:
                res = f"⚠️ Uptobox sudah tidak dapat dibypass. Gunakan metode lain."
            elif bool(match(r"https?:\/\/try2link\.\S+", link)):
                await editMessage(ray, f"⏳ <b>Memproses Try2Link...</b>\n\n<code>{link}</code>")
                res = await try2link(link)
            elif bool(match(r"https?:\/\/ronylink\.\S+", link)):
                await editMessage(ray, f"⏳ <b>Memproses RonyLink...</b>\n\n<code>{link}</code>")
                res = await transcript(link, "https://go.ronylink.com/", "https://livejankari.com/", 9)
            elif bool(match(r"https?:\/\/(gyanilinks|gtlinks)\.\S+", link)):
                await editMessage(ray, f"⏳ <b>Memproses GyaniLinks...</b>\n\n<code>{link}</code>")
                res = await gyanilinks(link)
            elif bool(match(r"https?:\/\/.+\.tnshort\.\S+", link)):
                await editMessage(ray, f"⏳ <b>Memproses TNShort...</b>\n\n<code>{link}</code>")
                res = await transcript(link, "https://go.tnshort.net/", "https://market.finclub.in/", 8)
            elif bool(match(r"https?:\/\/(xpshort|push.bdnewsx|techymozo)\.\S+", link)):
                res = await transcript(link, "https://techymozo.com/", "https://portgyaan.in/", 8)
            elif bool(match(r"https?:\/\/go.lolshort\.\S+", link)):
                res = await transcript(link, "https://get.lolshort.tech/", "https://tech.animezia.com/", 8)
            elif bool(match(r"https?:\/\/onepagelink\.\S+", link)):
                res = await transcript(link, "https://go.onepagelink.in/", "https://gorating.in/", 3.1)
            elif bool(match(r"https?:\/\/earn.moneykamalo\.\S+", link)):
                res = await transcript(link, "https://go.moneykamalo.com/", "https://bloging.techkeshri.com/", 4)
            elif bool(match(r"https?:\/\/droplink\.\S+", link)):
                res = await transcript(link, "https://droplink.co/", "https://tiktokcounter.net/", 3.1)
            elif bool(match(r"https?:\/\/tinyfy\.\S+", link)):
                res = await transcript(link, "https://tinyfy.in", "https://www.yotrickslog.tech/", 0)
            elif bool(match(r"https?:\/\/adrinolinks\.\S+", link)):
                res = await transcript(link, "https://adrinolinks.in", "https://bhojpuritop.in/", 8)
            elif bool(match(r"https?:\/\/krownlinks\.\S+", link)):
                res = await transcript(link, "https://go.hostadviser.net/", "blog.hostadviser.net/", 8)
            elif bool(match(r"https?:\/\/(du-link|dulink)\.\S+", link)):
                res = await transcript(link, "https://du-link.in", "https://profitshort.com/", 0)
            elif bool(match(r"https?:\/\/indianshortner\.\S+", link)):
                res = await transcript(link, "https://indianshortner.com/", "https://moddingzone.in/", 5)
            elif bool(match(r"https?:\/\/m.easysky\.\S+", link)):
                res = await transcript(link, "https://techy.veganab.co/", "https://veganab.co/", 8)
                res = await transcript(link, "https://vip.linkbnao.com", "https://ffworld.xyz/", 2)
            elif bool(match(r"https?:\/\/.+\.tnlink\.\S+", link)):
                res = await transcript(link, "https://go.tnshort.net/", "https://market.finclub.in/", 0.8)
            elif bool(match(r"https?:\/\/link4earn\.\S+", link)):
                res = await transcript(link, "https://link4earn.com", "https://studyis.xyz/", 6)
            elif bool(match(r"https?:\/\/shortingly\.\S+", link)):
                res = await transcript(link, "https://go.blogytube.com/", "https://blogytube.com/", 5)
            elif bool(match(r"https?:\/\/short2url\.\S+", link)):
                res = await transcript(link, "https://techyuth.xyz/blog", "https://blog.coin2pay.xyz/", 10)
            elif bool(match(r"https?:\/\/urlsopen\.\S+", link)):
                res = await transcript(link, "https://s.humanssurvival.com/", "https://1topjob.xyz/", 5)
            elif bool(match(r"https?:\/\/mdisk\.\S+", link)):
                res = await transcript(link, "https://mdisk.pro", "https://m.meclipstudy.in/", 8)
            elif bool(match(r"https?:\/\/(pkin|go.paisakamalo)\.\S+", link)):
                res = await transcript(link, "https://go.paisakamalo.in", "https://healthtips.techkeshri.com/", 5)
            elif bool(match(r"https?:\/\/linkpays\.\S+", link)):
                res = await transcript(link, "https://tech.smallinfo.in/Gadget/", "https://finance.filmypoints.in/", 6)
            elif bool(match(r"https?:\/\/sklinks\.\S+", link)):
                res = await transcript(link, "https://sklinks.in", "https://dailynew.online/", 5)
            elif bool(match(r"https?:\/\/link1s\.\S+", link)):
                res = await transcript(link, "https://link1s.com", "https://anhdep24.com/", 9)
            elif bool(match(r"https?:\/\/tulinks\.\S+", link)):
                res = await transcript(link, "https://tulinks.one", "https://www.blogger.com/", 8)
            elif bool(match(r"https?:\/\/.+\.tulinks\.\S+", link)):
                res = await transcript(link, "https://go.tulinks.online", "https://tutelugu.co/", 8)
            elif bool(match(r"https?:\/\/(.+\.)?vipurl\.\S+", link)):
                res = await transcript(link, "https://count.vipurl.in/", "https://kiss6kartu.in/", 5)
            elif bool(match(r"https?:\/\/indyshare\.\S+", link)):
                res = await transcript(link, "https://indyshare.net", "https://insurancewolrd.in/", 3.1)
            elif bool(match(r"https?:\/\/linkyearn\.\S+", link)):
                res = await transcript(link, "https://linkyearn.com", "https://gktech.uk/", 5)
            elif bool(match(r"https?:\/\/earn4link\.\S+", link)):
                res = await transcript(link, "https://m.open2get.in/", "https://ezeviral.com/", 8)
            elif bool(match(r"https?:\/\/linksly\.\S+", link)):
                res = await transcript(link, "https://go.linksly.co/", "https://en.themezon.net/", 5)
            elif bool(match(r"https?:\/\/.+\.mdiskshortner\.\S+", link)):
                res = await transcript(link, "https://loans.yosite.net/", "https://yosite.net/", 10)
            elif bool(match(r"https?://(?:\w+\.)?rocklinks\.\S+", link)):
                res = await transcript(link, "https://insurance.techymedies.com/", "https://blog.disheye.com/", 5)
            elif bool(match(r"https?:\/\/mplaylink\.\S+", link)):
                res = await transcript(link, "https://tera-box.cloud/", "https://mvplaylink.in.net/", 5)
            elif bool(match(r"https?:\/\/(shrinke|shrinkme)\.\S+", link)):
                res = await transcript(link, "https://en.shrinke.me/", "https://themezon.net/", 15)
            elif bool(match(r"https?:\/\/urlspay\.\S+", link)):
                res = await transcript(link, "https://finance.smallinfo.in/", "https://tech.filmypoints.in/", 5)
            elif bool(match(r"https?:\/\/.+\.tnvalue\.\S+", link)):
                res = await transcript(link, "https://page.finclub.in/", "https://finclub.in/", 8)
            elif bool(match(r"https?:\/\/sxslink\.\S+", link)):
                res = await transcript(link, "https://getlink.sxslink.com/", "https://cinemapettai.in/", 5)
            elif bool(match(r"https?:\/\/ziplinker\.\S+", link)):
                res = await transcript(link, "https://ziplinker.net/web/", "https://ontechhindi.com/", 5)
            elif bool(match(r"https?:\/\/moneycase\.\S+", link)):
                res = await transcript(link, "https://last.moneycase.link/", "https://www.infokeeda.xyz/", 3.1)
            elif bool(match(r"https?:\/\/urllinkshort\.\S+", link)):
                res = await transcript(link, "https://web.urllinkshort.in", "https://suntechu.in/", 5)
            elif bool(match(r"https?:\/\/.+\.dtglinks\.\S+", link)):
                res = await transcript(link, "https://happyfiles.dtglinks.in/", "https://tech.filohappy.in/", 5)
            elif bool(match(r"https?:\/\/v2links\.\S+", link)):
                res = await transcript(link, "https://vzu.us/", "https://newsbawa.com/", 5)
            elif bool(match(r"https?:\/\/kpslink\.\S+", link)):
                res = await transcript(link, "https://kpslink.in/", "https://infotamizhan.xyz/", 3.1)
            elif bool(match(r"https?:\/\/v2.kpslink\.\S+", link)):
                res = await transcript(link, "https://v2.kpslink.in/", "https://infotamizhan.xyz/", 5)
            elif bool(match(r"https?:\/\/tamizhmasters\.\S+", link)):
                res = await transcript(link, "https://tamizhmasters.com/", "https://pokgames.com/", 5)
            elif bool(match(r"https?:\/\/tglink\.\S+", link)):
                res = await transcript(link, "https://tglink.in/", "https://www.proappapk.com/", 5)
            elif bool(match(r"https?:\/\/pandaznetwork\.\S+", link)):
                res = await transcript(link, "https://pandaznetwork.com/", "https://panda.freemodsapp.xyz/", 5)
            elif bool(match(r"https?:\/\/url4earn\.\S+", link)):
                res = await transcript(link, "https://go.url4earn.in/", "https://techminde.com/", 8)
            elif bool(match(r"https?:\/\/ez4short\.\S+", link)):
                res = await transcript(link, "https://ez4short.com/", "https://ez4mods.com/", 5)
            elif bool(match(r"https?:\/\/dalink\.\S+", link)):
                res = await transcript(link,"https://get.tamilhit.tech/MR-X/tamil/", "https://www.tamilhit.tech/", 8)
            elif bool(match(r"https?:\/\/.+\.omnifly\.\S+", link)):
                res = await transcript(link, "https://f.omnifly.in.net/", "https://ignitesmm.com/", 5)
            elif bool(match(r"https?:\/\/sheralinks\.\S+", link)):
                res = await transcript(link, "https://sheralinks.com/", "https://blogyindia.com/", 0.8)
            elif bool(match(r"https?:\/\/bindaaslinks\.\S+", link)):
                res = await transcript(link, "https://thebindaas.com/blog/", "https://blog.appsinsta.com/", 5)
            elif bool(match(r"https?:\/\/viplinks\.\S+", link)):
                res = await transcript(link, "https://m.vip-link.net/", "https://m.leadcricket.com/", 5)
            elif bool(match(r"https?:\/\/.+\.short2url\.\S+", link)):
                res = await transcript(link, "https://techyuth.xyz/blog/", "https://blog.mphealth.online/", 10)
            elif bool(match(r"https?:\/\/shrinkforearn\.\S+", link)):
                res = await transcript(link, "https://shrinkforearn.in/", "https://wp.uploadfiles.in/", 8)
            elif bool(match(r"https?:\/\/bringlifes\.\S+", link)):
                res = await transcript(link, "https://bringlifes.com/", "https://loanoffering.in/", 5)
            elif bool(match(r"https?:\/\/.+\.linkfly\.\S+", link)):
                res = await transcript(link, "https://insurance.yosite.net/", "https://yosite.net/", 10)
            elif bool(match(r"https?:\/\/.+\.anlinks\.\S+", link)):
                res = await transcript(link,"https://anlinks.in/","https://dsblogs.fun/", 5)
            elif bool(match(r"https?:\/\/.+\.earn2me\.\S+", link)):
                res = await transcript(link, "https://blog.filepresident.com/", "https://easyworldbusiness.com/", 5)
            elif bool(match(r"https?:\/\/.+\.vplinks\.\S+", link)):
                res = await transcript(link, "https://get.vplinks.in/", "https://infotamizhan.xyz/", 5)
            elif bool(match(r"https?:\/\/.+\.narzolinks\.\S+", link)):
                res = await transcript(link, "https://go.narzolinks.click/", "https://hydtech.in/", 5)
            elif bool(match(r"https?:\/\/adsfly\.\S+", link)):
                res = await transcript(link, "https://go.adsfly.in/", "https://loans.quick91.com/", 5)
            elif bool(match(r"https?:\/\/earn2short\.\S+", link)):
                res = await transcript(link, "https://go.earn2short.in/", "https://tech.insuranceinfos.in/", 0.8)
            elif bool(match(r"https?:\/\/instantearn\.\S+", link)):
                res = await transcript(link, "https://get.instantearn.in/", "https://love.petrainer.in/", 5)
            elif bool(match(r"https?:\/\/linkjust\.\S+", link)):
                res = await transcript(link, "https://linkjust.com/", "https://forexrw7.com/", 3.1)
            elif bool(match(r"https?:\/\/pdiskshortener\.\S+", link)):
                res = await transcript(link, "https://pdiskshortener.com/", "", 10)
            elif bool(match(r"https?:\/\/(shareus|shrs)\.\S+", link)):
                res = await shareus(link)
            elif bool(match(r"https?:\/\/linkvertise\.\S+", link)):
                res = await linkvertise(link)
            elif bool(match(r"https?:\/\/rslinks\.\S+", link)):
                res = await rslinks(link)
            elif bool(match(r"https?:\/\/(bit|tinyurl|(.+\.)short|shorturl)\.\S+", link)):
                res = await shorter(link)
            elif bool(match(r"https?:\/\/appurl\.\S+", link)):
                res = await appurl(link)
            elif bool(match(r"https?:\/\/surl\.\S+", link)):
                res = await surl(link)
            elif bool(match(r"https?:\/\/thinfi\.\S+", link)):
                res = await thinfi(link)
            elif 'pling.com' in link:
                res = await sync_to_async(pling_bypass, link)
            else:
                await editMessage(ray, f"🔄 <b>Menggunakan generator direct link generik...</b>\n\n<code>{link}</code>")
                res = await sync_to_async(direct_link_generator, link)
            
            # Format the result for better presentation
            res = format_bypass_result(link, res)
            
            if len(res) > 3500:
                await editMessage(ray, f"📄 <b>Hasil terlalu panjang! Menyiapkan rentry...</b>\n\n<code>{link}</code>")
                res = await rentry(res)
            
            await asleep(1)
            e = datetime.now()
            ms = (e - s).seconds
            host = urlparse(link).netloc
            
            # Format username
            if message.from_user.username:
                uname = f'@{message.from_user.username}'
            else:
                uname = f'<code>{message.from_user.first_name}</code>'
            
            if uname is not None:
                cc = f'\n<b>👤 Diminta oleh:</b> {uname}'
            
            # Create a more visually appealing message
            success_message = (
                f"<b>🌐 <u>Link Original</u></b>\n"
                f"<code>{link}</code>\n\n"
                f"<b>✅ <u>Hasil Bypass</u></b>\n"
                f"{res}\n\n"
                f"<b>⏱️ Waktu Proses:</b> <code>{ms}s</code>\n"
                f"<b>🔗 Domain:</b> <code>{host}</code>"
            )
            
            buttons = ButtonMaker()
            buttons.ubutton("❤️ 𝚂𝚞𝚙𝚙𝚘𝚛𝚝 𝙼𝚎", "https://telegra.ph/Donate-and-Support-Us-03-21", "footer")
            button = buttons.build_menu(1)
            await editMessage(ray, success_message + cc, button)
            
        except Exception as e:
            await asleep(1)
            buttons = ButtonMaker()
            buttons.ubutton("📚 Daftar Link Didukung", "https://gist.github.com/aenulrofik/20405f81fc9da2d12478a5754b7bf34e")
            buttons.ubutton("🔄 Coba Lagi", f"/bypass {link}")
            b_limz = buttons.build_menu(2)
            error_message = f"<b>⚠️ Gagal membypass link!</b>\n<i>{str(e)}</i>\n\n<b>Link:</b> <code>{link}</code>"
            await editMessage(ray, error_message, b_limz)

    elif len(message.command) == 1:
         buttons = ButtonMaker()
         buttons.ubutton("📚 Daftar Link Didukung", "https://gist.github.com/aenulrofik/20405f81fc9da2d12478a5754b7bf34e")
         buttons.ubutton("💡 Cara Penggunaan", f"/help {BotCommands.DirectCommand[0]}")
         b_limz1 = buttons.build_menu(2)
         help_text = (
            "<b>⚠️ Link tidak ditemukan!</b>\n\n"
            "<b>Cara Penggunaan:</b>\n"
            f"<code>/{BotCommands.DirectCommand[0]} link_shorterurl</code>\n"
            "atau balas ke pesan yang berisi link dengan perintah ini."
         )
         await sendMessage(message, help_text, b_limz1)


bot.add_handler(MessageHandler(direct, filters=command(BotCommands.DirectCommand) & CustomFilters.authorized))