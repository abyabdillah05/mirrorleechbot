import base64
import urllib3

from hashlib import sha256
from http.cookiejar import MozillaCookieJar
from json import loads
from os import path
from re import findall, match, search
from time import sleep
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from lxml.etree import HTML
from requests import Session, post
from requests import session as req_session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot import config_dict
from bot.helper.ext_utils.status_utils import speed_string_to_bytes, get_readable_time
from bot.helper.ext_utils.links_utils import is_share_link
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.ext_utils.help_messages import PASSWORD_ERROR_MESSAGE


_caches = {}

user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"

def direct_link_generator(link: str):
    """ direct links generator """
    domain = urlparse(link).hostname
    if not domain:
        raise DirectDownloadLinkException("ERROR: URL Salah!")
    if "youtube.com" in domain or "youtu.be" in domain:
        raise DirectDownloadLinkException(
            "ERROR: Gunakan perintah YT-DLP untuk mengunduh Youtube!")
    elif "mediafire.com" in domain:
        return mediafire(link)
    elif "uptobox.com" in domain:
        return uptobox(link)
    elif "osdn.net" in domain:
        return osdn(link)
    elif "github.com" in domain:
        return github(link)
    elif "hxfile.co" in domain:
        return hxfile(link)
    elif "1drv.ms" in domain:
        return onedrive(link)
    elif "pixeldrain.com" in domain:
        return pixeldrain(link)
    elif "racaty" in domain:
        return racaty(link)
    elif "1fichier.com" in domain:
        if len(config_dict['ALLDEBRID_API']) == 0:
            return fichier(link)
        else:
            return alldebrid(link)
    elif "solidfiles.com" in domain:
        return solidfiles(link)
    elif "krakenfiles.com" in domain:
        return krakenfiles(link)
    elif "upload.ee" in domain:
        return uploadee(link)
    elif "gofile.io" in domain:
        return gofile(link)
    elif "send.cm" in domain:
        if len(config_dict['ALLDEBRID_API']) == 0:
            return send_cm(link)
        else:
            return alldebrid(link)
    elif "easyupload.io" in domain:
        return easyupload(link)
    elif "streamvid.net" in domain:
        return streamvid(link)
    elif "shrdsk.me" in domain:
        return shrdsk(link)
    elif "u.pcloud.link" in domain:
        return pcloud(link)
    elif any(x in domain for x in ["akmfiles.com", "akmfls.xyz"]):
        return akmfiles(link)
    elif any(
        x in domain
        for x in [
            "dood.watch",
            "doodstream.com",
            "dood.to",
            "dood.so",
            "dood.cx",
            "dood.la",
            "dood.ws",
            "dood.sh",
            "doodstream.co",
            "dood.pm",
            "dood.wf",
            "dood.re",
            "dood.video",
            "dooood.com",
            "dood.yt",
            "doods.yt",
            "dood.stream",
            "doods.pro",
            "ds2play.com",
        ]
    ):
        return pake(link)
    elif any(
        x in domain
        for x in [
            "streamtape.com",
            "streamtape.co",
            "streamtape.cc",
            "streamtape.to",
            "streamtape.net",
            "streamta.pe",
            "streamtape.xyz",
        ]
    ):
        return streamtape(link)
    elif any(x in domain for x in ["wetransfer.com", "we.tl"]):
        return wetransfer(link)
    elif any(
        x in domain
        for x in [
            "terabox.com",
            "nephobox.com",
            "4funbox.com",
            "mirrobox.com",
            "momerybox.com",
            "teraboxapp.com",
            "1024tera.com",
            "terabox.app",
        ]
    ):
        return terabox(link)
    elif any(
        x in domain
        for x in [
            "filelions.co",
            "filelions.site",
            "filelions.live",
            "filelions.to",
            "filelions.online",
            "cabecabean.lol",
            "embedwish.com",
            "streamwish.com",
            "kitabmarkaz.xyz",
            "wishfast.top",
            "streamwish.to",
        ]
    ):
        return filelions_and_streamwish(link)
    elif any(x in domain for x in ["streamhub.ink", "streamhub.to"]):
        return streamhub(link)
    elif any(x in domain for x in ["linkbox.to", "lbx.to"]):
        return linkBox(link)
    elif is_share_link(link):
        if "gdtot" in domain:
            return gdtot(link)
        elif "filepress" in domain:
            return filepress(link)
        else:
            return sharer_scraper(link)
    elif any(
        x in domain
        for x in [
            "anonfiles.com",
            "zippyshare.com",
            "letsupload.io",
            "hotfile.io",
            "bayfiles.com",
            "megaupload.nz",
            "letsupload.cc",
            "filechan.org",
            "myfile.is",
            "vshare.is",
            "rapidshare.nu",
            "lolabits.se",
            "openload.cc",
            "share-online.is",
            "upvid.cc",
            "uptobox.com",
            "uptobox.fr",
        ]
    ):
        raise DirectDownloadLinkException(f"ERROR: R.I.P {domain}")
    elif "mp4upload.com" in domain:
        return mp4upload(link)
    elif "androiddatahost.com" in domain:
        return androiddatahost(link)
    elif "apkadmin.com" in domain or "sharemods.com" in domain:
        return apkadmin(link)
    elif "sourceforge" in domain:
        return sourceforge(link)
    elif "androidfilehost.com" in link:
        return androidfilehost(link)
    elif "tusfiles.net" in domain or "tusfiles.com" in domain:
        return tusfiles(link)
    elif "pandafiles.com" in domain:
        return pandafiles(link)
    elif "uploadhaven.com" in domain:
        return uploadhaven(link)
    elif "uploadrar.com" in domain:
        return uploadrar(link)
    elif "romsget.io" in domain:
        return link if domain == "static.romsget.io" else romsget(link)
    elif "hexupload.net" in domain:
        return hexupload(link)
    # Add AllDebrid supported link here
    elif any(
        x in domain
        for x in [
            "4shared.com",
            "alfafile.net",
            "alterupload.com",
            "apkadmin.com",
            "cjoint.net",
            "clickndownload.org",
            "clicknupload.co",
            "clicknupload.vip",
            "clipwatching.com",
            "darkibox.com",
            "ddl.to",
            "desfichiers.com",
            "dfichiers.com",
            "dl4free.com",
            "drop.download",
            "dropapk.to",
            "dropgalaxy.in",
            "fastbit.cc",
            "file-upload.com",
            "file.al",
            "filedot.to",
            "filedot.xyz",
            "filespace.com",
            "flashbit.cc",
            "gigapeta.com",
            "gulf-up.com",
            "harefile.com",
            "hexupload.net",
            "hitf.cc",
            "hitf.to",
            "hitfile.net",
            "htfl.net",
            "isra.cloud",
            "load.to",
            "megadl.fr",
            "mesfichiers.org",
            "mexa.sh",
            "mexashare.com",
            "modsbase.com",
            "mp4upload.com",
            "piecejointe.net",
            "pjointe.com",
            "playvidto.com",
            "prefiles.com",
            "rapidfileshare.net",
            "rapidgator.net",
            "rg.to",
            "scribd.com",
            "sendit.cloud",
            "sharemods.com",
            "simfileshare.net",
            "tenvoi.com",
            "trbbt.net",
            "turb.cc",
            "turb.pw",
            "turbo.to",
            "turbobif.com",
            "turbobit.cc",
            "turbobit.cloud",
            "turbobit.net",
            "up-4ever.net",
            "up-load.io",
            "upload-4ever.com",
            "upload42.com",
            "uploadboy.com",
            "uploadev.com",
            "uploadev.org",
            "uploadrar.com",
            "uploadydl.com",
            "uppit.com",
            "userscloud.com",
            "userupload.net",
            "vev.io",
            "vidoza.net",
            "vidoza.org",
            "vidto-do.com",
            "vidtodo.com",
            "vipfile.cc",
            "wayupload.com",
            "world-files.com",
            "worldbytez.com",
        ]
    ):
        return alldebrid(link)
    else:
        raise DirectDownloadLinkException(
            f"Tidak ada fungsi Generator Direct Link untuk {link}")


