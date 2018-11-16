from __future__ import absolute_import

import requests

from config import setting
from datetime import datetime
from log import logger
from plugins.weixin.models.wxmedia import wxmedias


class ArticleService:

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
                # show_cover_pic = n['show_cover_pic']
                # author = n['author']
                digest = n['digest']
                content = n['content']
                # url = n['url']
                # content_source_url = n['content_source_url']
                print(title)
                print(title.encode("ISO-8859-1").decode("utf-8"))
                print(digest)
                print(digest.encode("ISO-8859-1").decode("utf-8"))
                print(content.encode("ISO-8859-1").decode("utf-8"))
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
