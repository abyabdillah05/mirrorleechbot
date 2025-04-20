
from urllib.parse import quote
import re, base64, random
import aiohttp
import asyncio

headers = {'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'}

class CariFile:
    def __init__(self) -> None:
        self.headers = headers
        self.result = {'status':'failed', 'sign':'', 'timestamp':'', 'shareid':'', 'uk':'', 'list':[]}

    async def search(self, url: str) -> None:
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            async with session.get(url, allow_redirects=True) as resp:
                final_url = str(resp.url)
                try:
                    self.short_url = re.search(r'surl=([^ &]+)', final_url).group(1)
                except:
                    return
            
            await self.getMainFile()
            await self.getSign()

    async def getSign(self) -> None:
        api = 'https://terabox.hnn.workers.dev/api/get-info'
        post_url = f'{api}?shorturl={self.short_url}&pwd='
        headers_post = {
            'accept-language':'en-US,en;q=0.9,id;q=0.8',
            'referer':'https://terabox.hnn.workers.dev/',
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(post_url, headers=headers_post, allow_redirects=True) as resp:
                    pos = await resp.json()
                    if pos['ok']:
                        self.result['sign'] = pos['sign']
                        self.result['timestamp'] = pos['timestamp']
                        self.result['status'] = 'success'
                    else: 
                        self.result['status'] = 'failed'
        except:
            self.result['status'] = 'failed'

    async def getMainFile(self) -> None:
        url = f'https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl=1{self.short_url}&root=1'
        async with self.session.get(url, headers=self.headers, cookies={'cookie':''}) as resp:
            req = await resp.json()
            all_file = await self.packData(req, self.short_url)
            if len(all_file):
                self.result['shareid'] = req['shareid']
                self.result['uk'] = req['uk']
                self.result['list'] = all_file

    async def getChildFile(self, short_url, path:str='', root:str='0') -> list[dict[str, any]]:
        params = {'app_id':'250528', 'shorturl':short_url, 'root':root, 'dir':path}
        url = 'https://www.terabox.com/share/list?' + '&'.join([f'{a}={b}' for a,b in params.items()])
        async with self.session.get(url, headers=self.headers, cookies={'cookie':''}) as resp:
            req = await resp.json()
            return await self.packData(req, short_url)

    async def packData(self, req: dict, short_url: str) -> list[dict[str, any]]:
        all_file = []
        for item in req.get('list', []):
            file_data = {
                'is_dir': item['isdir'],
                'path': item['path'],
                'fs_id': item['fs_id'],
                'name': item['server_filename'],
                'size': item.get('size') if not bool(int(item.get('isdir'))) else '',
            }
            
            if item.get('isdir'):
                file_data['list'] = await self.getChildFile(short_url, item['path'], '0')
            else:
                file_data['list'] = []
                
            all_file.append(file_data)
        return all_file

class CariLink:
    def __init__(self, shareid: str, uk: str, sign: str, timestamp: str, fs_id: str, server_filename: str) -> None:
        self.domain = 'https://terabox.hnn.workers.dev/'
        self.api = f'{self.domain}api'
        self.headers = {
            'accept-language': 'en-US,en;q=0.9,id;q=0.8',
            'referer': self.domain,
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        self.result = {'status': 'failed', 'download_link': {}}
        self.params = {
            'shareid': str(shareid),
            'uk': str(uk),
            'sign': str(sign),
            'timestamp': str(timestamp),
            'fs_id': str(fs_id),
        }
        self.server = server_filename

    async def generate(self) -> None:
        params = self.params
        try:
            url = f'{self.api}/get-downloadp'
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, headers=self.headers, allow_redirects=True) as resp:
                    pos = await resp.json()
                    self.result['download_link'].update({'url': self.wrap_url(pos['downloadLink'])})
        except Exception as e:
            print(e)

        if len(list(self.result['download_link'].keys())) != 0:
            self.result['status'] = 'success'

    def wrap_url(self, original_url: str) -> str:
        quoted_url = quote(original_url, safe='')
        b64_encoded = base64.urlsafe_b64encode(quoted_url.encode()).decode()
        return f'https://{self.server}.workers.dev/?url={b64_encoded}'