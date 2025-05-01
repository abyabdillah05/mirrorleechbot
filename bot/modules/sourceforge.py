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
    elif data[1] == "navigate":
        await obj.navigate_by_id(data[2])
    elif data[1] == "select":
        await obj.select_file_by_id(data[2])
    elif data[1] == "download":
        await obj.download_selected()
    elif data[1] == "back":
        await obj.navigate_back()
    elif data[1] == "cancel":
        await editMessage(message, "<b>Task canceled by user</b>")
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
        
        LOGGER.info(f"Fetching directory contents from: {path_url}")
        
        async with ClientSession() as session:
            async with session.get(path_url) as response:
                content = await response.text()
                
        soup = BeautifulSoup(content, "html.parser")
        
        # Check for different HTML structures that SourceForge might use
        folders = []
        files = []
        
        # Method 1: Standard table rows
        rows = soup.find_all("tr", class_="folder") + soup.find_all("tr", class_="file")
        
        if not rows:
            # Method 2: Try alternate structure - div based
            folder_divs = soup.select(".folder-name")
            file_divs = soup.select(".file-name")
            
            for div in folder_divs:
                a_tag = div.find("a")
                if a_tag:
                    name = a_tag.text.strip()
                    href = a_tag.get("href", "")
                    if "/files/" in href:
                        item_path = href.split("/files/")[1]
                    else:
                        item_path = f"{current_path}/{name}" if current_path else name
                    folders.append({"name": name, "path": item_path})
            
            for div in file_divs:
                a_tag = div.find("a")
                if a_tag:
                    name = a_tag.text.strip()
                    href = a_tag.get("href", "")
                    if "/files/" in href:
                        item_path = href.split("/files/")[1]
                    else:
                        item_path = f"{current_path}/{name}" if current_path else name
                    
                    size_span = div.find_next("span", class_="size")
                    size = size_span.text.strip() if size_span else "Unknown"
                    files.append({"name": name, "path": item_path, "size": size})
        else:
            # Process standard table rows
            for row in rows:
                name_td = row.find("th", class_="name") or row.find("td", class_="name")
                if not name_td:
                    continue
                    
                name_a = name_td.find("a")
                if not name_a:
                    continue
                    
                name = name_a.text.strip()
                href = name_a.get("href", "")
                
                # Extract path from href
                if "/files/" in href:
                    item_path = href.split("/files/")[1]
                else:
                    # If path cannot be extracted correctly, use current path + name
                    if current_path:
                        item_path = f"{current_path}/{name}"
                    else:
                        item_path = name
                
                if "folder" in row.get("class", []):
                    folders.append({"name": name, "path": item_path})
                else:
                    size_td = row.find("td", class_="size")
                    size = size_td.text.strip() if size_td else "Unknown"
                    files.append({"name": name, "path": item_path, "size": size})
        
        # Method 3: Try to find items in the general structure
        if not folders and not files:
            # Look for any link that has a path structure indicating a file or folder
            all_links = soup.find_all("a")
            for link in all_links:
                href = link.get("href", "")
                if "/files/" in href and project in href:
                    # Extract the path
                    try:
                        path_part = href.split(f"/projects/{project}/files/")[1]
                        # Determine if it's likely a folder or file
                        name = link.text.strip()
                        if not name:
                            continue
                            
                        if href.endswith("/download"):
                            # Likely a file
                            path_part = path_part.replace("/download", "")
                            files.append({"name": name, "path": path_part, "size": "Unknown"})
                        else:
                            # Likely a folder
                            folders.append({"name": name, "path": path_part})
                    except:
                        continue

        LOGGER.info(f"Found {len(folders)} folders and {len(files)} files")
        return {"folders": folders, "files": files, "project": project}
    except Exception as e:
        LOGGER.error(f"Error getting SourceForge content: {str(e)}")
        raise DirectDownloadLinkException(f"Failed to get directory contents: {str(e)}")

