
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from models.media.folder import folders
from models import row2dict, rows2data, bind_dict, change_dict
from services.media.folder import FolderService
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


class FolderMixin(object):

    def get_folder(self, id):
        row = db.get(folders, id)
        if row:
            return row2dict(row, folders)
        else:
            raise HTTPNotFound(title="no_folder")


@hug.object.urls('')
class Folders(object):
    '''文件目录REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''文件目录
        '''
        try:
            parentId = request.params.get('parentId')
            # filter_name = request.params.get('filterName')
            t = folders.alias('f')
            p = folders.alias('b')
            joins = {'parent': {
                     'select': ['id', 'parent_id', 'name'],
                     'column': t.c.parent_id,
                     'table': p,
                     'join_column': p.c.id}}
            query = db.filter_join(t, joins, request, ['Name'])
            folder_list = []
            if parentId is not None:
                query = query.where(t.c.parent_id == parentId)
            else:
                query = query.where(t.c.level == 1)
            if q is not None:
                query = query.where(t.c.Name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            folder_list = rows2data(rs, folders, joins)
            # for folder in folder_list:
            #     if folder['Name'] == filter_name:
            #         return [folder]
            return folder_list
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        文件目录REST API Post接口
        :param: id int 文件目录ID
        :return: json
        '''
        folder = bind_dict(folders, body)
        d = db.save(folders, folder)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(folders, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class FolderInst(FolderMixin, object):

    def get(self, id: int):
        t = self.get_folder(id)
        return t

    def patch(self, id: int, body):
        t = self.get_folder(id)
        if t:
            t = change_dict(folders, t, body)
            db.update(folders, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除文件目录
        :param: id int 文件目录ID
        :return:
        '''
        db.delete(folders, id)


@hug.get('/getAllFolders')
def get_all_folders(request, response, parent_id=None):
    datas = []
    t = folders.alias('f')
    query = select([t.c.id, t.c.code, t.c.name, t.c.parent_id])
    if parent_id:
        query = query.where(t.c.parent_id == parent_id)
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1],
                      'name': r[2], 'parent_id': r[3]})
    return datas


def query_all_folders():
    rs = db.fetch_all(folders, ['name'])
    folder_dict = {}
    for r in rs:
        code = r[1]
        folder_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return folder_dict


def init_folders():
    try:
        logger.info('<init_folders> start...')
        FolderService.init_folders()
        db.connect()
        count = db.count(folders)
        # if count > 1:
        #     db.close()
        #     return
        now = datetime.now()
        # folder1 = {'code': 'docs', 'name': '文档',
        #            'created_date': now, 'last_modifed': now}
        # folder2 = {'code': 'images', 'name': '图片',
        #            'created_date': now, 'last_modifed': now}
        # folder3 = {'code': 'videos', 'name': '视频',
        #            'created_date': now, 'last_modifed': now}
        # folder4 = {'code': 'voices', 'name': '音频',
        #            'created_date': now, 'last_modifed': now}
        # db.insert(folders, folder1)
        # db.insert(folders, folder2)
        # db.insert(folders, folder3)
        # db.insert(folders, folder4)

        # folder5 = {'code': 'weixin', 'name': '微信',
        #            'created_date': now,
        #            'last_modifed': now}
        # r = db.save(folders, folder5)
        r = {'id': 5}
        if r is not None:
            pid = r['id']
            folder51 = {'code': 'images', 'name': '图片',
                        'parent_id': pid, 'level': 2,
                        'created_date': now, 'last_modifed': now}
            folder52 = {'code': 'videos', 'name': '视频',
                        'parent_id': pid, 'level': 2,
                        'created_date': now, 'last_modifed': now}
            folder53 = {'code': 'voices', 'name': '音频',
                        'parent_id': pid, 'level': 2,
                        'created_date': now, 'last_modifed': now}
            folder54 = {'code': 'news', 'name': '图文',
                        'parent_id': pid, 'level': 2,
                        'created_date': now, 'last_modifed': now}
            db.insert(folders, folder51)
            db.insert(folders, folder52)
            db.insert(folders, folder53)
            db.insert(folders, folder54)
        db.close()
        logger.info('<init_folders> end!')
    except Exception:
        logger.exception('<init_folders> error: ')
