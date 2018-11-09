# coding=utf-8
from __future__ import absolute_import
import hug

from api.auth.user import check_sysadmin, query_current_user
from cache import orgcache
from config import mdb
from falcon import HTTPNotFound
from models.mdb.ams.amscso import amscsos
from models import row2dict, rows2dict
from services.collect.collect import CollectService
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}
LF = '%{}%'


class AmscsosMixin(object):
    def get_amscso(self, code):
        t = amscsos.alias('t')
        query = select([t.c]).where(t.c.comCode == code)
        row = mdb.fetch_one(query)
        if row:
            return row2dict(row, amscsos)
        else:
            raise HTTPNotFound(title="no_amscso")


@hug.object.urls('')
class Amscsos(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        qcode = request.params.get('qcode')
        qprovice = request.params.get('qprovice')
        qcity = request.params.get('qcity')
        t = amscsos.alias('t')
        query = mdb.filter(t, request, ['comName'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org_id = u.get('organization_id')
            ccodes = orgcache.get_ccodes(org_id)
            if ccodes and len(ccodes) > 0:
                query = query.where(t.c.comCode.in_(ccodes))
        if q:
            query = query.where(t.c.comName.like(LF.format(q)))
        if qcode:
            query = query.where(t.c.comCode.like(LF.format(qcode)))
        if qprovice:
            query = query.where(t.c.proviceNo.like(LF.format(qprovice)))
        if qcity:
            query = query.where(t.c.cityNo.like(LF.format(qcity)))
        rs = mdb.paginate_data(query, request, response)
        return rows2dict(rs, amscsos)


@hug.object.http_methods('/{id}')
class AmscsosInst(AmscsosMixin, object):
    def get(self, id: str):
        cso = self.get_amscso(id)
        return cso


@hug.get('/getAllAmsCSOList')
def query_all_amscsos(request, response):
    t = amscsos.alias('t')
    query = select([t.c.comCode, t.c.comName])
    query = query.order_by(t.c.comCode.asc())
    u = query_current_user(request)
    if u and not check_sysadmin(u):
        org_id = u.get('organization_id')
        ccodes = orgcache.get_ccodes(org_id)
        if ccodes and len(ccodes) > 0:
            query = query.where(t.c.comCode.in_(ccodes))
    rs = mdb.execute(query).fetchall()
    amscso_list = []
    for r in rs:
        amscso_list.append({'comCode': r[0], 'comName': r[1]})
    return amscso_list


@hug.get('/getAmsCSOTreeList')
def query_amscso_tree_list(request, response):
    t = amscsos.alias('t')
    query = select([t.c.comCode, t.c.comName])
    u = query_current_user(request)
    if u and not check_sysadmin(u):
        org_id = u.get('organization_id')
        ccodes = orgcache.get_ccodes(org_id)
        if ccodes and len(ccodes) > 0:
            query = query.where(t.c.comCode.in_(ccodes))
    query = query.order_by(t.c.comCode.asc())
    rs = mdb.execute(query).fetchall()
    amscso_list = []
    for r in rs:
        amscso_list.append({'key': 'CSO-' + r[0], 'code': r[0], 'name': r[1]})
    return amscso_list


def query_all_amscso_list(province, q):
    mdb.connect()
    t = amscsos.alias('t')
    query = select([t])
    if province:
        query = query.where(t.c.proviceNo == province)
    if q:
        query = query.where(t.c.comName.like(LF.format(q)))
    rs = mdb.execute(query).fetchall()
    mdb.close()
    return rows2dict(rs, amscsos)


def init_amscsos():
    mapping = [{'name': 'comCode', 'title': 'comCode', 'type': 'Text'},
               {'name': 'comName', 'title': 'comName', 'type': 'Text'},
               {'name': 'comShortName', 'title': 'comShortName',
                'type': 'Text'},
               {'name': 'phone', 'title': 'phone', 'type': 'Text'},
               {'name': 'zipCode', 'title': 'zipCode', 'type': 'Text'},
               {'name': 'fax', 'title': 'fax', 'type': 'Text'},
               {'name': 'proviceNo', 'title': 'proviceNo', 'type': 'Text'},
               {'name': 'cityNo', 'title': 'cityNo', 'type': 'Text'},
               {'name': 'address', 'title': 'address', 'type': 'Text'},
               {'name': 'datime', 'title': 'datime', 'type': 'DateTime',
                'format': '%Y-%m-%d'}]
    mdb.connect()
    collect = CollectService()
    collect.import_from_csv('AMS_AMSCSO_201805211546.csv', mdb,
                            amscsos, ['comCode'], mapping)
    mdb.close()
