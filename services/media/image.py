from __future__ import absolute_import

import requests
import cv2
import os
import uuid

from config import setting
from datetime import datetime
from log import logger
from models.media.folder import folders
from models.media.file import files, FileType
from models.media.image import images
from sqlalchemy.sql import select


class ImageService:

    def __init__(self, db=None):
        self.db = db

    def find_folder(self, root, path):
        folder = None
        try:
            t = folders.alias('f')
            query = select([t.c.id, t.c.name]).where(t.c.code == root)
            row = self.db.execute(query).fetchone()
            if row is not None:
                query = select([t.c.id, t.c.name]).where(t.c.code == path)
                query = query.where(t.c.parent_id == row[0])
                row = self.db.execute(query).fetchone()
                if row is not None:
                    full_path = self.create_image_folder(root, path)
                    url_path = self.create_url_path(root, path)
                    folder = {'id': row[0], 'code': path, 'name': row[1],
                              'full_path': full_path, 'url_path': url_path}
        except Exception:
            logger.exception('<find_folder> root: ' + root +
                             ', path: ' + path + ', error: ')
            folder = None
        return folder

    def save_image(self, folder, file_name, url):
        media_file = None
        try:
            folder_id = folder['id']
            full_path = folder['full_path']
            url_path = folder['url_path']
            logger.info('<save_image> folder_id: ' + str(folder_id) +
                        ', file_name: ' + file_name)
            uid = str(uuid.uuid1())
            new_file_name = uid + os.path.splitext(file_name)[1]
            r = self.download(full_path, new_file_name, url)
            if r:
                save_file_name = full_path + os.path.sep + new_file_name
                file_size = os.path.getsize(save_file_name)
                print(file_size)
                img = cv2.imread(save_file_name)
                sp = img.shape
                print(sp)
                print(sp[0])
                print(sp[1])

                file_path = "{0}/{1}".format(url_path, new_file_name)
                data = {'uuid': uid,
                        'name': new_file_name,
                        'original_filename': file_name,
                        'type': FileType.IMAGE,
                        'file_path': file_path,
                        # 'file_szie': 
                        'folder_id': folder_id,
                        'created_date': datetime.now()}
                media_file = self.db.save(files, data)
        except Exception:
            logger.exception('<save_image> error: ')
            media_file = None
        return media_file

    def create_image_folder(self, root, path):
        image_path = None
        try:
            logger.info('<create_image_folder> root: ' + root +
                        ', path: ' + path)
            media_root = setting['media_root']
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            base_path = media_root + os.path.sep + root
            base_path = base_path + os.path.sep + path
            self.create_abs_folder(base_path)
            image_path = base_path + os.path.sep + date
            self.create_abs_folder(image_path)
        except Exception:
            logger.exception('<create_image_folder> root: ' + root +
                             ', path: ' + path + ', error: ')
            image_path = False
        return image_path

    def create_url_path(self, root, path):
        url_path = ''
        try:
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            url_path = "{0}/{1}/{2}".format(root, path, date)
        except Exception:
            logger.exception('<create_url_path> root: ' + root +
                             ', path: ' + path + ', error: ')
        return url_path

    def create_image_url(self, file_path):
        image_url = ''
        try:
            media_url = setting['media_url']
            image_url = "{0}/{1}".format(media_url, file_path)
        except Exception:
            logger.exception('<create_url_path> error: ')
        return image_url

    def create_abs_folder(self, name):
        result = True
        try:
            logger.info('<create_abs_folder> name: ' + name)
            if not os.path.exists(name):
                os.makedirs(name)
        except Exception:
            logger.exception('<create_abs_folder> error: ')
            result = False
        return result

    def get_ext_name(self, file_name):
        try:
            return os.path.splitext(file_name)[1]
        except Exception:
            logger.exception('<get_ext_name> error: ')
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
            logger.exception('<download> file_name: ' + file_name + ', error: ')
            result = False
        return result
