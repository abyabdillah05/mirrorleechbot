import pycurl
import json
import os
import requests
import re

from requests import Session
from logging import getLogger
from time import time
from io import BytesIO
from random import choice
from urllib.parse import quote
from bot.helper.ext_utils.bot_utils import async_to_sync
from bot.helper.ext_utils.files_utils import get_mime_type
from http.cookiejar import MozillaCookieJar

LOGGER = getLogger(__name__)
user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"

class DdlUploader:
    def __init__(self, listener, path):
        self._last_uploaded = 0
        self._processed_bytes = 0
        self.listener = listener
        self._gf_api = listener.gf_api
        self._pd_api = listener.pd_api
        self._gf_folder = listener.gf_folder
        self._token = self._gf_api if self._gf_api else None
        self._api_key = self._pd_api if self._pd_api else None
        self._path = path
        self._start_time = time()
        self._is_cancelled = False
        self._pycurl = pycurl.Curl()

        self.cookie = MozillaCookieJar()
        #self.cookie.load("buzzheavier.txt", ignore_discard=True, ignore_expires=True)
        self._cookies ={}
        #for cookie in self.cookie:
        #    self._cookies[cookie.name] = cookie.value
        self.session: Session = Session()
        #self.session.cookies.update(other=self.cookie)
        #self.session.cookies.update(self.session.cookies.get_dict())

    def _upload_progress(self, download_t, download_d, upload_t, upload_d):
        if self._is_cancelled:
            LOGGER.info("Upload was cancelled during the process")
            return 1
        chunk_size = upload_d - self._last_uploaded
        self._last_uploaded = upload_d
        self._processed_bytes += chunk_size
        return 0
    
    def get_token(self):
        with requests.Session() as session:
            headers = {
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "*/*",
                "Connection": "keep-alive",
            }
            url = f"https://api.gofile.io/accounts"
            try:
                res = session.post(url, headers=headers).json()
                if res["status"] != "ok":
                    async_to_sync(self.listener.onUploadError, "Gagal membuat token gofile.")
                return res["data"]["token"]
            except Exception as e:
                async_to_sync(self.listener.onUploadError, e)

    def getid(self):
        url = "https://api.gofile.io/accounts/getid"
        headers = {
            "Authorization": "Bearer " + self._token,
        }
        try:
            response = requests.get(url, headers=headers).json()
            if response["status"] != "ok":
                async_to_sync(self.listener.onUploadError, "Gagal mendapatkankan token gofile.")
            return response["data"]["id"]
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)

    def get_rootfolder(self):
        url = f"https://api.gofile.io/accounts/{self.getid()}"
        headers = {
            "Authorization": "Bearer " + self._token
        }
        try:
            response = requests.get(url, headers=headers).json()
            if response["status"] != "ok":
                async_to_sync(self.listener.onUploadError, "Gagal mengambil root folder gofile.")
            return response["data"]["rootFolder"]
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)

    def fetch_servers(self):
        headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }
        url = "https://api.gofile.io/servers"
        try:
            with requests.Session() as session:
                r = session.get(url, headers=headers).json()
                if r.get("status") != "ok":
                    async_to_sync(self.listener.onUploadError, "Gagal mengambil list server gofile, atau semua server sedang penuh !")
                return r.get("data", {})
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)
    
    def set_option(self, contentId):
        url = f"https://api.gofile.io/contents/{contentId}/update"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }
        data = {
            "attribute": "public",
            "attributeValue": "true",
        }
        try:
            response = requests.put(url, headers=headers, json=data).json()
            if response.get("status") != "ok":
                async_to_sync(self.listener.onUploadError, "Gagal saat membuat file menjadi publik")
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)
                
    def create_folder(self, parentFolderId, folder_name):
        url = "https://api.gofile.io/contents/createFolder"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }
        data = {
            "parentFolderId": parentFolderId,
            "folderName": folder_name
        }
        try:
            response = requests.post(url, headers=headers, json=data).json()
            if response.get("status") != "ok":
                async_to_sync(self.listener.onUploadError, "Gagal saat membuat folder")
            data = response.get("data", {})
            return data
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)
    
    def gf_uploadFolder(self, size):
        server = choice(self.fetch_servers()["servers"]).get("name")
        dir_path = self._path
        if self._token is None:
            self._token = self.get_token()
        if not self._gf_folder:
            folder_data = self.create_folder(
                (self.get_rootfolder()), os.path.basename(dir_path))
        else:
            folder_data = self.create_folder(
                self._gf_folder, os.path.basename(dir_path))
        folder_id = folder_data["id"]
        self.set_option(folder_data["id"])
        folder_ids = {".": folder_id}
        files_count = 0
        folders_count = 0
        for root, dirs, files in os.walk(dir_path):
            if self._is_cancelled:
                break
            files_count += len(files)
            folders_count += len(dirs)
            rel_path = os.path.relpath(root, dir_path)
            if rel_path == ".":
                parentFolderId = folder_id
                newFolder = folder_id
            else:
                parentFolderId = folder_ids.get(os.path.dirname(rel_path), folder_id)
                folder_name = os.path.basename(rel_path)
                newFolder = self.create_folder(parentFolderId, folder_name)["id"]
                folder_ids[rel_path] = newFolder
            for file in files:
                file_path = os.path.join(root, file)
                self.gf_upload(server, file_path, newFolder, isfolder=True)
        self._pycurl.close()
        mime_type = "Folder"
        link = (f"https://gofile.io/d/{folder_data['code']}")
        async_to_sync(self.listener.onUploadComplete, link, size, files_count, folders_count, mime_type, None, None, server)

    def gf_upload(self, server=None, file_path=None, folder_id=None, isfolder=False):
        private = False if self._token is None else True
        if server is None:
            server = choice(self.fetch_servers()["servers"]).get("name")
        response_buffer = BytesIO()
        ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
        self._pycurl.setopt(self._pycurl.URL, f"https://{server}.gofile.io/contents/uploadfile")
        self._pycurl.setopt(pycurl.CAINFO, ca_cert_path)
        if isfolder or private:
            self._pycurl.setopt(self._pycurl.HTTPHEADER, ['Authorization: Bearer ' + self._token])
        self._pycurl.setopt(self._pycurl.POST, 1)
        self._pycurl.setopt(self._pycurl.WRITEDATA, response_buffer)
        self._pycurl.setopt(self._pycurl.NOPROGRESS, False)
        self._pycurl.setopt(self._pycurl.XFERINFOFUNCTION, self._upload_progress)
        if isfolder:
            self._pycurl.setopt(self._pycurl.HTTPPOST, [
                ('folderId', folder_id),
                ('file', (self._pycurl.FORM_FILE, f"{file_path}".encode("UTF-8"))),
            ])
        elif private and not isfolder:
            if self._gf_folder:
                self.set_option(self._gf_folder)
                self._pycurl.setopt(self._pycurl.HTTPPOST, [
                    ('folderId', self._gf_folder),
                    ('file', (self._pycurl.FORM_FILE, f"{self._path}".encode("UTF-8"))),
                ])
            else:
                folder_data = self.create_folder(
                    self.get_rootfolder(), os.path.basename(self._path))
                folder_id = folder_data["id"]
                self.set_option(folder_data["id"])
                self._pycurl.setopt(self._pycurl.HTTPPOST, [
                    ('folderId', folder_id),
                    ('file', (self._pycurl.FORM_FILE, f"{self._path}".encode("UTF-8"))),
                ])
        else:
            self._pycurl.setopt(self._pycurl.HTTPPOST, [
                ('file', (self._pycurl.FORM_FILE, f"{self._path}".encode("UTF-8")))
            ])
        try:
            self._pycurl.perform()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled during the process")
                return
            
            response_data = response_buffer.getvalue()
            if not response_data:
                async_to_sync(self.listener.onUploadError, "Terjadi kesalahan saat proses upload ke gofile")
                return
            response = response_data.decode()
            try:
                r = json.loads(response)
            except Exception as e:
                async_to_sync(self.listener.onUploadError, "Terjadi kesalahan saat mengupload file ke gofile: " + str(e))
                return
            if isfolder:
                if not self._is_cancelled:
                    return
            elif r.get('status') == 'ok':
                data = r.get('data', {})
                link = data.get('downloadPage')
                size = data.get('size')
                files = 1
                folders = 0
                mime_type = data.get('mimetype')
                async_to_sync(self.listener.onUploadComplete, link, size, files, folders, mime_type, None, None, server)
            else:
                async_to_sync(self.listener.onUploadError, f"Terjadi kesalahan saat mengupload file ke gofile: {r.get('message')}")
                return
        except pycurl.error as e:
            if not self._is_cancelled:
                async_to_sync(self.listener.onUploadError, e)
                return
        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)
            return
        
    def bh_uploader(self, file: str, url: str, number: int, start: int, end: int) -> dict:
        response_buffer = BytesIO()
        try:
            with open(file, mode="rb") as file_obj:
                file_obj.seek(start)
        except Exception as e:
            LOGGER.error(f"File error: {e}")
        ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
        self._pycurl.setopt(self._pycurl.URL, url)
        self._pycurl.setopt(pycurl.CAINFO, ca_cert_path)
        self._pycurl.setopt(self._pycurl.PUT, 1)
        self._pycurl.setopt(self._pycurl.UPLOAD, 1)
        self._pycurl.setopt(self._pycurl.READDATA, file_obj)
        self._pycurl.setopt(self._pycurl.INFILESIZE, (end - start))
        self._pycurl.setopt(self._pycurl.HTTPHEADER, 
                            [
                    f"Content-Length: {end - start}",
                    f"Cookie: {self._cookies}",
                ],
            )
        self._pycurl.setopt(self._pycurl.FOLLOWLOCATION, True)
        self._pycurl.setopt(self._pycurl.NOPROGRESS, False)
        self._pycurl.setopt(self._pycurl.HEADERFUNCTION, response_buffer.write)
        self._pycurl.setopt(self._pycurl.XFERINFOFUNCTION, self._upload_progress)
        try:
            self._pycurl.perform()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled during the process")
                return
            data = response_buffer.getvalue().decode("UTF-8")
            if not data:
                async_to_sync(self.listener.onUploadError,'Terjadi kesalahan saat proses upload ke buzzheavier')
                return
            for line in data.split("\r\n"):
                if line.lower().startswith("etag:"):
                    etag = line.split(":", 1)[1].strip()

            return {
                "ETag": etag,
                "PartNumber": number,
            }
        except pycurl.error as e:
            if not self._is_cancelled:
                async_to_sync(self.listener.onUploadError, f'Error A:{e}')
                return
        except Exception as e:
            async_to_sync(self.listener.onUploadError, f'Error B:{e}')
            return
        finally:
            self._pycurl.close()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled")
                return
    
    def bh_upload(self, size):
        LOGGER.info(f"Uploading to Buzzheavier... {self._path}")
        try:
            if os.path.isdir(self._path):
                files = 0
                folders = 0
                for root, dirs, files in os.walk(self._path):
                    files += len(files)
                    folders += len(dirs)
                folder = self.bh_create_folder(name=os.path.basename(self._path))
                for file in sorted(os.listdir(path=self._path)):
                    file = os.path.join(os.path, file)

                    if os.path.isdir(file):
                        LOGGER.info(
                            "Buzzheavier does not support Multi Folder yet! Skipping."
                        )
                        continue
                size = os.path.getsize(file)
                name = os.path.basename(file)
                complete = list()
                ids, urls = self.bh_get_server(name=name, size=size)

                with open(file=file, mode="rb"):
                    bhsize: int = 5 * 1024 * 1024 * 1024
                    for i in range((size + bhsize - 1) // bhsize):
                        start = i * bhsize
                        end = min((i + 1) * bhsize, size)
                        try:
                            part = self.bh_uploader(
                            file=file,
                            url=urls[i],
                            number=(i + 1),
                            start=start,
                            end=end,
                        )
                            complete.append(part)
                        except Exception as e:
                            async_to_sync(self.listener.onUploadError, f"ERROR C: {e}")
                            return
                    self.bh_get_complete(ids=ids, folder=folder, complete=complete)
                link = f"https://buzzheavier.com/d/{folder}"
        
            else:
                size = os.path.getsize(self._path)
                name = os.path.basename(self._path)
                mime_type = get_mime_type(self._path)
                files = 1
                folders = 0
                ids, urls = self.bh_get_server(name=name, size=size)
                complete = list()
                with open(file=self._path, mode="rb"):
                    bhsize: int = 5 * 1024 * 1024 * 1024
                    for i in range((size + bhsize - 1) // bhsize):
                        start = i * bhsize
                        end = min((i + 1) * bhsize, size)
                        try:
                            part = self.bh_uploader(
                            file=self._path,
                            url=urls[i],
                            number=(i + 1),
                            start=start,
                            end=end,
                        )
                            complete.append(part)
                        except Exception as e:
                            async_to_sync(self.listener.onUploadError, f"ERROR C: {e}")
                            return
                link = self.bh_get_complete(ids=ids, folder="bswd5iv1g7z1", complete=complete)
        except Exception as e:
            async_to_sync(self.listener.onUploadError, f"ERROR D: {e}")

        async_to_sync(self.listener.onUploadComplete, link, size, files, folders, mime_type, None, None, "buzzheavier.com")
    
    def bh_get_server(self, name: str, size: int) -> tuple:
        req = self.session.post(
            url=f"https://buzzheavier.com/f/",
            json={
                "name": name,
                "size": size,
            },
        )
        data = req.json()
        return data["uploadId"], data["uploadUrls"]
    
    def bh_get_complete(self, ids: str, folder: str, complete: list) -> str:
        req = self.session.post(
            url=f"https://buzzheavier.com/f/{ids}",
            params={
                "directoryId": folder,
            },
            json={
                "directoryId": folder,
                "parts": complete,
            },
        )
        data = req.json()
        return f"https://buzzheavier.com/{data['id']}"
    
    def bh_create_folder(self, name: str) -> str:
        req = self.session.post(
            url="https://buzzheavier.com/d/",
                headers={
                "hx-current-url": f"https://buzzheavier.com/d/",
                "hx-request": "true",
                "hx-target": "tbody",
                "hx-trigger": "create-directory-btn",
            },
            files={
                "name": (None, name),
            },
        )
        data = req.text
        folder = re.search(
            pattern=r"(?P<id>[a-z0-9]{12})",
            string=data,
        )
        if folder:
            return folder.group("id")
        return data
    
    def pd_upload(self, size):
        file_name = f"{os.path.basename(self._path)}".encode("UTF-8")
        if self._api_key is None:
            api_key = "a0ac91f8-dabb-40b1-b81c-17b237a3df49"
        else:
            api_key = self._api_key
        server = "pixeldrain.com"
        response_buffer = BytesIO()
        ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
        self._pycurl.setopt(self._pycurl.URL, f"https://{server}/api/file")
        self._pycurl.setopt(pycurl.CAINFO, ca_cert_path)
        self._pycurl.setopt(self._pycurl.POST, 1)
        self._pycurl.setopt(self._pycurl.USERPWD, f":{api_key}")
        self._pycurl.setopt(self._pycurl.WRITEDATA, response_buffer)
        self._pycurl.setopt(self._pycurl.NOPROGRESS, False)
        self._pycurl.setopt(self._pycurl.XFERINFOFUNCTION, self._upload_progress)
        self._pycurl.setopt(self._pycurl.HTTPPOST, [
                ('name', file_name),
                ('anonymouse', 'false'),
                ('file', (self._pycurl.FORM_FILE, f"{self._path}".encode("UTF-8"))),
            ])
        try:
            self._pycurl.perform()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled during the process")
                return
            response_data = response_buffer.getvalue()
            if not response_data:
                async_to_sync(self.listener.onUploadError,'Terjadi kesalahan saat proses upload ke pixeldrain')
                return
            response = response_data.decode()
            try:
                r = json.loads(response)
            except Exception as e:
                async_to_sync(self.listener.onUploadError,f'Terjadi kesalahan saat proses upload ke pixeldrain: {e}')
                return
            data = r.get('id')
            link = f"https://{server}/u/{data}"
            files = 1
            folders = 0
            mime_type = get_mime_type(self._path)
            async_to_sync(self.listener.onUploadComplete, link, size, files, folders, mime_type, None, None, server)
            
        except pycurl.error as e:
            if not self._is_cancelled:
                async_to_sync(self.listener.onUploadError, f'Pycurl error:{e}')
                return
        except Exception as e:
            async_to_sync(self.listener.onUploadError, f'Error: {e}')
            return
        finally:
            self._pycurl.close()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled")
                return
        
    @property
    def speed(self):
        try:
            return self._processed_bytes / (time() - self._start_time)
        except ZeroDivisionError:
            return 0

    @property
    def processed_bytes(self):
        return self._processed_bytes

    async def cancel_task(self):
        self._is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.listener.name}")
        await self.listener.onUploadError("Upload dibatalkan oleh User !")