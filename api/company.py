
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from models.company import companies
from models.organization import organizations, OrgType
from models.rawleads import rawleads
from models.viableleads import viableleads
from models import rows2dict, row2dict, change_dict, bind_dict
from sqlalchemy.sql import select, or_
from falcon import HTTPNotFound, HTTP_201, HTTP_204

IGNORES = {'created_date', 'last_modifed'}


class CompanyMixin(object):
    def get_company(self, id):
        row = db.get(companies, id)
        if row:
            return row2dict(row, companies)
        else:
            raise HTTPNotFound(title="no_company")


@hug.object.urls('')
class Companies(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        try:
            t = companies.alias('c')
            query = db.filter(companies, request, ['name'])
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, companies)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        company = bind_dict(companies, body)
        d = db.save(companies, company)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(companies, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class CompanyInst(CompanyMixin, object):
    def get(self, id: int):
        t = self.get_company(id)
        return t

    def patch(self, id: int, body):
        t = self.get_company(id)
        if t:
            t = change_dict(companies, t, body)
            db.update(companies, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        db.delete(companies, id)


def query_all_companies_dict(db):
    rs = db.fetch_all(companies, ['id'])
    clean_ids = []
    company_dict = {}
    for r in rs:
        code = r[1]
        if company_dict.get(code) is None:
            data = {'id': r[0], 'code': code, 'name': r[2]}
            company_dict[code] = data
        else:
            clean_ids.append(r[0])
    if len(clean_ids) > 0:
        print(clean_ids)
        for cid in clean_ids:
            db.execute(rawleads.update().where(
                rawleads.c.company_id == cid).values({'company_id': None}))
            db.execute(viableleads.update().where(
                viableleads.c.company_id == cid).values({'company_id': None}))
            db.delete(companies, cid)
    return company_dict


def init_companies():
    now = datetime.now()
    db.connect()
    org_dict = {}
    com_dict = query_all_companies_dict(db)
    t = organizations.alias('t')
    query = select([t.c.id, t.c.code, t.c.parent_id,
                    t.c.name, t.c.short_name,
                    t.c.province, t.c.city])
    query = query.where(or_(t.c.org_type == OrgType.Company,
                            t.c.org_type == OrgType.Branch))
    rows = db.execute(query).fetchall()
    for r in rows:
        org_id = r[0]
        org_dict[org_id] = r[1]
    for r in rows:
        code = r[1]
        parent_id = r[2]
        memo = code
        if parent_id is not None:
            parent_code = org_dict.get(parent_id)
            if parent_code:
                memo = parent_code + '@' + code
        com = com_dict.get(code)
        if com is None:
            db.insert(companies, {'code': code, 'name': r[3],
                                  'short_name': r[4], 'memo': memo,
                                  'created_date': now})
        else:
            db.update(companies, {'id': com['id'], 'code': code, 'name': r[3],
                                  'short_name': r[4], 'memo': memo,
                                  'last_modifed': now})
    db.close()
