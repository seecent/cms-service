
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from models.auth.user import departments
from models import row2dict, rows2dict, bind_dict, change_dict
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


class DepartmentMixin(object):
    def get_department(self, id):
        row = db.get(departments, id)
        if row:
            return row2dict(row, departments)
        else:
            raise HTTPNotFound(title="no_department")


@hug.object.urls('')
class Departments(object):
    '''部门管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''部门
        '''
        try:
            t = departments.alias('d')
            query = db.filter(departments, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, departments)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        部门REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        department = bind_dict(departments, body)
        d = db.save(departments, department)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(departments, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class DepartmentInst(DepartmentMixin, object):
    def get(self, id: int):
        t = self.get_department(id)
        return t

    def patch(self, id: int, body):
        t = self.get_department(id)
        if t:
            t = change_dict(departments, t, body)
            db.update(departments, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除部门
        :param: id int 部门ID
        :return:
        '''
        db.delete(departments, id)


@hug.get('/getAllDepartments')
def get_all_departments():
    datas = []
    t = departments.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_departments():
    rs = db.fetch_all(departments, ['name'])
    department_dict = {}
    for r in rs:
        code = r[1]
        department_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return department_dict


def init_departments():
    db.connect()
    count = db.count(departments)
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
    db.insert(departments, dept1)
    db.insert(departments, dept2)
    db.insert(departments, dept3)
    db.insert(departments, dept4)
    db.close()
