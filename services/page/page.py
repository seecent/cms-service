# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import os

from api.errorcode import ErrorCode
from config import setting
from datetime import datetime
from log import logger
from models.page.page import pages


class PageService:

    def save(self, db, data):
        try:
            data['created_date'] = datetime.now()
            r = db.save(pages, data)
            page_id = r.get('id')
            logger.info('<save> new page: ' + str(page_id))
        except Exception:
            logger.exception('<save> error: ')

    def save_page(self, db, root, path, uuid, content, data):
        """
        保存页面信息和页面html文件。

        :param db: 数据库操作db对象。
        :param root: 页面文件根目录。
        :param path: 页面主题目录。
        :param uuid: uuid。
        :param content: 页面html内容。
        :param data: 页面信息
        :retrun: result。
        """
        logger.info('<save_page> root: ' + root +
                    ', path: ' + path + ', uuid: ' + uuid)
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        tx = db.begin()
        try:
            data['created_date'] = datetime.now()
            r = db.save(pages, data)
            page_id = r.get('id')
            logger.info('<save> new page: ' + str(page_id))

            file_name = str(page_id) + '.html'
            path = self.create_page_folder('weixin', 'articles')
            self.save_file(path, file_name, content)

            purl = self.create_url_path('weixin', 'articles', file_name)
            db.update(pages, {'id': page_id, 'file_path': purl})
            tx.commit()
            result['data'] = {'page_id': page_id}
        except Exception as e:
            logger.exception('<save_page> root: ' + root +
                             ', path: ' + path +
                             ', file_name: ' + file_name + ', error: ')
            tx.rollback()
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    def save_file(self, path, file_name, content):
        """
        保存页面html文件。

        :param path: 目录。
        :param content: 页面html内容。
        :param file_name: html文件名称。
        :retrun: True or False。
        """
        result = True
        try:
            logger.info('<save_file> path: ' + path +
                        ', file_name: ' + file_name)
            save_file_name = path + os.path.sep + file_name
            with open(save_file_name, 'w') as f:
                f.write(content)
        except Exception:
            logger.exception('<save_file> path: ' + path +
                             ', file_name: ' + file_name +
                             ', error: ')
            result = False
        return result

    def create_page_folder(self, root, path):
        page_path = None
        try:
            logger.info('<create_page_folder> root: ' + root +
                        ', path: ' + path)
            media_root = setting['page_root']
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            base_path = media_root + os.path.sep + root
            base_path = base_path + os.path.sep + path
            self.create_abs_folder(base_path)
            page_path = base_path + os.path.sep + date
            self.create_abs_folder(page_path)
        except Exception:
            logger.exception('<create_page_folder> root: ' + root +
                             ', path: ' + path + ', error: ')
            page_path = False
        return page_path

    def create_url_path(self, root, path, file_name=None):
        url_path = ''
        try:
            date = datetime.strftime(datetime.now(), "%Y%m%d")
            if file_name is not None:
                url_path = "{0}/{1}/{2}/{3}".format(root, path, date,
                                                    file_name)
            else:
                url_path = "{0}/{1}/{2}".format(root, path, date)
        except Exception:
            logger.exception('<create_url_path> root: ' + root +
                             ', path: ' + path + ', error: ')
        return url_path

    def create_page_url(self, file_path):
        image_url = ''
        try:
            media_url = setting['page_url']
            image_url = "{0}/{1}".format(media_url, file_path)
        except Exception:
            logger.exception('<create_page_url> error: ')
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
