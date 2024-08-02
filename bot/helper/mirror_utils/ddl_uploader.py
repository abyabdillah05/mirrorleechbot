import pycurl
import json
import os
import requests

from logging import getLogger
from time import time
from io import BytesIO
from random import choice
from bot.helper.ext_utils.bot_utils import async_to_sync
from bot.helper.ext_utils.files_utils import get_mime_type

LOGGER = getLogger(__name__)
user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"

class DdlUploader:
    def __init__(self, listener, path):
        self._last_uploaded = 0
        self._processed_bytes = 0
        self.listener = listener
        self._token = None
        self._path = path
        self._start_time = time()
        self._is_cancelled = False
        self._pycurl = pycurl.Curl()

    def _upload_progress(self, download_t, download_d, upload_t, upload_d):
        if self._is_cancelled:
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
        self._token = self.get_token()
        folder_data = self.create_folder(
            (self.get_rootfolder()), os.path.basename(dir_path))
        self.set_option(folder_data["id"])
        folder_id = folder_data["id"]
        folder_ids = {".": folder_id}
        files_count = 0
        folders_count = 0
        for root, dirs, files in os.walk(dir_path):
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
        if server is None:
            server = choice(self.fetch_servers()["servers"]).get("name")
        response_buffer = BytesIO()
        ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
        self._pycurl.setopt(self._pycurl.URL, f"https://{server}.gofile.io/contents/uploadfile")
        self._pycurl.setopt(pycurl.CAINFO, ca_cert_path)
        if isfolder:
            self._pycurl.setopt(self._pycurl.HTTPHEADER, ['Authorization: Bearer ' + self._token])
        self._pycurl.setopt(self._pycurl.POST, 1)
        self._pycurl.setopt(self._pycurl.WRITEDATA, response_buffer)
        self._pycurl.setopt(self._pycurl.NOPROGRESS, False)
        self._pycurl.setopt(self._pycurl.XFERINFOFUNCTION, self._upload_progress)
        if isfolder:
            self._pycurl.setopt(self._pycurl.HTTPPOST, [
                ('folderId', folder_id),
                ('file', (self._pycurl.FORM_FILE, file_path))
            ])
        else:
            self._pycurl.setopt(self._pycurl.HTTPPOST, [
                ('file', (self._pycurl.FORM_FILE, self._path))
            ])
        try:
            self._pycurl.perform()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled during the process")
                return
            
            response_data = response_buffer.getvalue()
            if not response_data:
                async_to_sync(self.listener.onUploadError, "Terjadi kesalahan saat proses upload ke gofile")
            response = response_data.decode()
            try:
                r = json.loads(response)
            except json.JSONDecodeError as e:
                async_to_sync(self.listener.onUploadError, e)
                return
            if isfolder:
                return
            else:
                data = r.get('data', {})
                link = data.get('downloadPage')
                size = data.get('size')
                files = 1
                folders = 0
                mime_type = data.get('mimetype')
                async_to_sync(self.listener.onUploadComplete, link, size, files, folders, mime_type, None, None, server)

        except pycurl.error as e:
            if not self._is_cancelled:
                async_to_sync(self.listener.onUploadError, e)
                return

        except Exception as e:
            async_to_sync(self.listener.onUploadError, e)
            return
        
    def bh_upload(self, size):
        file_name = os.path.basename(self._path)
        servers = ["buzzheavier.com", "trashbytes.net", "flashbang.sh"]
        server = choice(servers)
        response_buffer = BytesIO()
        ca_cert_path = '/etc/ssl/certs/ca-certificates.crt'
        self._pycurl.setopt(self._pycurl.URL, f"https://w.{server}/{file_name}")
        self._pycurl.setopt(pycurl.CAINFO, ca_cert_path)
        self._pycurl.setopt(self._pycurl.UPLOAD, 1)
        self._pycurl.setopt(self._pycurl.READFUNCTION, open(self._path, 'rb').read)
        self._pycurl.setopt(self._pycurl.READDATA, open(self._path, 'rb'))
        self._pycurl.setopt(self._pycurl.WRITEFUNCTION, response_buffer.write)
        self._pycurl.setopt(self._pycurl.NOPROGRESS, False)
        self._pycurl.setopt(self._pycurl.XFERINFOFUNCTION, self._upload_progress)
        try:
            self._pycurl.perform()
            if self._is_cancelled:
                LOGGER.info("Upload was cancelled during the process")
                return
            response_data = response_buffer.getvalue()
            if not response_data:
                async_to_sync(self.listener.onUploadError,'Received empty response from server')
            response = response_data.decode()
            try:
                r = json.loads(response)
            except json.JSONDecodeError as e:
                async_to_sync(self.listener.onUploadError,f'Error decoding JSON: {e}')
            data = r.get('id')
            link = f"https://buzzheavier.com/f/{data}"
            files = 1
            folders = 0
            mime_type = get_mime_type(self._path)
            async_to_sync(self.listener.onUploadComplete, link, size, files, folders, mime_type, None, None, server)

        except pycurl.error as e:
            if not self._is_cancelled:
                async_to_sync(self.listener.onUploadError, f'{e}')
                return

        except Exception as e:
            async_to_sync(self.listener.onUploadError, f'{e}')
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
        LOGGER.info(f"Cancelling Upload: {self._listener.name}")
        await self.listener.onUploadError("Upload dibatalkan oleh User !")