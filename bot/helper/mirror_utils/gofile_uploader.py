import asyncio
import requests
import json
from random import choice

user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
class GofileUploader:
    def __init__(self, listener):
        self.l = listener
    
    def fetch_servers(self):
        headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*",
        "Connection": "keep-alive",
        }
        url = f"https://api.gofile.io/servers"
        try:
            with requests.Session() as session:
                r = session.get(url, headers=headers).json()
                if r["status"] == "ok":
                    return r["data"]
                else:
                    raise Exception
        except:
            raise Exception

    async def gofile_upload(self, item_path):
        try:
            list_server = self.fetch_servers()
        except:
            list_server = None
        if list_server:
            server = choice(list_server["servers"])["name"]
        else:
            return {"status": "error", "message": f"Tidak ada server gofile yang tersedia, silahkan coba beberapa saat lagi !"}
        
        command = [
            'curl',
            '-X', 'POST',
            f'https://{server}.gofile.io/contents/uploadfile',
            '-F', f'file=@{item_path}',
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            try:
                response_data = json.loads(stdout.decode())
                if response_data.get('status') == 'ok':
                    return response_data, server
                else:
                    return {"status": "error", "message": f"Terjadi kesalahan saat mencoba upload ke Gofile: {response_data.get('message')}"}
            except json.JSONDecodeError as e:
                return {"status": "error", "message": f"{e}"}
        else:
            return {"status": "error", "message": f"{stderr.decode()}"}