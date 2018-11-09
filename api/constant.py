
from __future__ import absolute_import
import hug

# from api.auth import api_key_auth
from config import db, mdb
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from models.constant import constants
from models.mdb.ods.ldcode import ldcode
from models import row2dict, rows2dict, bind_dict, change_dict
from services.collect.collect import CollectService
from sqlalchemy.sql import select, and_

IGNORES = {'created_date', 'last_modifed'}


class ConstantMixin(object):
    def get_constant(self, id):
        row = db.get(constants, id)
        if row:
            return row2dict(row, constants)
        else:
            raise HTTPNotFound(title="no_constant")


@hug.object.urls('')
class Constants(object):
    # @hug.object.get(requires=api_key_auth)
    @hug.object.get()
    def get(self, request, response, q: str=None):
        try:
            t = constants.alias('c')
            query = db.filter(constants, request, ['name'])
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, constants)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        constant = bind_dict(constants, body)
        d = db.save(constants, constant)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        codes = request.params.get('codes')
        const_types = request.params.get('const_types')
        tx = db.begin()
        try:
            counter = 0
            while counter < len(codes):
                db.execute(constants.delete().where(and_(constants.c.code ==
                                                    codes[counter],
                                                    constants.c.const_type ==
                                                    const_types[counter])))
                counter += 1
            tx.commit()
        except BaseException:
            tx.rollback()
            raise
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class ConstantInst(ConstantMixin, object):
    def get(self, id: int):
        t = self.get_constant(id)
        return t

    def patch(self, id: int, body):
        t = self.get_constant(id)
        if t:
            t = change_dict(constants, t, body)
            db.update(constants, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        db.delete(constants, id)


def query_all_constants():
    rs = db.fetch_all(constants, ['name'])
    constant_dict = {}
    for r in rs:
        code = r[1]
        constant_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return constant_dict


def init_constants():
    db.connect()
    count = db.count(constants)
    if count > 1:
        db.close()
        return
    now = datetime.now()
    constant1 = {'code': 'M',
                 'name': '男性',
                 'const_type': 'sex',
                 'const_type_label': '性别',
                 'order_no': 1,
                 'created_date': now,
                 'last_modifed': now}
    constant2 = {'code': 'F',
                 'name': '女性',
                 'const_type': 'sex',
                 'const_type_label': '性别',
                 'order_no': 2,
                 'created_date': now,
                 'last_modifed': now}
    db.insert(constants, constant1)
    db.insert(constants, constant2)
    db.close()

    init_constants_from_csv()


def init_constants_from_csv():
    mapping = [{'name': 'code', 'title': 'CODE', 'type': 'Text'},
               {'name': 'name', 'title': 'NAME', 'type': 'Text'},
               {'name': 'const_type', 'title': 'TYPE', 'type': 'Text'},
               {'name': 'const_label', 'title': 'LABEL', 'type': 'Text'},
               {'name': 'const_alias', 'title': 'ALIAS', 'type': 'Text'},
               {'name': 'order_no', 'title': 'ORDERNO', 'type': 'Number'},
               {'name': 'created_date', 'default_value': datetime.now()}]
    collect = CollectService()
    collect.import_from_csv('locations.csv', constants,
                            ['CODE', 'TYPE'], mapping, 'conf')


def sync_form_mdb(code_type):
    now = datetime.now()
    db.connect()
    mdb.connect()
    t = ldcode.alias('d')
    query = select([t.c.code, t.c.codeName])
    rs = mdb.execute(query.where(t.c.codeType == code_type)).fetch_all()
    for r in rs:
        d = {'code': r[0],
             'name': r[1],
             'const_type': code_type,
             'const_type_label': code_type,
             'created_date': now,
             'last_modifed': now}
        db.insert(constants, d)
    db.close()
    mdb.close()
