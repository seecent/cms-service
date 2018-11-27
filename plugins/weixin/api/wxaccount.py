
from __future__ import absolute_import
import hug

from api.errorcode import ErrorCode
from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from plugins.weixin.models.wxaccount import wxaccounts, AccountStatus
from plugins.weixin.services.account import WxAccountService
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

wxaccountService = WxAccountService()

IGNORES = {'app_secret', 'access_token', 'created_date', 'last_modifed'}


class WxAccountMixin(object):

    def get_wxaccount(self, id):
        row = db.get(wxaccounts, id)
        if row:
            return row2dict(row, wxaccounts)
        else:
            raise HTTPNotFound(title="no_wxaccount")


@hug.object.urls('')
class WxAccounts(object):
    '''微信公众号管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''微信公众号
        '''
        try:
            t = wxaccounts.alias('d')
            query = db.filter(wxaccounts, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, wxaccounts, IGNORES)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        微信公众号REST API Post接口
        :param: id int 微信公众号ID
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
            excludes = ['refresh_time', 'effective_time']
            t = change_dict(wxaccounts, t, body, excludes)
            db.update(wxaccounts, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除微信公众号
        :param: id int 微信公众号ID
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
        result = wxaccountService.refresh_access_token(db, account_id)
    except Exception:
        logger.exception('<sync_access_token> error: ')
        result = {'code': ErrorCode.EXCEPTION.value,
                  'message': ErrorCode.EXCEPTION.name}

    return result


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
