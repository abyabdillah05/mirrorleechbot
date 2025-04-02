from bot.helper.ext_utils.status_utils import (get_readable_time,
                                               get_readable_file_size,
                                               MirrorStatus,)
from bot.helper.ext_utils.fs_utils import get_path_size

class NeedromDownloadStatus:
    def __init__(self, name, starttime, obj):
        self.__name = name
        self.__starttime = starttime
        self.__obj = obj
        self.__state = "Downloading"

    def progress(self):
        """Return progress as a percentage string"""
        if self.__obj.size:
            return f"{round(self.__obj.processed_bytes / self.__obj.size * 100, 2)}%"
        return '0%'

    def speed(self):
        return get_readable_file_size(self.__obj.speed)

    def name(self):
        return self.__name

    def size(self):
        return get_readable_file_size(self.__obj.size)

    def eta(self):
        return get_readable_time(self.__obj.eta)

    def status(self):
        return MirrorStatus.STATUS_DOWNLOADING

    def processed_bytes(self):
        return get_readable_file_size(self.__obj.processed_bytes)

    def download(self):
        return self.__obj

    def gid(self):
        return self.__name

    def download_speed(self):
        return self.speed()
    
    def set_state(self, state):
        self.__state = state
    
    def get_state(self):
        return self.__state