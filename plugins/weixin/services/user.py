from __future__ import absolute_import

import requests

from config import setting
from datetime import datetime
from log import logger
from plugins.weixin.models.wxuser import wxusers
from sqlalchemy.sql import select


class WxUserService:

    def sync_wxusers(self, db, account, openids_dict, next_openid=None):
        account_id = account['id']
        try:
            logger.info('<sync_wxusers> account: ' + str(account_id) +
                        ', next_openid: ' + str(next_openid))
            access_token = account['access_token']
            api_url = setting['weixin_api_url']
            api_url += "user/get?access_token={0}".format(access_token)
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            res = requests.post(api_url, headers=headers)
            logger.info('<sync_wxusers> status_code: ' +
                        str(res.status_code))
            if res.status_code == 200:
                logger.info('<sync_wxusers> res json: ' +
                            str(res.json()))
                data = res.json()
                if "data" in data:
                    total = data['total']
                    count = data['count']
                    logger.info('<sync_wxusers> next_openid: ' +
                                str(next_openid) +
                                ", total: " + str(total) +
                                ", count: " + str(count))
                    data = data['data']
                    openids = data['openid']
                    for openid in openids:
                        print(openid)
                        self.sync_wxuser(db, account, openid, openids_dict)
                    if "next_openid" in data:
                        next_openid = data['next_openid']
                        if next_openid is not None:
                            self.sync_wxusers(next_openid)
        except Exception:
            logger.exception('<sync_wxusers> error: ')

    def sync_wxuser(self, db, account, openid, openids_dict={}):
        try:
            logger.info('<sync_wxuser> account: ' + account['name'] +
                        ', openid: ' + openid)
            api_url = setting['weixin_api_url']
            api_url += "user/info?access_token={0}&openid={1}&lang=zh_CN".format(
                account['access_token'], openid)
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            res = requests.post(api_url, headers=headers)
            logger.info('<sync_wxuser> openid: ' + openid +
                        ', status_code: ' + str(res.status_code))
            if res.status_code == 200:
                logger.info('<sync_wxuser> openid: ' + openid +
                            ', res json: ' + str(res.json()))
                data = res.json()
                print(data.pop('groupid'))
                tagid_list = data.pop('tagid_list')
                print(tagid_list)
                user_id = openids_dict.get(openid)
                if user_id is None:
                    data['created_date'] = datetime.now()
                    data['account_id'] = account['id']
                    r = db.save(wxusers, data)
                    user_id = r.get('id')
                    logger.info('<sync_wxuser> new wxuser: ' + str(user_id))
                    openids_dict[openid] = user_id
                else:
                    data['id'] = user_id
                    logger.info('<sync_wxuser> update wxuser: ' + str(user_id))
                    data['last_modifed'] = datetime.now()
                    db.update(wxusers, data)
        except Exception:
            logger.exception('<sync_wxuser> account: ' + account['name'] +
                             ', openid: ' + openid + ', error: ')

    def query_all_openids_dict(self, db):
        openids = {}
        t = wxusers.alias('u')
        query = select([t.c.id, t.c.openid])
        rows = db.execute(query).fetchall()
        for r in rows:
            openids[r[1]] = r[0]
        return openids
