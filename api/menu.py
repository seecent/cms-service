
from __future__ import absolute_import
import hug

from api.auth.user import check_current_user
from config import db, menus as conf_menus
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201,\
    HTTPInternalServerError
from log import logger
from models.auth.menu import menus
from models.auth.role import rolemenus
from models import bind_dict, change_dict, row2dict, rows2data
from services.oprationlog import OprationLogService
from sqlalchemy.sql import select, or_, func


IGNORES = {'last_modifed'}
log = OprationLogService()


class MenuMixin(object):

    def get_menu(self, id):
        t = menus.alias('m')
        row = db.get(t, id)
        if row:
            return row2dict(row, menus)
        else:
            raise HTTPNotFound(title="no_menu")


@hug.object.urls('')
class Menus(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = menus.alias('m')
        joins = {'parent': {
                 'select': 'name',
                 'table': menus.alias('p')}
                 }
        query = db.filter_join(t, joins, request, ['code'])
        if q:
            q = '%{}%'.format(q)
            filters = or_(t.c.code.like(q),
                          t.c.name.like(q),
                          t.c.path.like(q))
            query = query.where(filters)
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)

        return rows2data(rows, menus, joins, IGNORES)

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        parent_id = body['parent_id']
        menu = bind_dict(menus, body)
        menu = bind_menu(menu, parent_id)
        d = db.save(menus, menu)
        log.create(result['user'], request, d.get('id'),
                   'menus', menu, db)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        try:
            tx = db.begin()
            for id in ids:
                db.execute(rolemenus.delete().where(rolemenus.c.menu_id == id))
                db.set_null_on_delete(menus, 'parent_id', id)
                db.delete(menus, id)
            tx.commit()
        except BaseException:
            logger.exception('<delete> menus: ' + str(ids) + ', error: ')
            raise HTTPInternalServerError(title='delete_menus_error')

        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class MenuInst(MenuMixin, object):

    def get(self, id: int):
        menu = self.get_menu(id)
        return menu

    def patch(self, request, response, id: int, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        menu = self.get_menu(id)
        if menu:
            parent_id = body['parent_id']
            data = change_dict(menus, menu, body)
            data = change_menu(data, menu, parent_id)
            db.update(menus, data)
            log.update(result['user'], request, id,
                       'menus', menu, data, db)
        return menu

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            current_user = result['user']
            logger.info('<delete> menu[' + str(id) +
                        '] user: ' + current_user['username'])
            tx = db.begin()
            db.execute(rolemenus.delete().where(rolemenus.c.menu_id == id))
            db.set_null_on_delete(menus, 'parent_id', id)
            db.delete(menus, id)
            tx.commit()
            log.delete(current_user, request, id, 'menus', db)
        except BaseException:
            tx.rollback()
            raise HTTPInternalServerError(title='delete_menu_error')

        return {'code': 0, 'message': 'OK'}


def bind_menu(menu, parent_id):
    """
    自动赋值菜单级别grade值和菜单id值，grade值为上级菜单grade + 1，
    菜单id值为同级别菜单id最大值+1。

    :param menu: 菜单dict。
    :param parent_id: 上级菜单ID。
    :returns: menu, 菜单dict。
    """
    parent = None
    max_menuid = 0
    t = menus.alias('m')
    query = select([func.max(t.c.id)]).where(t.c.parent_id == parent_id)
    row = db.fetch_one(query)
    if row:
        max_menuid = int(row[0])
    if parent_id is not None:
        parent_id = int(parent_id)
        row = db.get(t, parent_id)
        if row:
            parent = row2dict(row, menus)
            if max_menuid == 0:
                menu['id'] = parent_id * 100 + 1
            else:
                menu['id'] = max_menuid + 1
            menu['grade'] = parent['grade'] + 1
    else:
        menu['id'] = max_menuid + 1
        menu['grade'] = 1

    # 根据path自动生成URL
    menu_path = menu.get('path')
    if 'http' in menu_path:
        # 通过URL集成外部系统方式菜单不处理
        pass
    else:
        if parent:
            menu['url'] = parent['url'] + '/' + menu_path
        else:
            menu['url'] = '/' + menu_path

    return menu


def change_menu(data, menu, parent_id):
    """
    自动赋值菜单级别grade值和菜单id值，grade值为上级菜单grade + 1，
    菜单id值为同级别菜单id最大值+1。

    :param menu: 菜单dict。
    :param parent_id: 上级菜单ID。
    :returns: menu, 菜单dict。
    """
    parent = None
    if parent_id is not None:
        parent_id = int(parent_id)
        row = db.get(menus, parent_id)
        if row:
            parent = row2dict(row, menus)
            data['grade'] = parent['grade'] + 1
    else:
        data['grade'] = 1

    # 根据path自动生成URL
    menu_path = data.get('path')
    if menu_path is None:
        menu_path = menu.get('path')
    if menu_path is None:
        return data
    if 'http' in menu_path:
        # 通过URL集成外部系统方式菜单不处理
        pass
    else:
        if parent:
            data['url'] = parent['url'] + '/' + menu_path
        else:
            data['url'] = '/' + menu_path

    return data


def init_menus():
    db.connect()
    menu_dict = {}
    rows = db.execute(select([menus.c.id])).fetchall()
    for r in rows:
        menu_dict[r[0]] = r[0]

    # 初始化菜单
    init_menu_lists(db, menu_dict, None, 1, conf_menus)

    # 删除无效菜单
    for k, v in menu_dict.items():
        db.execute(rolemenus.delete().where(rolemenus.c.menu_id == k))
        db.delete(menus, k)
    db.close()


def init_menu_lists(db, menu_dict, parent, grade, menu_list):
    now = datetime.now()
    order_no = 0
    for m in menu_list:
        order_no += 1
        mid = None
        code = ''
        parent_id = None
        parent_code = ''
        parent_url = ''
        if parent is not None:
            parent_id = parent['id']
            parent_code = parent['code']
            parent_url = parent['url']
        if grade == 1:
            mid = order_no
            code = 'M' + str(mid)
        elif grade == 2:
            mid = parent_id * 100 + order_no
            code = parent_code + '.M' + str(parent_id * 10 + order_no)
        elif grade == 3:
            mid = parent_id * 10000 + order_no
            code = parent_code + '.M' + str(mid)
        else:
            mid = parent_id * 1000000 + order_no
            code = parent_code + '.M' + str(mid)
        name = m.get('name')
        path = m.get('path')
        icon = m.get('icon')
        target = m.get('target')
        permissions = m.get('permissions', None)
        if permissions and type(permissions) == list:
            permissions = ','.join(str(p) for p in permissions)
        url = ''
        if 'http' in path:
            url = path
        else:
            url = parent_url + '/' + path
        data = {'id': mid, 'code': code, 'name': name,
                'icon': icon, 'path': path, 'url': url,
                'grade': grade, 'order_no': order_no,
                'parent_id': parent_id, 'target': target,
                'permissions': permissions,
                'created_date': now, 'last_modifed': now}
        if menu_dict.get(mid):
            menu_dict.pop(mid)
            db.update(menus, data)
        else:
            db.insert(menus, data)

        children = m.get('children')
        if children:
            data['id'] = mid
            init_menu_lists(db, menu_dict, data, grade + 1, children)
