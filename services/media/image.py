from __future__ import absolute_import

import requests
import os
import uuid

from config import setting
from datetime import datetime
from log import logger
from models.media.folder import folders
from models.media.file import files
from models.media.image import images
from services.media.folder import FolderService


folderservice = FolderService()


class ImageService:

    def __init__(self, db=None):
        self.db = db

    def save_image(self, root, path, file_name, url):
        media_file = None
        try:
            media_root = setting['media_root']
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            base_path = media_root + os.path.sep + root
            base_path = base_path + os.path.sep + root
            folderservice.create_abs_folder(base_path)
            save_path = base_path + os.path.sep + date
            folderservice.create_abs_folder(save_path)

            uid = str(uuid.uuid1())
            new_file_name = uid + '.' + os.path.splitext(file_name)[1]
            r = self.download(save_path, new_file_name, url)
            if r:
                file_path = "{0}/{1}/{3}".format(root, path, new_file_name)
        except Exception:
            logger.exception('<save_image> error=')
            media_file = None
        return media_file

    def get_ext_name(self, file_name):
        try:
            return os.path.splitext(file_name)[1]
        except Exception:
            logger.exception('<get_ext_name> error=')
        return None

    def download(self, path, file_name, url):
        result = True
        try:
            logger.info('<download> file_name: ' + file_name +
                        ', url: ' + url)
            save_file_name = path + os.path.sep + file_name
            r = requests.get(url)
            with open(save_file_name, 'wb') as f:
                f.write(r.content)
        except Exception:
            logger.exception('<download> file_name: ' + file_name + ', error=')
            result = False
        return result
