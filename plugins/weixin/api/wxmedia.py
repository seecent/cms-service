
from __future__ import absolute_import
import hug
import requests

from config import db, setting
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from plugins.weixin.api.wxaccount import refresh_access_token
from plugins.weixin.models.wxmedia import wxmedias
from plugins.weixin.services.material import WxMediaService
from models import row2dict, rows2dict, bind_dict, change_dict
from services.media.image import ImageService
from sqlalchemy.sql import select

wxmediaservice = WxMediaService()
IGNORES = {'created_date', 'last_modifed'}


class WxMediaMixin(object):

    def get_wxmedia(self, id):
        row = db.get(wxmedias, id)
        if row:
            return row2dict(row, wxmedias)
        else:
            raise HTTPNotFound(title="no_wxmedia")


@hug.object.urls('')
class WxMedias(object):
    '''部门管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''部门
        '''
        try:
            t = wxmedias.alias('d')
            query = db.filter(wxmedias, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, wxmedias)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        部门REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        wxmedia = bind_dict(wxmedias, body)
        d = db.save(wxmedias, wxmedia)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(wxmedias, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class WxMediaInst(WxMediaMixin, object):

    def get(self, id: int):
        t = self.get_wxmedia(id)
        return t

    def patch(self, id: int, body):
        t = self.get_wxmedia(id)
        if t:
            t = change_dict(wxmedias, t, body)
            db.update(wxmedias, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除部门
        :param: id int 部门ID
        :return:
        '''
        db.delete(wxmedias, id)


@hug.get('/getAllWxMedias')
def get_all_wxmedias():
    datas = []
    t = wxmedias.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_wxmedias():
    rs = db.fetch_all(wxmedias, ['name'])
    wxmedia_dict = {}
    for r in rs:
        code = r[1]
        wxmedia_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return wxmedia_dict


def query_all_mediaids_dict(db, media_type):
    media_ids = {}
    t = WxMedias.alias('m')
    query = select([t.c.id, t.c.media_id])
    rows = db.execute(query).fetchall()
    for r in rows:
        media_ids[r[1]] = r[0]
    return media_ids


def sync_all_wxmedias():
    try:
        db.connect()
        account = refresh_access_token(db, 1)
        if account is not None:
            account['access_token'] = "15_g9sGIxfuEyq9thyKzPTWMHizA0q74ZwDaL1LAYBuEAzzMFj5bt-6cEyTgbZzhu__O7FfCWSzViZQ2TcKZ7edwBi9l5t5KI-LrDaAXoAYru0QurOpZsMvGJmpBWzjRjhHsfjHoYjfzbNMrgn1YHQhAJARAJ"
            # media_ids_dict = query_all_mediaids_dict(db, None)
            wxmediaservice.sync_wxmedias(db, account, 'news', 0, 1)
        db.close()
    except Exception:
        logger.exception('<sync_all_wxusers> error: ')


def sync_all_wxmeida_images():
    try:
        db.connect()
        account = refresh_access_token(db, 1)
        if account is not None:
            imageservice = ImageService()
            folder = imageservice.find_folder(db, 'weixin', 'images')
            if folder is not None:
                t = wxmedias.alias('m')
                query = select([t.c.id, t.c.name, t.c.url])
                query.where(t.c.account_id == 1)
                rows = db.execute(query).fetchall()
                for r in rows:
                    imageservice.save_image(db, folder, r[1], r[2])
        db.close()
    except Exception:
        logger.exception('<sync_all_wxmeida_images> error: ')


def sync_wxmedias(db, account, media_ids_dict, media_type, offset, count):
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
        logger.info('<sync_wxmedias> res json: ' +
                    str(res.json()))
        # bs = str(res.json()).encode("ISO-8859-1")
        # print(bs)
        # logger.info('<sync_wxmedias> res json: ' +
        #             bs.decode("utf-8"))
        data = res.json()
        if "item" in data:
            total = data['total_count']
            count = data['item_count']
            title = data['title']
            print(title.encode("ISO-8859-1").decode("utf-8"))
            logger.info('<sync_wxmedias> type: ' + media_type +
                        ", total: " + str(total) + ", count: " + str(count))
            items = data['item']
            for item in items:
                save_wxmedia(db, account, item, media_ids_dict)
    except Exception:
        logger.exception('<sync_wxmedias> error: ')


def sync_wxmedia(db, account, media_id, media_ids_dict):
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
                logger.info('<sync_wxmedia> update wxmedia: ' + str(user_id))
                data['last_modifed'] = datetime.now()
                db.update(wxmedias, data)
    except Exception:
        logger.exception('<sync_wxmedia> error: ')


def save_wxmedia(db, account, data, media_ids_dict):
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
        logger.exception('<save_wxmedia> error: ')
