import asyncio
import aiohttp
import json
from random import choice

user_agent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
class GofileUploader:
    def __init__(self, listener):
        self.l = listener
    
    async def fetch_servers(self):
        url = "https://api.gofile.io/servers"
        headers = {
        "User-Agent": user_agent
    }
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(url, headers=headers) as r:
                    json.loads(r)
                    if r["status"] == "ok":
                        return r["data"]
                    else:
                        return None
        except:
            raise None

    async def gofile_upload(self, item_path):
        try:
            list_server = await self.fetch_servers()
        except:
            list_server = None
        if list_server:
            server = choice(list_server["servers"])["name"]
        else:
            server = "store1"
        
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
                    return response_data
                else:
                    return {"status": "error", "message": f"Terjadi kesalahan saat mencoba upload ke Gofile: {response_data.get('message')}"}
            except json.JSONDecodeError as e:
                return {"status": "error", "message": f"{e}"}
        else:
            return {"status": "error", "message": f"{stderr.decode()}", "server": server}