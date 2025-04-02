import aiohttp
from bot import LOGGER

## SafelinkU Short Link Generator Use Rest API ##

## Created by Tg @WzdDizzyFlasher ##
## You can edit API_TOKEN and API_URL if you have your own API ##
## Credit https://safelinku.com ##

class SafeLinkU:
    API_TOKEN = "ed0bb713b96184949787aefd37e0db0d889cb3ed"
    API_URL = "https://safelinku.com/api/v1/links"
    
    @staticmethod
    async def create_short_link(url, alias=None, passcode=None):
        headers = {
            "Authorization": f"Bearer {SafeLinkU.API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {"url": url}
        if alias:
            payload["alias"] = alias
        if passcode:
            payload["passcode"] = passcode
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(SafeLinkU.API_URL, headers=headers, json=payload) as response:
                    if response.status == 201:
                        data = await response.json()
                        LOGGER.info(f"SafelinkU short link created: {data.get('url', url)}")
                        return data.get("url", url)
                    else:
                        LOGGER.error(f"SafelinkU API error: Status {response.status}")
                        LOGGER.error(await response.text())
                        return url
        except Exception as e:
            LOGGER.error(f"Error creating SafelinkU short link: {str(e)}")
            return url
        
## You can make another class for other short link generator in here ##
## Thanks :) ##
## You can edit this file but don't remove the credits ##