@new_task
async def sourceforge_extract(url):
    """Extract mirror servers from a SourceForge download URL or get directory contents"""
    cek = r"^(http:\/\/|https:\/\/)?(www\.)?sourceforge\.net\/.*"
    if not match(cek, url):
        raise DirectDownloadLinkException(
            "ERROR: Invalid link, use SourceForge non-DDL link"
        )
    
    # Clean URL format
    if "/download" in url:
        url = url.split("/download")[0]
        
    async with ClientSession() as session:
        try:
            project = findall(r"projects?/(.*?)/files", url)[0]
            file_path = url.split(f"/projects/{project}/files/")[1] if f"/projects/{project}/files/" in url else ""
            
            # First try to get directory contents
            try:
                content = await get_sf_content(url, file_path)
                # If we got here, it's most likely a directory
                return content
            except Exception as dir_err:
                LOGGER.info(f"URL might be a direct file, trying mirror choices")
                
            # If failed to get directory contents, try to get mirror servers
            mirror_url = f"https://sourceforge.net/settings/mirror_choices?projectname={project}&filename={file_path}"
            LOGGER.info(f"Getting mirror choices from: {mirror_url}")
            
            async with session.get(mirror_url) as response:
                content = await response.text()
                
            soup = BeautifulSoup(content, "html.parser")
            mirror_list = soup.find("ul", {"id": "mirrorList"})
            
            if not mirror_list:
                raise DirectDownloadLinkException(f"Mirror servers not found or file has been removed")
            
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
        self._timeout = 300
        self.event = Event()
        self._servers = []
        self._link = ""
        self._final_link = ""
        self._reply_to = None
        self.is_cancelled = False
        self._project = ""
        self._file_path = ""
        self._current_path = ""
        self._path_stack = []
        self._selected_files = []
        self._file_data = {}
        self._path_map = {}
        self._next_id = 1

    def _get_short_id(self, path):
        """Get a short ID for a path or create one if it doesn't exist"""
        for id_str, stored_path in self._path_map.items():
            if stored_path == path:
                return id_str
                
        # Create a new short ID
        id_str = str(self._next_id)
        self._path_map[id_str] = path
        self._next_id += 1
        return id_str

    def _get_path_from_id(self, id_str):
        """Get the path associated with an ID"""
        return self._path_map.get(id_str)

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
            if self._reply_to:
                await editMessage(self._reply_to, "<b>Timeout, task canceled</b>")
            self.is_cancelled = True
            self.event.set()
        finally:
            self._listener.client.remove_handler(*handler)
            
    async def main(self, link):
        """Main entry point for the SourceForge handler"""
        self._link = link
        future = self._event_handler()
        
        try:
            # Create initial loading message first, so it's always available
            self._reply_to = await sendMessage(
                self._listener.message, 
                f"<b>Processing SourceForge link...</b>"
            )
            
            # Special shortcut for direct download links
            if "/download" in link:
                try:
                    self._final_link = sourceforge(link)
                    self.event.set()
                    await wrap_future(future)
                    await deleteMessage(self._reply_to)
                    return self._final_link
                except Exception as e:
                    LOGGER.info(f"Using standard flow for direct link: {str(e)}")
                    link = link.split("/download")[0]
            
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
                await editMessage(self._reply_to, "<b>Invalid SourceForge URL</b>")
                self.is_cancelled = True
                self.event.set()
                return
        except DirectDownloadLinkException as e:
            if self._reply_to:
                await editMessage(self._reply_to, str(e))
            else:
                self._reply_to = await sendMessage(self._listener.message, str(e))
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
                
            butt.ibutton("Random Server", f"sourceforge random", position="header")
            butt.ibutton("Cancel", f"sourceforge cancel", position="footer")
            butts = butt.build_menu(3)
            
            msg = f"<b>Select SourceForge Mirror Server</b>\n\n"
            msg += f"<b>Project:</b> <code>{self._project}</code>\n"
            msg += f"<b>File:</b> <code>{self._file_path.split('/')[-1]}</code>\n\n"
            msg += f"<b>Choose a server close to your location for better speed</b>\n\n"
            msg += f"<b>Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
            
            await editMessage(self._reply_to, msg, butts)
        else:
            await editMessage(self._reply_to, "ERROR: No mirror servers available")
            self.is_cancelled = True
            self.event.set()
            return
    
    async def _show_directory_contents(self, content):
        """Display directory contents with navigation buttons"""
        folders = content.get("folders", [])
        files = content.get("files", [])
        
        butt = ButtonMaker()
        
        # Add navigation buttons in header
        header_btns = []
        if self._path_stack:
            header_btns.append(("Back", "sourceforge back"))
        if self._selected_files:
            header_btns.append(("Download Selected", "sourceforge download"))
        
        # Add header buttons
        for text, callback in header_btns:
            butt.ibutton(text, callback, position="header")
        
        # Add folders
        for folder in folders:
            folder_name = folder["name"]
            path = folder["path"]
            path_id = self._get_short_id(path)
            # Limit folder name length if needed
            disp_name = folder_name if len(folder_name) < 25 else folder_name[:22] + "..."
            butt.ibutton(f"📁 {disp_name}", f"sourceforge navigate {path_id}")
        
        # Add files with selection option
        for file in files:
            file_name = file["name"]
            path = file["path"]
            path_id = self._get_short_id(path)
            selected = "✓ " if path in self._selected_files else ""
            # Limit file name length if needed
            disp_name = file_name if len(file_name) < 25 else file_name[:22] + "..."
            butt.ibutton(f"{selected}{disp_name}", f"sourceforge select {path_id}")
            
            # Store file data for later use
            self._file_data[path] = {
                "name": file_name,
                "path": path,
                "size": file.get("size", "Unknown")
            }
        
        # Always add cancel button in footer
        butt.ibutton("Cancel", "sourceforge cancel", position="footer")
        
        # For better organization, use 2 buttons per row
        butts = butt.build_menu(2)
        
        current_path_display = f"/{self._current_path}" if self._current_path else "/"
        
        msg = f"<b>SourceForge Directory Browser</b>\n\n"
        msg += f"<b>Project:</b> <code>{self._project}</code>\n"
        msg += f"<b>Current Path:</b> <code>{current_path_display}</code>\n\n"
        
        if self._selected_files:
            msg += f"<b>Selected Files:</b> {len(self._selected_files)}\n\n"
        
        if not folders and not files:
            msg += "<b>This directory is empty</b>\n"
        else:
            msg += f"<b>Contents:</b> {len(folders)} folders, {len(files)} files\n"
        
        msg += f"\n<b>Timeout:</b> <code>{get_readable_time(self._timeout-(time()-self._time))}</code>"
        
        await editMessage(self._reply_to, msg, butts)
    
    async def navigate_by_id(self, path_id):
        """Navigate to a directory using its ID"""
        path = self._get_path_from_id(path_id)
        if not path:
            await editMessage(self._reply_to, f"<b>Error: Invalid path ID</b>")
            return
        
        await self.navigate(path)
        
    async def select_file_by_id(self, file_id):
        """Select a file using its ID"""
        path = self._get_path_from_id(file_id)
        if not path:
            await editMessage(self._reply_to, f"<b>Error: Invalid file ID</b>")
            return
        
        await self.select_file(path)
    
    async def navigate(self, path):
        """Navigate to a directory"""
        try:
            # Update message to show loading state
            await editMessage(self._reply_to, f"<b>Navigating to directory...</b>")
            
            # Push current path to stack for back navigation
            if self._current_path:
                self._path_stack.append(self._current_path)
            
            self._current_path = path
            
            # Get contents of the new path
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            try:
                content = await get_sf_content(project_url, path)
                await self._show_directory_contents(content)
            except Exception as e:
                LOGGER.error(f"Navigation error: {str(e)}")
                # Try direct URL as fallback for some SourceForge projects
                try:
                    direct_url = f"https://sourceforge.net/projects/{self._project}/files/{path}/"
                    LOGGER.info(f"Trying direct URL: {direct_url}")
                    content = await get_sf_content(direct_url, "")
                    await self._show_directory_contents(content)
                except Exception as e2:
                    await editMessage(self._reply_to, f"<b>Error navigating to directory</b>")
                    self.is_cancelled = True
                    self.event.set()
        except Exception as e:
            await editMessage(self._reply_to, f"<b>Error navigating to directory</b>")
            self.is_cancelled = True
            self.event.set()
    
    async def navigate_back(self):
        """Navigate back to previous directory"""
        try:
            # Update message to show loading state
            await editMessage(self._reply_to, f"<b>Going back to previous directory...</b>")
            
            if self._path_stack:
                self._current_path = self._path_stack.pop()
            else:
                self._current_path = ""
                
            # Get contents of the previous/root path
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            content = await get_sf_content(project_url, self._current_path)
            
            await self._show_directory_contents(content)
        except Exception as e:
            await editMessage(self._reply_to, f"<b>Error navigating back</b>")
            self.is_cancelled = True
            self.event.set()
    
    async def select_file(self, file_path):
        """Select or deselect a file"""
        try:
            # Toggle file selection
            if file_path in self._selected_files:
                self._selected_files.remove(file_path)
            else:
                self._selected_files.append(file_path)
            
            # Update UI to reflect selection
            project_url = f"https://sourceforge.net/projects/{self._project}/files"
            content = await get_sf_content(project_url, self._current_path)
            
            await self._show_directory_contents(content)
        except Exception as e:
            await editMessage(self._reply_to, f"<b>Error selecting file</b>")
            self.is_cancelled = True
            self.event.set()
    
    async def download_selected(self):
        """Process all selected files for download"""
        if not self._selected_files:
            await editMessage(self._reply_to, "<b>No files selected for download</b>")
            return
        
        try:
            await editMessage(self._reply_to, f"<b>Processing {len(self._selected_files)} selected files...</b>")
            
            # If only one file is selected, handle it directly
            if len(self._selected_files) == 1:
                file_path = self._selected_files[0]
                file_url = f"https://sourceforge.net/projects/{self._project}/files/{file_path}"
                
                result = await sourceforge_extract(file_url)
                if isinstance(result, dict) and "servers" in result:
                    self._servers = result["servers"]
                    self._project = result["project"]
                    self._file_path = result["file_path"]
                    await self._show_server_selection()
                else:
                    raise DirectDownloadLinkException("Failed to get server information")
            else:
                # Multiple files selected - use a random server for all
                sample_file = self._selected_files[0]
                
                # Get mirror choices for first file
                mirror_url = f"https://sourceforge.net/settings/mirror_choices?projectname={self._project}&filename={sample_file}"
                LOGGER.info(f"Getting mirror choices from: {mirror_url}")
                
                async with ClientSession() as session:
                    async with session.get(mirror_url) as response:
                        content = await response.text()
                
                soup = BeautifulSoup(content, "html.parser")
                mirror_list = soup.find("ul", {"id": "mirrorList"})
                
                if not mirror_list:
                    raise DirectDownloadLinkException(f"Mirror servers not found")
                
                mirrors = mirror_list.find_all("li")
                servers = []
                
                for mirror in mirrors:
                    servers.append(mirror['id'])
                    
                if servers and servers[0] == "autoselect":
                    servers.pop(0)
                
                # Select a random server from available mirrors
                server = random.choice(servers)
                LOGGER.info(f"Selected random server: {server}")
                
                # Create links for all selected files
                links = []
                for file_path in self._selected_files:
                    file_data = self._file_data.get(file_path, {})
                    file_name = file_data.get("name", "Unknown")
                    direct_link = f"https://{server}.dl.sourceforge.net/project/{self._project}/{file_path}?viasf=1"
                    links.append({"name": file_name, "url": direct_link})
                    LOGGER.info(f"Created link for {file_name}: {direct_link}")
                
                # Set the final link and complete the process
                self._final_link = links
                await editMessage(self._reply_to, f"<b>Server selected:</b> <code>{server}</code>\n<b>Processing download for {len(links)} files...</b>")
                self.event.set() # Ensure the event is set to complete processing
        except Exception as e:
            LOGGER.error(f"Error in download_selected: {str(e)}")
            await editMessage(self._reply_to, f"<b>Error processing download</b>")
            self.is_cancelled = True
            self.event.set()  # Make sure to set the event even on error
    
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
            await editMessage(self._reply_to, f"<b>Error processing server</b>")
            self.is_cancelled = True
            self.event.set()
            
    async def random_server(self):
        """Select a random mirror server"""
        server = random.choice(self._servers)
        await self.start(server)

## Big thanks to @aenulrofik for this awesome feature ##
## Please don't remove the credits — respect the creator! ##