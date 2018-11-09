# coding=utf-8
from __future__ import absolute_import
import hug

from api.auth.user import check_sysadmin, query_current_user
from api.statistics.saleleadsstat import stat_sales_active_leads
from cache import orgcache
from config import db, mdb
from datetime import datetime
from falcon import HTTPNotFound
from models.mdb.ams.amscso import amscsos
from models.mdb.ams.amssso import amsssos
from models.mdb.ams.amssales import amssales
from models import row2data, rows2data
from services.collect.collect import CollectService
from sqlalchemy.sql import select
from models.statistics.saleleadsstat import saleleadsstats

IGNORES = {'created_date', 'last_modifed'}
LF = '%{}%'


class AmssalesMixin(object):
    def get_amssales(self, id):
        t = amssales.alias('a')
        c = amscsos.alias('c')
        s = amsssos.alias('s')
        joins = {'amscso': {
            'select': ['comCode', 'comName'],
            'column': t.c.comCode,
            'table': c,
            'join_column': c.c.comCode},
            'amssso': {
                'select': ['ssoCode', 'ssoName'],
                'column': t.c.ssoCode,
                'table': s,
                'join_column': s.c.ssoCode}}
        query = mdb.filter_join(t, joins, None)
        query = query.where(t.c.staffNo == id)
        row = mdb.fetch_one(query)
        if row:
            return row2data(row, amssales, joins)
        else:
            raise HTTPNotFound(title="no_amssales")


@hug.object.urls('')
class Amssales(object):
    @hug.object.get()
    def get(self, request, response, q: str = None):
        qcomCode = request.params.get('qcomCode')
        qssoCode = request.params.get('qssoCode')
        qstaffNo = request.params.get('qstaffNo')
        qdutyName = request.params.get('qdutyName')
        t = amssales.alias('a')
        c = amscsos.alias('c')
        s = amsssos.alias('s')
        d = saleleadsstats.alias('d')
        joins = {'amscso': {
            'select': ['comCode', 'comName'],
            'column': t.c.comCode,
            'table': c,
            'join_column': c.c.comCode},
            'amssso': {
                'select': ['ssoCode', 'ssoName'],
                'column': t.c.ssoCode,
                'table': s,
                'join_column': s.c.ssoCode},
            'leadstatistics': {
                'select': ['daily_lead_count',
                           'week_lead_count',
                           'month_lead_count',
                           'month_call_count',
                           'month_visit_count',
                           'month_order_count'],
                'column': t.c.staffNo,
                'table': d,
                'join_column': d.c.saleno}
        }
        query = mdb.filter_join(t, joins, request, ['name'])
        qssoCodes = None
        if qssoCode:
            qssoCodes = qssoCode.split(",")
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org_id = u.get('organization_id')
            dcodes = orgcache.get_dcodes(org_id, qssoCodes)
            if dcodes and len(dcodes) > 0:
                query = query.where(t.c.ssoCode.in_(dcodes))
            else:
                ccodes = orgcache.get_ccodes(org_id, qcomCode)
                if ccodes and len(ccodes) > 0:
                    query = query.where(t.c.comCode.in_(ccodes))
        else:
            if qcomCode:
                query = query.where(c.c.comCode == qcomCode)
            if qssoCodes and len(qssoCodes) > 0:
                query = query.where(t.c.ssoCode.in_(qssoCodes))
        if q:
            query = query.where(t.c.name.like(LF.format(q)))
        if qstaffNo:
            query = query.where(t.c.staffNo.like(LF.format(qstaffNo)))
        if qdutyName:
            query = query.where(t.c.dutyName.like(LF.format(qdutyName)))
        rs = mdb.paginate_data(query, request, response)
        datas = rows2data(rs, amssales, joins)
        for d in datas:
            if d.get('agStatus') == 1:
                sale_no = d['staffNo']
                d['leadstatistics'] = stat_sales_active_leads(db, sale_no,
                                                              datetime.now())
        return datas


@hug.object.http_methods('/{id}')
class AmssalesInst(AmssalesMixin, object):
    def get(self, id: str):
        sales = self.get_amssales(id)
        return sales


@hug.get('/getAmsSalesTreeList')
def query_amssales_tree_list(request, response, ssoCode: str = None):
    sales_list = []
    if ssoCode:
        t = amssales.alias('t')
        query = select([t.c.staffNo, t.c.name])
        query = query.where(t.c.ssoCode == ssoCode)
        query = query.where(t.c.agStatus == 1)
        query = query.where(t.c.dutyName.like('%总监%'))
        query = query.order_by(t.c.name.asc())
        rs = mdb.execute(query)
        for r in rs:
            sales_list.append({'key': r[0], 'code': r[0], 'name': r[1]})
    return {'ssoCode': ssoCode, 'list': sales_list}


