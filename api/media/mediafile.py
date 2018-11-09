
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from models.media.file import files
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


class FileMixin(object):
    def get_file(self, id):
        row = db.get(files, id)
        if row:
            return row2dict(row, files)
        else:
            raise HTTPNotFound(title="no_file")


@hug.object.urls('')
class Files(object):
    '''部门管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''部门
        '''
        try:
            t = files.alias('d')
            query = db.filter(files, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, files)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        部门REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        file = bind_dict(files, body)
        d = db.save(files, file)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(files, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class FileInst(FileMixin, object):
    def get(self, id: int):
        t = self.get_file(id)
        return t

    def patch(self, id: int, body):
        t = self.get_file(id)
        if t:
            t = change_dict(files, t, body)
            db.update(files, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除部门
        :param: id int 部门ID
        :return:
        '''
        db.delete(files, id)


@hug.get('/getAllFiles')
def get_all_files():
    datas = []
    t = files.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_files():
    rs = db.fetch_all(files, ['name'])
    file_dict = {}
    for r in rs:
        code = r[1]
        file_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return file_dict


def init_files():
    db.connect()
    count = db.count(files)
    if count > 1:
        db.close()
        return
    now = datetime.now()
    dept1 = {'code': '1001', 'name': '销售部',
             'created_date': now,
             'last_modifed': now}
    dept2 = {'code': '1002', 'name': '银保部',
             'created_date': now,
             'last_modifed': now}
    dept3 = {'code': '1003', 'name': '收展部',
             'created_date': now,
             'last_modifed': now}
    dept4 = {'code': '1004', 'name': '数字创新',
             'created_date': now,
             'last_modifed': now}
    db.insert(files, dept1)
    db.insert(files, dept2)
    db.insert(files, dept3)
    db.insert(files, dept4)
    db.close()
