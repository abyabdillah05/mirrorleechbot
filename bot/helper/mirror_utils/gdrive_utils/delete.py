from logging import getLogger
from googleapiclient.errors import HttpError

from bot.helper.mirror_utils.gdrive_utils.helper import GoogleDriveHelper

LOGGER = getLogger(__name__)


class gdDelete(GoogleDriveHelper):
    def __init__(self):
        super().__init__()

    def deletefile(self, link, user_id):
        try:
            file_id = self.getIdFromUrl(link, user_id)
        except (KeyError, IndexError):
            return "Google Drive ID tidak ditemukan!"
        self.service = self.authorize()
        msg = ""
        try:
            self.service.files().delete(
                fileId=file_id, supportsAllDrives=True
            ).execute()
            msg = "File berhasil dihapus!"
            LOGGER.info(f"Delete Result: {msg}")
        except HttpError as err:
            if "File not found" in str(err) or "insufficientFilePermissions" in str(
                err
            ):
                if not self.alt_auth and self.use_sa:
                    self.alt_auth = True
                    self.use_sa = False
                    LOGGER.error("File not found. Trying with token.pickle...")
                    return self.deletefile(link, user_id)
                err = "File tidak ditemukan atau tidak ada izin untuk melakukan!"
            LOGGER.error(f"Delete Result: {err}")
            msg = str(err)
        return msg