@hug.get('/getAmsSSOTreeList')
def query_amssso_tree_list(request, response):
    cso_list = []
    q1 = select([amscsos.c.comCode, amscsos.c.comName])
    rs1 = mdb.execute(q1.order_by(amscsos.c.comName.asc()))
    for r in rs1:
        d = {'key': 'CSO-' + r[0], 'code': r[0], 'name': r[1]}
        cso_list.append(d)

    sso_list = []
    q2 = select([amsssos.c.ssoCode, amsssos.c.ssoName, amsssos.c.comCode])
    rs2 = mdb.execute(q2.order_by(amsssos.c.ssoName.asc()))
    for r in rs2:
        d = {'key': 'SSO-' + r[0], 'code': r[0], 'name': r[1], 'comCode': r[2]}
        sso_list.append(d)

    sales_list = []
    q3 = select([amssales.c.staffNo, amssales.c.name, amssales.c.ssoCode])
    q3 = q3.where(amssales.c.agStatus == 1)
    q3 = q3.where(amssales.c.dutyName.like('%总监%'))
    rs3 = mdb.execute(q3.order_by(amssales.c.name.asc()))
    for r in rs3:
        d = {'key': r[0], 'staffNo': r[0], 'name': r[1], 'ssoCode': r[2]}
        sales_list.append(d)

    sales_dict = group_by(sales_list, 'ssoCode')
    for d in sso_list:
        ssoCode = d['code']
        if ssoCode in sales_dict.keys():
            d['children'] = sales_dict[ssoCode]

    sso_dict = group_by(sso_list, 'comCode')
    for d in cso_list:
        comCode = d['code']
        if comCode in sso_dict.keys():
            d['children'] = sso_dict[comCode]

    return cso_list


def group_by(datas, name):
    m = {}
    for d in datas:
        k = d.pop(name)
        if k in m.keys():
            ls = m[k]
            ls.append(d)
        else:
            ls = []
            ls.append(d)
            m[k] = ls
    return m


def query_all_amssales():
    rs = mdb.fetch_all(amssales, ['name'])
    amscso_dict = {}
    for r in rs:
        code = r[1]
        amscso_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return amscso_dict


def init_amssales():
    mapping = [{'name': 'staffNo', 'title': 'staffno', 'type': 'Text'},
               {'name': 'name', 'title': 'name', 'type': 'Text'},
               {'name': 'sex', 'title': 'sex', 'type': 'Text'},
               {'name': 'birthday', 'title': 'birthday', 'type': 'Text'},
               {'name': 'idno', 'title': 'idno', 'type': 'Text'},
               {'name': 'phone', 'title': 'phone', 'type': 'Text'},
               {'name': 'email', 'title': 'email', 'type': 'Text'},
               {'name': 'address', 'title': 'address', 'type': 'Text'},
               {'name': 'channel', 'title': 'channel', 'type': 'Text'},
               {'name': 'comCode', 'title': 'comcode', 'type': 'Text'},
               {'name': 'ssoCode', 'title': 'ssocode', 'type': 'Text'},
               {'name': 'dutyDeg', 'title': 'dutyDeg', 'type': 'Text'},
               {'name': 'dutyName', 'title': 'dutyname', 'type': 'Text'},
               {'name': 'joinDate', 'title': 'joinDate', 'type': 'Number'},
               {'name': 'agStatus', 'title': 'agStatus', 'type': 'Number'},
               {'name': 'startMthnum', 'title': 'startMthnum',
                'type': 'Number'},
               {'name': 'quafNo', 'title': 'quafno', 'type': 'Text'},
               {'name': 'quafStartDate', 'title': 'quafstartDate',
                'type': 'Number'},
               {'name': 'quafEndDate', 'title': 'quafendDate',
                'type': 'Number'},
               {'name': 'abossnum', 'title': 'abossnum', 'type': 'Text'},
               {'name': 'bbossnum', 'title': 'bbossnum', 'type': 'Text'},
               {'name': 'cbossnum', 'title': 'cbossnum', 'type': 'Text'},
               {'name': 'dbossnum', 'title': 'dbossnum', 'type': 'Text'},
               {'name': 'ibossnum', 'title': 'ibossnum', 'type': 'Text'}]
    mdb.connect()
    collect = CollectService()
    collect.import_from_csv('AMS_AMSSALES_201805211547.csv', mdb,
                            amssales, ['staffno'], mapping)
    mdb.close()
