from time import time
from html import escape
from enum import Enum
from psutil import (
    cpu_percent, 
    disk_usage, 
    net_io_counters,
    virtual_memory
)
from typing import Dict, List, Tuple, Optional, Union

from bot import task_dict, task_dict_lock, botStartTime, config_dict, OWNER_ID, SUDO_USERS
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker


SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]

class MirrorStatus:
    STATUS_DOWNLOADING = "Download.."
    STATUS_UPLOADING = "Upload.."
    STATUS_QUEUEDL = "Antrian.."
    STATUS_QUEUEUP = "Antrian.."
    STATUS_PAUSED = "Berhenti.."
    STATUS_ARCHIVING = "Arsip.."
    STATUS_EXTRACTING = "Extract.."
    STATUS_CLONING = "Cloning.."
    STATUS_SEEDING = "Seeding.."
    STATUS_SPLITTING = "Split.."
    STATUS_CHECKING = "Mengecek.."
    STATUS_SAMVID = "Sample Video"
    STATUS_DUMPING = "Dumping.."
    STATUS_VIDEDIT = "Video Editor.."

STATUS_VALUES = [
    ("ALL", "All"),
    ("DL", MirrorStatus.STATUS_DOWNLOADING),
    ("UP", MirrorStatus.STATUS_UPLOADING),
    ("QD", MirrorStatus.STATUS_QUEUEDL),
    ("QU", MirrorStatus.STATUS_QUEUEUP),
    ("AR", MirrorStatus.STATUS_ARCHIVING),
    ("EX", MirrorStatus.STATUS_EXTRACTING),
    ("CL", MirrorStatus.STATUS_CLONING),
    ("SD", MirrorStatus.STATUS_SEEDING),
    ("SV", MirrorStatus.STATUS_SAMVID),
    ("DM", MirrorStatus.STATUS_DUMPING),
    ("VE", MirrorStatus.STATUS_VIDEDIT),
]

class StatusType:
    """Defines different status context types"""
    PRIVATE = "private"  # Individual user statuses
    GROUP = "group"      # Group-specific statuses 
    GLOBAL = "global"    # All tasks across contexts

class StatusPermission:
    """Handles permission checks for status operations"""
    
    @staticmethod
    def is_owner(user_id: int) -> bool:
        """Check if user is the bot owner"""
        return user_id == OWNER_ID
    
    @staticmethod
    def is_sudo(user_id: int) -> bool:
        """Check if user has sudo privileges"""
        return user_id in SUDO_USERS or StatusPermission.is_owner(user_id)
    
    @staticmethod
    def can_access_status(user_id: int, status_owner_id: int, status_type: str, 
                          status_chat_id: int, current_chat_id: int) -> bool:
        """Determine if a user can access/modify a status
        
        Args:
            user_id: ID of user trying to access status
            status_owner_id: ID of user who owns the status
            status_type: Type of status (private/group/global)
            status_chat_id: Chat ID where status was created
            current_chat_id: Current chat ID where access is attempted
        
        Returns:
            bool: True if user can access, False otherwise
        """
        # Owner can access everything
        if StatusPermission.is_owner(user_id):
            return True
            
        # Sudo users can access group status and their own status
        if StatusPermission.is_sudo(user_id):
            if status_type == StatusType.PRIVATE:
                return user_id == status_owner_id
            return True
            
        # Regular users can only access their own status or group status in same group
        if status_type == StatusType.PRIVATE:
            return user_id == status_owner_id
        elif status_type == StatusType.GROUP:
            return status_chat_id == current_chat_id
            
        # Global status is owner only
        return False

    @staticmethod
    def can_use_button(user_id: int, button_type: str, status_owner_id: int, status_type: str) -> bool:
        """Check if user can use a specific button type
        
        Args:
            user_id: ID of user trying to use button
            button_type: Type of button (refresh, close, etc)
            status_owner_id: ID of user who owns the status
            status_type: Type of status (private/group/global)
            
        Returns:
            bool: True if user can use button, False otherwise
        """
        # For navigation, pagination, and viewing buttons
        if button_type in ['pre', 'nex', 'ref', 'info', 'ov', 'st', 'ps']:
            # Anyone with access to the status can use these
            return True
            
        # For destructive actions like close
        elif button_type == 'close':
            # Owner can close any status
            if StatusPermission.is_owner(user_id):
                return True
                
            # For private status, only the owner can close
            if status_type == StatusType.PRIVATE:
                return user_id == status_owner_id
                
            # For group status, sudo users can close
            if status_type == StatusType.GROUP:
                return StatusPermission.is_sudo(user_id)
                
            # Global status is owner-only
            return False
            
        # Default: deny access
        return False

