
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201,\
    HTTPInternalServerError
from models.auth.menu import menus
from models.auth.user import users
from models.auth.role import roles, rolemenus, userroles
from models import row2dict, rows2dict, rows2data, bind_dict, change_dict
from sqlalchemy.sql import select, and_


IGNORES = {'date_created', 'last_updated', 'created_date', 'last_modifed'}


class RoleMixin(object):

    def get_role(self, id):
        row = db.get(roles, id)
        if row:
            return row2dict(row, roles, IGNORES)
        else:
            raise HTTPNotFound(title="no_role")


@hug.object.urls('')
class Roles(object):
    '''角色管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''角色
        '''
        try:
            t = roles.alias('d')
            query = db.filter(roles, request)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, roles, IGNORES)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        角色REST API Post接口
        :param: id int 部门ID
        :return: json
        '''
        role = bind_dict(roles, body)
        role['authority'] = 'ROLE_' + role['code'].upper()
        d = db.save(roles, role)
        return d


@hug.object.http_methods('/{id}')
class RoleInst(RoleMixin, object):

    def get(self, id: int):
        t = self.get_role(id)
        return t

    def patch(self, id: int, body):
        t = self.get_role(id)
        if t:
            role = change_dict(roles, t, body)
            if role.__contains__('code'):
                role['authority'] = 'ROLE_' + role['code'].upper()
            else:
                role.pop('authority')
            db.update(roles, role)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除角色
        :param: id int 角色ID
        :return:
        '''
        try:
            tx = db.begin()
            db.execute(userroles.delete().where(userroles.c.role_id == id))
            db.execute(rolemenus.delete().where(rolemenus.c.role_id == id))
            db.delete(roles, id)
            tx.commit()
        except BaseException:
            tx.rollback()
            raise HTTPInternalServerError(title='delete_role_error')

        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}/users')
class RoleUser(RoleMixin, object):

    def get(self, request, response, id: int):
        query = db.query(users).select_from(users.join(
            userroles, userroles.c.user_id == users.c.id)).where(
            userroles.c.role_id == id)
        rs = db.paginate_data(query, request, response)
        return rows2dict(rs, users)


@hug.object.http_methods('/{id}/menus')
class RoleMenu(RoleMixin, object):

    def get(self, id: int):
        t = rolemenus.alias('r')
        joins = {'menu': {
                 'select': ['id', 'code', 'name'],
                 'table': roles.alias('m')}}
        query = db.filter_join(t, joins, None)
        query = query.where(t.c.role_id == id)
        rows = db.execute(query).fetchall()
        if rows:
            return rows2data(rows, t, joins, IGNORES)
        else:
            return []

    def patch(self, id: int, body):
        tx = db.begin()
        try:
            menu_ids = body.get('menuIds', [])
            old_menu_ids = []
            query = select([rolemenus.c.role_id, rolemenus.c.menu_id])
            query = query.where(rolemenus.c.role_id == id)
            rows = db.execute(query).fetchall()
            for r in rows:
                old_menu_ids.append(r[1])
            now = datetime.now()
            for mid in menu_ids:
                if mid in old_menu_ids:
                    old_menu_ids.remove(mid)
                else:
                    data = {'role_id': id, 'menu_id': mid,
                            'created_date': now, 'last_modifed': now}
                    db.execute(rolemenus.insert(), data)
            for mid in old_menu_ids:
                filter = and_(rolemenus.c.role_id == id,
                              rolemenus.c.menu_id == mid)
                db.execute(rolemenus.delete().where(filter))
            tx.commit()
        except BaseException:
            tx.rollback()
            raise HTTPInternalServerError(title='update_user_menu_error')

        return {'code': 0, 'message': 'OK'}


@hug.get('/getAllRoles')
def get_all_roles():
    role_list = []
    t = roles.alias('r')
    query = select([t.c.id, t.c.code, t.c.name])
    query = query.where(t.c.code != 'sysadmin')
    rows = db.execute(query).fetchall()
    for r in rows:
        role_list.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return role_list


@hug.get('/getAllUsers')
def get_all_users(request, response, q: str=None):
    id = request.params.get('id')
    t = users.alias('u')
    ur = userroles.alias('ur')
    query = db.query(t).select_from(t.join(
        ur, ur.c.user_id == t.c.id)).where(
        ur.c.role_id == id)
    sorts = request.params.get('sort', ['username'])
    query = db.order_by(t, query, sorts)
    rs = db.paginate_data(query, request, response)
    return rows2dict(rs, t)


def query_all_roles():
    rs = db.fetch_all(roles, ['name'])
    role_dict = {}
    for r in rs:
        code = r[3]
        role_dict[code] = {'id': r[0], 'code': code, 'name': r[4]}
    return role_dict


def init_roles():
    db.connect()
    count = db.count(roles)
    if count < 1:
        now = datetime.now()
        role1 = {'code': 'sysadmin',
                 'authority': 'ROLE_SYSTEM_ADMIN',
                 'name': '系统管理员',
                 'date_created': now,
                 'last_updated': now}
        role2 = {'code': 'admin',
                 'authority': 'ROLE_ADMIN',
                 'name': '管理员',
                 'date_created': now,
                 'last_updated': now}
        role3 = {'code': 'sales',
                 'authority': 'ROLE_SALES',
                 'name': '销售',
                 'date_created': now,
                 'last_updated': now}
        role1_id = db.insert(roles, role1)
        role2_id = db.insert(roles, role2)
        role3_id = db.insert(roles, role3)
        init_role_menus(db, role1_id, 'sysadmin')
        init_role_menus(db, role2_id, 'admin')
        init_role_menus(db, role3_id, 'sales')
    else:
        count = db.count(rolemenus)
        if count < 1:
            query = select([roles.c.id, roles.c.code])
            rows = db.execute(query).fetchall()
            for r in rows:
                init_role_menus(db, r[0], r[1])
    db.close()


def init_role_menus(db, role_id, role_code):
    now = datetime.now()
    db.execute(rolemenus.delete().where(rolemenus.c.role_id == role_id))
    query = select([menus.c.id, menus.c.url])
    rows = db.execute(query).fetchall()
    for r in rows:
        if role_code == 'sales' and 'system' in r[1]:
            continue
        elif role_code == 'admin' and 'system' in r[1]:
            continue
        data = {'role_id': role_id, 'menu_id': r[0],
                'created_date': now, 'last_modifed': now}
        db.execute(rolemenus.insert(), data)
