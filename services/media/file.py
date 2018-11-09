from __future__ import absolute_import

import requests
import os

from config import setting
from datetime import datetime
from log import logger
from services.media.folder import FolderService


folderservice = FolderService()


class FileService:

    def __init__(self, db=None):
        self.db = db

    def download(self, path, file_name, url):
        try:
            media_root = setting['media_root']
            now = datetime.now()
            base_path = media_root + os.path.sep + path
            folderservice.create_abs_folder(base_path)
            dir_name = base_path + os.path.sep + \
                datetime.strftime(now, "%Y%m%d")
            folderservice.create_abs_folder(dir_name)
            save_file_name = dir_name + os.path.sep + file_name
            r = requests.get(url)
            media_root = setting['media_root']
            with open(save_file_name, 'wb') as f:
                f.write(r.content)
        except Exception:
            logger.exception('<download> error=')
