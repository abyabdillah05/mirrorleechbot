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

from bot.helper.ext_utils.status_utils import get_readable_time,get_readable_file_size
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException

from bot import (
    botname,
    LOGGER,
    LOG_CHAT_ID,
    OWNER_ID
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
## Minor Modifications By Tg @IgnoredProjectXcl ##

@new_task
async def main_select(_, query, obj):
    data = query.data.split()
    message = query.message
    await query.answer()
    
    if data[1] == "start":
        await obj.start(data[2])
    elif data[1] == "random":
        await obj.random_server()
    elif data[1] == "navigate":
        await obj.navigate(data[2], data[3] if len(data) > 3 else None)
    elif data[1] == "select":
        await obj.select_file(data[2])
    elif data[1] == "download":
        await obj.download_selected()
    elif data[1] == "back":
        await obj.navigate_back()
    elif data[1] == "cancel":
        await editMessage(message, "<b>Task canceled by user!</b>")
        obj.is_cancelled = True
        obj.event.set()

@new_task
async def get_sf_content(url, current_path=""):
    """Get files and folders from a SourceForge path"""
    try:
        # Form proper URL to access project files
        project = findall(r"projects?/(.*?)/files", url)[0]
        base_url = f"https://sourceforge.net/projects/{project}/files"
        path_url = f"{base_url}/{current_path}" if current_path else base_url
        
        async with ClientSession() as session:
            async with session.get(path_url) as response:
                content = await response.text()
                
        soup = BeautifulSoup(content, "html.parser")
        
        # Find all table rows containing files and folders
        rows = soup.find_all("tr", class_="folder") + soup.find_all("tr", class_="file")
        
        folders = []
        files = []
        
        for row in rows:
            name_td = row.find("th", class_="name") or row.find("td", class_="name")
            if not name_td:
                continue
                
            name_a = name_td.find("a")
            if not name_a:
                continue
                
            name = name_a.text.strip()
            item_path = name_a.get("href").split("/files/")[1] if "/files/" in name_a.get("href", "") else name_a.get("href", "")
            
            if "folder" in row.get("class", []):
                folders.append({"name": name, "path": item_path})
            else:
                size_td = row.find("td", class_="size")
                size = size_td.text.strip() if size_td else "Unknown"
                files.append({"name": name, "path": item_path, "size": size})
        
        return {"folders": folders, "files": files, "project": project}
    except Exception as e:
        LOGGER.error(f"Error getting SourceForge content: {str(e)}")
        raise DirectDownloadLinkException(f"Failed to get directory contents: {str(e)}")

@new_task
async def sourceforge_extract(url):
    """Extract mirror servers from a SourceForge download URL"""
    cek = r"^(http:\/\/|https:\/\/)?(www\.)?sourceforge\.net\/.*"
    if not match(cek, url):
        raise DirectDownloadLinkException(
            "ERROR: Invalid link, use SourceForge non-DDL link!\n\n<blockquote><code>Example: https://sourceforge.net/projects/xxx/files/xxx/xxx.zip</code></blockquote>"
        )
    
    # Clean URL format
    if "/download" in url:
        url = url.split("/download")[0]
        
    async with ClientSession() as session:
        try:
            project = findall(r"projects?/(.*?)/files", url)[0]
            file_path = url.split(f"/projects/{project}/files/")[1] if f"/projects/{project}/files/" in url else ""
            
            # Check if URL points to a directory
            if not any(url.endswith(ext) for ext in ['.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.msi', '.deb', '.rpm']):
                # It might be a directory, return content instead
                return await get_sf_content(url, file_path)
                
            # For files, get mirror servers
            mirror_url = f"https://sourceforge.net/settings/mirror_choices?projectname={project}&filename={file_path}"
            async with session.get(mirror_url) as response:
                content = await response.text()
                
            soup = BeautifulSoup(content, "html.parser")
            mirror_list = soup.find("ul", {"id": "mirrorList"})
            
            if not mirror_list:
                raise DirectDownloadLinkException(f"Mirror servers not found or file has been removed.")
            
            mirrors = mirror_list.find_all("li")
            servers = []
            
            for mirror in mirrors:
                servers.append(mirror['id'])
                
            if servers and servers[0] == "autoselect":
                servers.pop(0)
                
            return {"servers": servers, "project": project, "file_path": file_path}
        except Exception as e:
            raise DirectDownloadLinkException(f"ERROR: {str(e)}")

class SourceforgeExtract:
    def __init__(self, listener):
        self._listener = listener
        self._time = time()
        self._timeout = 300  # Increased timeout
        self.event = Event()
        self._servers = []
        self._link = ""
        self._final_link = ""
        self._reply_to = None
        self.is_cancelled = False
        self._project = ""
        self._current_path = ""  # Current directory path
        self._path_stack = []  # Stack for back navigation
        self._selected_files = []  # Selected files for download
        self._file_data = {}  # Store file data for final download

    @new_thread
    async def _event_handler(self):
        """Handle button events"""
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
            await editMessage(self._reply_to, "<b>Timeout, task canceled!</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
            
    async def main(self, link):
        """Main entry point for the SourceForge handler"""
        self._link = link
        future = self._event_handler()
        
        try:
            # Check if the link is a file or directory
            result = await sourceforge_extract(link)
            
            if isinstance(result, dict) and "servers" in result:
                # It's a file download
                self._servers = result["servers"]
                self._project = result["project"]
                self._file_path = result["file_path"]
                await self._show_server_selection()
            elif isinstance(result, dict) and "folders" in result:
                # It's a directory listing
                self._project = result["project"]
                self._current_path = self._link.split("/files/")[1] if "/files/" in self._link else ""
                await self._show_directory_contents(result)
            else:
                await sendMessage(self._listener.message, "Invalid SourceForge URL")
                self.is_cancelled = True
                self.event.set()
                return
        except DirectDownloadLinkException as e:
            await sendMessage(self._listener.message, str(e))
            self.is_cancelled = True
            self.event.set()
            return
            
        await wrap_future(future)
        
        if not self.is_cancelled and self._final_link:
            await deleteMessage(self._reply_to)
            return self._final_link
    
    async def _show_server_selection(self):
        """Show server selection buttons"""
        butt = ButtonMaker()
        
        if isinstance(self._servers, list) and self._servers:
            for server in self._servers:
                butt.ibutton(f"{server}", f"sourceforge start {server}")
                
            butt.ibutton("Select Random Server", f"sourceforge random", position="header")
            butt.ibutton("Cancel", f"sourceforge cancel", position="footer")
            butts = butt.build_menu(3)
            
            msg = f"<b>SourceForge Mirror Server Selection</b>\n\n"
            msg += f"<b>Project:</b> <code>{self._project}</code>\n"
            msg += f"<b>Please select a mirror server:</b>\n"
            msg += f"<i>Tip: Choose a server closest to your location for optimal speed</i>\n\n"
            msg += f"<b>Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
            msg += f"\n\n<b>Powered By {botname}</b>"
            
            self._reply_to = await sendMessage(self._listener.message, msg, butts)
        else:
            await sendMessage(self._listener.message, "ERROR: No mirror servers available!")
            self.is_cancelled = True
            self.event.set()
            return
    
    async def _show_directory_contents(self, content):
        """Display directory contents with navigation buttons"""
        folders = content.get("folders", [])
        files = content.get("files", [])
        
        butt = ButtonMaker()
        
        # Add navigation buttons
        if self._path_stack:
            butt.ibutton("Back", "sourceforge back", position="header")
        
        # Add folders
        for folder in folders:
            folder_name = folder["name"]
            encoded_path = folder["path"].replace(" ", "%20")
            butt.ibutton(f"📁 {folder_name}", f"sourceforge navigate {encoded_path}")
        
        # Add files with selection option
        for file in files:
            file_name = file["name"]
            encoded_path = file["path"].replace(" ", "%20")
            selected = "✓ " if encoded_path in self._selected_files else ""
            butt.ibutton(f"{selected}📄 {file_name}", f"sourceforge select {encoded_path}")
            
            # Store file data for later use
            self._file_data[encoded_path] = {
                "name": file_name,
                "path": encoded_path,
                "size": file.get("size", "Unknown")
            }
        
        # Add download button if files are selected
        if self._selected_files:
            butt.ibutton("Download Selected", "sourceforge download", position="footer")
        
        butt.ibutton("Cancel", "sourceforge cancel", position="footer")
        
        butts = butt.build_menu(1)  # One button per row for better readability
        
        current_path_display = f"/{self._current_path}" if self._current_path else "/"
        
        msg = f"<b>SourceForge Directory Browser</b>\n\n"
        msg += f"<b>Project:</b> <code>{self._project}</code>\n"
        msg += f"<b>Current Path:</b> <code>{current_path_display}</code>\n\n"
        
        if self._selected_files:
            msg += f"<b>Selected Files:</b> {len(self._selected_files)}\n\n"
        
        if not folders and not files:
            msg += "<b>This directory is empty.</b>\n"
        else:
            msg += f"<b>Contents:</b> {len(folders)} folders, {len(files)} files\n"
        
        msg += f"\n<b>Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        msg += f"\n\n<b>Powered By {botname}</b>"
        
        if self._reply_to:
            self._reply_to = await editMessage(self._reply_to, msg, butts)
        else:
            self._reply_to = await sendMessage(self._listener.message, msg, butts)
    
    async def navigate(self, path, subfolder=None):
        """Navigate to a directory"""
        try:
            # Push current path to stack for back navigation
            if self._current_path:
                self._path_stack.append(self._current_path)
            
            self._current_path = path
            
            # Get contents of the new path
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            content = await get_sf_content(project_url, path)
            
            await self._show_directory_contents(content)
        except Exception as e:
            await editMessage(self._reply_to, f"<b>Error navigating to directory:</b> <code>{str(e)}</code>")
            self.is_cancelled = True
            self.event.set()
    
    async def navigate_back(self):
        """Navigate back to previous directory"""
        if self._path_stack:
            self._current_path = self._path_stack.pop()
            
            # Get contents of the previous path
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            content = await get_sf_content(project_url, self._current_path)
            
            await self._show_directory_contents(content)
        else:
            # If at root directory, show root contents
            self._current_path = ""
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            content = await get_sf_content(project_url)
            
            await self._show_directory_contents(content)
    
    async def select_file(self, file_path):
        """Select or deselect a file"""
        if file_path in self._selected_files:
            self._selected_files.remove(file_path)
        else:
            self._selected_files.append(file_path)
        
        # Update UI to reflect selection
        project_url = f"https://sourceforge.net/projects/{self._project}/files"
        content = await get_sf_content(project_url, self._current_path)
        
        await self._show_directory_contents(content)
    
    async def download_selected(self):
        """Process all selected files for download"""
        if not self._selected_files:
            await editMessage(self._reply_to, "<b>No files selected for download.</b>")
            return
        
        # If only one file is selected, handle it directly
        if len(self._selected_files) == 1:
            file_path = self._selected_files[0]
            file_url = f"https://sourceforge.net/projects/{self._project}/files/{file_path}"
            
            try:
                result = await sourceforge_extract(file_url)
                if isinstance(result, dict) and "servers" in result:
                    self._servers = result["servers"]
                    self._project = result["project"]
                    self._file_path = result["file_path"]
                    await self._show_server_selection()
                else:
                    raise DirectDownloadLinkException("Failed to get server information")
            except Exception as e:
                await editMessage(self._reply_to, f"<b>Error processing download:</b> <code>{str(e)}</code>")
                self.is_cancelled = True
                self.event.set()
        else:
            # Multiple files selected
            # For multiple files, we'll use a random server for all
            links = []
            
            # First, get servers for one file to use for all
            sample_file = self._selected_files[0]
            sample_url = f"https://sourceforge.net/projects/{self._project}/files/{sample_file}"
            
            try:
                result = await sourceforge_extract(sample_url)
                if isinstance(result, dict) and "servers" in result:
                    server = random.choice(result["servers"])
                    
                    # Create links for all selected files
                    for file_path in self._selected_files:
                        file_data = self._file_data.get(file_path, {})
                        file_name = file_data.get("name", "Unknown")
                        direct_link = f"https://{server}.dl.sourceforge.net/project/{self._project}/{file_path}?viasf=1"
                        links.append({"name": file_name, "url": direct_link})
                    
                    # This will require modification in the caller to handle multiple links
                    self._final_link = links
                    await editMessage(self._reply_to, f"<b>Server selected:</b> <code>{server}</code>\n<b>Processing download for {len(links)} files...</b>")
                    self.event.set()
                else:
                    raise DirectDownloadLinkException("Failed to get server information")
            except Exception as e:
                await editMessage(self._reply_to, f"<b>Error processing download:</b> <code>{str(e)}</code>")
                self.is_cancelled = True
                self.event.set()
    
    async def start(self, server):
        """Start download with selected server"""
        try:
            self._final_link = f"https://{server}.dl.sourceforge.net/project/{self._project}/{self._file_path}?viasf=1"
            
            await editMessage(
                self._reply_to, 
                f"<b>Mirror server selected:</b> <code>{server}</code>\n<b>Processing download...</b>"
            )
            
            self.event.set()
        except Exception as e:
            await editMessage(self._reply_to, f"<b>Error processing server:</b> <code>{str(e)}</code>")
            self.is_cancelled = True
            self.event.set()
            
    async def random_server(self):
        """Select a random mirror server"""
        server = random.choice(self._servers)
        await self.start(server)

## Big thanks to @aenulrofik for this awesome feature ##
## Please don't remove the credits — respect the creator! ##