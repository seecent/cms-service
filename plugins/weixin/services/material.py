# -*- coding: utf-8 -*-
# @Time    : 2018/11/12 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

import requests

from config import setting
from datetime import datetime
from log import logger
from plugins.weixin.models.wxmedia import wxmedias
from services.page.page import PageService


pageservice = PageService()


class WxMediaService:

    def sync_wxmedias(self, db, account, media_type, offset, count,
                      media_ids_dict={}):
        """
        同步微信公众永久素材列表。

        :param db: 数据库操作db对象。
        :param account: 微信公众号账户信息。
        :param media_type: 素材类型，image|vedio|voice|news。
        :param offset: 起始索引。
        :param count: 获取数量。
        :param media_ids_dict: 已有素材ID字典。
        :retrun: {'total': 总数量, 'count': 本次获取数量}。
        """
        result = {'total': 0, 'count': 0}
        try:
            logger.info('<sync_wxmedias> account: ' + account['name'] +
                        ', media_type: ' + media_type +
                        ', offset: ' + str(offset) +
                        ', count: ' + str(count))
            access_token = account['access_token']
            api_url = setting['weixin_api_url']
            api_url += "material/batchget_material?access_token={0}".format(
                access_token)
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            params = {'type': media_type, 'offset': offset, 'count': count}
            res = requests.post(api_url, json=params, headers=headers)
            logger.info('<sync_wxmedias> status_code: ' +
                        str(res.status_code))
            if res.status_code != 200:
                return result
            logger.debug('<sync_wxmedias> res json: ' + str(res.json()))
            data = res.json()
            if "item" in data:
                result['total'] = data['total_count']
                result['count'] = data['item_count']
                logger.info('<sync_wxmedias> account: ' + account['name'] +
                            ", media_type: " + media_type +
                            ", result: " + str(result))
                items = data['item']
                if media_type == 'image':
                    for item in items:
                        self.save_image(db, account, item, media_ids_dict)
                elif media_type == 'news':
                    for item in items:
                        self.save_news(db, account, item, media_ids_dict)
        except Exception:
            logger.exception('<sync_wxmedias> account: ' + account['name'] +
                             ', error: ')

        return result

    def sync_wxmedia(self, db, account, media_id, media_ids_dict):
        """
        同步微信公众永久素材。

        :param db: 数据库操作db对象。
        :param account: 微信公众号账户信息。
        :param media_id: 素材media_id。
        :param media_ids_dict: 已有素材ID字典。
        :retrun: {'total': 总数量, 'count': 本次获取数量}。
        """
        try:
            logger.info('<sync_wxmedia> account: ' + account['name'] +
                        ', media_id: ' + media_id)
            api_url = setting['weixin_api_url']
            api_url += "material/get_material?access_token={0}".format(
                account['access_token'])
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            params = {'media_id': media_id}
            res = requests.post(api_url, json=params, headers=headers)
            logger.info('<sync_wxmedia> media_id: ' + media_id +
                        ', status_code: ' + str(res.status_code))
            if res.status_code == 200:
                logger.info('<sync_wxmedia> media_id: ' + media_id +
                            ', res json: ' + str(res.json()))
                data = res.json()
                print(data.pop('groupid'))
                tagid_list = data.pop('tagid_list')
                print(tagid_list)
                user_id = media_ids_dict.get(media_id)
                if user_id is None:
                    data['created_date'] = datetime.now()
                    data['account_id'] = account['id']
                    r = db.save(wxmedias, data)
                    user_id = r.get('id')
                    logger.info('<sync_wxmedia> new wxmedia: ' + str(user_id))
                    media_ids_dict['media_id'] = user_id
                else:
                    data['id'] = user_id
                    logger.info('<sync_wxmedia> update wxmedia: ' +
                                str(user_id))
                    data['last_modifed'] = datetime.now()
                    db.update(wxmedias, data)
        except Exception:
            logger.exception('<sync_wxmedia> account: ' + account['name'] +
                             ', error: ')

    def save_wxmedia(self, db, account, data, media_ids_dict):
        """
        保存素材

        :param db: 数据库操作db对象。
        :param account: 微信公众号账户信息。
        :param data: 素材media_id。
        :param media_ids_dict: 已有素材ID字典。
        :retrun: None。
        """
        try:
            media_id = data['media_id']
            logger.info('<save_wxmedia> account: ' + account['name'] +
                        ', media_id: ' + media_id)
            tid = media_ids_dict.get(media_id)
            if tid is None:
                data['created_date'] = datetime.now()
                data['account_id'] = account['id']
                r = db.save(wxmedias, data)
                tid = r.get('id')
                logger.info('<save_wxmedia> new wxmedia: ' + str(tid))
                media_ids_dict[media_id] = tid
            else:
                data['id'] = tid
                logger.info('<save_wxmedia> update wxmedia: ' + str(tid))
                data['last_modifed'] = datetime.now()
                db.update(wxmedias, data)
        except Exception:
            logger.exception('<save_wxmedia> account: ' + account['name'] +
                             ', error: ')

    def save_image(self, db, account, data, media_ids_dict):
        """
        保存图片

        :param db: 数据库操作db对象。
        :param account: 微信公众号账户信息。
        :param data: 素材media_id。
        :param media_ids_dict: 已有素材ID字典。
        :retrun: None。
        """
        try:
            media_id = data['media_id']
            logger.info('<save_image> account: ' + account['name'] +
                        ', media_id: ' + media_id)
            tid = media_ids_dict.get(media_id)
            if tid is None:
                data['created_date'] = datetime.now()
                data['account_id'] = account['id']
                r = db.save(wxmedias, data)
                tid = r.get('id')
                logger.info('<save_image> new wxmedia: ' + str(tid))
                media_ids_dict[media_id] = tid
            else:
                data['id'] = tid
                logger.info('<save_image> update wxmedia: ' + str(tid))
                data['last_modifed'] = datetime.now()
                db.update(wxmedias, data)
        except Exception:
            logger.exception('<save_image> account: ' + account['name'] +
                             ', error: ')

    def save_news(self, db, account, data, media_ids_dict):
        """
        保存图文

        :param db: 数据库操作db对象。
        :param account: 微信公众号账户信息。
        :param data: 素材media_id。
        :param media_ids_dict: 已有素材ID字典。
        :retrun: None。
        """
        try:
            media_id = data['media_id']
            cdata = data['content']
            news_list = cdata['news_item']
            for n in news_list:
                title = n['title']
                # thumb_media_id = n['thumb_media_id']
                show_cover_pic = n['show_cover_pic']
                author = n['author']
                digest = n['digest']
                content = n['content']
                # url = n['url']
                # content_source_url = n['content_source_url']
                title = title.encode("ISO-8859-1").decode("utf-8")
                author = author.encode("ISO-8859-1").decode("utf-8")
                digest = digest.encode("ISO-8859-1").decode("utf-8")
                content = content.encode("ISO-8859-1").decode("utf-8")
                print(title)
                print(digest)
                print(content)
                pdata = {'uuid': media_id,
                         'name': title,
                         'title': title,
                         'digest': digest,
                         'author': author,
                         'show_cover_pic': show_cover_pic}
                pageservice.save_page(db, 'weixin', 'articles', media_id,
                                      content, pdata)
            logger.info('<save_news> account: ' + account['name'] +
                        ', media_id: ' + media_id)
            # tid = media_ids_dict.get(media_id)
            # if tid is None:
            #     data['created_date'] = datetime.now()
            #     data['account_id'] = account['id']
            #     r = db.save(wxmedias, data)
            #     tid = r.get('id')
            #     logger.info('<save_news> new wxmedia: ' + str(tid))
            #     media_ids_dict[media_id] = tid
            # else:
            #     data['id'] = tid
            #     logger.info('<save_news> update wxmedia: ' + str(tid))
            #     data['last_modifed'] = datetime.now()
            #     db.update(wxmedias, data)
        except Exception:
            logger.exception('<save_news> account: ' + account['name'] +
                             ', error: ')
