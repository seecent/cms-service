
from __future__ import absolute_import
import hug

from api.errorcode import ErrorCode
from config import db
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from plugins.weixin.models.wxuser import wxusers
from plugins.weixin.services.account import WxAccountService
from plugins.weixin.services.user import WxUserService
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}
wxaccountService = WxAccountService()
wxuserService = WxUserService()


class WxUserMixin(object):

    def get_wxuser(self, id):
        row = db.get(wxusers, id)
        if row:
            return row2dict(row, wxusers)
        else:
            raise HTTPNotFound(title="no_wxuser")


@hug.object.urls('')
class WxUsers(object):
    '''微信用户管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''微信用户
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
        微信用户REST API Post接口
        :param: id int 微信用户ID
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
        删除微信用户
        :param: id int 微信用户ID
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


@hug.post('/syncAllWxUsers')
def sync_all_wxusers(request, response, accountId):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    try:
        logger.info('<sync_all_wxusers> account: ' + str(accountId))
        db.connect()
        result = wxaccountService.refresh_access_token(db, accountId)
        if result['code'] == ErrorCode.OK.value:
            account = result['account']
            openids_dict = wxuserService.query_all_openids_dict(db)
            wxuserService.sync_wxusers(db, account, openids_dict)
        db.close()
    except Exception:
        logger.exception('<sync_all_wxusers> error: ')
        result = {'code': ErrorCode.EXCEPTION.value,
                  'message': ErrorCode.EXCEPTION.name}

    return result


@hug.post('/syncWxUser')
def sync_wxuser(request, response, accountId, userId, openId):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    try:
        logger.info('<sync_wxuser> account: ' + str(accountId) +
                    ', userId: ' + userId +
                    ', openId: ' + openId)
        db.connect()
        result = wxaccountService.refresh_access_token(db, accountId)
        if result['code'] == ErrorCode.OK.value:
            account = result['account']
            openids_dict = {}
            openids_dict[openId] = userId
            wxuserService.sync_wxuser(db, account, openId, openids_dict)
        db.close()
    except Exception:
        logger.exception('<sync_wxuser> error: ')
        result = {'code': ErrorCode.EXCEPTION.value,
                  'message': ErrorCode.EXCEPTION.name}

    return result
