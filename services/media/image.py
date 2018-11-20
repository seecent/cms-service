# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import requests
import cv2
import os
import uuid

from api.errorcode import ErrorCode
from config import setting
from datetime import datetime
from log import logger
from models.media.folder import folders
from models.media.file import files, FileType
from models.media.image import images
from services.media.folder import FolderService
from sqlalchemy.sql import select


IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif']

folderservice = FolderService()


class ImageService:

    def find_folder(self, db, root_dir, dir_name):
        """
        查找图片文件目录
        Parameters
        ----------
        root_dir : str
          根目录名称
        dir_name : str
          目录名称

        Returns
        -------
        folder
          目录信息
        """
        folder = None
        try:
            t = folders.alias('f')
            query = select([t.c.id, t.c.name]).where(t.c.code == root_dir)
            row = db.execute(query).fetchone()
            if row is not None:
                query = select([t.c.id, t.c.name]).where(t.c.code == dir_name)
                query = query.where(t.c.parent_id == row[0])
                row = db.execute(query).fetchone()
                if row is not None:
                    full_path = self.create_image_folder(root_dir, dir_name)
                    url_path = self.create_url_path(root_dir, dir_name)
                    folder = {'id': row[0], 'code': dir_name, 'name': row[1],
                              'full_path': full_path, 'url_path': url_path}
        except Exception:
            logger.exception('<find_folder> root_dir: ' + root_dir +
                             ', dir_name: ' + dir_name + ', error: ')
            folder = None
        return folder

    def save_image(self, db, folder, file_name, url):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
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
                file_path = "{0}/{1}".format(url_path, new_file_name)
                data = {'uuid': uid,
                        'name': new_file_name,
                        'original_filename': file_name,
                        'type': FileType.IMAGE,
                        'file_path': file_path,
                        'file_szie': file_size,
                        'folder_id': folder_id,
                        'created_date': datetime.now()}

                img = cv2.imread(save_file_name)
                sp = img.shape
                print(sp)
                print(sp[0])
                print(sp[1])
                image_date = {'img_height': sp[0], 'img_width': sp[1]}
                result = self.save(db, uid, file_name, data, image_date)
        except Exception as e:
            logger.exception('<save_image> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)

        return result

    def upload(self, db, folder_id, file_name, file_content,
               user={}, create_date_folder=True):
        """
        上传图片文件，包括将上传文件保存到磁盘和保存上传文件数据库信息。
        Parameters
        ----------
        folder_id : str
          上传文件目录ID
        file_name : str
          上传文件名称
        file_content : str
          上传文件内容
        user : dict
          操作用户信息
        create_date_folder : boolean
          是否根据日期每天新建一个子目录

        Returns
        -------
        result
          文件上传结果
        """
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            logger.info('<upload> folder_id: ' +
                        str(folder_id) + ', file_name: ' + file_name)
            ext_name = os.path.splitext(file_name)[1]
            ext_name = ext_name.lower()
            if len(ext_name) > 1:
                ext_name = ext_name[1:]
            if ext_name not in IMAGE_TYPES:
                result['code'] = ErrorCode.UNSUPPORTED_FILE_TYPE.value
                result['message'] = ErrorCode.UNSUPPORTED_FILE_TYPE.name
                return result
            if folder_id is not None:
                folder = folderservice.get_folder_path(db, folder_id)
                if folder is not None:
                    now = datetime.now()
                    media_root = setting['media_root']
                    path = folder['path']
                    path_list = path.split(os.path.sep)
                    dir_name = media_root + os.path.sep + path
                    folderservice.create_abs_folder(dir_name)
                    if create_date_folder:
                        date = datetime.strftime(now, "%Y%m%d")
                        path_list.append(date)
                        dir_name = dir_name + os.path.sep + date
                        folderservice.create_abs_folder(dir_name)
                    result = self.save_image_file(
                        dir_name, file_name, file_content)
                    if result['code'] == ErrorCode.OK.value:
                        uuid = result['uid']
                        name = result['name']
                        path_list.append(name)
                        file_path = '/'.join(path_list)
                        data = {'uuid': uuid,
                                'name': name,
                                'original_filename': file_name,
                                'file_path': file_path,
                                'type': FileType.IMAGE,
                                'file_size': result['fileSize'],
                                'folder_id': folder_id,
                                'created_date': now}
                        image_date = {'img_height': result['height'],
                                      'img_width': result['width']}
                        result = self.save(
                            db, uuid, file_name, data, image_date)
                        result['uuid'] = uuid
                        result['save_name'] = name
                        result['file_name'] = file_name
                else:
                    result['code'] = ErrorCode.NOT_FOUND.value
                    result['message'] = "folder {0} not found!".format(
                        folder_id)
            else:
                result['code'] = ErrorCode.MISS_PARAM.value
                result['message'] = "miss param folder_id!"
        except Exception as e:
            logger.exception('<upload> folder_id: ' + str(folder_id) +
                             ', file_name: ' + file_name + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    def save(self, db, uuid, file_name, file_data, image_date):
        """
        保存文件数据库信息
        Parameters
        ----------
        db : db
          db 操作对象
        uuid : str
          生成的uuid
        file_name : str
          文件名称
        data : dict
          数据

        Returns
        -------
        result
          保存结果
        """
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        tx = db.begin()
        try:
            logger.debug('<save> uuid: ' + uuid + ', file_name: ' + file_name)
            file = db.save(files, file_data)
            file_id = file['id']
            image_date['id'] = file_id
            db.insert(images, image_date)
            tx.commit()
            result['file_id'] = file_id
        except Exception as e:
            logger.exception('<save> uuid: ' + uuid +
                             ', file_name: ' + file_name + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
            tx.rollback()

        return result

    def create_image_folder(self, root_dir, dir_name):
        """
        创建图片文件目录，根据日期每天新建一个目录
        Parameters
        ----------
        root_dir : str
          根目录
        dir_name : str
          目录名称

        Returns
        -------
        image_path
          图片文件目录完整路径
        """
        image_path = None
        try:
            logger.info('<create_image_folder> root_dir: ' + root_dir +
                        ', dir_name: ' + dir_name)
            media_root = setting['media_root']
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            root_path = media_root + os.path.sep + root_dir
            dir_path = root_path + os.path.sep + dir_name
            image_path = dir_path + os.path.sep + date
            self.create_abs_folder(image_path)
        except Exception:
            logger.exception('<create_image_folder> root_dir: ' + root_dir +
                             ', dir_name: ' + dir_name + ', error: ')
            image_path = False
        return image_path

    def create_url_path(self, root, path):
        """
        创建图片相对URL
        Parameters
        ----------
        root : str
          根目录
        path : str
          目录名称

        Returns
        -------
        url_path
          图片相对URL
        """
        url_path = ''
        try:
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            url_path = "{0}/{1}/{2}".format(root, path, date)
        except Exception:
            logger.exception('<create_url_path> root: ' + root +
                             ', path: ' + path + ', error: ')
        return url_path

    def create_image_url(self, file_path):
        """
        创建图片完整URL
        Parameters
        ----------
        root : str
          根目录
        path : str
          目录名称

        Returns
        -------
        image_url
          图片完整URL
        """
        image_url = ''
        try:
            media_url = setting['media_url']
            image_url = "{0}/{1}".format(media_url, file_path)
        except Exception:
            logger.exception('<create_image_url> error: ')
        return image_url

    def create_abs_folder(self, name):
        result = True
        try:
            logger.debug('<create_abs_folder> name: ' + name)
            if not os.path.exists(name):
                logger.info('<create_abs_folder> name: ' + name)
                os.makedirs(name)
        except Exception:
            logger.exception('<create_abs_folder> error: ')
            result = False
        return result

    def get_ext_name(self, file_name):
        """
        获取文件扩展名
        Parameters
        ----------
        file_name : str
          文件名称

        Returns
        -------
        ext_name
          文件扩展名
        """
        ext_name = None
        try:
            ext = os.path.splitext(file_name)[1]
            if len(ext) > 1:
                ext = ext.lower()
                ext_name = ext[1:]
            return ext_name
        except Exception:
            logger.exception('<get_ext_name> file_name: ' +
                             file_name + ', error: ')
            ext_name = None
        return ext_name

    def save_image_file(self, dir_name, file_name, file_content):
        """
        保存图片文件
        Parameters
        ----------
        dir_name : str
          文件保存目录
        file_name : str
          文件原名称
        file_content : str
          文件内容

        Returns
        -------
        result
          文件保存结果
        """
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            logger.info('<save_image_file> dir_name: ' +
                        dir_name + ', file_name: ' + file_name)
            uid = str(uuid.uuid1())
            ext = os.path.splitext(file_name)[1]
            ext = ext.lower()
            new_file_name = uid + ext
            save_file_name = dir_name + os.path.sep + new_file_name
            logger.info('<save_image_file> save_file_name: ' + save_file_name)
            with open(save_file_name, 'wb') as f:
                f.write(file_content)
                f.close()

            img = cv2.imread(save_file_name)
            sp = img.shape
            print(sp)
            print(sp[0])
            print(sp[1])
            result['uid'] = uid
            result['name'] = new_file_name
            result['fileName'] = file_name
            result['fileSize'] = os.path.getsize(save_file_name)
            result['height'] = sp[0]
            result['width'] = sp[1]
        except Exception as e:
            logger.exception('<save_image_file> file_name: ' +
                             file_name + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)

        return result

    def download(self, save_dir, save_file_name, url):
        """
        下载文件
        Parameters
        ----------
        save_dir : str
          下载文件保存目录完整路径
        save_file_name : str
          下载文件保存名称
        url : str
          下载文件URL地址

        Returns
        -------
        result
          True or False
        """
        result = True
        try:
            logger.info('<save_file> save_dir: ' + save_dir +
                        ', save_file_name: ' + save_file_name)
            r = requests.get(url)
            with open(save_dir + os.path.sep + save_file_name, 'wb') as f:
                f.write(r.content)
        except Exception:
            logger.exception('<download> error: ')
            result = False

        return result
