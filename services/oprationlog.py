# -*- coding: utf-8 -*-
# @Time    : 2018/8/8 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import

from datetime import datetime
from models.operationlog import operationlogs, OperType, OperResult

DF = "%Y-%m-%d %H:%M:%S"
OBJECTS = {'users': '用户', 'roles': '角色', 'menus': '菜单',
           'locations': '区域', 'organizations': '组织机构',
           'templates': '导入模板'}
OPER_TYPES = {'Login': '登录',
              'Logout': '退出',
              'Create': '新增',
              'Update': '修改',
              'Delete': '删除',
              'Upload': '上传',
              'Download': '下载',
              'Import': '导入',
              'Export': '导出'}


class OprationLogService:

    def _name(self, obj, oper_type):
        name = OBJECTS[obj]
        oper = OPER_TYPES[oper_type.name]
        if OperType.Login == oper_type:
            return name + oper
        elif OperType.Logout == oper_type:
            return name + oper
        else:
            return oper + name

    def _detail(self, obj, oper_type):
        name = OBJECTS[obj]
        oper = OPER_TYPES[oper_type.name]
        if OperType.Login == oper_type:
            return name + oper
        elif OperType.Logout == oper_type:
            return name + oper
        else:
            return oper + name

    def save_log(self, log, db=None):
        try:
            if db is not None:
                db.insert(operationlogs, log)
            else:
                db.connect()
                db.insert(operationlogs, log)
                db.close()
        except Exception:
            pass

    def info(self, conn, data):
        conn.execute(operationlogs.insert(), data)

    def success(self, user, name, detail, otype, oid, oname, db=None):
        log = {'name': name,
               'detail': detail,
               'object_id': oid,
               'object': oname,
               'type': otype,
               'result': OperResult.Success,
               'user_id': user.get('id'),
               'username': user.get('username'),
               'created_date': datetime.now()}
        self.save_log(log, db)

    def fail(self, user, name, detail, otype, oid, oname, db=None):
        log = {'name': name,
               'detail': detail,
               'object_id': oid,
               'object': oname,
               'type': otype,
               'result': OperResult.Fail,
               'user_id': user.get('id'),
               'username': user.get('username'),
               'created_date': datetime.now()}
        self.save_log(log, db)

    def collect(self, user, ip, name, detail, result, oid, db=None):
        log = {'name': name,
               'detail': detail,
               'object_id': oid,
               'object': 'collections',
               'type': OperType.Import,
               'result': result,
               'user_id': user.get('id'),
               'username': user.get('username'),
               'ip_address': ip,
               'created_date': datetime.now()}
        self.save_log(log, db)

    def login(self, user_id, username, ip, result, msg=None, db=None):
        detail = None
        if result == OperResult.Success:
            detail = '用户[{}]登录成功登录系统！'.format(username)
        else:
            detail = '用户[{0}]登录系统失败, {1}！'.format(username, msg)
        log = {'name': '用户登录',
               'detail': detail,
               'object_id': user_id,
               'object': 'users',
               'type': OperType.Login,
               'result': result,
               'user_id': user_id,
               'username': username,
               'ip_address': ip,
               'created_date': datetime.now()}
        self.save_log(log, db)

    def logout(self, user_id, username, ip, result, msg=None, db=None):
        detail = None
        if result == OperResult.Success:
            detail = '用户[{}]注销成功！'.format(username)
        else:
            detail = '用户[{0}]注销失败, {1}！'.format(username, msg)
        log = {'name': '用户注销',
               'detail': detail,
               'object_id': user_id,
               'object': 'users',
               'type': OperType.Login,
               'result': result,
               'user_id': user_id,
               'username': username,
               'ip_address': ip,
               'created_date': datetime.now()}
        self.save_log(log, db)

    def loginSSO(self, user_id, username, ip, result, msg=None, db=None):
        detail = None
        if result == OperResult.Success:
            detail = '用户[{}]通过单点登录成功登录系统！'.format(username)
        else:
            detail = '用户[{0}]过单点登录系统失败, {1}！'.format(username, msg)
        log = {'name': '用户登录',
               'detail': detail,
               'object_id': user_id,
               'object': 'users',
               'type': OperType.Login,
               'result': result,
               'user_id': user_id,
               'username': username,
               'ip_address': ip,
               'created_date': datetime.now()}
        self.save_log(log, db)

    def logoutSSO(self, user_id, username, ip, result, msg=None, db=None):
        detail = None
        if result == OperResult.Success:
            detail = '用户[{}]单点登录注销成功！'.format(username)
        else:
            detail = '用户[{0}]单点登录注销失败, {1}！'.format(username, msg)
        log = {'name': '用户注销',
               'detail': detail,
               'object_id': user_id,
               'object': 'users',
               'type': OperType.Login,
               'result': result,
               'user_id': user_id,
               'username': username,
               'ip_address': ip,
               'created_date': datetime.now()}
        self.save_log(log, db)

    def create(self, user, request, oid, obj_name, data,
               db=None, msg=None):
        try:
            if user is None:
                return
            obj_label = OBJECTS.get(obj_name, obj_name)
            if 'created_date' in data.keys():
                created_date = data['created_date']
                data['created_date'] = datetime.strftime(created_date, DF)
            detail = None
            if msg is None:
                result = OperResult.Success
                detail = '新增{0}[{1}]成功！数据：{2}'.format(
                    obj_label, str(oid), str(data))
            else:
                detail = '新增{0}[{1}]失败！数据：{2}，失败原因: {3}！'.format(
                    obj_label, str(oid), str(data), msg)
            log = {'name': '新增{}'.format(obj_label),
                   'detail': detail,
                   'object_id': oid,
                   'object': obj_name,
                   'type': OperType.Create,
                   'result': result,
                   'user_id': user.get('user_id'),
                   'username': user.get('username'),
                   'ip_address': request.remote_addr,
                   'created_date': datetime.now()}
            self.save_log(log, db)
        except Exception:
            pass

    def update(self, user, request, oid, obj_name, data,
               change_dict, db=None, msg=None):
        try:
            if user is None:
                return
            update_dict = {}
            for k, v in change_dict.items():
                old_v = data.get(k)
                if v != old_v:
                    update_dict[k] = str(old_v) + ' -> ' + str(v)
            obj_label = OBJECTS.get(obj_name, obj_name)
            detail = None
            if msg is None:
                result = OperResult.Success
                detail = '修改{0}[{1}]成功！数据：{2}'.format(
                    obj_label, str(oid), str(update_dict))
            else:
                detail = '修改{0}[{1}]失败！数据：{2}，失败原因: {3}！'.format(
                    obj_label, str(oid), str(update_dict), msg)
            log = {'name': '修改{}'.format(obj_label),
                   'detail': detail,
                   'object_id': oid,
                   'object': obj_name,
                   'type': OperType.Update,
                   'result': result,
                   'user_id': user.get('user_id'),
                   'username': user.get('username'),
                   'ip_address': request.remote_addr,
                   'created_date': datetime.now()}
            self.save_log(log, db)
        except Exception:
            pass

    def delete(self, user, request, oid, obj_name,
               db=None, msg=None):
        try:
            if user is None:
                return
            obj_label = OBJECTS.get(obj_name, obj_name)
            detail = None
            if msg is None:
                result = OperResult.Success
                detail = '删除{0}[{1}]成功！'.format(obj_label, str(oid))
            else:
                detail = '删除{0}[{1}]失败！失败原因: {2}！'.format(
                    obj_label, str(oid), msg)
            log = {'name': '删除{}'.format(obj_label),
                   'detail': detail,
                   'object_id': oid,
                   'object': obj_name,
                   'type': OperType.Delete,
                   'result': result,
                   'user_id': user.get('user_id'),
                   'username': user.get('username'),
                   'ip_address': request.remote_addr,
                   'created_date': datetime.now()}
            self.save_log(log, db)
        except Exception:
            pass

    def batch_delete(self, user, request, oids, obj_name,
                     db=None, msg=None):
        try:
            if user is None:
                return
            obj_label = OBJECTS.get(obj_name, obj_name)
            detail = None
            if msg is None:
                result = OperResult.Success
                detail = '批量删除{0}[{1}]成功！'.format(obj_label, str(oids))
            else:
                detail = '批量删除{0}[{1}]失败！失败原因: {2}！'.format(
                    obj_label, str(oids), msg)
            log = {'name': '批量删除{}'.format(obj_label),
                   'detail': detail,
                   'object_id': None,
                   'object': obj_name,
                   'type': OperType.Delete,
                   'result': result,
                   'user_id': user.get('user_id'),
                   'username': user.get('username'),
                   'ip_address': request.remote_addr,
                   'created_date': datetime.now()}
            self.save_log(log, db)
        except Exception:
            pass
