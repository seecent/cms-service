
from __future__ import absolute_import
import hug


from api.ams.amscso import query_all_amscso_list
from api.ams.amssso import query_all_amssso_list
from api.location import query_all_locations_dict
from api.auth.user import check_sysadmin, check_current_user,\
    query_current_user
from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201,\
    HTTPInternalServerError
from log import logger
from models.organization import organizations, OrgType
from models.location import LocationType
from models import bind_dict, change_dict, row2dict, rows2data
from services.oprationlog import OprationLogService
from sqlalchemy.sql import select, or_


IGNORES = {'last_modifed'}
log = OprationLogService()


class OrganizationMixin(object):
    def get_organization(self, id):
        t = organizations.alias('o')
        row = db.get(t, id)
        if row:
            return row2dict(row, organizations, IGNORES)
        else:
            raise HTTPNotFound(title="no_organization")


@hug.object.urls('')
class Organizations(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = organizations.alias('o')
        p = organizations.alias('p')
        joins = {'parent': {
                 'select': 'name',
                 'table': p}
                 }
        query = db.filter_join(t, joins, request, ['-created_date'])
        if q:
            q = '%{}%'.format(q)
            filters = or_(t.c.code.like(q),
                          t.c.name.like(q),
                          t.c.short_name.like(q))
            query = query.where(filters)
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org = u.get('org')
            if org is not None:
                w = or_(t.c.id == org['id'],
                        t.c.parent_id == org['id'],
                        p.c.parent_id == org['id'])
                query = query.where(w)
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)

        return rows2data(rows, organizations, joins, IGNORES)

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        org = bind_dict(organizations, body)
        d = db.save(organizations, org)
        log.create(result['user'], request, d.get('id'),
                   'organizations', org, db)
        return d

    @hug.object.delete()
    def delete(self, request, response):
        ids = request.params.get('ids')
        try:
            tx = db.begin()
            for id in ids:
                if id != 1:
                    db.set_null_on_delete(organizations, 'parent_id', id)
                    db.delete(organizations, id)
            tx.commit()
        except BaseException:
            logger.exception('<delete> organizations: ' + str(ids) +
                             ', error: ')
            raise HTTPInternalServerError(title='delete_organizations_error')

        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class OrganizationInst(OrganizationMixin, object):
    def get(self, id: int):
        org = self.get_organization(id)
        return org

    def patch(self, request, response, id: int, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        org = self.get_organization(id)
        if org:
            data = change_dict(organizations, org, body)
            db.update(organizations, data)
            log.update(result['user'], request, id,
                       'organizations', org, data, db)
            org = data
        return org

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        oid = str(id)
        try:
            current_user = result['user']
            logger.info('<delete> organization[' + oid +
                        '] user: ' + current_user['username'])
            if id != 1:
                tx = db.begin()
                db.set_null_on_delete(organizations, 'parent_id', id)
                db.delete(organizations, id)
                tx.commit()
                log.delete(current_user, request, id, 'organizations', db)
        except BaseException:
            logger.exception('<delete> organization[' + oid + '] error: ')
            tx.rollback()
            raise HTTPInternalServerError(title='delete_organization_error')
        return {'code': 0, 'message': 'OK'}


@hug.get('/getAllOrgs')
def query_all_orgs(request, response, parent_id=None):
    orgs = []
    t = organizations.alias('t')
    query = select([t.c.id, t.c.code,
                    t.c.name,
                    t.c.parent_id])
    if parent_id:
        query = query.where(t.c.parent_id == parent_id)
    else:
        p = organizations.alias('p')
        join = t.outerjoin(p, t.c.parent_id == p.c.id)
        query = query.select_from(join)
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org = u.get('org')
            if org is not None:
                w = or_(t.c.id == org['id'],
                        t.c.parent_id == org['id'],
                        p.c.parent_id == org['id'])
                query = query.where(w)
    rows = db.execute(query).fetchall()
    for r in rows:
        orgs.append({'id': r[0], 'code': r[1],
                     'name': r[2], 'parent_id': r[3]})
    return orgs


@hug.get('/syncOrganizations')
def sync_organizations(request, response):
    try:
        logger.info('<sync_organizations> start...')
        init_organizations()
        logger.info('<sync_organizations> end!')
    except BaseException:
        logger.exception('<sync_organizations> error: ')
    return {'code': 0, 'message': 'OK'}


def get_organization(id):
    """
    获取组织机构信息
    """
    if id is None:
        return None
    t = organizations.alias('t')
    query = select([t.c.code, t.c.name, t.c.org_type, t.c.parent_id])
    query = query.where(t.c.id == id)
    row = db.fetch_one(query)
    if row:
        ccode = None   # 公司编码
        cname = None   # 公司名称
        dcode = None   # 部门编码
        dname = None   # 部门名称
        org_type = row[2]
        if org_type == OrgType.Department:
            dcode = row[0]
            dname = row[1]
            parent_id = row[3]
            if parent_id is not None:
                query = query.where(t.c.id == parent_id)
                row = db.fetch_one(query)
                if row:
                    if row[2] != OrgType.Department:
                        ccode = row[0]
                        cname = row[1]
        else:
            ccode = row[0]
            cname = row[1]
        return {'id': id, 'org_type': org_type,
                'ccode': ccode, 'cname': cname,
                'dcode': dcode, 'dname': dname}
    return None


def query_all_organizations(db):
    orgs = []
    t = organizations.alias('t')
    query = select([t.c.id, t.c.code, t.c.name,
                    t.c.province, t.c.city])
    rows = db.execute(query).fetchall()
    for r in rows:
        orgs.append({'id': r[0], 'code': r[1], 'name': r[2],
                     'province': r[3], 'city': r[4]})
    return orgs


def init_organizations():
    '''初始化组织机构
    '''
    now = datetime.now()
    query = select([organizations.c.id]).\
        where(organizations.c.short_name == '中信保诚')
    db.connect()
    row = db.fetch_one(query)
    if row:
        rootid = row[0]
    else:
        name = '中信保诚人寿保险有限公司'
        root = {'name': name,
                'code': '1001',
                'short_name': '中信保诚',
                'org_type': OrgType.GroupCompany,
                'telephone': '（010）85878699',
                'fax': '（010）85878577',
                'email': 'Eservice@citicpru.com.cn',
                'postcode': '100020',
                'address': '北京市朝阳区东三环中路1号环球金融中心',
                'created_date': now, 'last_modifed': now}

        rootid = db.insert(organizations, root)
    if rootid:
        org_dict = {}
        orgs = query_all_organizations(db)
        for o in orgs:
            org_dict[o['code']] = o
        province = LocationType.Province
        province_dict = query_all_locations_dict(db, province, 'name')
        city = LocationType.City
        city_dict = query_all_locations_dict(db, city, 'short_name')
        companies = sync_companies(db, rootid, OrgType.Company, None, '分公司',
                                   org_dict, province_dict, city_dict, now)
        for com in companies:
            sync_companies(db, com['id'], OrgType.Branch, com['province'],
                           '支公司', org_dict, province_dict, city_dict, now)
            # sync_companies(db, com['id'], OrgType.Branch, com['province'],
            #                '营销服务部', org_dict, province_dict, city_dict, now)

        sync_departments(db, org_dict, now)
        province_dict.clear()
        city_dict.clear()
        org_dict.clear()
    db.close()


def sync_companies(db, parent_id, org_type, province, q,
                   org_dict, province_dict, city_dict, now):
    '''同步分公司或支公司
    '''
    logger.info('<sync_companies> province: ' + str(province) + ', q=' + q)
    companies = []
    csos = query_all_amscso_list(province, q)
    logger.info('<sync_companies> province: ' + str(province) +
                ', companies count: ' + str(len(csos)))
    for d in csos:
        code = d['comCode']
        name = d['comName']
        org = org_dict.get(code)
        if org is None:
            logger.info('<sync_companies> add company[' + code + ']: ' + name)
            province = d.get('proviceNo')
            city = d.get('cityNo')
            location_id = None
            if OrgType.Company == org_type:
                if province is not None:
                    location = province_dict.get(province)
                    if location:
                        location_id = location['id']
            elif OrgType.Branch == org_type:
                if city is not None:
                    location = city_dict.get(city)
                    if location:
                        location_id = location['id']
            org = {'name': name,
                   'code': code,
                   'short_name': d.get('comShortName'),
                   'parent_id': parent_id,
                   'org_type': org_type,
                   'telephone': d.get('phone'),
                   'fax': d.get('fax'),
                   'postcode': d.get('zipCode'),
                   'province': province,
                   'city': city,
                   'address': d.get('address'),
                   'location_id': location_id,
                   'created_date': now}
            orgid = db.insert(organizations, org)
            org['id'] = orgid
            org_dict[code] = org
        companies.append(org)
    return companies


def sync_departments(db, org_dict, now):
    '''同步部门
    '''
    logger.info('<sync_departments> start...')
    ssos = query_all_amssso_list(None)
    logger.info('<sync_departments> departments count: ' + str(len(ssos)))
    for d in ssos:
        code = d['ssoCode']
        name = d['ssoName']
        com_code = d['comCode']
        porg = org_dict.get(com_code)
        org = org_dict.get(code)
        if org is None and porg is not None:
            logger.info('<sync_departments> add department[' + code + ']: ' +
                        name)
            org = {'name': name,
                   'code': code,
                   'parent_id': porg['id'],
                   'org_type': OrgType.Department,
                   'province': porg.get('province'),
                   'city': porg.get('city'),
                   'created_date': now}
            orgid = db.insert(organizations, org)
            org['id'] = orgid
            # org_dict[code] = org
    logger.info('<sync_departments> end!')
