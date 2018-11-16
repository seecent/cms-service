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


folderservice = FolderService()
IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif']
VIDEO_TYPES = ['mp4']
VOICE_TYPES = ['mp3']
EXCEL_TYPES = ['xls', 'xlsx']
WORD_TYPES = ['doc', 'docx']
PPT_TYPES = ['ppt', 'pptx']


class FileService:

    def __init__(self, db=None):
        self.db = db

    def create(self, db, folder_id, file_name, file_content, user={}):
        """
        保存上传文件信息
        Parameters
        ----------
        folder_id : str
          上传文件目录ID
        file_name : str
          上传文件保存名称
        file_content : str
          上传文件内容

        Returns
        -------
        result
          文件上传结果
        """
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            logger.info('<create> folder_id: ' +
                        str(folder_id) + ', file_name: ' + file_name)
            file_type = self.check_file_type(file_name)
            if file_type is None:
                result['code'] = ErrorCode.UNSUPPORTED_FILE_TYPE.value
                result['message'] = ErrorCode.UNSUPPORTED_FILE_TYPE.name
                return result
            if folder_id is not None:
                folder = folderservice.get_folder_path(db, folder_id)
                if folder is not None:
                    media_root = setting['media_root']
                    path = folder['path']
                    print(path)
                    now = datetime.now()
                    date = datetime.strftime(now, "%Y%m%d")
                    base_path = media_root + os.path.sep + path
                    folderservice.create_abs_folder(base_path)
                    dir_name = base_path + os.path.sep + date
                    folderservice.create_abs_folder(dir_name)
                    result = self.save_file(dir_name, file_name, file_content)
                    if result['code'] == ErrorCode.OK.value:
                        name = result['name']
                        file_path = '/'.join(path.split(os.path.sep)
                                             ) + '/' + date + '/' + name
                        data = {'uuid': result['uid'],
                                'name': name,
                                'original_filename': file_name,
                                'file_path': file_path,
                                'type': file_type,
                                'file_size': result['fileSize'],
                                'folder_id': folder_id,
                                'created_date': now}
                        db.insert(files, data)
                else:
                    result['code'] = ErrorCode.NOT_FOUND.value
                    result['message'] = "folder {0} not found!".format(
                        folder_id)
            else:
                result['code'] = ErrorCode.MISS_PARAM.value
                result['message'] = "miss param folder_id!"
        except Exception as e:
            logger.exception('<create> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    def save_file(self, dir_name, file_name, file_content):
        """
        保存上传文件
        Parameters
        ----------
        path : str
          上传文件保存路径
        filename : str
          上传文件保存名称
        filecontent : str
          上传文件内容

        Returns
        -------
        result
          文件上传结果
        """
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            logger.info('<save_file> dir_name: ' +
                        dir_name + ', file_name: ' + file_name)
            uid = str(uuid.uuid1())
            ext = os.path.splitext(file_name)[1]
            ext = ext.lower()
            filename = uid + ext
            save_filename = dir_name + os.path.sep + filename
            logger.info('<save_file> save_filename: ' + save_filename)
            with open(save_filename, 'wb') as f:
                f.write(file_content)
                f.close()
            result['uid'] = uid
            result['name'] = filename
            result['fileName'] = file_name
            result['originalFileName'] = file_name
            result['fileSize'] = os.path.getsize(save_filename)
        except Exception as e:
            logger.exception('<save_file> file_name: ' +
                             file_name + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)

        return result

    def download(self, path, file_name, url):
        """
        下载文件
        Parameters
        ----------
        path : str
          下载文件保存路径
        file_name : str
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
        try:
            return os.path.splitext(file_name)[1]
        except Exception:
            logger.exception('<get_ext_name> file_name: ' +
                             file_name + ', error: ')
        return None
