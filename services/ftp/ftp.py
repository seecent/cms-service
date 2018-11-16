# -*- coding: utf-8 -*-
# @Time    : 2018/8/8 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import ftplib
import os

from config import ftp_config
from datetime import datetime
from log import logger


class FTPService(object):

    def __init__(self, host=None, port=None,
                 username=None, password=None,
                 path=None):
        if host is None:
            host = ftp_config['server']
        if port is None:
            port = ftp_config['port']
        if username is None:
            username = ftp_config['username']
        if password is None:
            password = ftp_config['password']
        if path is None:
            path = ftp_config['path']
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_path = path
        self.ftp = ftplib.FTP()

    def connect(self):
        try:
            logger.info('<connect> host: ' + self.host +
                        ', port: ' + str(self.port))
            self.ftp.connect(self.host, self.port)
        except Exception as e:
            logger.exception('<connect> error: ')

    def login(self):
        try:
            self.ftp.login(self.username, self.password)
        except Exception as e:
            logger.exception('<login> error: ')

    def quit(self):
        try:
            self.ftp.quit()
        except Exception as e:
            logger.exception('<quit> error: ')

    def upload_file(self, remote_dir, path, file_name, local_file_name):
        logger.info('<upload_file> remote_dir: ' + remote_dir +
                    ', path: ' + path +
                    ', local_file_name: ' + local_file_name)
        try:
            if not os.path.isfile(local_file_name):
                return
            ftp = self.ftp
            base_path = self.base_path
            ftp.cwd(base_path)
            dir_list = []
            ftp.dir('.', dir_list.append)
            if self._check_dir_exist(dir_list, remote_dir):
                ftp.cwd(base_path + '/' + remote_dir)
                dir_list = []
                ftp.dir('.', dir_list.append)
                if self._check_dir_exist(dir_list, path):
                    path = base_path + '/' + remote_dir + '/' + path
                else:
                    path = base_path + '/' + remote_dir + '/' + path
                    ftp.mkd(path)
                    logger.info('<upload_file> mkd path: ' + path)
            else:
                remote_path = base_path + '/' + remote_dir
                ftp.mkd(remote_path)
                logger.info('<upload_file> mkd remote_dir: ' +
                            remote_path)

            remote_file = path + '/' + file_name
            logger.info('<upload_file> remote_file: ' + remote_file)
            file_handler = open(local_file_name, 'rb')
            r = ftp.storbinary('STOR ' + remote_file, file_handler, 1024)
            logger.info('<upload_file> remote_file: ' + remote_file +
                        ', result: ' + r)
            file_handler.close()
        except Exception as e:
            logger.exception('<upload_file> error: ')
            return False
        return True

    def _check_dir_exist(self, dir_list, dir_name):
        for d in dir_list:
            if dir_name in d:
                return True
        return False

    def download_file(self, save_dir, remote_dir, file_name, date_time):
        logger.info('<download_file> save_dir: ' + save_dir +
                    ', remote_dir: ' + remote_dir +
                    ', file_name: ' + file_name +
                    ', date_time: ' + str(date_time))
        result = True
        try:
            dirStr = datetime.strftime(date_time, "%Y%m%d")
            save_path = save_dir + dirStr
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            save_filename = save_path + os.path.sep + file_name
            ftp = self.ftp
            base_path = self.base_path
            ftp.cwd(base_path)
            remote_file = base_path + '/' + remote_dir
            remote_file = remote_file + '/' + dirStr + '/' + file_name
            logger.info('<download_file> remote_file: ' + remote_file)
            logger.info('<download_file> local_file_name: ' +
                        save_filename)
            file_handler = open(save_filename, 'wb')
            r = ftp.retrbinary('RETR ' + remote_file, file_handler.write)
            logger.info('<download_file> remote_file: ' + remote_file +
                        ', result: ' + r)
            if '226 Transfer complete' in r:
                result = True
            else:
                result = False

            file_handler.close()
        except Exception as e:
            logger.exception('<download_file> error: ')
            result = False
        return result
