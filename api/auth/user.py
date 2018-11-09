from __future__ import absolute_import
import hug
from api.errorcode import ErrorCode
from datetime import datetime
from config import db, store
from falcon import HTTPNotFound, HTTP_204, HTTPForbidden, HTTP_201,\
    HTTPInternalServerError, HTTPMissingParam
from log import logger
from models import change_dict, row2dict, rows2data
from models.collection import collections
from models.monitorchart import monitorcharts
from models.auth.user import users, preferences, tokens, UserStatus,\
    TokenAction, gen_password, get_password, generate_token, parse_token
from models.auth.role import roles, userroles, rolemenus
from models.organization import organizations, OrgType
from models.operationlog import operationlogs
from models.auth.menu import menus
from services.oprationlog import OprationLogService
from sqlalchemy.sql import select, and_, or_
from sqlalchemy.exc import IntegrityError


IGNORES = {'hashed_password', 'salt'}
DF = "%Y-%m-%d %H:%M:%S"
log = OprationLogService()


class UserMixin(object):

    def get_user(self, id):
        row = db.get(users, id)
        if row:
            return row2dict(row, users, IGNORES)
        else:
            raise HTTPNotFound(title="no_user")


@hug.object.urls('')
class Users(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = users.alias('u')
        o = organizations.alias('o')
        joins = {'organization': {
                 'select': ['id', 'code', 'name'],
                 'table': o}}
        query = db.filter_join(t, joins, request, ['username'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org = u.get('org')
            if org is not None:
                w = or_(t.c.organization_id == org['id'],
                        o.c.parent_id == org['id'])
                query = query.where(w)
        if q:
            q = '%{}%'.format(q)
            filters = or_(t.c.username.like(q),
                          t.c.firstname.like(q),
                          t.c.lastname.like(q))
            query = query.where(filters)
        rs = db.paginate_data(query, request, response)
        user_list = rows2data(rs, t, joins, IGNORES)
        # 查询用户角色
        for u in user_list:
            u['roles'] = query_user_roles(u)
        return user_list

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        current_user = query_current_user(request)
        if current_user is None:
            return {'code': ErrorCode.UNAUTHORIZED.value,
                    'message': ErrorCode.UNAUTHORIZED.name}
        client_ip = request.remote_addr
        passwd = body.pop("password", "default_123")
        salt, passwd = gen_password(passwd)
        username = body['username']
        if not username:
            raise HTTPMissingParam(title='miss_param_user_username')
        enname = body.pop("enname", None)
        fullname = body.pop("fullname", None)
        mobile = body.pop("mobile", None)
        email = body.pop("email", None)
        roleIds = body.pop("roleIds", [])
        organization_id = body.pop("organization_id", None)
        department = body.pop("department", None)
        now = datetime.now()
        user = {'username': username,
                'enname': enname,
                'fullname': fullname,
                'mobile': mobile,
                'email': email,
                'salt': salt,
                'organization_id': organization_id,
                'department': department,
                'hashed_password': passwd,
                'date_created': now}
        logger.info('<post> create user[' + username + '], client_ip: ' +
                    client_ip)
        tx = db.begin()
        try:
            r = db.execute(users.insert(), user)
            user_id = r.inserted_primary_key[0]

            apitoken = generate_token(username)
            token = {'value': apitoken,
                     'user_id': user_id,
                     'created_date': now,
                     'last_modifed': now}
            db.execute(tokens.insert(), token)
            token = {'action': TokenAction.FEEDS,
                     'value': generate_token(username),
                     'user_id': user_id,
                     'created_date': now,
                     'last_modifed': now}
            db.execute(tokens.insert(), token)

            preference = {'language': 'zh-CN',
                          'timezone': 'sia/Shanghai',
                          'user_id': user_id,
                          'created_date': now,
                          'last_modifed': now}
            db.execute(preferences.insert(), preference)

            # 保存用户角色信息
            datas = []
            for role_id in roleIds:
                data = {'user_id': user_id, 'role_id': role_id,
                        'created_date': now, 'last_modifed': now}
                datas.append(data)
            db.execute(userroles.insert(), datas)

            tx.commit()
            user.pop('salt')
            user.pop('hashed_password')
            user['date_created'] = datetime.strftime(now, DF)
            log.create(current_user, request, user_id, 'users', user, db)
        except BaseException as e:
            logger.exception('<post> save user[' + username + '], error: ')
            tx.rollback()
            error_msg = ''
            if type(e) == IntegrityError:
                error_msg = str(e.orig)
            raise HTTPInternalServerError(title='save_user_error',
                                          description=error_msg)

        return user


@hug.object.http_methods('/{id}')
class UserInst(UserMixin, object):

    def get(self, id: int):
        u = self.get_user(id)
        u['roles'] = query_user_roles(u)
        return u

    def patch(self, request, response, id: int, body):
        current_user = query_current_user(request)
        if current_user is None:
            return {'code': ErrorCode.UNAUTHORIZED.value,
                    'message': ErrorCode.UNAUTHORIZED.name}
        user = self.get_user(id)
        if user:
            try:
                if 'roleIds' in body.keys():
                    body.pop("roleIds")
                excludes = ['hashed_password', 'salt', 'usertype',
                            'version', 'password', 'account_expired',
                            'account_locked', 'password_expired',
                            'password_errors', 'enabled']
                if 'username' not in body.keys():
                    excludes.append('username')
                u = change_dict(users, user, body, excludes)
                if 'status' in u and u['status'] == 'Active':
                    u['account_locked'] = False
                    u['enabled'] = True
                    u['password_errors'] = 0
                db.update(users, u)
                log.update(current_user, request, id, 'users', user, u, db)
            except BaseException:
                uid = str(id)
                logger.exception('<patch> update user[' + uid + '] error: ')
                raise HTTPInternalServerError(title='update_user_error')
        return user

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        logger.info('<delete> user: ' + str(id))
        current_user = query_current_user(request)
        if current_user is None:
            return {'code': ErrorCode.UNAUTHORIZED.value,
                    'message': ErrorCode.UNAUTHORIZED.name}
        user = self.get_user(id)
        if user:
            username = user['username']
            if username == 'lms_admin':
                raise HTTPForbidden(title='sysadmin_not_allow_delete')
            else:
                c = db.count(collections, collections.c.user_id == id)
                if c > 0:
                    u = {'id': id, 'status': UserStatus.Removed,
                         'last_updated': datetime.now()}
                    db.update(users, u)
                    return {'code': 0, 'message': 'OK'}
            try:
                tx = db.begin()
                db.execute(userroles.delete().where(userroles.c.user_id == id))
                stmt = preferences.delete().where(preferences.c.user_id == id)
                db.execute(stmt)
                db.execute(tokens.delete().where(tokens.c.user_id == id))
                stmt = uausermaps.delete().where(uausermaps.c.user_id == id)
                db.execute(stmt)
                db.set_null_on_delete(collections, 'user_id', id)
                db.set_null_on_delete(monitorcharts, 'user_id', id)
                db.set_null_on_delete(operationlogs, 'user_id', id)
                db.execute(users.delete().where(users.c.id == id))
                tx.commit()
                log.delete(current_user, request, id, 'users', db)
                return {'code': 0, 'message': 'OK'}
            except Exception:
                uid = str(id)
                logger.exception('<delete> user[' + uid + '] error: ')
                tx.rollback()
                raise HTTPInternalServerError(title='delete_user_error')


@hug.post('/update_password')
def update_password(username, password, new_password):
    logger.info('<update_password> user: ' + username)
    error_msg = '修改密码失败，原密码错误！'
    query = select([users.c.id,
                    users.c.salt,
                    users.c.hashed_password])
    query = query.where(users.c.username == username)
    row = db.fetch_one(query)
    if row:
        user_id = row[0]
        salt = row[1]
        hashed_password = row[2]
        if get_password(salt, hashed_password) == password:
            salt, passwd = gen_password(new_password)
            stmt = users.update().where(users.c.id == user_id).\
                values(salt=salt, hashed_password=passwd)
            db.execute(stmt)
            return {'code': 0, 'message': '密码修改成功！',
                    'id': user_id, 'username': username}
        else:
            raise HTTPInternalServerError(title='wrong_user_or_password',
                                          description=error_msg)
    else:
        raise HTTPInternalServerError(title='wrong_user_or_password',
                                      description=error_msg)


@hug.object.http_methods('/{id}/preference')
class UserPrefer(UserMixin, object):

    def get(self, id: int):
        query = select([preferences.c.id,
                        preferences.c.language,
                        preferences.c.timezone,
                        preferences.c.memo])
        query = query.where(preferences.c.user_id == id)
        row = db.fetch_one(query)
        if row:
            p = {'id': row[0],
                 'language': row[1],
                 'timezone': row[2],
                 'memo': row[3]}
            return p
        else:
            raise HTTPNotFound(title="no_user_preference")

    def patch(self, id: int, body):
        language = body['language']
        timezone = body['timezone']
        memo = body['memo']
        preference = {'language': language,
                      'timezone': timezone,
                      'memo': memo}
        stmt = preferences.update().where(preferences.c.user_id == id).\
            values(preference)
        db.execute(stmt)
        return preference


@hug.object.http_methods('/{id}/roles')
class UserRole(UserMixin, object):

    def get(self, id: int):
        t = userroles.alias('ur')
        joins = {'role': {
                 'select': ['id', 'name'],
                 'table': roles.alias('r')}}
        query = db.filter_join(t, joins, None)
        query = query.where(t.c.user_id == id)
        rows = db.execute(query).fetchall()
        if rows:
            return rows2data(rows, t, joins)
        else:
            return []

    def patch(self, id: int, body):
        tx = db.begin()
        try:
            role_ids = body.get('roleIds', [])
            if len(role_ids) > 0:
                old_role_ids = []
                query = select([userroles.c.role_id, userroles.c.user_id])
                query = query.where(userroles.c.user_id == id)
                rows = db.execute(query).fetchall()
                for r in rows:
                    old_role_ids.append(r[0])
                now = datetime.now()
                for rid in role_ids:
                    if rid in old_role_ids:
                        old_role_ids.remove(rid)
                    else:
                        data = {'user_id': id, 'role_id': rid,
                                'created_date': now, 'last_modifed': now}
                        db.execute(userroles.insert(), data)
                for rid in old_role_ids:
                    filter = and_(userroles.c.user_id == id,
                                  userroles.c.role_id == rid)
                    db.execute(userroles.delete().where(filter))
                tx.commit()
        except BaseException:
            uid = str(id)
            logger.exception('<patch> update user[' + uid + '] roles error: ')
            tx.rollback()
            raise HTTPInternalServerError(title='update_user_role_error')

        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}/menus')
class UserMenu(UserMixin, object):

    def get(self, id: int):
        user_menus = []
        role_ids = []
        u = self.get_user(id)
        if u is None:
            return []
        query = select([userroles.c.role_id, userroles.c.user_id])
        query = query.where(userroles.c.user_id == id)
        rows = db.execute(query).fetchall()
        for r in rows:
            role_ids.append(r[0])

        if role_ids and len(role_ids) > 0:
            t = rolemenus.alias('r')
            m = menus.alias('m')
            joins = {'menu': {
                     'select': ['id', 'code', 'name',
                                'path', 'icon',
                                'grade', 'parent_id',
                                'url', 'url_params',
                                'target'],
                     'table': m}}
            query = db.filter_join(t, joins, None)
            query = query.where(t.c.role_id.in_(role_ids))
            rows = db.execute(query.order_by(m.c.id.asc())).fetchall()
            menu_list = rows2data(rows, t, joins)
            # 去除重复记录
            merge_list = []
            menu_ids = []
            for d in menu_list:
                menu = d['menu']
                mid = menu['id']
                if mid not in menu_ids:
                    menu_ids.append(mid)
                    merge_list.append(menu)
            user_menus = menus2tree(None, 1, merge_list, u)
        return user_menus


def menus2tree(parent, grade, menu_list, user=None):
    """
    构造用户菜单Treedata。

    :param parent: 上级菜单。
    :param grade: 菜单级别。
    :param menu_list: 菜单列表。
    :returns: 用户菜单Treedata。
    """
    root_menus = []
    if parent is None:
        find_list = []
        for m in menu_list:
            if m['grade'] == grade:
                find_list.append(m)
        for m in find_list:
            root_menus.append(tree_menu_data(m, user))
        for p in find_list:
            menu_list.remove(p)
        for p in root_menus:
            menus2tree(p, grade + 1, menu_list, user)
    else:
        find_list = []
        parent_id = parent['id']
        for m in menu_list:
            if m['parent_id'] == parent_id:
                find_list.append(m)
        if len(find_list) > 0:
            children = []
            for m in find_list:
                children.append(tree_menu_data(m, user))
            parent['children'] = children
            for m in find_list:
                menu_list.remove(m)
            for p in children:
                menus2tree(p, grade + 1, menu_list, user)
    return root_menus


def tree_menu_data(m, user):
    menu_path = m['path']
    if menu_path is None or menu_path == '':
        menu_path = m['url']
    d = {'id': m['id'],
         'code': m['code'],
         'name': m['name'],
         'icon': m['icon'],
         'path': menu_path}
    url_params = m.get('url_params')
    if url_params is not None and url_params.strip() != '':
        if user:
            uid = str(user.get('id'))
            uname = user.get('username')
            orgid = str(user.get('organization_id'))
            path = m['path']
            url = m['url']
            url_params = url_params.format(uid=uid, uname=uname, orgid=orgid)
            d['url'] = url + url_params
            d['path'] = path + url_params
    if m['target'] is not None:
        d['target'] = m['target']
    return d


def check_sysadmin(user):
    """
    检查用户是否是系统管理员。

    :param user: 用户信息。
    :returns: True or False。
    """
    if user is None:
        return False
    for r in user['roles']:
        if r['code'] == 'sysadmin':
            return True
    return False


def check_admin(user):
    """
    检查用户是否是管理员。

    :param user: 用户信息。
    :returns: True or False。
    """
    if user is None:
        return False
    for r in user['roles']:
        if r['code'] == 'admin':
            return True
    return False


def check_user_roles(user, role_code):
    """
    检查用户是否包含指定编码角色。

    :param user: 用户信息。
    :param role_code: 角色编码。
    :returns: True or False。
    """
    if user is None:
        return False
    for r in user['roles']:
        if r['code'] == role_code:
            return True
    return False


def query_user_roles(user):
    """
    查询用户角色。

    :param user: 用户信息。
    :returns: 用户角色列表。
    """
    role_list = []
    t = userroles.alias('ur')
    joins = {'role': {
             'select': ['id', 'code', 'name'],
             'table': roles.alias('r')}}
    query = db.filter_join(t, joins, None, ['role.name'])
    query = query.where(t.c.user_id == user['id'])
    rows = db.execute(query).fetchall()
    if rows:
        user_roles = rows2data(rows, t, joins)
        for ur in user_roles:
            role_list.append(ur['role'])
    return role_list


def query_current_user(request):
    """
    查询当前登录用户信息。

    :param request: HTTP request对象。
    :returns: 当前登录用户dict。
    """
    token = request.get_header('apikey')
    if token:
        try:
            u = store.get(token)
            if u is not None:
                if 'roles' not in u:
                    u['roles'] = query_user_roles(u)
                    store.set(token, u)
                if 'org' not in u:
                    org_id = u.get('organization_id')
                    u['org'] = get_organization(org_id)
                    store.set(token, u)
            else:
                u = {}
                username = parse_token(token)
                query = select([users.c.id,
                                users.c.username,
                                users.c.fullname,
                                users.c.usertype,
                                users.c.organization_id,
                                users.c.department])
                query = query.where(users.c.username == username)
                row = db.fetch_one(query)
                if row:
                    user_id = row[0]
                    org_id = row[4]
                    u['id'] = user_id
                    u['user_id'] = user_id
                    u['username'] = row[1]
                    u['fullname'] = row[2]
                    u['usertype'] = row[3]
                    u['organization_id'] = org_id
                    u['department'] = row[5]
                    u['roles'] = query_user_roles(u)
                    u['org'] = get_organization(org_id)
                    store.set(token, u)
            return u
        except Exception as e:
            logger.exception('<query_current_user> error: ')
            return None


def check_current_user(request):
    current_user = query_current_user(request)
    if current_user is not None:
        return {'code': ErrorCode.OK.value,
                'message': ErrorCode.OK.name,
                'user': current_user}
    else:
        return {'code': ErrorCode.UNAUTHORIZED.value,
                'message': ErrorCode.UNAUTHORIZED.name}


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


def init_users():
    """
    初始化用户信息。
    """
    db.connect()
    count = db.count(users)
    if count < 1:
        create_user('lms_admin', 'admin_123', 'Administrator', '系统管理员',
                    '18699000001', 'lmsadmin@lms.com', '中信保诚', 'SysAdmin', db)
        create_user('admin', 'admin_123', 'admin', '管理员',
                    '18699000002', 'admin@lms.com', '中信保诚', 'Admin', db)
        create_user('mk0001', 'default_123', 'mk0001', '销售',
                    '18699000003', 'mk0001@lms.com', '销售部', 'Sales', db)
        create_user('yb0001', 'default_123', 'mk0001', '银保',
                    '18699000004', 'yb0001@lms.com', '银保部', 'Sales', db)
        create_user('sz0001', 'default_123', 'mk0001', '收展部',
                    '18699000005', 'sz0001@lms.com', '收展部', 'Sales', db)
    else:
        count = db.count(userroles)
        if count < 1:
            query = select([users.c.id, users.c.usertype])
            rows = db.execute(query).fetchall()
            for r in rows:
                init_user_role(db, r[0], r[1].name)
    db.close()


def create_user(username, password, enname, fullname, mobile, email,
                org, usertype, db):
    """
    创建用户账号。

    :param username: 用户名。
    :param password: 密码。
    :param mobile: 用户手机号。
    :param org: 用户部门名称。
    :param usertype: 用户类型。
    :param db: db。
    """
    now = datetime.now()
    salt, passwd = gen_password(password)
    user = {'username': username,
            'enname': enname,
            'fullname': fullname,
            'salt': salt, 'hashed_password': passwd,
            'usertype': usertype,
            'mobile': mobile,
            'email': email,
            'department': org,
            'date_created': now}

    user_id = db.insert(users, user)

    apitoken = generate_token(username)
    token = {'value': apitoken,
             'user_id': user_id,
             'created_date': now,
             'last_modifed': now}
    db.save(tokens, token)

    token = {'action': TokenAction.FEEDS,
             'value': generate_token(username),
             'user_id': user_id,
             'created_date': now,
             'last_modifed': now}
    db.save(tokens, token)

    preference = {'language': 'zh-CN',
                  'timezone': 'sia/Shanghai',
                  'user_id': user_id,
                  'created_date': now,
                  'last_modifed': now}
    db.save(preferences, preference)

    init_user_role(db, user_id, usertype)


def init_user_role(db, user_id, user_type):
    """
    初始化用户角色。

    :param user_id: 用户ID。
    :param user_type: 用户类型。
    """
    now = datetime.now()
    query = select([roles.c.id]).where(roles.c.code == user_type.lower())
    rows = db.execute(query).fetchall()
    for r in rows:
        data = {'user_id': user_id, 'role_id': r[0],
                'created_date': now, 'last_modifed': now}
        db.execute(userroles.insert(), data)