class StatusButtonManager:
    """Generates appropriate buttons based on context"""
    
    @staticmethod
    def generate_buttons(status_type: str, sid: int, cmd_user_id: int, 
                        page_no: int, pages: int, tasks_count: int, 
                        status_filter: str = "All") -> ButtonMaker:
        """Generate appropriate buttons based on context and task count
        
        Args:
            status_type: Type of status (private/group/global)
            sid: Status ID (usually user_id or chat_id)
            cmd_user_id: User ID who initiated the command
            page_no: Current page number
            pages: Total number of pages
            tasks_count: Number of tasks
            status_filter: Current status filter
            
        Returns:
            ButtonMaker: Button object with appropriate layout
        """
        buttons = ButtonMaker()
        
        # External link button always in header
        buttons.ubutton("Join", "https://t.me/pikachukocak3", position="header")
        
        # For pages with many tasks - show pagination controls
        if tasks_count > config_dict["STATUS_LIMIT"]:
            buttons.ibutton("⏪ Prev", f"status {sid} pre")
            buttons.ibutton("🔄 Refresh", f"status {sid} ref", position="header")
            buttons.ibutton("⏩ Next", f"status {sid} nex")
            
            # Page step buttons (footer)
            if tasks_count > 30:
                for i in [1, 2, 4, 6, 8, 10, 15, 20]:
                    buttons.ibutton(i, f"status {sid} ps {i}", position="footer")
        else:
            # For pages with few tasks - just refresh
            if tasks_count > 0:
                buttons.ibutton("🔄 Refresh", f"status {sid} ref", position="header")
        
        # Helper buttons
        if status_type != StatusType.GLOBAL:
            buttons.ibutton("Help", f"status {sid} help", position="header")
            buttons.ibutton("Info", f"status {sid} info", position="header")
            buttons.ibutton("Overview", f"status {sid} ov", position="header")
        
        # Status filter buttons - only if multiple status types exist or more than 20 tasks
        if status_filter != "All" or tasks_count > 20:
            for label, status_value in STATUS_VALUES:
                if status_value != status_filter:
                    buttons.ibutton(label, f"status {sid} st {status_value}")
        
        # No tasks - show special message 
        if tasks_count == 0 and status_filter == "All":
            buttons.ibutton("Not Exist Status", f"status {sid} null")
        
        # Close button always at bottom
        buttons.ibutton("🔽 Tutup", f"status {sid} close", position="footer")
        
        # Global status gets more specialized buttons if owned by owner
        if status_type == StatusType.GLOBAL and StatusPermission.is_owner(cmd_user_id):
            buttons.ibutton("📊 Stats", f"status {sid} stats", position="header")
            buttons.ibutton("🗑️ Clean All", f"status {sid} cleanall", position="footer")
        
        return buttons

