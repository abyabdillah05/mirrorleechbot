from urllib.parse import quote
import re, requests, base64, random

headers : dict[str, str] = {'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36'}
class CariFile():
    def __init__(self) -> None:
        self.r : object = requests.Session()
        self.headers : dict[str,str] = headers
        self.result : dict[str,any] = {'status':'failed', 'sign':'', 'timestamp':'', 'shareid':'', 'uk':'', 'list':[]}

    def search(self, url:str) -> None:
        req : str = self.r.get(url, allow_redirects=True)
        self.short_url : str = re.search(r'surl=([^ &]+)',str(req.url)).group(1)
        self.getMainFile()
        self.getSign()

    def getSign(self) -> None:
        api = 'https://terabox.hnn.workers.dev/api/get-info'
        post_url = f'{api}?shorturl={self.short_url}&pwd='
        headers_post : dict[str,str] = {
            'accept-language':'en-US,en;q=0.9,id;q=0.8',
            'referer':'https://terabox.hnn.workers.dev/',
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        try:
            r = requests.Session()
            pos = r.get(post_url, headers=headers_post, allow_redirects=True).json()
            if pos['ok']:
                self.result['sign']      = pos['sign']
                self.result['timestamp'] = pos['timestamp']
                self.result['status']    = 'success'
            else: self.result['status']  = 'failed'
            r.close()
        except: self.result['status']    = 'failed'

    def getMainFile(self) -> None:
        url: str = f'https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl=1{self.short_url}&root=1'
        req : object = self.r.get(url, headers=self.headers, cookies={'cookie':''}).json()
        all_file = self.packData(req, self.short_url)
        if len(all_file):
            self.result['shareid']   = req['shareid']
            self.result['uk']        = req['uk']
            self.result['list']      = all_file

    def getChildFile(self, short_url, path:str='', root:str='0') -> list[dict[str, any]]:
        params = {'app_id':'250528', 'shorturl':short_url, 'root':root, 'dir':path}
        url = 'https://www.terabox.com/share/list?' + '&'.join([f'{a}={b}' for a,b in params.items()])
        req : object = self.r.get(url, headers=self.headers, cookies={'cookie':''}).json()
        return(self.packData(req, short_url))

    def packData(self, req:dict, short_url:str) -> list[dict[str, any]]:
        all_file = [{
            'is_dir' : item['isdir'],
            'path'   : item['path'],
            'fs_id'  : item['fs_id'],
            'name'   : item['server_filename'],
            'size'   : item.get('size') if not bool(int(item.get('isdir'))) else '',
            'list'   : self.getChildFile(short_url, item['path'], '0') if item.get('isdir') else [],
        } for item in req.get('list', [])]
        return(all_file)

class CariLink():
    def __init__(self, shareid:str, uk:str, sign:str, timestamp:str, fs_id:str) -> None:
        self.domain : str = 'https://terabox.hnn.workers.dev/'
        self.api    : str = f'{self.domain}api'
        self.r : object = requests.Session()
        self.headers : dict[str,str] = {
            'accept-language':'en-US,en;q=0.9,id;q=0.8',
            'referer':self.domain,
            'sec-fetch-mode':'cors',
            'sec-fetch-site':'same-origin',
            'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
        self.result : dict[str,dict] = {'status':'failed', 'download_link':{}}
        self.params : dict[str,any] = {
            'shareid'   : str(shareid),
            'uk'        : str(uk),
            'sign'      : str(sign),
            'timestamp' : str(timestamp),
            'fs_id'     : str(fs_id),
        }
        self.base_urls = [
            'plain-grass-58b2.comprehensiveaquamarine',
            'royal-block-6609.ninnetta7875',
            'bold-hall-f23e.7rochelle',
            'winter-thunder-0360.belitawhite',
            'fragrant-term-0df9.elviraeducational',
            'purple-glitter-924b.miguelalocal'
        ]

    def generate(self) -> None:
        params : dict = self.params
        try:
            url=  f'{self.api}/get-downloadp'
            pos = self.r.post(url, json=params, headers=self.headers, allow_redirects=True).json()
            self.result['download_link'].update({'url':self.wrap_url(pos['downloadLink'])})
        except Exception as e: print(e)

        if len(list(self.result['download_link'].keys())) != 0:
            self.result['status'] = 'success'
        self.r.close()

    def wrap_url(self, original_url:str) -> str:
        selected_base = random.choice(self.base_urls)
        quoted_url = quote(original_url, safe='')
        b64_encoded = base64.urlsafe_b64encode(quoted_url.encode()).decode()
        return f'https://{selected_base}.workers.dev/?url={b64_encoded}'