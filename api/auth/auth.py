
from __future__ import absolute_import
import hug

from api.exceptions import Unauthorized, ValidateTokenFailure
from config import db, store
from datetime import datetime
from falcon import HTTPNotFound, HTTPInternalServerError
from log import logger
from models.auth.user import users, UserStatus, tokens, TokenAction,\
    get_password, parse_token
from models.operationlog import operationlogs, OperType, OperResult
from sqlalchemy.sql import select, and_


@hug.post('/token')
def login_token(request, response, username, password):
    client_ip = request.remote_addr
    logger.info('<login> user[' + username + '] login, client_ip: ' +
                client_ip)
    query = select([users.c.id,
                    users.c.salt,
                    users.c.hashed_password,
                    users.c.password_errors,
                    users.c.usertype,
                    users.c.organization_id,
                    users.c.department,
                    users.c.status,
                    users.c.fullname])
    query = query.where(and_(users.c.username == username,
                             users.c.status != 'Removed'))
    row = db.fetch_one(query)
    if row:
        user_id = row[0]
        salt = row[1]
        hashed_password = row[2]
        password_errors = row[3]
        usertype = row[4]
        organization_id = row[5]
        department = row[6]
        status = row[7]
        fullname = row[8]
        if UserStatus.Locked == status:
            logger.warn('<login> user[' + username +
                        '] login failed, error: user is locked! ip: ' +
                        client_ip)
            error_msg = '用户已被锁定，禁止登录！'
            login_fail_log(db.conn, user_id, client_ip, username, error_msg)
            raise HTTPInternalServerError(title='user_is_locked',
                                          description=error_msg)
        if get_password(salt, hashed_password) == password:
            query = select([tokens.c.value])
            filters = and_(tokens.c.user_id == user_id,
                           tokens.c.action == TokenAction.API)
            query = query.where(filters)
            row = db.fetch_one(query)
            if row:
                token = row[0]
                store.set(token, {'id': user_id,
                                  'user_id': user_id,
                                  'username': username,
                                  'fullname': fullname,
                                  'usertype': usertype,
                                  'organization_id': organization_id,
                                  'department': department,
                                  'login_time': datetime.now()})
                logger.info('<login> user[' + username +
                            '] login success!')
                login_log(db.conn, user_id, client_ip,
                          username, OperResult.Success)
                if password_errors > 0:
                    u = {'id': user_id, 'password_errors': 0}
                    db.update(users, u)
                return {'token': token}
            else:
                logger.warn('<login> user[' + username +
                            '] login failed, error: no token! ip: ' +
                            client_ip)
                error_msg = 'Token不存在！'
                login_fail_log(db.conn, user_id, client_ip,
                               username, error_msg)
                raise HTTPNotFound(title='no_token', description=error_msg)
        else:
            logger.warn('<login> user[' + username +
                        '] login failed, error: wrong password! ip: ' +
                        client_ip)
            login_fail_log(db.conn, user_id, client_ip, username, '密码错误。')
            error_msg = '用户名或密码错误！'
            password_errors += 1
            if password_errors >= 5:
                logger.info('<login> lock user[' + username +
                            '] password_errors: ' + str(password_errors))
                u = {'id': user_id,
                     'account_locked': True,
                     'password_errors': password_errors,
                     'enabled': False,
                     'status': UserStatus.Locked,
                     'last_updated': datetime.now()}
                db.update(users, u)
            else:
                u = {'id': user_id,
                     'password_errors': password_errors,
                     'last_updated': datetime.now()}
                db.update(users, u)
            raise HTTPInternalServerError(title='wrong_user_or_password',
                                          description=error_msg)
    else:
        logger.warn('<login> user[' + username +
                    '] login failed, error: no user! ip: ' + client_ip)
        error_msg = '用户不存在！'
        login_fail_log(db.conn, None, client_ip, username, error_msg)
        raise HTTPInternalServerError(title='wrong_user_or_password',
                                      description=error_msg)


def get_token(user_id):
    query = select([tokens.c.value])
    filters = and_(tokens.c.user_id == user_id,
                   tokens.c.action == TokenAction.API)
    query = query.where(filters)
    row = db.fetch_one(query)
    if row:
        return row[0]
    return None


def api_key_auth(request, response):
    api_key = request.get_header('apikey')
    if api_key:
        username = parse_token(api_key)
        query = select([users.c.id])
        query = query.where(users.c.username == username)
        row = db.fetch_one(query)
        if row:
            return True
        else:
            raise ValidateTokenFailure(
                'Validate token failure')
    else:
        raise Unauthorized('Invalid Authentication')


@hug.post('/logout')
def logout_token(request, response, token):
    if token:
        try:
            store.delete(token)
            client_ip = request.remote_addr
            username = parse_token(token)
            logger.info('<logout> user[' + username + '] logout, \
                client_ip: ' + client_ip)
            query = select([users.c.id])
            query = query.where(users.c.username == username)
            row = db.fetch_one(query)
            if row:
                user_id = row[0]
                logout_log(db.conn, user_id, client_ip, username)
            else:
                logout_log(db.conn, None, client_ip, username)
        except Exception as e:
            logger.exception('<logout> error=')
            raise HTTPInternalServerError(title='logout_error')


def login_log(conn, user_id, client_ip, username, result):
    detail = '用户' + username
    if result == OperResult.Success:
        detail = detail + '成功登录系统。'
    else:
        detail = detail + '登录系统失败。'
    save_log(conn, user_id, client_ip, username, '用户登录', detail, result)


def login_fail_log(conn, user_id, client_ip, username, error):
    detail = '用户' + username + '登录系统失败, ' + error
    result = OperResult.Fail
    save_log(conn, user_id, client_ip, username, '用户登录', detail, result)


def logout_log(conn, user_id, client_ip, username):
    detail = '用户' + username + '退出登录。'
    save_log(conn, user_id, client_ip, username,
             '用户注销', detail, OperResult.Success)


def save_log(conn, user_id, client_ip, username, name, detail, result):
    try:
        operationlog = {'name': name,
                        'detail': detail,
                        'object_id': user_id,
                        'object': 'users',
                        'type': OperType.Login,
                        'result': result,
                        'user_id': user_id,
                        'username': username,
                        'ip_address': client_ip,
                        'created_date': datetime.now()}
        conn.execute(operationlogs.insert(), operationlog)
    except Exception:
        pass
