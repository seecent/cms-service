
from __future__ import absolute_import
import hug
import requests
import time

from api.errorcode import ErrorCode
from config import db, setting
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from plugins.weixin.models.wxaccount import wxaccounts, AccountStatus
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


class WxAccountMixin(object):

    def get_wxaccount(self, id):
        row = db.get(wxaccounts, id)
        if row:
            return row2dict(row, wxaccounts)
        else:
            raise HTTPNotFound(title="no_wxaccount")


@hug.object.urls('')
class WxAccounts(object):
    '''部门管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''部门
        '''
        try:
            t = wxaccounts.alias('d')
            query = db.filter(wxaccounts, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, wxaccounts)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        部门REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        wxaccount = bind_dict(wxaccounts, body)
        d = db.save(wxaccounts, wxaccount)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(wxaccounts, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class WxAccountInst(WxAccountMixin, object):

    def get(self, id: int):
        t = self.get_wxaccount(id)
        return t

    def patch(self, id: int, body):
        t = self.get_wxaccount(id)
        if t:
            t = change_dict(wxaccounts, t, body)
            db.update(wxaccounts, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除部门
        :param: id int 部门ID
        :return:
        '''
        db.delete(wxaccounts, id)


@hug.get('/getAllWxAccounts')
def get_all_wxaccounts():
    datas = []
    t = wxaccounts.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_wxaccounts():
    rs = db.fetch_all(wxaccounts, ['name'])
    wxaccount_dict = {}
    for r in rs:
        code = r[1]
        wxaccount_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return wxaccount_dict


@hug.get('/syncAccessToken')
def sync_access_token(request, response):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    try:
        account_id = request.params.get('id')
        logger.info('<sync_access_token> id: ' + str(account_id))
        account = refresh_access_token(db, account_id)
        if account is None:
            result = {'code': ErrorCode.EXCEPTION.value,
                      'message': ErrorCode.EXCEPTION.name}
    except Exception:
        logger.exception('<sync_access_token> error: ')
        result = {'code': ErrorCode.EXCEPTION.value,
                  'message': ErrorCode.EXCEPTION.name}

    return result


def refresh_access_token(db, account_id):
    account = None
    try:
        logger.info('<refresh_access_token> account_id: ' + str(account_id))
        row = db.get(wxaccounts, account_id)
        if row:
            account = row2dict(row, wxaccounts)
            return account
            effective_time = account['effective_time']
            now = int(time.time())
            if effective_time is not None and effective_time > now:
                pass
            else:
                logger.info('<refresh_access_token> account: ' +
                            account['name'])
                appid = account['app_id']
                secret = account['app_secret']
                api_url = setting['weixin_api_url'] + \
                    "token?grant_type=client_credential&"
                api_url += "appid={0}&secret={1}".format(appid, secret)
                headers = {"Content-Type": "application/json;charset=UTF-8"}
                res = requests.post(api_url, headers=headers)
                logger.info('<refresh_access_token> status_code: ' +
                            str(res.status_code))
                if res.status_code == 200:
                    logger.info('<refresh_access_token> res json: ' +
                                str(res.json()))
                    data = res.json()
                    if "access_token" in data:
                        effect_time = now + data['expires_in']
                        access_token = data['access_token']
                        account['effective_time'] = effect_time
                        account['access_token'] = access_token
                        db.update(wxaccounts, {'id': account_id,
                                               'access_token': access_token,
                                               'refresh_time': now,
                                               'effective_time': effect_time})
                else:
                    account = None
    except Exception:
        logger.exception('<refresh_access_token> error: ')
        account = None

    return account


def init_wxaccounts():
    db.connect()
    count = db.count(wxaccounts)
    if count > 1:
        db.close()
        return
    now = datetime.now()
    account = {'name': '微信公众号',
               'code': 'gh_62241ba29385',
               'app_id': 'wx8a55d4f043c6ae91',
               'app_secret': 'fe864a5bfccfff0ca07c121f9bb8f81c',
               'status': AccountStatus.Active,
               'created_date': now,
               'last_modifed': now}
    db.insert(wxaccounts, account)
    db.close()