class StatusContext:
    """Determines the appropriate status context"""
    
    @staticmethod
    def determine_context(message, cmd_args=None) -> Tuple[str, int, int]:
        """Determine the appropriate status context based on message and arguments
        
        Args:
            message: The message object
            cmd_args: Command arguments if any
            
        Returns:
            Tuple[str, int, int]: (status_type, user_id/chat_id, cmd_user_id)
        """
        cmd_user_id = message.from_user.id
        
        # If command has arguments
        if cmd_args:
            # Check for specific formats
            if cmd_args == "me":
                # User requesting their own status privately
                return StatusType.PRIVATE, cmd_user_id, cmd_user_id
            elif cmd_args == "all" and StatusPermission.is_owner(cmd_user_id):
                # Owner requesting global status
                return StatusType.GLOBAL, 0, cmd_user_id
            elif cmd_args.isdigit():
                # User requesting specific user's status (sudo/owner only)
                target_id = int(cmd_args)
                if StatusPermission.is_sudo(cmd_user_id):
                    return StatusType.PRIVATE, target_id, cmd_user_id
        
        # Default behavior based on chat type
        is_private = message.chat.type == "private"
        if is_private:
            return StatusType.PRIVATE, cmd_user_id, cmd_user_id
        else:
            return StatusType.GROUP, message.chat.id, cmd_user_id

class StatusRequest:
    """Represents a status request with context information"""
    
    def __init__(self, user_id: int, chat_id: int, status_type: str, 
                cmd_user_id: int, page_no: int = 1, status_filter: str = "All", 
                page_step: int = 1):
        """Initialize a status request with context information
        
        Args:
            user_id: User ID requesting the status
            chat_id: Chat ID where status is being requested
            status_type: Type of status (private/group/global)
            cmd_user_id: User ID who initiated the command
            page_no: Current page number
            status_filter: Current status filter
            page_step: Number of items to show per page
        """
        self.user_id = user_id
        self.chat_id = chat_id
        self.status_type = status_type
        self.cmd_user_id = cmd_user_id
        self.page_no = page_no
        self.status_filter = status_filter
        self.page_step = page_step
        
    @property
    def sid(self) -> int:
        """Get the status ID based on context"""
        if self.status_type == StatusType.PRIVATE:
            return self.user_id
        elif self.status_type == StatusType.GROUP:
            return self.chat_id
        else:  # Global
            return 0
            
    def get_filtered_tasks(self) -> List:
        """Get tasks filtered according to context and filter"""
        if self.status_type == StatusType.PRIVATE:
            # For private status, only show user's own tasks
            if self.status_filter == "All":
                return [tk for tk in task_dict.values() if tk.listener.user_id == self.user_id]
            else:
                return [
                    tk for tk in task_dict.values() 
                    if tk.status() == self.status_filter and tk.listener.user_id == self.user_id
                ]
        elif self.status_type == StatusType.GROUP:
            # For group status, show tasks from that group
            if self.status_filter == "All":
                return [tk for tk in task_dict.values() if tk.listener.message.chat.id == self.chat_id]
            else:
                return [
                    tk for tk in task_dict.values()
                    if tk.status() == self.status_filter and tk.listener.message.chat.id == self.chat_id
                ]
        else:
            # Global status shows all tasks
            if self.status_filter == "All":
                return list(task_dict.values())
            else:
                return [tk for tk in task_dict.values() if tk.status() == self.status_filter]

# Original utility functions, kept for compatibility

async def getTaskByGid(gid: str):
    async with task_dict_lock:
        return next((tk for tk in task_dict.values() if tk.gid() == gid), None)

async def getAllTasks(req_status: str):
    async with task_dict_lock:
        if req_status == "all":
            return list(task_dict.values())
        return [tk for tk in task_dict.values() if tk.status() == req_status]

def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes is None:
        return "0B"
    
    is_negative = size_in_bytes < 0
    size_in_bytes = abs(size_in_bytes)

    index = 0
    while size_in_bytes >= 1024 and index < len(SIZE_UNITS) - 1:
        size_in_bytes /= 1024
        index += 1

    formatted_size = f"{size_in_bytes:.2f}{SIZE_UNITS[index]}"
    return f"-{formatted_size}" if is_negative else formatted_size

def get_readable_time(seconds: int):
    periods = [("h", 86400), ("j", 3600), ("m", 60), ("d", 1)]
    result = ""
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f"{int(period_value)}{period_name}"
    return result

