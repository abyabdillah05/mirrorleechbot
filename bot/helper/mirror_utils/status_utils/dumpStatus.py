from time import time

from bot import LOGGER, subprocess_lock
from bot.helper.ext_utils.status_utils import (
    MirrorStatus
)
from .helper.ext_utils.common_utils import (get_readable_file_size,
                                            get_readable_time)

class DumpStatus:
    def __init__(self, listener, size, gid):
        self._size = size
        self._gid = gid
        self._start_time = time()
        self.listener = listener
        self.start_time = 0
        self.engine = "Payload_Dumper"

    def gid(self):
        return self._gid

    def speed_raw(self):
        return "-"

    def progress_raw(self):
        try:
            return self.processed_raw() / self._size * 100
        except:
            return 0

    def progress(self):
        return f"-"

    def speed(self):
        return f"-"

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self._size)

    def eta(self):
        try:
            seconds = (self._size - self.processed_raw()) / self.speed_raw()
            return get_readable_time(seconds)
        except:
            return "-"

    def status(self):
        return MirrorStatus.STATUS_DUMPING

    def processed_bytes(self):
        return "-"

    def processed_raw(self):
        return "-"

    def task(self):
        return self

    async def cancel_task(self):
        LOGGER.info(f"Cancelling Extract: {self.listener.name}")
        async with subprocess_lock:
            if (
                self.listener.suproc is not None
                and self.listener.suproc.returncode is None
            ):
                self.listener.suproc.kill()
            else:
                self.listener.suproc = "cancelled"
        await self.listener.onUploadError("Dumping dibatalkan oleh User!")
