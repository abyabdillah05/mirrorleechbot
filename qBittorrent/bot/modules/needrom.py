import re
import os
import asyncio
import time
from aiofiles.os import path as aiopath
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from bot import bot, LOGGER
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, deleteMessage
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.links_utils import is_url
from bot.helper.ext_utils.status_utils import get_readable_time, get_readable_file_size
from bot.helper.ext_utils.exceptions import NeedromException
from bot.helper.mirror_utils.download_utils.needrom_dwext import NeedromBypass
from bot.helper.mirror_utils.gdrive_utils.helper import GoogleDriveHelper
from bot.helper.mirror_utils.status_utils.needrom_status import NeedromDownloadStatus
from bot.helper.telegram_helper.button_build import ButtonMaker

from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.modules.mirror_leech import Mirror as MirrorLeechListener

class NeedromDL:
    
    def __init__(self, bot, message, needrom_link=None, isLeech=False, isZip=False, extract=False,
                 pswd=None, tag=None, compress=None, extract_split=False, select=False, seed=False):
        self.bot = bot
        self.message = message
        self.needrom_link = needrom_link
        self.isLeech = isLeech
        self.isZip = isZip
        self.extract = extract
        self.pswd = pswd
        self.tag = tag
        self.compress = compress
        self.extract_split = extract_split
        self.select = select
        self.seed = seed
        self.user_id = message.from_user.id
        self.user_name = message.from_user.mention
        self._bypass = NeedromBypass()
        self._status = None
        self._error = None
        self._start_time = time.time()
        self._last_update_time = time.time()
        self._canceled = False
        self._progress = None
        self._processed_bytes = 0
        self._size = 0
        self._listener = None
        self._filename = None
        
    @new_task
    async def process(self):
        LOGGER.info(f"Processing Needrom link: {self.needrom_link}")
        
        try:
            self._progress = await sendMessage(self.message, 
                                          "<b>🔍 Analyzing Needrom link and bypassing protection...</b>")
            
            result = await self._bypass.extract_download_link(self.needrom_link)
            direct_link = result['direct_link']
            file_info = result['file_info']
            
            if not direct_link:
                raise NeedromException("Failed to extract direct download link")
            
            # Determine filename from file info or direct link
            self._filename = file_info.get('filename', os.path.basename(urlparse(direct_link).path))
            if not any(self._filename.endswith(ext) for ext in ['.zip', '.rar', '.7z']):
                ext = file_info.get('extension', 'zip').lower()
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                self._filename += ext
            
            size_text = f"<b>Size: </b>{file_info.get('filesize', 'Unknown')}"
            
            # Update progress message
            await editMessage(self._progress, 
                             f"<b>📥 Preparing to download from Needrom</b>\n\n"
                             f"<b>File: </b><code>{self._filename}</code>\n"
                             f"{size_text}\n\n"
                             f"<b>⏳ Initializing download...</b>")
            
            # Create listener for the download
            self._listener = MirrorLeechListener(
                message=self.message,
                isZip=self.isZip,
                extract=self.extract,
                isLeech=self.isLeech,
                pswd=self.pswd,
                tag=self.tag,
                compress=self.compress
            )
            
            path = f"{self._listener.dir}/{self._filename}"
            
            # Create status tracker
            self._status = NeedromDownloadStatus(self._filename, self._start_time, self)
            
            # Start the download
            await editMessage(self._progress, 
                             f"<b>📥 Downloading from Needrom</b>\n\n"
                             f"<b>File: </b><code>{self._filename}</code>\n"
                             f"{size_text}\n\n"
                             f"<b>⏱️ Starting download...</b>")
            
            self._status.set_state("Downloading")
            success = await self._bypass.download_file(
                direct_link, 
                path, 
                progress_callback=self._update_progress
            )
            
            if not success:
                raise NeedromException("Download failed")
            
            await self._bypass.close()
            
            # Clean up progress message
            if self._progress:
                await deleteMessage(self._progress)
                self._progress = None
            
            # Handle download completion
            self._status.set_state("Completed")
            if self.isLeech:
                LOGGER.info(f"Leeching file: {self._filename}")
                await self._listener.onDownloadComplete()
            else:
                LOGGER.info(f"Mirroring file: {self._filename}")
                await self._listener.onDownloadComplete()
            
        except NeedromException as e:
            # Handle Needrom-specific errors
            self._error = str(e)
            LOGGER.error(f"Needrom error: {str(e)}")
            
            if self._progress:
                await editMessage(self._progress, f"<b>❌ Needrom Download Failed:</b> {str(e)}")
                
            await self._bypass.close()
            
            # Clean up if there's a listener
            if self._listener:
                await self._listener.onDownloadError(str(e))
                
            return
            
        except Exception as e:
            # Handle general errors
            self._error = str(e)
            LOGGER.error(f"Error during Needrom processing: {str(e)}")
            
            if self._progress:
                await editMessage(self._progress, f"<b>❌ Error:</b> {str(e)}")
                
            await self._bypass.close()
            
            # Clean up if there's a listener
            if self._listener:
                await self._listener.onDownloadError(str(e))
                
            return
    
    def _update_progress(self, downloaded_bytes, total_bytes, progress):
        """Update progress information for status tracking"""
        self._processed_bytes = downloaded_bytes
        self._size = total_bytes
        
        # Update progress message if sufficient time has passed
        current_time = time.time()
        if current_time - self._last_update_time > 2 and self._progress and not self._canceled:
            self._last_update_time = current_time
            
            # Schedule progress update without awaiting
            asyncio.create_task(self._update_progress_message(downloaded_bytes, total_bytes, progress))
    
    async def _update_progress_message(self, downloaded_bytes, total_bytes, progress):
        """Update the progress message with current download status"""
        if not self._progress or self._canceled:
            return
            
        try:
            percentage = round(progress * 100, 2)
            
            # Calculate speed
            elapsed_time = time.time() - self._start_time
            speed = downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
            
            # Calculate ETA
            eta = (total_bytes - downloaded_bytes) / speed if speed > 0 and total_bytes > downloaded_bytes else 0
            
            await editMessage(self._progress, 
                            f"<b>📥 Downloading from Needrom</b>\n\n"
                            f"<b>File: </b><code>{self._filename}</code>\n"
                            f"<b>Size: </b>{get_readable_file_size(total_bytes)}\n\n"
                            f"<b>Progress: </b>{percentage}%\n"
                            f"<b>Downloaded: </b>{get_readable_file_size(downloaded_bytes)} / {get_readable_file_size(total_bytes)}\n"
                            f"<b>Speed: </b>{get_readable_file_size(speed)}/s\n"
                            f"<b>ETA: </b>{get_readable_time(eta)}")
        except Exception as e:
            LOGGER.error(f"Error updating progress message: {str(e)}")
        
    async def cancel_download(self):
        """Cancel an ongoing download"""
        self._canceled = True
        self._status.set_state("Canceled")
        
        if self._progress:
            await editMessage(self._progress, "<b>❌ Download has been canceled!</b>")
        
        await self._bypass.close()

        # Clean up partial file
        if hasattr(self, '_filename') and self._listener:
            path = f"{self._listener.dir}/{self._filename}"
            if path and await aiopath.exists(path):
                try:
                    os.remove(path)
                    LOGGER.info(f"Removed partial download: {path}")
                except:
                    pass
        
        # Notify listener about cancellation
        if self._listener:
            await self._listener.onDownloadError("Download canceled by user")
        
        return
    
    @property
    def processed_bytes(self):
        return self._processed_bytes
    
    @property
    def size(self):
        return self._size
    
    @property
    def status(self):
        return self._status
    
    @property
    def name(self):
        return self._filename or "Unknown"
    
    @property
    def speed(self):
        if not self._status:
            return 0
        
        elapsed_time = time.time() - self._start_time
        if elapsed_time == 0:
            return 0
        
        return self._processed_bytes / elapsed_time
    
    @property
    def eta(self):
        if not self._status or self._size == 0 or self._processed_bytes == 0:
            return 0
        
        speed = self.speed
        if speed == 0:
            return 0
        
        remaining_bytes = self._size - self._processed_bytes
        return remaining_bytes / speed


