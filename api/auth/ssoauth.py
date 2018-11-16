
from __future__ import absolute_import
import hug
import json
import urllib

from api.auth.user import menus2tree
from api.errorcode import ErrorCode
from api.exceptions import ValidateTokenFailure
from config import db, store, sso_settings
from datetime import datetime
from falcon import HTTPMissingParam, HTTPInternalServerError
from log import logger
from models.auth.menu import menus
from models.operationlog import OperResult
from models import rows2dict
from services.oprationlog import OprationLogService
from sqlalchemy.sql import select


# 数据库操作日志服务
log = OprationLogService()


def user_info(user=None):
    if user:
        userid = user.get('user_id')
        username = user.get('username')
        # enname = user.get('enname')
        fullname = user.get('fullname')
        if fullname is None or fullname == '':
            fullname = username
        return dict(username=username, name=fullname, avatar='',
                    userid=userid, notifyCount=0)
    else:
        return dict(username='None', name='FullName', avatar='',
                    userid=-1, notifyCount=0)


def get_user_menus(db, user, menu_codes):
    if menu_codes is not None and len(menu_codes) > 0:
        t = menus.alias('m')
        query = select([t]).order_by(t.c.id.asc())
        rows = db.execute(query).fetchall()
        menu_list = []
        datas = rows2dict(rows, t)
        for d in datas:
            if d['code'] in menu_codes:
                menu_list.append(d)
        user_menus = menus2tree(None, 1, menu_list, user)
        return user_menus
    else:
        return []


@hug.post('/token')
def auth_token(request, response, code):
    token = None
    user = None
    user_menus = []
    client_ip = request.remote_addr
    code = urllib.parse.unquote(code)
    logger.info('<auth_token> code: ' + code + ', ip: ' + client_ip)
    if not code:
        raise HTTPMissingParam(title='miss_param_code')
    try:
        app_id = sso_settings["app_id"]
        app_secret = sso_settings["app_secret"]
        api_url = sso_settings["auth_url"]
        logger.info('<auth_token> api_url=' + api_url +
                    ', code=' + code)
        params = {'appid': app_id, 'appsecret': app_secret, 'code': code}
        data = urllib.parse.urlencode(params).encode('utf-8')
        request = urllib.request.Request(api_url, data)
        response = urllib.request.urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.info('<auth_token> response=' + str(result))
        if result['code'] == 0:
            token = result.get('token')
            userId = result.get('userId')
            username = result.get('username')
            enname = result.get('enname')
            fullname = result.get('fullname')
            companyId = result.get('companyId')
            organizationId = result.get('organizationId')
            user = {'id': result.get('id'),
                    'user_id': userId,
                    'username': username,
                    'enname': enname,
                    'fullname': fullname,
                    'company_id': _check_int_value(companyId),
                    'organization_id': _check_int_value(organizationId),
                    'login_time': datetime.now()}

            menu_codes = result.get('menus')
            user_menus = get_user_menus(db, user, menu_codes)
            user['menus'] = user_menus
            store.set(token, user)
            log.loginSSO(None, username, client_ip, OperResult.Success,
                         None, db)
        else:
            username = ''
            msg = result['message']
            log.loginSSO(None, username, client_ip, OperResult.Fail, msg, db)
            raise ValidateTokenFailure('token_validation_failure')
    except Exception as e:
        logger.exception('<auth_token> code: ' + code + ', error: ')
        raise HTTPInternalServerError(title='login_error')
    return {'token': token, 'user': user_info(user), 'menus': user_menus}


@hug.post('/logout')
def logout_token(request, response):
    try:
        client_ip = request.remote_addr
        token = request.get_header('apikey')
        if token:
            user = store.get(token)
            if user:
                username = user.get('username')
                logger.info('<logout_token> user[' + username + '] logout!')
                log.logoutSSO(None, username, client_ip,
                              OperResult.Success, None, db)
            store.delete(token)
            # logout_url = sso_settings["sso_url"] + '/logout'
            # logger.info('<logout_token> logout_url=' + logout_url +
            #             ', token=' + token)
            # params = {'accessToken': token}
            # data = urllib.parse.urlencode(params).encode('utf-8')
            # request = urllib.request.Request(logout_url, data)
            # response = urllib.request.urlopen(request)
            # result = json.loads(response.read().decode('utf-8'))
            # logger.info('<logout_token> response=' + str(result))
        else:
            logger.error('<logout_token> ip: ' + client_ip +
                         ', error: token is None!')
    except Exception as e:
        logger.exception('<logout_token> error: ')
        raise HTTPInternalServerError(title='logout_error')


