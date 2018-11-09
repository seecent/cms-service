# -*- coding: utf-8 -*-
# @Time    : 2018/8/8 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import os
import paramiko

from config import ftp_config
from datetime import datetime
from log import logger


class SFTPService(object):

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

    def ssh(self):
        result = True
        try:
            logger.info('<ssh> host: ' + self.host +
                        ', port: ' + str(self.port))
            # 创建SSH对象
            self.ssh = paramiko.SSHClient()
            # 允许连接不在know_hosts文件中的主机
            # 第一次登录的认证信息
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接服务器
            self.ssh.connect(self.host, self.port,
                             self.username, self.password)
            # 执行命令
            stdin, stdout, stderr = self.ssh.exec_command('pwd')
            # 获取命令结果
            res, err = stdout.read(), stderr.read()
            if res:
                response = str(res.decode())
                logger.info('<ssh> result: ' + response)
                if response:
                    response = self._strip_line(response)
                    self.base_path = response + self.base_path
                result = True
            else:
                logger.info('<ssh> result: ' + str(err.decode()))
                result = False
        except Exception as e:
            logger.exception('<ssh> error=')
            result = False
        return result

    def cmd(self, command):
        try:
            logger.info('<cmd> command: ' + command)
            # 执行命令
            stdin, stdout, stderr = self.ssh.exec_command(command)
            # 获取命令结果
            res, err = stdout.read(), stderr.read()
            result = res if res else err
            logger.info('<cmd> result: ' + str(result.decode()))
        except Exception as e:
            logger.exception('<cmd> error=')

    def connect(self):
        result = True
        try:
            logger.info('<connect> host: ' + self.host +
                        ', port: ' + str(self.port))
            self.transport = paramiko.Transport((self.host, self.port))
            self.transport.connect(username=self.username,
                                   password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception as e:
            logger.exception('<connect> error=')
            result = False
        return result

    def close(self):
        try:
            if self.transport is not None:
                self.transport.close()
        except Exception as e:
            logger.exception('<close> error=')

    def upload_file(self, remote_dir, path, file_name, local_file_name):
        logger.info('<upload_file> remote_dir: ' + remote_dir +
                    ', path: ' + path +
                    ', local_file_name: ' + local_file_name)
        try:
            if not os.path.isfile(local_file_name):
                return
            sftp = self.sftp
            base_path = self.base_path
            remote_path = base_path + '/' + remote_dir
            if not self.is_dir_exist(base_path, remote_dir):
                logger.info('<upload_file> mkdir remote_dir: ' +
                            remote_path)
                sftp.mkdir(remote_path)
            remote_file_path = base_path + '/' + remote_dir + '/' + path
            if not self.is_dir_exist(remote_path, path):
                logger.info('<upload_file> mkdir path: ' + remote_file_path)
                sftp.mkdir(remote_file_path)
            remote_file = remote_file_path + '/' + file_name
            logger.info('<upload_file> remote_file: ' + remote_file)
            sftp.put(local_file_name, remote_file)
        except Exception as e:
            logger.exception('<upload_file> error=')
            return False
        return True

    def mk_dir(self, dir_name):
        result = True
        try:
            self.sftp.mkdir(dir_name)
        except Exception as e:
            # logger.exception('<mk_dir> error=')
            result = False
        return result

    def is_dir_exist(self, dir_path, dir_name):
        result = True
        try:
            logger.info('<is_dir_exist> dir_path: ' + dir_path +
                        ', dir_name: ' + dir_name)
            dir_list = []
            files = self.sftp.listdir(dir_path)
            for filename in files:
                dir_list.append(filename)
            result = self._check_dir_exist(dir_list, dir_name)
            logger.info('<is_dir_exist> dir_path: ' + dir_path +
                        ', result: ' + str(result))
        except Exception as e:
            logger.exception('<is_dir_exist> dir_path: ' + dir_path +
                             ', error=')
            result = False
        return result

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
            base_path = self.base_path
            remote_file = base_path + '/' + remote_dir
            remote_file = remote_file + '/' + dirStr + '/' + file_name
            logger.info('<download_file> remote_file: ' + remote_file)
            logger.info('<download_file> local_file_name: ' +
                        save_filename)
            self.sftp.get(remote_file, save_filename)
        except Exception as e:
            logger.exception('<download_file> error=')
            result = False
        return result

    def download_files(self, save_dir, remote_dir, date_time):
        logger.info('<download_files> save_dir: ' + save_dir +
                    ', remote_dir: ' + remote_dir +
                    ', date_time: ' + str(date_time))
        file_names = []
        try:
            dirStr = datetime.strftime(date_time, "%Y%m%d")
            base_path = self.base_path
            if not self.is_dir_exist(base_path + '/' + remote_dir, dirStr):
                return file_names
            save_path = save_dir + dirStr
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            remote_path = base_path + '/' + remote_dir + '/' + dirStr
            files = self.sftp.listdir(remote_path)
            for filename in files:
                logger.info('<download_files> filename: ' +
                            filename)
                if filename.endswith('.txt'):
                    file_names.append(filename)
            for file_name in file_names:
                save_filename = save_path + os.path.sep + file_name
                remote_file = remote_path + '/' + file_name
                logger.info('<download_files> remote_file: ' + remote_file)
                logger.info('<download_files> local_file_name: ' +
                            save_filename)
                self.sftp.get(remote_file, save_filename)
        except Exception as e:
            logger.exception('<download_files> error=')
        return file_names

    def _check_dir_exist(self, dir_list, dir_name):
        if dir_name is dir_list:
            return True
        for d in dir_list:
            if dir_name in d:
                return True
        return False

    # 去除特殊字符
    def _strip_line(self, line):
        return line.strip("\n").strip("\r").strip("\ufeff")