@new_task
async def handle_needrom_link(client, message):
    """Handle /needrom command"""
    args = message.text.split(" ", maxsplit=1)
    
    if len(args) < 2:
        await show_help(message)
        return
    
    url = args[1].strip()
    
    if not is_url(url) or "needrom.com" not in url:
        await sendMessage(message, "<b>❌ Invalid Needrom URL!</b> Please provide a valid Needrom download link.")
        return
    
    # Process command parameters
    cmd_args = url.split(" ")
    url = cmd_args[0]
    cmd_args = cmd_args[1:] if len(cmd_args) > 1 else []
    
    # Set defaults
    isLeech = False  
    isZip = False    
    extract = False
    
    # Parse args
    for arg in cmd_args:
        arg = arg.strip().lower()
        if arg == 'zip':
            isZip = True
        elif arg == 'extract':
            extract = True
        elif arg == 'leech':
            isLeech = True
    
    needrom_dl = NeedromDL(
        bot, 
        message, 
        needrom_link=url, 
        isLeech=isLeech,
        isZip=isZip,
        extract=extract
    )
    
    await needrom_dl.process()


@new_task
async def handle_needrom_link_leech(client, message):
    """Handle /leechneedrom command"""
    args = message.text.split(" ", maxsplit=1)
    
    if len(args) < 2:
        await show_help(message)
        return
    
    url = args[1].strip()
    
    if not is_url(url) or "needrom.com" not in url:
        await sendMessage(message, "<b>❌ Invalid Needrom URL!</b> Please provide a valid Needrom download link.")
        return
    
    # Process command parameters
    cmd_args = url.split(" ")
    url = cmd_args[0]
    cmd_args = cmd_args[1:] if len(cmd_args) > 1 else []
    
    # Set defaults
    isZip = False    
    extract = False
    
    # Parse args
    for arg in cmd_args:
        arg = arg.strip().lower()
        if arg == 'zip':
            isZip = True
        elif arg == 'extract':
            extract = True
    
    needrom_dl = NeedromDL(
        bot, 
        message, 
        needrom_link=url, 
        isLeech=True,
        isZip=isZip,
        extract=extract
    )
    
    await needrom_dl.process()


async def show_help(message):
    """Show help message for Needrom commands"""
    help_text = """
<b>📱 Needrom Downloader Help</b>

<b>Commands:</b>
<code>/needrom [URL] [options]</code> - Download and mirror file from Needrom
<code>/leechneedrom [URL] [options]</code> - Download and leech file from Needrom

<b>Options:</b>
<code>zip</code> - Create a zip archive of the downloaded file
<code>extract</code> - Extract the downloaded archive

<b>Examples:</b>
<code>/needrom https://www.needrom.com/download/example-rom</code>
<code>/needrom https://www.needrom.com/download/example-rom zip</code>
<code>/leechneedrom https://www.needrom.com/download/example-rom extract</code>
"""
    await sendMessage(message, help_text)


# Register the command handlers
bot.add_handler(
    MessageHandler(
        handle_needrom_link,
        filters=CustomFilters.authorized & 
                filters.command(BotCommands.NeedromCommand)
    )
)

#bot.add_handler(
#    MessageHandler(
#        handle_needrom_link_leech,
#        filters=CustomFilters.authorized & 
#                filters.command(BotCommands.LeechNeedromCommand)
#    )
#)