@hug.get('/current-info')
def current_info(request):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    token = request.get_header('apikey')
    logger.info('<current_info> token: ' + str(token))
    userinfo = user_info()
    usermenus = []
    if token:
        try:
            user = store.get(token)
            if user is None:
                rs = get_current_user(token)
                if rs['code'] == 0:
                    user = rs['user']
                    userinfo = user_info(user)
                    usermenus = rs.get('menus', [])
                else:
                    result = _token_validation_fail(rs, result)
            else:
                userinfo = user_info(user)
                usermenus = user.get('menus', [])
            logger.info('<current_info> user: ' + str(userinfo))
        except Exception as e:
            logger.exception('<current_info> token: ' + token + ', error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = ErrorCode.EXCEPTION.name
    else:
        result['code'] = ErrorCode.TOKEN_VALIDATION_FAILURE.value
        result['message'] = ErrorCode.TOKEN_VALIDATION_FAILURE.name

    result['user'] = userinfo
    result['menus'] = usermenus
    return result


def get_current_user(token):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    try:
        api_url = sso_settings["api_url"]
        api_url += '/authService/getCurrentUser'
        logger.info('<get_current_user> api_url=' + api_url +
                    ', accessToken=' + token)
        params = {'accessToken': token}
        data = urllib.parse.urlencode(params).encode('utf-8')
        request = urllib.request.Request(api_url, data)
        response = urllib.request.urlopen(request)
        rs = json.loads(response.read().decode('utf-8'))
        logger.info('<get_current_user> response=' + str(rs))
        if rs['code'] == 0:
            userId = rs.get('userId')
            username = rs.get('username')
            enname = rs.get('enname')
            fullname = rs.get('fullname')
            companyId = rs.get('companyId')
            organizationId = rs.get('organizationId')
            token = rs.get('token')
            user = {'id': rs.get('id'),
                    'user_id': userId,
                    'username': username,
                    'enname': enname,
                    'fullname': fullname,
                    'company_id': _check_int_value(companyId),
                    'organization_id': _check_int_value(organizationId),
                    'login_time': datetime.now()}
            store.set(token, user)
            result['user'] = user

            menu_codes = rs.get('menus')
            result['menus'] = get_user_menus(db, user, menu_codes)
        else:
            result['code'] = ErrorCode.TOKEN_VALIDATION_FAILURE.value
            result['message'] = ErrorCode.TOKEN_VALIDATION_FAILURE.name
            # raise ValidateTokenFailure('token_validation_failure')
    except Exception as e:
        logger.exception('<get_current_user> token: ' + token + ', error: ')
        result['code'] = ErrorCode.EXCEPTION.value
        result['message'] = ErrorCode.EXCEPTION.name
    return result


@hug.get('/usermenus')
def user_menus(request):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    user_menus = []
    try:
        token = request.get_header('apikey')
        if token:
            user = store.get(token)
            if user is None:
                user = get_current_user(token)
            menus = user.get('menus')
            if menus and len(menus) > 0:
                user_menus = menus
            else:
                api_url = sso_settings["api_url"]
                api_url += '/authService/getCurrentUser'
                logger.info('<user_menus> api_url=' + api_url +
                            ', accessToken=' + token)
                params = {'accessToken': token}
                data = urllib.parse.urlencode(params).encode('utf-8')
                request = urllib.request.Request(api_url, data)
                response = urllib.request.urlopen(request)
                rs = json.loads(response.read().decode('utf-8'))
                logger.info('<user_menus> response=' + str(rs))
                if result['code'] == 0:
                    menu_codes = rs.get('menus')
                    user_menus = get_user_menus(db, user, menu_codes)
                else:
                    result = _token_validation_fail(rs, result)
        else:
            # raise ValidateTokenFailure('token_validation_failure')
            result['code'] = ErrorCode.TOKEN_VALIDATION_FAILURE.value
            result['message'] = ErrorCode.TOKEN_VALIDATION_FAILURE.name
    except Exception as e:
        logger.exception('<user_menus> error: ')
        result['code'] = ErrorCode.EXCEPTION.value
        result['message'] = ErrorCode.EXCEPTION.name

    result['menus'] = user_menus
    return result


def _check_int_value(v):
    try:
        if v is not None and v != '':
            return int(v)
    except Exception as e:
        pass
    return None


def _token_validation_fail(rs, result):
    code = rs['code']
    codes = [ErrorCode.TOKEN_VALIDATION_FAILURE.value,
             ErrorCode.INVALID_TOKEN,
             ErrorCode.TOKEN_EXPIRED]
    if code in codes:
        result['code'] = ErrorCode.TOKEN_VALIDATION_FAILURE.value
        result['message'] = ErrorCode.TOKEN_VALIDATION_FAILURE.name
    else:
        result['code'] = rs['code']
        result['message'] = rs['message']
    return result