def get_captcha_token(session, params):
    recaptcha_api = "https://www.google.com/recaptcha/api2"
    res = session.get(f"{recaptcha_api}/anchor", params=params)
    anchor_html = HTML(res.text)
    if not (anchor_token := anchor_html.xpath('//input[@id="recaptcha-token"]/@value')):
        return
    params["c"] = anchor_token[0]
    params["reason"] = "q"
    res = session.post(f"{recaptcha_api}/reload", params=params)
    if token := findall(r'"rresp","(.*?)"', res.text):
        return token[0]


def uptobox(url):
    try:
        urls = findall(r"\bhttps?://.*uptobox\.com\S+", url)[0]
    except IndexError:
        raise DirectDownloadLinkException("ERROR: Link Uptobox tidak ditemukan!")
    if urls := findall(r"\bhttps?://.*\.uptobox\.com/dl\S+", url):
        return urls[0]
    if "::" in url:
        _password = url.split("::")[-1]
    else:
        _password = None
    with create_scraper() as session:
        try:
            file_id = findall(r"\bhttps?://.*uptobox\.com/(\w+)", url)[0]
            if UPTOBOX_TOKEN := config_dict["UPTOBOX_TOKEN"]:
                file_link = f"https://uptobox.com/api/link?token={UPTOBOX_TOKEN}&file_code={file_id}"
            else:
                file_link = f"https://uptobox.com/api/link?file_code={file_id}"
            if _password:
                file_link = file_link + f"&password={_password}"
            res = session.get(file_link).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if res["statusCode"] == 0:
            return res["data"]["dlLink"]
        elif res["statusCode"] == 16:
            sleep(1)
            waiting_token = res["data"]["waitingToken"]
            sleep(res["data"]["waiting"])
        elif res["statusCode"] == 17:
            raise DirectDownloadLinkException(f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}")
        elif res["statusCode"] == 39:
            raise DirectDownloadLinkException(
                f"ERROR: Uptobox sedang limit! Silahkan tunggu {get_readable_time(res['data']['waiting'])} lagi!")
        else:
            raise DirectDownloadLinkException(f"ERROR: {res['message']}")
        try:
            res = session.get(f"{file_link}&waitingToken={waiting_token}").json()
            return res["data"]["dlLink"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")


def mediafire(url, session=None):
    if "/folder/" in url:
        return mediafireFolder(url)
    if final_link := findall(r"https?:\/\/download\d+\.mediafire\.com\/\S+\/\S+\/\S+", url):
        return final_link[0]
    if session is None:
        session = Session()
        parsed_url = urlparse(url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    try:
        html = HTML(session.get(url).text)
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if error:= html.xpath("//p[@class='notranslate']/text()"):
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {error[0]}")
    if not (final_link := html.xpath("//a[@id='downloadButton']/@href")):
        session.close()
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    if final_link[0].startswith("//"):
        return mediafire(f"https://{final_link[0][2:]}", session)
    session.close()
    return final_link[0]


def mediafireFolder(url):
    try:
        raw = url.split("/", 4)[-1]
        folderkey = raw.split("/", 1)[0]
        folderkey = folderkey.split(",")
    except:
        raise DirectDownloadLinkException("ERROR: Link Folder tidak ditemukan!")
    if len(folderkey) == 1:
        folderkey = folderkey[0]
    details = {"contents": [], "title": "", "total_size": 0, "header": ""}
    
    session = session()
    adapter = HTTPAdapter(max_retries=Retry(
        total=10, read=10, connect=10, backoff_factor=0.3))
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session = create_scraper(
        browser={"browser": "firefox", "platform": "windows", "mobile": False},
        delay=10,
        sess=session,
    )
    folder_infos = []

    def __get_info(folderkey):
        try:
            if isinstance(folderkey, list):
                folderkey = ",".join(folderkey)
            _json = session.post("https://www.mediafire.com/api/1.5/folder/get_info.php", data={
                "recursive": "yes",
                "folder_key": folderkey,
                "response_format": "json"
            }).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Info Folder!")
        _res = _json["response"]
        if "folder_infos" in _res:
            folder_infos.extend(_res["folder_infos"])
        elif "folder_info" in _res:
            folder_infos.append(_res["folder_info"])
        elif "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")
        else:
            raise DirectDownloadLinkException("ERROR: Info Folder tidak ditemukan!")


    try:
        __get_info(folderkey)
    except Exception as e:
        raise DirectDownloadLinkException(e)

    details["title"] = folder_infos[0]["name"]

    def __scraper(url):
        try:
            html = HTML(session.get(url).text)
        except:
            return
        if final_link := html.xpath("//a[@id='downloadButton']/@href"):
            return final_link[0]

    def __get_content(folderKey, folderPath="", content_type="folders"):
        try:
            params = {
                "content_type": content_type,
                "folder_key": folderKey,
                "response_format": "json",
            }
            _json = session.get("https://www.mediafire.com/api/1.5/folder/get_content.php", params=params).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Info File!")
        _res = _json["response"]
        if "message" in _res:
            raise DirectDownloadLinkException(f"ERROR: {_res['message']}")
        _folder_content = _res["folder_content"]
        if content_type == "folders":
            folders = _folder_content["folders"]
            for folder in folders:
                if folderPath:
                    newFolderPath = path.join(folderPath, folder["name"])
                else:
                    newFolderPath = path.join(folder["name"])
                __get_content(folder["folderkey"], newFolderPath)
            __get_content(folderKey, folderPath, "files")
        else:
            files = _folder_content["files"]
            for file in files:
                item = {}
                if not (_url := __scraper(file["links"]["normal_download"])):
                    continue
                item["filename"] = file["filename"]
                if not folderPath:
                    folderPath = details["title"]
                item["path"] = path.join(folderPath)
                item["url"] = _url
                if "size" in file:
                    size = file["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)
    try:
        for folder in folder_infos:
            __get_content(folder["folderkey"], folder["name"])
    except Exception as e:
        raise DirectDownloadLinkException(e)
    finally:
        session.close()
    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def osdn(url):
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if not (direct_link:= html.xapth("//a[@class='mirror_link']/@href")):
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        return f"https://osdn.net{direct_link[0]}"


def github(url):
    try:
        findall(r"\bhttps?://.*github\.com.*releases\S+", url)[0]
    except IndexError:
        raise DirectDownloadLinkException("Link Github Release tidak ditemukan!")
    with create_scraper() as session:
        _res = session.get(url, stream=True, allow_redirects=False)
        if "location" in _res.headers:
            return _res.headers["location"]
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def hxfile(url):
    with create_scraper() as session:
        try:
            file_code = url.split("/")[-1]
            html = HTML(session.post(url, data={"op": "download2", "id": file_code}).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if direct_link:= html.xpath("//a[@class='btn btn-dow']/@href"):
        return direct_link[0]
    raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def onedrive(link):
    with create_scraper() as session:
        try:
            link = session.get(link).url
            parsed_link = urlparse(link)
            link_data = parse_qs(parsed_link.query)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if not link_data:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        folder_id = link_data.get("resid")
        if not folder_id:
            raise DirectDownloadLinkException("ERROR: Link Folder tidak ditemukan!")
        folder_id = folder_id[0]
        authkey = link_data.get("authkey")
        if not authkey:
            raise DirectDownloadLinkException("ERROR: AuthKey tidak ditemukan!")
        authkey = authkey[0]
        boundary = uuid4()
        headers = {"content-type": f"multipart/form-data;boundary={boundary}"}
        data = f"--{boundary}\r\nContent-Disposition: form-data;name=data\r\nPrefer: Migration=EnableRedirect;FailOnMigratedFiles\r\nX-HTTP-Method-Override: GET\r\nContent-Type: application/json\r\n\r\n--{boundary}--"
        try:
            resp = session.get( f"https://api.onedrive.com/v1.0/drives/{folder_id.split('!', 1)[0]}/items/{folder_id}?$select=id,@content.downloadUrl&ump=1&authKey={authkey}", headers=headers, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if "@content.downloadUrl" not in resp:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    return resp["@content.downloadUrl"]


def pixeldrain(url):
    url = url.strip("/ ")
    file_id = url.split("/")[-1]
    if url.split("/")[-2] == "l":
        info_link = f"https://pixeldrain.com/api/list/{file_id}"
        dl_link = f"https://pixeldrain.com/api/list/{file_id}/zip?download"
    else:
        info_link = f"https://pixeldrain.com/api/file/{file_id}/info"
        dl_link = f"https://pixeldrain.com/api/file/{file_id}?download"
    with create_scraper() as session:
        try:
            resp = session.get(info_link).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if resp["success"]:
        return dl_link
    else:
        raise DirectDownloadLinkException(
            f"ERROR: {resp['message']}!")


def streamtape(url):
    splitted_url = url.split("/")
    _id = splitted_url[4] if len(splitted_url) >= 6 else splitted_url[-1]
    try:
        with Session() as session:
            html = HTML(session.get(url).text)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if not (script := html.xpath("//script[contains(text(),'ideoooolink')]/text()")):
        raise DirectDownloadLinkException("ERROR: Script tidak ditemukan!")
    if not (link := findall(r"(&expires\S+)'", script[0])):
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    return f"https://streamtape.com/get_video?id={_id}{link[-1]}"


def racaty(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            json_data = {
                "op": "download2",
                "id": url.split("/")[-1]
            }
            html = HTML(session.post(url, data=json_data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if (direct_link := html.xpath("//a[@id='uniqueExpirylink']/@href")):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def fichier(link):
    regex = r"^([http:\/\/|https:\/\/]+)?.*1fichier\.com\/\?.+"
    gan = match(regex, link)
    if not gan:
        raise DirectDownloadLinkException(
            "ERROR: Link 1Fichier tidak ditemukan!")
    if "::" in link:
        pswd = link.split("::")[-1]
        url = link.split("::")[-2]
    else:
        pswd = None
        url = link
    cget = create_scraper().request
    try:
        if pswd is None:
            req = cget("post", url)
        else:
            pw = {"pass": pswd}
            req = cget("post", url, data=pw)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if req.status_code == 404:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    html = HTML(req.text)
    if dl_url:= html.xpath("//a[@class='ok btn-general btn-orange']/@href"):
        return dl_url[0]
    if not (ct_warn := html.xpath("//div[@class='ct_warn']")):
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    if len(ct_warn) == 3:
        str_2 = ct_warn[-1].text
        if "you must wait" in str_2.lower():
            if numbers := [int(word) for word in str_2.split() if word.isdigit()]:
                raise DirectDownloadLinkException(f"ERROR: 1Fichier sedang limit! Silahkan tunggu {numbers[0]} menit lagi!")
            else:
                raise DirectDownloadLinkException("ERROR: 1Fichier sedang limit!")
        elif "protect access" in str_2.lower():
            raise DirectDownloadLinkException(f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(link)}")
        else:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    elif len(ct_warn) == 4:
        str_1 = ct_warn[-2].text
        str_3 = ct_warn[-1].text
        if "you must wait" in str_1.lower():
            if numbers := [int(word) for word in str_1.split() if word.isdigit()]:
                raise DirectDownloadLinkException(f"ERROR: 1Fichier sedang limit! Silahkan tunggu {numbers[0]} menit lagi!")
            else:
                raise DirectDownloadLinkException("ERROR: 1Fichier sedang limit!")
        elif "bad password" in str_3.lower():
            raise DirectDownloadLinkException("ERROR: Password salah!")
        else:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def solidfiles(url):
    with create_scraper() as session:
        try:
            headers = {
                "User-Agent": user_agent
            }
            pageSource = session.get(url, headers=headers).text
            mainOptions = str(
                search(r"viewerOptions\"\,\ (.*?)\)\;", pageSource).group(1))
            return loads(mainOptions)["downloadUrl"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")


def krakenfiles(url):
    with Session() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        html = HTML(_res.text)
        if post_url:= html.xpath("//form[@id='dl-form']/@action"):
            post_url = f"https:{post_url[0]}"
        else:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        if token:= html.xpath("//input[@id='dl-token']/@value"):
            data = {"token": token[0]}
        else:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        try:
            _json = session.post(post_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Info File!")
    if _json["status"] != "ok":
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    return _json["url"]


def uploadee(url):
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if link := html.xpath("//a[@id='d_l']/@href"):
        return link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def terabox(url):
    if not path.isfile("terabox.txt"):
        raise DirectDownloadLinkException("ERROR: Cookies (terabox.txt) tidak ditemukan!")
    try:
        jar = MozillaCookieJar("terabox.txt")
        jar.load()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    cookies = {}
    for cookie in jar:
        cookies[cookie.name] = cookie.value

    details = {"contents":[], "title": "", "total_size": 0}
    details["header"] = " ".join(f"{key}: {value}" for key, value in cookies.items())

    def __fetch_links(session, dir_="", folderPath=""):
        params = {
            "app_id": "250528",
            "jsToken": jsToken,
            "shorturl": shortUrl
            }
        if dir_:
            params["dir"] = dir_
        else:
            params["root"] = "1"
        try:
            _json = session.get("https://www.1024tera.com/share/list", params=params, cookies=cookies).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if _json["errno"] not in [0, "0"]:
            if "errmsg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['errmsg']}")
            else:
                raise DirectDownloadLinkException("ERROR: Terjadi kesalahan!")

        if "list" not in _json:
            return
        contents = _json["list"]
        for content in contents:
            if content["isdir"] in ["1", 1]:
                if not folderPath:
                    if not details["title"]:
                        details["title"] = content["server_filename"]
                        newFolderPath = path.join(details["title"])
                    else:
                        newFolderPath = path.join(details["title"], content["server_filename"])
                else:
                    newFolderPath = path.join(folderPath, content["server_filename"])
                __fetch_links(session, content["path"], newFolderPath)
            else:
                if not folderPath:
                    if not details["title"]:
                        details["title"] = content["server_filename"]
                    folderPath = details["title"]
                item = {
                    "url": content["dlink"],
                    "filename": content["server_filename"],
                    "path" : path.join(folderPath),
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)

    with Session() as session:
        try:
            _res = session.get(url, cookies=cookies)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if jsToken := findall(r"window\.jsToken.*%22(.*)%22", _res.text):
            jsToken = jsToken[0]
        else:
            raise DirectDownloadLinkException("ERROR: jsToken tidak ditemukan!")
        shortUrl = parse_qs(urlparse(_res.url).query).get("surl")
        if not shortUrl:
            raise DirectDownloadLinkException("ERROR: ShortUrl tidak ditemukan!")
        try:
            __fetch_links(session)
        except Exception as e:
            raise DirectDownloadLinkException(e)
    if len(details["contents"]) == 1:
        return details["contents"][0]["url"]
    return details


def filepress(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            raw = urlparse(url)
            json_data = {
                "id": raw.path.split("/")[-1],
                "method": "publicDownlaod",
            }
            api = f"{raw.scheme}://{raw.hostname}/api/file/downlaod/"
            res2 = session.post(api, headers={"Referer": f"{raw.scheme}://{raw.hostname}"}, json=json_data).json()
            json_data2 = {
               "id":res2["data"],
               "method": "publicUserDownlaod",
            }
            api2 = "https://new2.filepress.store/api/file/downlaod2/"
            res = session.post(api2, headers={"Referer": f"{raw.scheme}://{raw.hostname}"}, json=json_data2).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if "data" not in res:
        raise DirectDownloadLinkException(f"ERROR: {res['statusText']}")
    return f"https://drive.google.com/uc?id={res['data']}&export=download"


def gdtot(url):
    cget = create_scraper().request
    try:
        res = cget("GET", f"https://gdbot.pro/file/{url.split('/')[-1]}")
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    token_url = HTML(res.text).xpath(
        "//a[contains(@class,'inline-flex items-center justify-center')]/@href")
    if not token_url:
        try:
            url = cget("GET", url).url
            p_url = urlparse(url)
            res = cget(
                "GET", f"{p_url.scheme}://{p_url.hostname}/ddl/{url.split('/')[-1]}")
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if (drive_link := findall(r"myDl\('(.*?)'\)", res.text)) and "drive.google.com" in drive_link[0]:
            return drive_link[0]
        else:
            raise DirectDownloadLinkException(
                "ERROR: Link Drive tidak ditemukan!")
    token_url = token_url[0]
    try:
        token_page = cget("GET", token_url)
    except Exception as e:
        raise DirectDownloadLinkException(
            f"ERROR: {e.__class__.__name__} with {token_url}")
    path = findall("\('(.*?)'\)", token_page.text)
    if not path:
        raise DirectDownloadLinkException("ERROR: Tidak bisa membypass link!")
    path = path[0]
    raw = urlparse(token_url)
    final_url = f"{raw.scheme}://{raw.hostname}{path}"
    return sharer_scraper(final_url)


def sharer_scraper(url):
    cget = create_scraper().request
    try:
        url = cget("GET", url).url
        raw = urlparse(url)
        header = {
            "User-Agent": user_agent}
        res = cget("GET", url, headers=header)
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    key = findall("'key',\s+'(.*?)'", res.text)
    if not key:
        raise DirectDownloadLinkException("ERROR: Key tidak ditemukan!")
    key = key[0]
    if not HTML(res.text).xpath("//button[@id='drc']"):
        raise DirectDownloadLinkException(
            "ERROR: Link File tidak ditemukan!")
    boundary = uuid4()
    headers = {
        "Content-Type": f"multipart/form-data; boundary=----WebKitFormBoundary{boundary}",
        "x-token": raw.hostname,
        "User-Agent": user_agent
    }

    data = f"------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name='action'\r\n\r\ndirect\r\n" \
        f"------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name='key'\r\n\r\n{key}\r\n" \
        f"------WebKitFormBoundary{boundary}\r\nContent-Disposition: form-data; name='action_token'\r\n\r\n\r\n" \
        f"------WebKitFormBoundary{boundary}--\r\n"
    try:
        res = cget("POST", url, cookies=res.cookies,
                   headers=headers, data=data).json()
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if "url" not in res:
        raise DirectDownloadLinkException(
            "ERROR: Link Drive tidak ditemukan!")
    if "drive.google.com" in res["url"]:
        return res["url"]
    try:
        res = cget("GET", res["url"])
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if (drive_link := HTML(res.text).xpath("//a[contains(@class,'btn')]/@href")) and "drive.google.com" in drive_link[0]:
        return drive_link[0]
    else:
        raise DirectDownloadLinkException(
            "ERROR: Link Drive tidak ditemukan!")


def wetransfer(url):
    with create_scraper() as session:
        try:
            url = session.get(url).url
            splited_url = url.split("/")
            json_data = {
                "security_hash": splited_url[-1],
                "intent": "entire_transfer"
            }
            res = session.post(f"https://wetransfer.com/api/v4/transfers/{splited_url[-2]}/download", json=json_data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if "direct_link" in res:
        return res["direct_link"]
    elif "message" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['message']}")
    elif "error" in res:
        raise DirectDownloadLinkException(f"ERROR: {res['error']}")
    else:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def akmfiles(url):
    with create_scraper() as session:
        try:
            html = HTML(session.post(url, data={"op": "download2", "id": url.split("/")[-1]}).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if (direct_link := html.xpath("//a[contains(@class,'btn btn-dow')]/@href")):
        return direct_link[0]
    else:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def shrdsk(url):
    with create_scraper() as session:
        try:
            _json = session.get(f"https://us-central1-affiliate2apk.cloudfunctions.net/get_data?shortid={url.split('/')[-1]}").json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if "download_data" not in _json:
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        try:
            _res = session.get(f"https://shrdsk.me/download/{_json['download_data']}", allow_redirects=False)
            if "Location" in _res.headers:
                return _res.headers["Location"]
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def linkBox(url:str):
    parsed_url = urlparse(url)
    try:
        shareToken = parsed_url.path.split("/")[-1]
    except:
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")

    details = {"contents":[], "title": "", "total_size": 0}

    def __singleItem(session, itemId):
        try:
            _json = session.get("https://www.linkbox.to/api/file/detail", params={"itemId": itemId}).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: Data tidak ditemukan!")
        itemInfo = data["itemInfo"]
        if not itemInfo:
            raise DirectDownloadLinkException("ERROR: Item Info tidak ditemukan!")
        filename = itemInfo["name"]
        sub_type = itemInfo.get("sub_type")
        if sub_type and not filename.endswith(sub_type):
            filename += f".{sub_type}"
        if not details["title"]:
            details["title"] = filename
        item = {
            "path": "",
            "filename": filename,
            "url": itemInfo["url"],
        }
        if "size" in itemInfo:
            size = itemInfo["size"]
            if isinstance(size, str) and size.isdigit():
                size = float(size)
            details["total_size"] += size
        details["contents"].append(item)
        
    def __fetch_links(session, _id=0, folderPath=""):
        params = {
            "shareToken": shareToken,
            "pageSize": 1000,
            "pid": _id,
        }
        try:
            _json = session.get("https://www.linkbox.to/api/file/share_out_list", params=params).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        data = _json["data"]
        if not data:
            if "msg" in _json:
                raise DirectDownloadLinkException(f"ERROR: {_json['msg']}")
            raise DirectDownloadLinkException("ERROR: Data tidak ditemukan!")
        if data["shareType"] == "singleItem":
            return __singleItem(session, data["itemId"])
        if not details["title"]:
            details["title"] = data["dirName"]
        contents = data["list"]
        if not contents:
            return
        for content in contents:
            if content["type"] == "dir" and "url" not in content:
                if not folderPath:
                    newFolderPath = path.join(details["title"], content["name"])
                else:
                    newFolderPath = path.join(folderPath, content["name"])
                if not details["title"]:
                    details["title"] = content["name"]
                __fetch_links(session, content["id"], newFolderPath)
            elif "url" in content:
                if not folderPath:
                    folderPath = details["title"]
                filename = content["name"]
                if (sub_type := content.get("sub_type")) and not filename.endswith(sub_type):
                    filename += f".{sub_type}"
                item = {
                    "path": path.join(folderPath),
                    "filename": filename,
                    "url": content["url"],
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)
    try:
        with Session() as session:
            __fetch_links(session)
    except DirectDownloadLinkException as e:
        raise e
    return details


def gofile(url):
    try:
        if "::" in url:
            _password = url.split("::")[-1]
            _password = sha256(_password.encode("utf-8")).hexdigest()
            url = url.split("::")[-2]
        else:
            _password = ""
        _id = url.split("/")[-1]
    except Exception as e:
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")

    def __get_token(session):
        if "gofile_token" in _caches:
            __url = f"https://api.gofile.io/getAccountDetails?token={_caches['gofile_token']}"
        else:
            __url = "https://api.gofile.io/createAccount"
        try:
            __res = session.get(__url, verify=False).json()
            if __res["status"] != "ok":
                if "gofile_token" in _caches:
                    del _caches["gofile_token"]
                return __get_token(session)
            _caches["gofile_token"] = __res["data"]["token"]
            return _caches["gofile_token"]
        except Exception as e:
            raise e

    def __fetch_links(session, _id, folderPath=""):
        _url = f"https://api.gofile.io/getContent?contentId={_id}&token={token}&websiteToken=7fd94ds12fds4&cache=true"
        if _password:
            _url += f"&password={_password}"
        try:
            _json = session.get(_url, verify=False).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if _json["status"] in "error-passwordRequired":
            raise DirectDownloadLinkException(f"ERROR: {PASSWORD_ERROR_MESSAGE.format(url)}")
        if _json["status"] in "error-passwordWrong":
            raise DirectDownloadLinkException("ERROR: Password salah!")
        if _json["status"] in "error-notFound":
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        if _json["status"] in "error-notPublic":
            raise DirectDownloadLinkException("ERROR: Folder tidak dapat diunduh!")

        data = _json["data"]

        if not details["title"]:
            details["title"] = data["name"] if data["type"] == "folder" else _id

        contents = data["contents"]
        for content in contents.values():
            if content["type"] == "folder":
                if not content["public"]:
                    continue
                if not folderPath:
                    newFolderPath = path.join(details["title"], content["name"])
                else:
                    newFolderPath = path.join(folderPath, content["name"])
                __fetch_links(content["id"], newFolderPath)
            else:
                if not folderPath:
                    folderPath = details["title"]
                item = {
                    "path": path.join(folderPath),
                    "filename": content["name"],
                    "url": content["link"],
                }
                if "size" in content:
                    size = content["size"]
                    if isinstance(size, str) and size.isdigit():
                        size = float(size)
                    details["total_size"] += size
                details["contents"].append(item)

    details = {"contents":[], "title": "", "total_size": 0}
    with Session() as session:
        try:
            token = __get_token(session)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        details["header"] = f"Cookie: accountToken={token}"
        try:
            __fetch_links(session, _id)
        except Exception as e:
            raise DirectDownloadLinkException(e)

    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def cf_bypass(url):
    "DO NOT ABUSE THIS"
    try:
        data = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000
        }
        _json = post("https://cf.jmdkh.eu.org/v1", headers={"Content-Type": "application/json"}, json=data).json()
        if _json["status"] == "ok":
            return _json["solution"]["response"]
    except Exception as e:
        e
    raise DirectDownloadLinkException("ERROR: Tidak bisa bypass CloudFlare!")


def send_cm_file(url, file_id=None):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    _passwordNeed = False
    with create_scraper() as session:
        if file_id is None:
            try:
                html = HTML(session.get(url).text)
            except Exception as e:
                raise DirectDownloadLinkException(
                    f"ERROR: {e.__class__.__name__}")
            if html.xpath("//input[@name='password']"):
                _passwordNeed = True
            if not (file_id := html.xpath("//input[@name='id']/@value")):
                raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        try:
            data = {"op": "download2", "id": file_id}
            if _password and _passwordNeed:
                data["password"] = _password
            _res = session.post("https://send.cm/", data=data, allow_redirects=False)
            if "Location" in _res.headers:
                return (_res.headers["Location"], "Referer: https://send.cm/")
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if _passwordNeed:
        raise DirectDownloadLinkException(f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}")
    raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def send_cm(url):
    if "/d/" in url:
        return send_cm_file(url)
    elif "/s/" not in url:
        file_id = url.split("/")[-1]
        return send_cm_file(url, file_id)
    splitted_url = url.split("/")
    details = {"contents": [], "title": "", "total_size": 0,
               "header": "Referer: https://send.cm/"}
    if len(splitted_url) == 5:
        url += "/"
        splitted_url = url.split("/")
    if len(splitted_url) >= 7:
        details["title"] = splitted_url[5]
    else:
        details["title"] = splitted_url[-1]
    session = Session()

    def __collectFolders(html):
        folders = []
        folders_urls = html.xpath("//h6/a/@href")
        folders_names = html.xpath("//h6/a/text()")
        for folders_url, folders_name in zip(folders_urls, folders_names):
            folders.append({"folder_link":folders_url.strip(),"folder_name":folders_name.strip()})
        return folders

    def __getFile_link(file_id):
        try:
            _res = session.post(
                "https://send.cm/", data={"op": "download2", "id": file_id}, allow_redirects=False)
            if "Location" in _res.headers:
                return _res.headers["Location"]
        except:
            pass

    def __getFiles(html):
        files = []
        hrefs = html.xpath("//tr[@class='selectable']//a/@href")
        file_names = html.xpath("//tr[@class='selectable']//a/text()")
        sizes = html.xpath("//tr[@class='selectable']//span/text()")
        for href, file_name, size_text in zip(hrefs, file_names, sizes):
            files.append({"file_id":href.split('/')[-1], "file_name":file_name.strip(), "size":speed_string_to_bytes(size_text.strip())})
        return files

    def __writeContents(html_text, folderPath=""):
        folders = __collectFolders(html_text)
        for folder in folders:
            _html = HTML(cf_bypass(folder["folder_link"]))
            __writeContents(_html, path.join(folderPath, folder["folder_name"]))
        files = __getFiles(html_text)
        for file in files:
            if not (link := __getFile_link(file["file_id"])):
                continue
            item = {"url": link,
                    "filename": file["filename"], "path": folderPath}
            details["total_size"] += file["size"]
            details["contents"].append(item)
    try:
        mainHtml = HTML(cf_bypass(url))
    except DirectDownloadLinkException as e:
        session.close()
        raise e
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Link!")
    try:
        __writeContents(mainHtml, details["title"])
    except DirectDownloadLinkException as e:
        session.close()
        raise e
    except Exception as e:
        session.close()
        raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Konten!")
    session.close()
    if len(details["contents"]) == 1:
        return (details["contents"][0]["url"], details["header"])
    return details


def doods(url: str):
    if "/e/" in url:
        url = url.replace("/e/", "/d/")
    parsed_url = urlparse(url)
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Token Link!")
        if not (link := html.xpath("//div[@class='download-content']//a/@href")):
            raise DirectDownloadLinkException("ERROR: Token tidak ditemukan!")
        link = f"{parsed_url.scheme}://{parsed_url.hostname}{link[0]}"
        sleep(2)
        try:
            _res = session.get(link)
        except Exception as e:
            raise DirectDownloadLinkException(
                f"ERROR: {e.__class__.__name__} ketika mencoba mendapatkan Link File!")
    if not (link := search(r"window\.open\('(\S+)'", _res.text)):
        raise DirectDownloadLinkException("ERROR: Direct Link tidak ditemukan!")
    return (link.group(1), f"Referer: {parsed_url.scheme}://{parsed_url.hostname}/")


def streamvid(url: str):
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"
    quality_defined = bool(url.endswith(("_o", "_h", "_n", "_l")))
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if quality_defined:
            data = {}
            if not (inputs := html.xpath("//form[@id='F1']//input")):
                raise DirectDownloadLinkException("ERROR: Input tidak ditemukan!")
            for i in inputs:
                if key := i.get("name"):
                    data[key] = i.get("value")
            try:
                html = HTML(session.post(url, data=data).text)
            except Exception as e:
                raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
            if not (script := html.xpath("//script[contains(text(),'document.location.href')]/text()")):
                if error := html.xpath("//div[@class='alert alert-danger'][1]/text()[2]"):
                    raise DirectDownloadLinkException(f"ERROR: {error[0]}")
                raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
            if directLink:=findall(r"document\.location\.href='(.*)'", script[0]):
                return directLink[0]
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        elif (qualities_urls := html.xpath("//div[@id='dl_versions']/a/@href")) and (qualities := html.xpath("//div[@id='dl_versions']/a/text()[2]")):
            error = "\nProvide a quality to download the video\nAvailable Quality:"
            for quality_url, quality in zip(qualities_urls, qualities):
                error += f"\n{quality.strip()} <code>{quality_url}</code>"
            raise DirectDownloadLinkException(f"{error}")
        elif error:= html.xpath("//div[@class='not-found-text']/text()"):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def easyupload(url):
    if "::" in url:
        _password = url.split("::")[-1]
        url = url.split("::")[-2]
    else:
        _password = ""
    file_id = url.split("/")[-1]
    with create_scraper() as session:
        try:
            _res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        first_page_html = HTML(_res.text)
        if first_page_html.xpath("//h6[contains(text(),'Password Protected')]") and not _password:
            raise DirectDownloadLinkException(f"ERROR:\n{PASSWORD_ERROR_MESSAGE.format(url)}")
        if not (match := search(r"https://eu(?:[1-9][0-9]?|100)\.easyupload\.io/action\.php", _res.text)):
            raise DirectDownloadLinkException("ERROR: Link EasyUpload tidak ditemukan!")
        action_url = match.group()
        session.headers.update({"referer": "https://easyupload.io/"})
        recaptcha_params = {
            "k": "6LfWajMdAAAAAGLXz_nxz2tHnuqa-abQqC97DIZ3",
            "ar": "1",
            "co": "aHR0cHM6Ly9lYXN5dXBsb2FkLmlvOjQ0Mw..",
            "hl": "en",
            "v": "0hCdE87LyjzAkFO5Ff-v7Hj1",
            "size": "invisible",
            "cb": "c3o1vbaxbmwe"
        }
        if not (captcha_token :=get_captcha_token(session, recaptcha_params)):
            raise DirectDownloadLinkException("ERROR: Token Captcha tidak ditemukan!")
        try:
            data = {"type": "download-token",
                    "url": file_id,
                    "value": _password,
                    "captchatoken": captcha_token,
                    "method": "regular"}
            json_resp = session.post(url=action_url, data=data).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if "download_link" in json_resp:
        return json_resp["download_link"]
    elif "data" in json_resp:
        raise DirectDownloadLinkException(
            f"ERROR: {json_resp['data']}")
    raise DirectDownloadLinkException(
        "ERROR: Direct Link tidak ditemukan!")


def filelions_and_streamwish(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    scheme = parsed_url.scheme
    if any(
        x in hostname
        for x in [
            "filelions.co",
            "filelions.live",
            "filelions.to", 
            "filelions.site", 
            "filelions.online", 
            "cabecabean.lol"
        ]
    ):
        apiKey = config_dict["FILELION_API"]
        apiUrl = "https://api.filelions.co"
    elif any(x in hostname for x in ["embedwish.com", "streamwish.com", "kitabmarkaz.xyz", "wishfast.top", "streamwish.to"]):
        apiKey = config_dict["STREAMWISH_API"]
        apiUrl = "https://api.streamwish.com"
    if not apiKey:
        raise DirectDownloadLinkException(f"ERROR: Api Key tidak ditemukan! URL : {scheme}://{hostname}")
    file_code = url.split("/")[-1]
    quality = ""
    if bool(file_code.endswith(("_o", "_h", "_n", "_l"))):
        spited_file_code = file_code.rsplit("_", 1)
        quality = spited_file_code[1]
        file_code = spited_file_code[0]
    url = f"{scheme}://{hostname}/{file_code}"
    with Session() as session:
        try:
            _res = session.get(f"{apiUrl}/api/file/direct_link", params={"key": apiKey, "file_code": file_code, "hls": "1"}).json()
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if _res["status"] != 200:
        raise DirectDownloadLinkException(f"ERROR: {_res['msg']}")
    result = _res["result"]
    if not result["versions"]:
        raise DirectDownloadLinkException("ERROR: Versi tidak ditemukan!")
    error = "\n<b>Pilih kualitas Video :</b>\n<b>Kualitas yang tersedia :</b>"
    for version in result["versions"]:
        if quality == version["name"]:
            return version["url"]
        elif version["name"] == "l":
            error += f"\n<b>Low</b>"
        elif version["name"] == "n":
            error += f"\n<b>Normal</b>"
        elif version["name"] == "o":
            error += f"\n<b>Original</b>"
        elif version["name"] == "h":
            error += f"\n<b>HD</b>"
        error +=f": <code>{url}_{version['name']}</code>"
    raise DirectDownloadLinkException(f"{error}")


def streamhub(url):
    file_code = url.split("/")[-1]
    parsed_url = urlparse(url)
    url = f"{parsed_url.scheme}://{parsed_url.hostname}/d/{file_code}"
    with create_scraper() as session:
        try:
            html = HTML(session.get(url).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if not (inputs := html.xpath("//form[@name='F1']//input")):
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
        data = {}
        for i in inputs:
            if key := i.get("name"):
                data[key] = i.get("value")
        session.headers.update({"referer": url})
        sleep(1)
        try:
            html = HTML(session.post(url, data=data).text)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
        if directLink := html.xpath("//a[@class='btn btn-primary btn-go downloadbtn']/@href"):
            return directLink[0]
        if error := html.xpath("//div[@class='alert alert-danger']/text()[2]"):
            raise DirectDownloadLinkException(f"ERROR: {error[0]}")
        raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def pcloud(url):
    with create_scraper() as session:
        try:
            res = session.get(url)
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {e.__class__.__name__}")
    if link := findall(r".downloadlink.:..(https:.*)..", res.text):
        return link[0].replace("\/", "/")
    raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")


def alldebrid(url: str) -> str:
    """
    URL : 
    https://api.alldebrid.com/
    
    Documentation :
    https://docs.alldebrid.com/
    
    Supported Sites : 
    https://alldebrid.com/hosts/
    """
    agent_name = "TelegramBot" # Maybe we can add this on env? So its can customizable.
    alldebrid_api = config_dict['ALLDEBRID_API']
    if len(alldebrid_api) == 0:
        raise DirectDownloadLinkException("ERROR: ALLDEBRID_API tidak ditemukan!")
    with Session() as session:
        r = session.get(
            f"https://api.alldebrid.com/v4/link/unlock?agent={agent_name}&apikey={alldebrid_api}&link={url}"
        )

        if r.ok:
            r = r.json()
            if r["status"] == "success":
                session.close()
                if r["data"]["host"] == "stream":
                    raise DirectDownloadLinkException("ERROR: Tidak support stream. Gunakan perintah YT-DLP!")
                return r["data"]["link"]
            else:
                session.close()
                raise DirectDownloadLinkException(f"ERROR: {r['error']['message']}")
        

def pake(url: str) -> str:
    """
    URL : 
    https://api.pake.tk
    
    Supported Sites :
    - Dood
    - Vidstream
    """
    with Session() as session:
        try:
            req = session.get(f"https://api.pake.tk/dood?url={url}").json()
            try:
                details = {"contents":[], "title": "", "total_size": 0}

                details["title"] = f"{req['data']['title']}.mp4"

                item = {
                    "path": path.join(details["title"]),
                    "filename": details["title"],
                    "url": f"https://dd-cdn.pakai.eu.org/download?url={req['data']['direct_link']}&title={details['title']}.mp4",
                }
            
                details["contents"].append(item)
                return details
            except ValueError:
                session.close()
                raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")


# Added from other repositories
def mp4upload(url):
    with Session() as session:
        try:
            url = url.replace("embed-", "")
            req = session.get(url).text
            soup = BeautifulSoup(req, "lxml")
            inputs = soup.find_all("input")
            data = {input.get("name"): input.get("value") for input in inputs}
            if not data:
                session.close()
                raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
            post = session.post(url, 
                                data=data, 
                                headers={
                                    "User-Agent": user_agent, 
                                    "Referer": "https://www.mp4upload.com/"
                                }).text
            soup = BeautifulSoup(post, "lxml")
            inputs = soup.find_all("form", {"name": "F1"})[0].find_all("input")
            data = {input.get("name"): input.get("value").replace(" ", "") for input in inputs}
            if not data:
                session.close()
                raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
            data["referer"] = url
            urllib3.disable_warnings()
            direct_link = session.post(
                url, 
                data=data, 
                verify=False
            ).url
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException("ERROR: Link File tidak ditemukan!")
    

def androiddatahost(url):
    with create_scraper() as session:
        try:
            req = session.get(url).content
            soup = BeautifulSoup(req, "html.parser")
            link = soup.find("div", {"download2"})
            direct_link = link.find("a")["href"]
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
    

def apkadmin(url: str) -> str:
    with create_scraper() as session:
        try:
            req = session.get(url).text
            soup = BeautifulSoup(req, "lxml")
            op = soup.find("input", {"name": "op"})["value"]
            ids = soup.find("input", {"name": "id"})["value"]
            post = session.post(url, 
                                data={
                                    "op": op,
                                    "id": ids,
                                    "rand": " ",
                                    "referer": " ",
                                    "method_free": " ",
                                    "method_premium": " ",
                                }).text
            soup = BeautifulSoup(post, "lxml")
            link = soup.find("div", {"class": "text text-center"})
            direct_link = link.find("a")["href"]
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
    

def sourceforge(url: str) -> str:
    with Session() as session:
        try:
            if "master.dl.sourceforge.net" in url:
                return f"{url}?viasf=1"
            if url.endswith("/download"):
                url = url.split("/download")[0]
            try:
                link = findall(r"\bhttps?://sourceforge\.net\S+", url)[0]
            except IndexError:
                session.close()
                raise DirectDownloadLinkException("ERROR: Link SourceForge tidak ditemukan!")
            file_id = findall(r"files(.*)", link)[0]
            project = findall(r"projects?/(.*?)/files", link)[0]
            req = session.get(f"https://sourceforge.net/settings/mirror_choices?projectname={project}&filename={file_id}").content
            soup = BeautifulSoup(req, "html.parser")
            mirror = soup.find("ul", {"id": "mirrorList"}).findAll("li")
            for i in mirror[1:]:
                direct_link = f"https://{i['id']}.dl.sourceforge.net/project/{project}/{file_id}?viasf=1"
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")


def androidfilehost(url):
    with Session() as session:
        try:
            try:
                url = findall(r"\bhttps?://.*androidfilehost.*fid.*\S+", url)[0]
            except IndexError:
                session.close()
                raise DirectDownloadLinkException("ERROR: Link AndroidFileHost tidak ditemukan!")
            file_id = findall(r"\?fid=(.*)", url)[0]
            cookies = session.get(url).cookies
            post = session.post(
                "https://androidfilehost.com/libs/otf/mirrors.otf.php", 
                headers={
                    "User-Agent": user_agent,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Referer": f"https://androidfilehost.com/?fid={file_id}",
                    "X-MOD-SBB-CTYPE": "xhr",
                    "X-Requested-With": "XMLHttpRequest",
                }, 
                data={
                    "submit": "submit", 
                    "action": "getdownloadmirrors", 
                    "fid": file_id
                }, 
                cookies=cookies
            ).json()
            if link := post["MIRRORS"]:
                direct_link = next(i for i in link if i["url"])["url"]
                return direct_link
            else:
                session.close()
                raise Exception(f"ERROR: Link File tidak ditemukan!")
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")


def tusfiles(url):
    with create_scraper() as session:
        try:
            req = session.get(url).text
            soup = BeautifulSoup(req, "lxml")
            input_ = soup.find_all("input")
            file_id = input_[1]["value"]
            post = session.post(
                "https://tusfiles.com/",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": user_agent
                }, 
                data={
                    "op": "download2", 
                    "id": file_id, 
                    "referer": url
                },
                allow_redirects=False
            )
            if direct_link := post.headers["location"]:
                return direct_link
            else:
                session.close()
                raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")  
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
    

def pandafiles(url):
    with create_scraper() as session:
        try:
            file_id = search(r"(?://|\.)(pandafiles\.com)/([0-9a-zA-Z]+)", url)[2]
            post = session.post(url, 
                               headers={
                                   "User-Agent": user_agent
                                }, 
                               data={
                                   "op": "download2", 
                                   "usr_login": "", 
                                   "id": file_id, 
                                   "referer": url, 
                                   "method_free": "Free Download"
                               }).content
            soup = BeautifulSoup(post)
            direct_link = soup.find("div", {"id": "direct_link"}).find("a")["href"]
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
    

def uploadhaven(url):
    with Session() as session:
        try:
            req = session.get(url,
                              headers={
                                  "User-Agent": user_agent
                              }).text
            soup = BeautifulSoup(req, "lxml")
            d = soup.find("div", {"class": "alert alert-danger col-md-12"})
            if d is not None:
                hot1 = soup.find("div", {"class": "alert alert-danger col-md-12"})
                hot_text = hot1.text.strip()
                session.close()
                raise DirectDownloadLinkException(f"ERROR: {str(hot_text)}")
            else:
                for _ in range(6, 0, -1):
                    sleep(1)
                post = session.post(
                    url,
                    data={
                        "_token": soup.find("input", {"name": "_token"})["value"],
                        "key": soup.find("input", {"name": "key"})["value"],
                        "time": soup.find("input", {"name": "time"})["value"],
                        "hash": soup.find("input", {"name": "hash"})["value"],
                        "type": "free",
                    },
                    headers={
                        "User-Agent": user_agent
                    }
                ).text
                soup = BeautifulSoup(post, "lxml")
                direct_link = soup.find("div", class_="alert alert-success mb-0").find("a")["href"]
                return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")


def uploadrar(url):
    with Session() as session:
        try:
            file_id = url.strip("/ ").split("/")[-1]
            post = session.post(
                url, 
                headers={
                    "User-Agent": user_agent,
                    "Referer": url
                },
                data={
                    "op": "download2",
                    "id": file_id,
                    "rand": "",
                    "method_free": "Free Download",
                    "method_premium": ""
                }
            ).text
            soup = BeautifulSoup(post, "lxml")
            direct_link = soup.find("span", {"id": "direct_link"}).find("a").get("href")
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
    

def romsget(url):
    with Session() as session:
        try:
            req = session.get(url).text
            soup = BeautifulSoup(req, "html.parser")
            upos = soup.find("form", {"id": "download-form"}).get("action")
            meid = soup.find("input", {"id": "mediaId"}).get("name")
            try:
                dlid = soup.find("button", {"data-callback": "onDLSubmit"}).get("dlid")
            except:
                dlid = soup.find("div", {"data-callback": "onDLSubmit"}).get("dlid")
            post = session.post("https://www.romsget.io" + upos, 
                               data={
                                   meid: dlid
                                }).text
            soup = BeautifulSoup(post, "html.parser")
            udl = soup.find("form", {"name": "redirected"}).get("action")
            prm = soup.find("input", {"name": "attach"}).get("value")
            direct_link = f"{udl}?attach={prm}"
            return direct_link
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")



def hexupload(url):
    with Session() as session:
        try:
            post = session.post(
                url, 
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-us,en;q=0.6",
                    "Sec-Fetch-Mode": "navigate",
                },
                data={
                    "op": "download2",
                    "id": url.split("/")[-1],
                    "rand": "",
                    "referer": url,
                    "method_free": "Free Download",
                }
            ).text
            link = search(r"ldl.ld\('([^']+)", post)
            if direct_link := base64.b64decode(link.group(1)).decode("utf-8").replace(" ", "%20"):
                return direct_link
            else:
                session.close()
                raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")
        except:
            session.close()
            raise DirectDownloadLinkException(f"ERROR: Link File tidak ditemukan!")