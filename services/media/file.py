# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import requests
import os
import uuid

from api.errorcode import ErrorCode
from config import setting
from datetime import datetime
from log import logger
from models.media.file import files, FileType
from services.media.folder import FolderService

IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif']
VIDEO_TYPES = ['mp4']
VOICE_TYPES = ['mp3']
EXCEL_TYPES = ['xls', 'xlsx']
WORD_TYPES = ['doc', 'docx']
PPT_TYPES = ['ppt', 'pptx']

folderservice = FolderService()


class FileService:

    def __init__(self, db=None):
        self.db = db

    def upload(self, db, folder_id, file_name, file_content,
               file_type, user={}, create_date_folder=True):
        """
        上传文件，包括将上传文件保存到磁盘和保存上传文件数据库信息。
        Parameters
        ----------
        folder_id : str
          上传文件目录ID
        file_name : str
          上传文件名称
        file_content : str
          上传文件内容
        file_type : FileType
          文件类型
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
            if file_type is None:
                file_type = self.check_file_type(file_name)
                if file_type is None:
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
                    result = self.save_file(dir_name, file_name, file_content)
                    if result['code'] == ErrorCode.OK.value:
                        uuid = result['uid']
                        name = result['name']
                        path_list.append(name)
                        file_path = '/'.join(path_list)
                        data = {'uuid': uuid,
                                'name': name,
                                'original_filename': file_name,
                                'type': file_type,
                                'file_path': file_path,
                                'file_size': result['fileSize'],
                                'folder_id': folder_id,
                                'created_date': now}
                        result = self.save(db, uuid, file_name, data)
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

    def save(self, db, uuid, file_name, data):
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
        try:
            logger.debug('<save> uuid: ' + uuid + ', file_name: ' + file_name)
            file_id = db.insert(files, data)
            result['file_id'] = file_id
        except Exception as e:
            logger.exception('<save> uuid: ' + uuid +
                             ', file_name: ' + file_name + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)

        return result

    def save_file(self, dir_name, file_name, file_content):
        """
        将文件保存到磁盘
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
            logger.info('<save_file> dir_name: ' +
                        dir_name + ', file_name: ' + file_name)
            uid = str(uuid.uuid1())
            ext = os.path.splitext(file_name)[1]
            ext = ext.lower()
            new_file_name = uid + ext
            save_file_name = dir_name + os.path.sep + new_file_name
            logger.info('<save_file> save_file_name: ' + save_file_name)
            with open(save_file_name, 'wb') as f:
                f.write(file_content)
                f.close()
            result['uid'] = uid
            result['name'] = new_file_name
            result['fileName'] = file_name
            result['fileSize'] = os.path.getsize(save_file_name)
        except Exception as e:
            logger.exception('<save_file> file_name: ' +
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

    def check_file_type(self, file_name):
        """
        检查文件扩展名是否在支持的范围内。
        Parameters
        ----------
        file_name : str
          文件名称

        Returns
        -------
        result
          文件类型
        """
        file_type = None
        try:
            ext = os.path.splitext(file_name)[1]
            ext = ext.lower()
            if len(ext) > 1:
                ext = ext[1:]
            if ext in IMAGE_TYPES:
                return FileType.IMAGE
            elif ext in VIDEO_TYPES:
                return FileType.VIDEO
            elif ext in VOICE_TYPES:
                return FileType.VOICE
            elif ext == 'txt':
                return FileType.TXT
            elif ext == 'csv':
                return FileType.CSV
            elif ext == 'pdf':
                return FileType.PDF
            elif ext in WORD_TYPES:
                return FileType.WORD
            elif ext in EXCEL_TYPES:
                return FileType.EXCEL
            elif ext in PPT_TYPES:
                return FileType.PPT
            else:
                logger.error('<check_file_type> file_name: ' +
                             file_name + ', ext: ' + ext +
                             ', error: Unsupported file type!')
        except Exception:
            logger.exception('<check_file_type> file_name: ' +
                             file_name + ', error: ')
            file_type = None
        return file_type

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
