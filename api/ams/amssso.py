# coding=utf-8
from __future__ import absolute_import
import hug

from api.auth.user import check_sysadmin, query_current_user
from cache import orgcache
from config import mdb
from models.mdb.ams.amscso import amscsos
from models.mdb.ams.amssso import amsssos
from models import rows2data, rows2dict
from services.collect.collect import CollectService
from sqlalchemy.sql import select

IGNORES = {'created_date', 'last_modifed'}


@hug.object.urls('')
class Amsssos(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        qcode = request.params.get('qcode')
        t = amsssos.alias('s')
        c = amscsos.alias('c')
        joins = {'amscso': {
                 'select': ['comCode', 'comName'],
                 'column': t.c.comCode,
                 'table': c,
                 'join_column': c.c.comCode}}
        query = mdb.filter_join(t, joins, request, ['ssoName'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org_id = u.get('organization_id')
            dcodes = orgcache.get_dcodes(org_id)
            if dcodes and len(dcodes) > 0:
                query = query.where(t.c.ssoCode.in_(dcodes))
            else:
                ccodes = orgcache.get_ccodes(org_id)
                if ccodes and len(ccodes) > 0:
                    query = query.where(t.c.comCode.in_(ccodes))
        if q:
            query = query.where(t.c.ssoName.like('%' + q + '%'))
        if qcode:
            query = query.where(t.c.ssoCode.like('%' + qcode + '%'))
        rs = mdb.paginate_data(query, request, response)
        return rows2data(rs, amsssos, joins)


@hug.get('/getAllAmsSSOList')
def query_all_amsssos(request, response, comCode: str=None):
    t = amsssos.alias('t')
    query = select([t.c.ssoCode, t.c.ssoName])
    u = query_current_user(request)
    if u and not check_sysadmin(u):
        org_id = u.get('organization_id')
        dcodes = orgcache.get_dcodes(org_id)
        if dcodes and len(dcodes) > 0:
            query = query.where(t.c.ssoCode.in_(dcodes))
        else:
            ccodes = orgcache.get_ccodes(org_id, comCode)
            if ccodes and len(ccodes) > 0:
                query = query.where(t.c.comCode.in_(ccodes))
    elif comCode:
        query = query.where(t.c.comCode == comCode)
    query = query.order_by(t.c.ssoName.asc())
    rs = mdb.execute(query).fetchall()
    amssso_list = []
    for r in rs:
        amssso_list.append({'ssoCode': r[0], 'ssoName': r[1]})
    return amssso_list


@hug.get('/getAmsSSOTreeList')
def query_amsssos_tree_list(request, response, comCode: str=None):
    amssso_list = []
    t = amsssos.alias('t')
    query = select([t.c.ssoCode, t.c.ssoName])
    u = query_current_user(request)
    if u and not check_sysadmin(u):
        org_id = u.get('organization_id')
        dcodes = orgcache.get_dcodes(org_id)
        if dcodes and len(dcodes) > 0:
            query = query.where(t.c.ssoCode.in_(dcodes))
        else:
            ccodes = orgcache.get_ccodes(org_id, comCode)
            if ccodes and len(ccodes) > 0:
                query = query.where(t.c.comCode.in_(ccodes))
    elif comCode:
        query = query.where(t.c.comCode == comCode)
    query = query.order_by(t.c.ssoName.asc())
    rs = mdb.execute(query).fetchall()
    for r in rs:
        amssso_list.append({'key': 'SSO-' + r[0],
                            'code': r[0],
                            'name': r[1]})
    return {'comCode': comCode, 'list': amssso_list}


def query_all_amssso_list(q):
    mdb.connect()
    t = amsssos.alias('t')
    query = select([t])
    if q:
        query = query.where(t.c.ssoName.like('%{}%'.format(q)))
    rs = mdb.execute(query).fetchall()
    mdb.close()
    return rows2dict(rs, amsssos)


def init_amsssos():
    mapping = [{'name': 'ssoCode', 'title': 'SSOCODE', 'type': 'Text'},
               {'name': 'ssoName', 'title': 'SSONAME', 'type': 'Text'},
               {'name': 'comCode', 'title': 'COMCODE', 'type': 'Text'}]
    mdb.connect()
    collect = CollectService()
    collect.import_from_csv('AMS_AMSSSO_201805211547.csv', mdb,
                            amsssos, ['SSOCODE'], mapping)
    mdb.close()
