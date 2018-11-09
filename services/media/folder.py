from __future__ import absolute_import

import os

from config import setting
from log import logger


class FolderService:

    def __init__(self, db=None):
        self.db = db

    @classmethod
    def init_folders(self):
        try:
            media_root = setting['media_root']
            logger.info('<init_folders> media_root: ' + media_root)
            if not os.path.exists(media_root):
                os.makedirs(media_root)

            # 1. create docs folder
            self.create_folder(media_root, 'docs')
            # 2. create images folder
            self.create_folder(media_root, 'images')
            # 3. create videos folder
            self.create_folder(media_root, 'videos')
            # 4. create voices folder
            self.create_folder(media_root, 'voices')
            # 5. create weixin folder
            weixin_dir = media_root + os.path.sep + 'weixin'
            self.create_folder(media_root, 'weixin')
            self.create_folder(weixin_dir, 'images')
            self.create_folder(weixin_dir, 'videos')
            self.create_folder(weixin_dir, 'voices')
            self.create_folder(weixin_dir, 'news')

        except Exception:
            logger.exception('<init_folders> error=')

    @classmethod
    def create_folder(self, parent, name):
        result = True
        try:
            dir_name = parent + os.path.sep + name
            logger.info('<create_folder> name: ' + dir_name)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        except Exception:
            logger.exception('<create_folder> error=')
            result = False
        return result

    def create_abs_folder(self, name):
        """
        创建绝对路径文件目录
        Parameters
        ----------
        name : str
          名称

        Returns
        -------
        result
          True of False。
        """
        result = True
        try:
            logger.info('<create_abs_folder> name: ' + name)
            if not os.path.exists(name):
                os.makedirs(name)
        except Exception:
            logger.exception('<create_abs_folder> error=')
            result = False
        return result
