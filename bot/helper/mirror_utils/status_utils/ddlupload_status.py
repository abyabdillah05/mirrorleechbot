from bot.helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)
from time import time


class DdlUploadStatus:
    def __init__(self, listener, obj, size, gid):
        self._obj = obj
        self._size = size
        self._gid = gid
        self.listener = listener
        self.start_time = 0
        self._service_name = self._get_service_name()
        self._last_uploaded = 0
        self._speed_samples = []
        self._last_sample_time = 0

    def _get_service_name(self):
        if hasattr(self._obj, 'isBuzzheavier') and self._obj.isBuzzheavier:
            return "BuzzHeavier"
        elif hasattr(self._obj, 'isPixeldrain') and self._obj.isPixeldrain:
            return "Pixeldrain"
        elif hasattr(self._obj, 'isGofile') and self._obj.isGofile:
            return "GoFile"
        else:
            return "DDL"

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
            return f"{round(progress_raw, 2)}%"
        except:
            return "0%"

    def speed(self):
        current_time = time()
        current_bytes = self._obj.processed_bytes
        
        if current_time - self._last_sample_time > 1:
            if self._last_uploaded > 0:
                sample_speed = (current_bytes - self._last_uploaded) / (current_time - self._last_sample_time)
                self._speed_samples.append(sample_speed)
                
                if len(self._speed_samples) > 5:
                    self._speed_samples.pop(0)
                    
            self._last_uploaded = current_bytes
            self._last_sample_time = current_time
            
        if self._speed_samples:
            avg_speed = sum(self._speed_samples) / len(self._speed_samples)
            return f"{get_readable_file_size(avg_speed)}/s"
        else:
            return f"{get_readable_file_size(self._obj.speed)}/s"

    def eta(self):
        """Return estimated time with better calculation"""
        try:
            remaining_bytes = self._size - self._obj.processed_bytes
            if remaining_bytes <= 0:
                return "0s"
                
            if self._speed_samples:
                avg_speed = sum(self._speed_samples) / len(self._speed_samples)
                seconds = remaining_bytes / avg_speed
            else:
                seconds = remaining_bytes / self._obj.speed
                
            return get_readable_time(seconds)
        except:
            return "-"

    def elapsed_time(self):
        return get_readable_time(time() - self.start_time)

    def gid(self):
        return self._gid

    def task(self):
        return self

    def service_name(self):
        """Return the name of the upload service"""
        return self._service_name
