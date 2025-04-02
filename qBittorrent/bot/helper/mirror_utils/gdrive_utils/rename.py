from logging import getLogger
from googleapiclient.errors import HttpError

from bot.helper.mirror_utils.gdrive_utils.helper import GoogleDriveHelper

LOGGER = getLogger(__name__)


class gdRename(GoogleDriveHelper):

    def __init__(self):
        super().__init__()

    def renamefile(self, link, new_name, user_id):
        try:
            file_id = self.getIdFromUrl(link, user_id)
        except (KeyError, IndexError):
            return "<code>Google Drive ID tidak ditemukan!</code>"
        self.service = self.authorize()
        msg = ''
        try:
            file_metadata = {'name': new_name}
            self.service.files().update(fileId=file_id, body=file_metadata).execute()
            msg = "<code>File berhasil direname!</code>"
            LOGGER.info(f"Rename Result: {msg}")
        except HttpError as err:
            if "File not found" in str(err) or "insufficientFilePermissions" in str(err):
                token_service = self.alt_authorize()
                if token_service is not None:
                    LOGGER.error('File not found. Trying with token.pickle...')
                    self.service = token_service
                    return self.renamefile(link, new_name, user_id)
                err = "<code>File tidak ditemukan atau tidak ada izin untuk melakukan rename!</code>"
            LOGGER.error(f"Rename Result: {err}")
            msg = str(err)
        return msg