def speed_string_to_bytes(size_text: str):
    size = 0
    size_text = size_text.lower()
    if "k" in size_text:
        size += float(size_text.split("k")[0]) * 1024
    elif "m" in size_text:
        size += float(size_text.split("m")[0]) * 1048576
    elif "g" in size_text:
        size += float(size_text.split("g")[0]) * 1073741824
    elif "t" in size_text:
        size += float(size_text.split("t")[0]) * 1099511627776
    elif "b" in size_text:
        size += float(size_text.split("b")[0])
    return size

def get_progress_bar_string(pct):
    pct = float(pct.strip("%"))
    p = min(max(pct, 0), 100)
    cFull = int(p // 8)
    p_str = "■" * cFull
    p_str += "□" * (12 - cFull)
    return f"[{p_str}]"

# New formatting functions for different status contexts

def format_private_status_message(tasks, user_id, username, first_name, page_no, status_filter, page_step):
    """Format status message for private context"""
    msg = ""
    
    # Header with user info
    msg += "╔═══ PRIVATE STATUS ═══╗\n"
    msg += f"╠ 👤 User: {first_name} (@{username})\n"
    msg += f"╠ 🆔 ID: {user_id}\n"
    msg += "╚════════════════════════════╝\n\n"
    
    # No tasks message
    if not tasks:
        msg += "No active tasks in your private list\n\n"
        msg += "Start downloading to see tasks here\n\n"
    else:
        # Pagination info
        STATUS_LIMIT = config_dict["STATUS_LIMIT"]
        tasks_no = len(tasks)
        pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
        
        msg += f"📋 Page {page_no}/{pages} | Tasks: {tasks_no}\n"
        msg += f"🔍 Filter: {status_filter}\n\n"
        
        # Show tasks for current page
        start_idx = (page_no - 1) * STATUS_LIMIT
        for task in tasks[start_idx:start_idx + STATUS_LIMIT]:
            msg += format_task_details(task)
    
    # System stats footer
    msg += format_system_stats()
    
    return msg

def format_group_status_message(tasks, chat_id, chat_title, page_no, status_filter, page_step):
    """Format status message for group context"""
    msg = ""
    
    # Header with group info
    msg += "╔═══ GROUP STATUS ═══╗\n"
    msg += f"╠ 👥 Group: {chat_title}\n"
    msg += f"╠ 🆔 ID: {chat_id}\n"
    msg += "╚════════════════════════════╝\n\n"
    
    # No tasks message
    if not tasks:
        msg += "No active tasks in this group\n\n"
        msg += "Start downloading in this group to see tasks here\n\n"
    else:
        # Pagination info
        STATUS_LIMIT = config_dict["STATUS_LIMIT"]
        tasks_no = len(tasks)
        pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
        
        msg += f"📋 Page {page_no}/{pages} | Tasks: {tasks_no}\n"
        msg += f"🔍 Filter: {status_filter}\n\n"
        
        # Show tasks for current page
        start_idx = (page_no - 1) * STATUS_LIMIT
        for task in tasks[start_idx:start_idx + STATUS_LIMIT]:
            msg += format_task_details(task, show_user=True)
    
    # System stats footer
    msg += format_system_stats()
    
    return msg

def format_global_status_message(tasks, page_no, status_filter, page_step):
    """Format status message for global context, showing one task per page"""
    msg = ""
    
    # Header with global info
    msg += "╔═══ GLOBAL STATUS ═══╗\n"
    msg += "╠ 🌐 Showing all tasks across all contexts\n"
    msg += "╠ 👑 Owner access only\n"
    msg += "╚════════════════════════════╝\n\n"
    
    # No tasks message
    if not tasks:
        msg += "No active tasks in any context\n\n"
    else:
        # When showing global status, only show one task per page with detailed info
        tasks_no = len(tasks)
        
        msg += f"📋 Page {page_no}/{tasks_no} | Total Tasks: {tasks_no}\n"
        msg += f"🔍 Filter: {status_filter}\n\n"
        
        if 1 <= page_no <= tasks_no:
            task = tasks[page_no - 1]
            
            # Show user info for this task
            msg += f"👤 User: {task.listener.user.first_name}\n"
            msg += f"🆔 User ID: {task.listener.user_id}\n\n"
            
            # Show detailed task info
            msg += format_task_details(task, detailed=True)
            
            # Additional details for global view
            msg += "\nDetailed Info:\n"
            chat_type = task.listener.message.chat.type
            chat_title = getattr(task.listener.message.chat, 'title', 'Private Chat')
            
            msg += f"• Origin: {chat_title} ({chat_type})\n"
            msg += f"• Started: {time_to_formatted_string(task.listener.extra_details['startTime'])}\n"
            msg += f"• Original Filename: {task.listener.name}\n"
            
            # Add target info if available
            if hasattr(task.listener, 'rclone_path'):
                msg += f"• Target: {task.listener.rclone_path}\n"
            elif hasattr(task.listener, 'upload_details'):
                msg += f"• Target: {task.listener.upload_details.get('drive_id', 'Unknown')}\n"
    
    # System stats footer
    msg += format_system_stats()
    
    return msg

def format_task_details(task, show_user=False, detailed=False):
    """Format details for a single task"""
    msg = ""
    
    # Task header and name
    msg += "╔═══════════════════════════╗\n"
    if task.listener.isPrivateChat:
        msg += "╠[ • Nama  : Private Task\n"
    else:
        msg += f"╠[ • Nama  : {escape(task.name())[:30]}\n"
        
    # Show view type
    view_type = "Private" if task.listener.message.chat.type == "private" else "Group"
    msg += f"╠[ • View Type  : {view_type}\n"
    msg += "╚═══════════════════════════╝\n"
    
    # Task details
    msg += "╔═══════════════════════════╗\n"
    
    # Status with emoji
    status = task.status()
    emoji = get_status_emoji(status)
    msg += f"╠[ • Status    : {emoji} {status}\n"
    
    # Progress
    if status not in [
        MirrorStatus.STATUS_SPLITTING,
        MirrorStatus.STATUS_SEEDING,
        MirrorStatus.STATUS_SAMVID,
        MirrorStatus.STATUS_DUMPING,
        MirrorStatus.STATUS_VIDEDIT,
    ]:
        msg += f"╠[ • Progress  : {get_progress_bar_string(task.progress())} {task.progress()}\n"
    
    # Show user if requested (for group view)
    if show_user:
        msg += f"╠[ • User      : @{task.listener.user.username} ({task.listener.user_id})\n"
    
    # Time elapsed
    time_elapsed = get_readable_time(time() - task.listener.extra_details['startTime'])
    msg += f"╠[ • Time      : {time_elapsed}\n"
    
    # Size
    msg += f"╠[ • Size      : {task.size()}\n"
    
    # Additional details by status type
    if status not in [
        MirrorStatus.STATUS_SPLITTING,
        MirrorStatus.STATUS_SEEDING,
        MirrorStatus.STATUS_SAMVID,
        MirrorStatus.STATUS_DUMPING,
        MirrorStatus.STATUS_VIDEDIT,
    ]:
        msg += f"╠[ • Diproses  : {task.processed_bytes()}\n"
        msg += f"╠[ • Estimasi  : {task.eta()}\n"
        msg += f"╠[ • Kecepatan : {task.speed()}\n"
        
        # Seeders/leechers for torrents
        if hasattr(task, 'seeders_num'):
            try:
                msg += f"╠[ • Seeders   : {task.seeders_num()}\n"
                msg += f"╠[ • Leechers  : {task.leechers_num()}\n"
            except:
                pass
    elif status == MirrorStatus.STATUS_SEEDING:
        msg += f"╠[ • Ratio     : {task.ratio()}\n"
        msg += f"╠[ • Waktu     : {task.seeding_time()}\n"
        msg += f"╠[ • Diupload  : {task.uploaded_bytes()}\n"
        msg += f"╠[ • Kecepatan : {task.seed_speed()}\n"
    
    # Engine info
    engine = ""
    ddl = task.listener
    if getattr(ddl, 'isGofile', False):
        engine = "GofileAPI"
    elif getattr(ddl, 'isBuzzheavier', False):
        engine = "BuzzheavierAPI"
    elif getattr(ddl, 'isPixeldrain', False):
        engine = "PixeldrainAPI"
    else:
        engine = f"{getattr(task, 'engine', 'Unknown')}"
    msg += f"╠[ • Engine    : {engine}\n"
    
    # Cancel command
    msg += f"╠[ • Cancel    : /{BotCommands.CancelTaskCommand[0]}_{task.gid()}\n"
    msg += "╚═══════════════════════════╝\n\n"
    
    return msg

def format_system_stats():
    """Format system stats footer"""
    msg = "Sistem Stats:\n"
    msg += f"CPU: {cpu_percent()}% | RAM: {virtual_memory().percent}% / {get_readable_file_size(virtual_memory().total)}\n"
    msg += f"FREE: {get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)} | UPT: {get_readable_time(time() - botStartTime)}\n"
    
    return msg

def time_to_formatted_string(timestamp):
    """Convert timestamp to readable date format"""
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_status_emoji(status):
    """Get emoji for status type"""
    emoji_map = {
        MirrorStatus.STATUS_DOWNLOADING: "🟢",
        MirrorStatus.STATUS_UPLOADING: "🔵",
        MirrorStatus.STATUS_QUEUEDL: "🟡",
        MirrorStatus.STATUS_QUEUEUP: "🟡",
        MirrorStatus.STATUS_PAUSED: "⚫",
        MirrorStatus.STATUS_ARCHIVING: "🟠",
        MirrorStatus.STATUS_EXTRACTING: "🟣",
        MirrorStatus.STATUS_CLONING: "⚪",
        MirrorStatus.STATUS_SEEDING: "🟤",
        MirrorStatus.STATUS_SPLITTING: "⚪",
        MirrorStatus.STATUS_CHECKING: "🔶",
        MirrorStatus.STATUS_SAMVID: "🔷",
        MirrorStatus.STATUS_DUMPING: "⚪",
        MirrorStatus.STATUS_VIDEDIT: "🔷",
    }
    return emoji_map.get(status, "⚪")

async def get_readable_message(sid, is_user, page_no=1, status_filter="All", page_step=1):
    """Legacy function for compatibility, now using the new system underneath"""
    status_type = StatusType.PRIVATE if is_user else StatusType.GROUP
    
    async with task_dict_lock:
        if status_filter == "All":
            tasks = (
                [tk for tk in task_dict.values() if tk.listener.user_id == sid]
                if is_user
                else list(task_dict.values())
            )
        elif is_user:
            tasks = [
                tk for tk in task_dict.values() 
                if tk.status() == status_filter and tk.listener.user_id == sid
            ]
        else:
            tasks = [tk for tk in task_dict.values() if tk.status() == status_filter]
        
        if len(tasks) == 0 and status_filter == "All":
            return None, None
            
        STATUS_LIMIT = config_dict["STATUS_LIMIT"]
        tasks_no = len(tasks)
        pages = (max(tasks_no, 1) + STATUS_LIMIT - 1) // STATUS_LIMIT
        
        if page_no > pages:
            page_no = (page_no - 1) % pages + 1
        elif page_no < 1:
            page_no = pages - (abs(page_no) % pages)
            
        if is_user:
            # Format as private status
            user = next((tk.listener.user for tk in tasks), None) if tasks else None
            username = getattr(user, 'username', 'Unknown')
            first_name = getattr(user, 'first_name', 'User')
            msg = format_private_status_message(tasks, sid, username, first_name, page_no, status_filter, page_step)
        else:
            # Format as group status
            chat_title = getattr(next((tk.listener.message.chat for tk in tasks), None) if tasks else None, 'title', 'Group')
            msg = format_group_status_message(tasks, sid, chat_title, page_no, status_filter, page_step)
        
        # Generate buttons
        buttons = StatusButtonManager.generate_buttons(
            status_type, sid, sid, page_no, pages, tasks_no, status_filter
        )
        
        return msg, buttons.build_menu(3)