
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201
from models.constant import constants
from models.location import locations, LocationType
from models import bind_dict, change_dict, row2dict, rows2data
from sqlalchemy.sql import select, and_, or_


IGNORES = {'last_modifed'}
NATIONS = []


class LocationMixin(object):
    def get_location(self, id):
        t = locations.alias('o')
        row = db.get(t, id)
        if row:
            return row2dict(row, locations)
        else:
            raise HTTPNotFound(title="no_location")


@hug.object.urls('')
class Locations(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = locations.alias('l')
        joins = {'parent': {
                 'select': 'name',
                 'table': locations.alias('p')}
                 }
        query = db.filter_join(t, joins, request, ['-created_date'])
        if q:
            q = '%{}%'.format(q)
            filters = or_(t.c.name.like(q),
                          t.c.short_name.like(q))
            query = query.where(filters)
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)

        return rows2data(rows, locations, joins, IGNORES)

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        org = bind_dict(locations, body)
        d = db.save(locations, org)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(locations, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class LocationInst(LocationMixin, object):
    def get(self, id: int):
        org = self.get_location(id)
        return org

    def patch(self, id: int, body):
        org = self.get_location(id)
        if org:
            org = change_dict(locations, org, body)
            db.update(locations, org)
        return org

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        db.delete(locations, id)
        return {'code': 0, 'message': 'OK'}


def query_all_locations_dict(db, location_type, key_name):
    '''查询地域信息。
        :param: location_type: 地域类型
        :param: key_name: key名称
        :retrun: 地域信息字典
    '''
    location_dict = {}
    t = locations.alias('t')
    query = select([t.c.id, t.c.code, t.c.name, t.c.short_name])
    query = query.where(t.c.type == location_type)
    rows = db.execute(query).fetchall()
    for r in rows:
        data = {'id': r[0], 'code': r[1],
                'name': r[2], 'short_name': r[3]}
        key = data[key_name]
        location_dict[key] = data
    return location_dict


def init_locations():
    '''初始化地地域信息
    '''
    db.connect()
    count = db.count(locations)
    if count > 1:
        db.close()
        return
    now = datetime.now()
    province = LocationType.Province
    city = LocationType.City
    district = LocationType.District
    provinces = init_location_datas(db, now, province, None, '%0000')
    for p in provinces:
        pcode = p['code'][0: 2]
        cities = init_location_datas(db, now, city, p, pcode + '%00')
        for c in cities:
            ccode = c['code'][0: 4]
            init_location_datas(db, now, district, c, ccode + '%')
    db.close()


def init_location_datas(db, now, location_type, parent, q):
    datas = []
    t = constants.alias('c')
    query = select([t.c.code, t.c.name])
    query = query.where(and_(t.c.const_type == 'location',
                             t.c.code.like(q)))
    rows = db.execute(query).fetchall()
    parent_id = None
    parent_code = None
    if parent is not None:
        parent_id = parent['id']
        parent_code = parent['code']
    for r in rows:
        code = r[0]
        if code == parent_code:
            continue
        name = r[1]
        data = {'id': int(code),
                'code': code,
                'name': name,
                'short_name': short_name(name, location_type),
                'type': location_type,
                'parent_id': parent_id,
                'created_date': now}
        db.execute(locations.insert(), data)
        datas.append(data)
    return datas


NATIONS = ['壮族', '藏族', '蒙族', '回族', '苗族',
           '羌族', '侗族', '彝族', '满族', '瑶族',
           '傣族', '畲族', '佤族', '白族', '土族',
           '怒族', '各族', '蒙古族', '土家族',
           '朝鲜族', '布依族', '纳西族', '哈尼族', '仡佬族',
           '拉祜族', '布朗族', '水族', '裕固族', '傈僳族',
           '仫佬族', '哈萨克族', '达斡尔族', '普米族',
           '保安族', '东乡族', '撒拉族', '毛南族', '独龙族',
           '景颇族', '鄂温克族']


def short_name(name, location_type):
    if location_type == LocationType.Province:
        short_name = name
        if '省' in name:
            short_name = name.replace('省', '')
        elif '市' in name:
            short_name = name.replace('市', '')
        elif '内蒙古' in name:
            short_name = '内蒙古'
        elif '西藏' in name:
            short_name = '西藏'
        elif '新疆' in name:
            short_name = '新疆'
        elif '宁夏' in name:
            short_name = '宁夏'
        elif '广西' in name:
            short_name = '广西'
        elif '香港' in name:
            short_name = '香港'
        elif '澳门' in name:
            short_name = '澳门'
    elif location_type == LocationType.City:
        short_name = name.replace('市', '')
        short_name = short_name.replace('地区', '')
        short_name = short_name.replace('自治州', '')
        if len(short_name) > 3:
            for n in NATIONS:
                short_name = short_name.replace(n, '')
    elif location_type == LocationType.District:
        short_name = name.replace('区', '')
        short_name = short_name.replace('自治', '')
        if len(short_name) > 3:
            for n in NATIONS:
                short_name = short_name.replace(n, '')
        if len(short_name) > 2:
            short_name = short_name.replace('县', '')
            short_name = short_name.replace('市', '')
            short_name = short_name.replace('盟', '')
    return short_name
