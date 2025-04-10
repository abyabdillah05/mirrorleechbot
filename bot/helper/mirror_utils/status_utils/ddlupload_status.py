from bot.helper.ext_utils.status_utils import (
    MirrorStatus
)
from bot.helper.ext_utils.common_utils import (get_readable_file_size,
                                            get_readable_time)
from time import time


class DdlUploadStatus:
    def __init__(self, listener, obj, size, gid):
        self._obj = obj
        self._size = size
        self._gid = gid
        self.listener = listener
        self.start_time = 0

    def processed_bytes(self):
        return get_readable_file_size(self._obj.processed_bytes)

    def size(self):
        return get_readable_file_size(self._size)

    def status(self):
        return MirrorStatus.STATUS_UPLOADING

    def name(self):
        return self.listener.name

    def progress(self):
        try:
            progress_raw = self._obj.processed_bytes / self._size * 100
        except:
            progress_raw = 0
        return f"{round(progress_raw, 2)}%"

    def speed(self):
        return f"{get_readable_file_size(self._obj.speed)}/s"

    def eta(self):
        try:
            seconds = (self._size - self._obj.processed_bytes) / self._obj.speed
            return get_readable_time(seconds)
        except:
            return "-"
    
    def elapsed_time(self):
        return get_readable_time(time() - self.start_time)

    def gid(self):
        return self._gid

    def task(self):
        return self._obj
