import random
from time import time
from asyncio import (
    wait_for,
    Event,
    wrap_future
    )
from re import (
    findall,
    match
    )
from functools import partial
from bs4 import BeautifulSoup
from aiohttp import ClientSession

from pyrogram.filters import (
    regex,
    user
    )
from pyrogram.handlers import CallbackQueryHandler

###################################
## Import Variables From Project ##
###################################

from bot.helper.ext_utils.status_utils import get_readable_time, get_readable_file_size
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.mirror_utils.download_utils.direct_link_generator import sourceforge

from bot import (
    botname,
    LOGGER
    )
from bot.helper.ext_utils.bot_utils import (
    new_task,
    new_thread
    )
from bot.helper.telegram_helper.message_utils import (
    sendMessage,
    deleteMessage,
    editMessage
    )

## Credit @aenulrofik ##
## Enhancement by Tg @IgnoredProjectXcl ##
## Please don't remove the credits — respect the creator! ##

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()
    if data[1] == "start":
        await obj.start(data[2])
    elif data[1] == "random":
        await obj.random_server()
    elif data[1] == "cancel":
        await editMessage(message, "<b>Operation cancelled by user</b>")
        obj.is_cancelled = True
        obj.event.set()
        
@new_task
async def sourceforge_extract(url):
    cek = r"^(http:\/\/|https:\/\/)?(www\.)?sourceforge\.net\/.*"
    if not match(cek, url):
        raise DirectDownloadLinkException("<b>Invalid SourceForge URL format</b>\n\n<blockquote>Example: https://sourceforge.net/projects/project-name/files/filename.zip</blockquote>")
    
    async with ClientSession() as session:
        try:
            if not url.endswith('/download'):
                url += '/download'
            project = findall(r"projects?/(.*?)/files", url)[0]
            file_path = findall(r"/files/(.*?)(?:/download|\?|$)", url)[0]
            file_name = file_path.split('/')[-1]
            
            # Get file information
            file_info = {}
            try:
                project_url = f"https://sourceforge.net/projects/{project}/files/{file_path}"
                async with session.get(project_url) as response:
                    content = await response.text()
                info_soup = BeautifulSoup(content, "html.parser")
                file_details = info_soup.select(".file-info .detail-item")
                for detail in file_details:
                    label = detail.select_one(".detail-label")
                    value = detail.select_one(".detail-value")
                    if label and value:
                        file_info[label.text.strip()] = value.text.strip()
            except:
                pass
                
            # Get mirrors with location data
            mirror_url = f"https://sourceforge.net/settings/mirror_choices?projectname={project}&filename={file_path}"
            async with session.get(mirror_url) as response:
                content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            mirror_list = soup.find("ul", {"id": "mirrorList"})
            if not mirror_list:
                raise DirectDownloadLinkException("<b>No mirror servers found or file has been removed</b>")
                
            mirrors = []
            for mirror in mirror_list.findAll("li"):
                if 'id' in mirror.attrs:
                    mirror_id = mirror['id']
                    mirror_name = mirror.text.strip()
                    location = ""
                    if "(" in mirror_name and ")" in mirror_name:
                        location = mirror_name.split("(")[1].split(")")[0].strip()
                    
                    # Extract ping time if available
                    ping_element = mirror.select_one(".location-info")
                    ping_time = None
                    if ping_element:
                        ping_text = ping_element.text.strip()
                        if "ms" in ping_text:
                            ping_time = ping_text
                            
                    mirrors.append({
                        "id": mirror_id,
                        "name": mirror_name,
                        "location": location,
                        "ping": ping_time
                    })
            
            # Remove autoselect option
            if mirrors and mirrors[0]['id'] == 'autoselect':
                mirrors.pop(0)
                
            if not mirrors:
                raise DirectDownloadLinkException("<b>No suitable mirrors found for this file</b>")
                
            return {"mirrors": mirrors, "file_info": file_info, "file_name": file_name, "project": project, "file_path": file_path}
        
        except Exception as e:
            raise DirectDownloadLinkException(f"<b>Error processing SourceForge link:</b> {str(e)}")

