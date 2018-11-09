
from __future__ import absolute_import
import hug
import json
import requests

from config import db, setting
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from plugins.weixin.api.wxaccount import refresh_access_token
from plugins.weixin.models.wxuser import wxusers
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


class WxUserMixin(object):

    def get_wxuser(self, id):
        row = db.get(wxusers, id)
        if row:
            return row2dict(row, wxusers)
        else:
            raise HTTPNotFound(title="no_wxuser")


@hug.object.urls('')
class WxUsers(object):
    '''部门管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''部门
        '''
        try:
            t = wxusers.alias('d')
            query = db.filter(wxusers, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, wxusers)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        部门REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        wxuser = bind_dict(wxusers, body)
        d = db.save(wxusers, wxuser)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(wxusers, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class WxUserInst(WxUserMixin, object):

    def get(self, id: int):
        t = self.get_wxuser(id)
        return t

    def patch(self, id: int, body):
        t = self.get_wxuser(id)
        if t:
            t = change_dict(wxusers, t, body)
            db.update(wxusers, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除部门
        :param: id int 部门ID
        :return:
        '''
        db.delete(wxusers, id)


@hug.get('/getAllWxUsers')
def get_all_wxusers():
    datas = []
    t = wxusers.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_wxusers():
    rs = db.fetch_all(wxusers, ['name'])
    wxuser_dict = {}
    for r in rs:
        code = r[1]
        wxuser_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return wxuser_dict


def query_all_openids_dict(db):
    openids = {}
    t = wxusers.alias('u')
    query = select([t.c.id, t.c.openid])
    rows = db.execute(query).fetchall()
    for r in rows:
        openids[r[1]] = r[0]
    return openids


def refresh_access_token():
    try:
        api_url = setting['weixin_api_url'] + \
            "token?grant_type=client_credential&"
        api_url += "appid={0}&secret={1}".format(
            "wx38214d0f5a5f7ebf", "74972e7b83a10721d3b82e54ab026d3e")
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        res = requests.post(api_url, headers=headers)
        logger.info('<refresh_access_token> status_code: ' +
                    str(res.status_code))
        logger.info('<refresh_access_token> res json: ' +
                    str(res.json()))
    except Exception:
        logger.exception('<refresh_access_token> error: ')


def sync_all_wxusers():
    try:
        db.connect()
        account = refresh_access_token(db, 1)
        if account is not None:
            account['access_token'] = "15_gPB5NreeYnYsPQlnrPwfNOgPqsF250bHOTtq01V0Zf-6mDNtABn14rmJWKyeueir2oL_obyLHHzShb0mlDPq0uQ5r7vgODbCSnCbyGSOYnTX6Cz5_6UXvrEnJ68FQGbAIATEU"
            sync_wxusers(db, account)
        db.close()
    except Exception:
        logger.exception('<sync_all_wxusers> error: ')


def sync_wxusers(db, account, next_openid=None):
    try:
        logger.info('<sync_wxusers> next_openid: ' + str(next_openid))
        access_token = account['access_token']
        openids_dict = query_all_openids_dict(db)
        # api_url = setting['weixin_api_url']
        # api_url += "user/get?access_token={0}".format("15__pu2urex8tNF1p97I72RKePSscBa0Cxw6jXGvaHMch7gbCFc-HReZATv1vv4E7V-qFBzAEp0yDDO1s1Gx6HSFf6ze_if3mpQBs3Aaa_RYd5rmzc9C6aLlgU8I4VibIg5ffpxyC4I6UFpVIxJYWUjAHADBZ")
        # headers = {"Content-Type": "application/json;charset=UTF-8"}
        # res = requests.post(api_url, headers=headers)
        # logger.info('<sync_wxusers> status_code: ' +
        #             str(res.status_code))
        # logger.info('<sync_wxusers> res json: ' +
        #             str(res.json()))
        t = '{"total": 49, "count": 49, "data": {"openid": ["o_yizjhVhgwnGN-IabBs3ybBt9VU", "o_yizju1VuA7xZowy4sFWnfSHos0", "o_yizjhAdbRj2O_IuNkJHXMNxM18", "o_yizjtuARuZIlh0PHxytSJYO9wM", "o_yizjkD4462FDF7QUmJpsDRCF98", "o_yizjsPVpPLezeB9cMHozhFKWec", "o_yizjoBTpUoYopJVToNLqAtK1z4", "o_yizjunkxDfZjxlJIjXWaSK-QcY", "o_yizjqhbyjOP7nv603VYHHYvjGw", "o_yizjkSERn6_rDFuqLriktHz5ec", "o_yizjgIaPQU_ysiv4k2eqA1bx7U", "o_yizjr4FSF4iRs2S8GkwMr-E3j4", "o_yizjtyP1-t4O2mxN-zAIiaLrzk", "o_yizjjKntBY9g7NMYQ8Zz7uQkyg", "o_yizjo83MBj6UXLXd4JtrAWhql8", "o_yizjlAU4t7uI-Ed8gLLoxxJNfQ", "o_yizjhnn7s0S-h4E3byxizkipmE", "o_yizjkHthEJr9n8ftjx2uaNus-w", "o_yizjntRhIsYz96KTb4ehy6E-cY", "o_yizjmSLIs5ixshdraR950XpAKM", "o_yizjle4JoQdt68gdoREdXIwe9o", "o_yizjtfvcN0_zhJIzrmNOJ8SvFE", "o_yizjt-XEEdwQPvPZQcdtzdz54o", "o_yizjiCIstCRAloeiYT5QqxLwtI", "o_yizjmIwDBumoqW-uYlclSxdxLU", "o_yizjh_NxiH6SS8A9uPJ0rvIB_A", "o_yizjvGAwc1pXI-YY5v4McBUhM8", "o_yizjt8gJP1rtxm6QEo3lq7Uku0", "o_yizjjdfIfsAce5j5cWA4sYfgmk", "o_yizjsUyzh1Sx9R4ajloM1cEEis", "o_yizjokzJB6YBQQqdm9F3B1opHM", "o_yizjqILda0q6sRp5HLJ3OovpPw", "o_yizjhGviofRG7twTu0kAsnOjcw", "o_yizjupThXgo1KOyfEzpNigkNfU", "o_yizjmF53kDEJ5ShSHQUwEiInIk", "o_yizjv6NIYdDjxGEw2POEJZR6XA", "o_yizjr-BGOpk7l8WVjQE-il0rr4", "o_yizjnXEl7gkB_FvSShCFB5h5_4", "o_yizjrgP6Jh0iingwravZpHEgQE", "o_yizjjK_1-E1giPWgWsy4Ih93s4", "o_yizjuwTS5tfpSLQZ0n-1G9PdFY", "o_yizjqEQNTBht_2kSHRquPI9DPs", "o_yizjoMMpE4dWliwywuTV_1sap0", "o_yizjv0-R2c-pMJFUQZ27Lq-jMk", "o_yizjifyqac3t3CYi1BhJZdydFA", "o_yizji1MR78LZ2YNd9cLxWxsx54", "o_yizjoegyyXruYN2F74_v2_-9AI", "o_yizjjv4prG4pHYyIRW1a9fuEaI", "o_yizjiwJr8Oy9_JBjU4woQ4O9kw"]}, "next_openid": "o_yizjiwJr8Oy9_JBjU4woQ4O9kw"}'
        data = json.loads(t)
        if "data" in data:
            total = data['total']
            count = data['count']
            logger.info('<sync_wxusers> next_openid: ' + str(next_openid) +
                        ", total: " + str(total) + ", count: " + str(count))
            data = data['data']
            openids = data['openid']
            for openid in openids:
                print(openid)
                sync_wxuser(db, account, openid, openids_dict)
            if "next_openid" in data:
                next_openid = data['next_openid']
                if next_openid is not None:
                    sync_wxusers(next_openid=None)
    except Exception:
        logger.exception('<sync_wxusers> error: ')


def sync_wxuser(db, account, openid, openids_dict):
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
        logger.exception('<sync_wxuser> error: ')
