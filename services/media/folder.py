# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import os

from config import setting
from log import logger
from models.media.folder import folders
from sqlalchemy.sql import select


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
            logger.exception('<init_folders> error: ')

    @classmethod
    def create_folder(self, parent, name):
        result = True
        try:
            dir_name = parent + os.path.sep + name
            logger.info('<create_folder> name: ' + dir_name)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        except Exception:
            logger.exception('<create_folder> error: ')
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
            logger.exception('<create_abs_folder> error: ')
            result = False
        return result

    def get_folder(self, db, folder_id):
        """
        根据目录ID从数据库获取文件目录信息。
        Parameters
        ----------
        name : int
          folder_id

        Returns
        -------
        result
          文件目录信息。
        """
        folder = None
        try:
            logger.debug('<get_folder> folder_id: ' + str(folder_id))
            t = folders.alias('f')
            query = select([t.c.id, t.c.code, t.c.name,
                            t.c.parent_id, t.c.level])
            query = query.where(t.c.id == folder_id)
            row = db.execute(query).fetchone()
            if row:
                folder = {'id': row[0],
                          'code': row[1],
                          'name': row[2],
                          'parent_id': row[3],
                          'level': row[4]}
        except Exception:
            logger.exception('<get_folder> folder_id: ' + str(folder_id) +
                             ', error: ')
            folder = None
        return folder

    def get_folder_path(self, db, folder_id):
        """
        根据目录ID文件目录路径。
        Parameters
        ----------
        name : int
          folder_id

        Returns
        -------
        result
          文件目录信息。
        """
        folder = None
        try:
            logger.info('<get_folder_path> folder_id: ' + str(folder_id))
            if folder_id is not None:
                t = folders.alias('f')
                query = select([t.c.id, t.c.code, t.c.name,
                                t.c.parent_id, t.c.level])
                query = query.where(t.c.id == folder_id)
                row = db.execute(query).fetchone()
                if row:
                    parent_id = row[3]
                    folder = {'id': row[0],
                              'code': row[1],
                              'name': row[2],
                              'parent_id': parent_id,
                              'level': row[4],
                              'path': row[1]}
                    print(folder)
                    if parent_id is not None:
                        parent_folder = self.get_folder(db, parent_id)
                        if parent_folder is not None:
                            folder['path'] = parent_folder[
                                'path'] + os.path.sep + row[1]
            else:
                return None
        except Exception:
            logger.exception('<get_folder_path> folder_id: ' + str(folder_id) +
                             ', error: ')
            folder = None
        return folder