class sourceforgeExtract:
    def __init__(self, listener):
        self._listener = listener
        self._time = time()
        self._timeout = 180
        self.event = Event()
        self._mirrors = []
        self._link = ""
        self._final_link = ""
        self._reply_to = None
        self._file_info = {}
        self._file_name = ""
        self._project = ""
        self._file_path = ""
        self.is_cancelled = False

    @new_thread
    async def _event_handler(self):
        pfunc = partial(main_select, obj=self)
        handler = self._listener.client.add_handler(
            CallbackQueryHandler(
                pfunc, filters=regex("^sourceforge") & user(self._listener.user_id)
            ),
            group=-1,
        )
        try:
            await wait_for(self.event.wait(), timeout=self._timeout)
        except:
            await editMessage(self._reply_to, "<b>Session timed out. Operation cancelled</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
            
    async def main(self, link):
        self._link = link
        future = self._event_handler()
        
        extract_data = await sourceforge_extract(link)
        if not extract_data:
            return None
            
        self._mirrors = extract_data["mirrors"]
        self._file_info = extract_data["file_info"]
        self._file_name = extract_data["file_name"]
        self._project = extract_data["project"]
        self._file_path = extract_data["file_path"]
        
        butt = ButtonMaker()
        
        # Build message with file info
        msg = "<b>SourceForge Link Detected</b>\n\n"
        msg += f"<b>File:</b> {self._file_name}\n"
        msg += f"<b>Project:</b> {self._project}\n"
        
        # Add file info if available
        if self._file_info:
            if "Size" in self._file_info:
                msg += f"<b>Size:</b> {self._file_info['Size']}\n"
            if "Date" in self._file_info:
                msg += f"<b>Date:</b> {self._file_info['Date']}\n"
            if "Downloads" in self._file_info:
                msg += f"<b>Downloads:</b> {self._file_info['Downloads']}\n"
                
        msg += "\n<b>Select a mirror server:</b>"
        
        # Sort mirrors by region for better organization
        regions = {}
        for mirror in self._mirrors:
            region = mirror.get('location', 'Unknown')
            if not region:
                region = 'Unknown'
            
            if region not in regions:
                regions[region] = []
            regions[region].append(mirror)

        # Create buttons grouped by region
        for region, mirrors in regions.items():
            for mirror in mirrors:
                button_text = mirror['id']
                ping_info = f" ({mirror['ping']})" if mirror.get('ping') else ""
                location_info = f" - {mirror['location']}" if mirror['location'] else ""
                button_text = f"{mirror['id']}{location_info}{ping_info}"
                
                # Truncate if too long
                if len(button_text) > 35:
                    button_text = button_text[:32] + "..."
                    
                butt.ibutton(button_text, f"sourceforge start {mirror['id']}")
            
        # Add random and cancel buttons
        butt.ibutton("Random Server", f"sourceforge random", position="header")
        butt.ibutton("Cancel", f"sourceforge cancel", position="footer")
        
        # Build button menu with 2 buttons per row
        butts = butt.build_menu(2)
        
        # Add timeout information
        msg += f"\n\n<b>Session expires in:</b> {get_readable_time(self._timeout)}"
        
        self._reply_to = await sendMessage(self._listener.message, msg, butts)
        await wrap_future(future)
        
        if not self.is_cancelled:
            await deleteMessage(self._reply_to)
            return self._final_link
    
    async def start(self, server):
        server_info = next((mirror for mirror in self._mirrors if mirror['id'] == server), None)
        location_text = f" ({server_info['location']})" if server_info and server_info['location'] else ""
        
        await editMessage(self._reply_to, f"<b>Selected server:</b> {server}{location_text}\n<b>Generating direct download link...</b>")
        self._final_link = f"https://{server}.dl.sourceforge.net/project/{self._project}/{self._file_path}?viasf=1"
        self.event.set()
    
    async def random_server(self):
        server = random.choice([mirror['id'] for mirror in self._mirrors])
        server_info = next((mirror for mirror in self._mirrors if mirror['id'] == server), None)
        location_text = f" ({server_info['location']})" if server_info and server_info['location'] else ""
        
        await editMessage(self._reply_to, f"<b>Randomly selected server:</b> {server}{location_text}\n<b>Generating direct download link...</b>")
        await self.start(server)

## Big thanks to @aenulrofik for this awesome feature ##
## Please don't remove the credits — respect the creator! ##