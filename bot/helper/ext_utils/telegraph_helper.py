import requests
from secrets import token_urlsafe
from asyncio import sleep
from telegraph.aio import Telegraph
from telegraph.exceptions import RetryAfterError

from bot import LOGGER, bot_loop, bot

botnname = bot.me.first_name

class TelegraphHelper:
    def __init__(self, author_name=None, author_url=None):
        self._telegraph = Telegraph(domain="graph.org")
        self._author_name = author_name
        self._author_url = author_url

    async def create_account(self):
        await self._telegraph.create_account(
            short_name=token_urlsafe(8),
            author_name=self._author_name,
            author_url=self._author_url,
        )
        LOGGER.info("Creating Telegraph Account")

    async def create_page(self, title, content):
        try:
            return await self._telegraph.create_page(
                title=title,
                author_name=self._author_name,
                author_url=self._author_url,
                html_content=content,
            )
        except RetryAfterError as st:
            LOGGER.warning(
                f"Telegraph Flood control exceeded. I will sleep for {st.retry_after} seconds."
            )
            await sleep(st.retry_after)
            return await self.create_page(title, content)
        
    def upload_file(self, path):
        data = {'file': open(path, 'rb')}
        try:
            response = requests.post("https://telegra.ph/upload", files=data)

            if response.status_code == 200:
                result = response.json()[0]['src']
                return f"https://telegra.ph{result}"
            else:
                return("Error:", response.text)
        except Exception as e:
            return f"ERROR: {e}"

    async def edit_page(self, path, title, content):
        try:
            return await self._telegraph.edit_page(
                path=path,
                title=title,
                author_name=self._author_name,
                author_url=self._author_url,
                html_content=content,
            )
        except RetryAfterError as st:
            LOGGER.warning(
                f"Telegraph Flood control exceeded. I will sleep for {st.retry_after} seconds."
            )
            await sleep(st.retry_after)
            return await self.edit_page(path, title, content)

    async def edit_telegraph(self, path, telegraph_content):
        nxt_page = 1
        prev_page = 0
        num_of_path = len(path)
        for content in telegraph_content:
            if nxt_page == 1:
                content += (
                    f'<b><a href="https://telegra.ph/{path[nxt_page]}">Next</a></b>'
                )
                nxt_page += 1
            else:
                if prev_page <= num_of_path:
                    content += f'<b><a href="https://telegra.ph/{path[prev_page]}">Prev</a></b>'
                    prev_page += 1
                if nxt_page < num_of_path:
                    content += f'<b> | <a href="https://telegra.ph/{path[nxt_page]}">Next</a></b>'
                    nxt_page += 1
            await self.edit_page(
                path=path[prev_page],
                title="Pencarian ",
                content=content,
            )
        return


telegraph = TelegraphHelper(
    "{botnname}", "https://t.me/KazumaXcl_Bot"
)

bot_loop.run_until_complete(telegraph.create_account())
