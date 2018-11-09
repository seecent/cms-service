
from __future__ import absolute_import

import re


def validate_value(name, label, date_type, value, params):
    keys = params.keys()
    r = 'True'
    nullable = True
    if 'nullable' in keys:
        nullable = params['nullable']
    if nullable and check_is_null(date_type, value):
        return {'code': 0, 'message': 'OK'}
    else:
        r = validate_not_null(name, label, date_type, value)
    if r == 'True':
        if 'validate' in keys:
            validate = params['validate']
            if validate == 'Email':
                r = validate_email(name, label, value)
            elif validate == 'PhoneNumber':
                r = validate_phonenumber(name, label, value)
            elif validate == 'MobilePhone':
                r = validate_mobile(name, label, value)
            elif validate == 'Enum':
                if 'enums' in keys:
                    enums = params['enums']
                    r = validate_enums(name, label, value, enums)
            else:
                r = validate_regular(name, label, value, validate)
        else:
            if date_type == 'Integer' or date_type == 'BigInteger':
                r = validate_number(name, label, value)
            elif date_type == 'Datetime':
                length = params.get('length')
                df = params.get('format')
                r = validate_datetime(name, label, value, length, df)
    if r == 'True':
        return {'code': 0, 'message': 'OK'}
    else:
        return {'code': 1, 'message': r}


def check_is_null(date_type, value):
    if value is None:
        return True
    if date_type == 'String':
        if value.strip() == '':
            return True
        else:
            v = value.strip().lower()
            if v == '':
                return True
            elif v == 'null':
                return True
            elif v == 'none':
                return True
            elif v == '空':
                return True
    return False


def validate_not_null(name, label, date_type, value):
    if check_is_null(date_type, value):
        msg = '{0}{1}的值验证失败，值不允许为空！'
        return msg.format(label, name)
    return 'True'


def validate_nullable(name, label, date_type, value):
    if check_is_null(date_type, value):
        msg = '{0}{1}的值验证失败，值不允许为空！'
        return msg.format(label, name)
    return 'True'


def validate_number(name, label, value):
    if isinstance(value, int):
        return 'True'
    if not re.match(r'^[0-9]*$', value):
        msg = '{0}{1}的值验证失败，{2}不是有效的数字值！'
        return msg.format(label, name, value)
    return 'True'


def validate_datetime(name, label, value, length, date_format):
    # msg = '{0}的值验证失败，{1}不是有效的日期时间，时间格式为：{2}！'
    # error = msg.format(name, value)
    return "True"


def validate_phonenumber(name, label, value):
    regx = r'^((\(0\d{2,3}\)|0\d{2,3})[ -]?)?\d{6,8}$'
    if not re.match(regx, value):
        msg = '{0}{1}的值验证失败，{2}不是有效的电话号码！'
        return msg.format(label, name, value)
    return "True"


def validate_mobile(name, label, value):
    regx = r'^((\(\d{2}\)|\d{2})[ -]?)?1[23456789]\d{9}$'
    if not re.match(regx, value):
        msg = '{0}{1}的值验证失败，{2}不是有效的手机号码！'
        return msg.format(label, name, value)
    return "True"


def validate_email(name, label, value):
    regx = r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$'
    if not re.match(regx, value):
        msg = '{0}{1}的值验证失败，{2}不是有效的电子邮箱地址！'
        return msg.format(label, name, value)
    return "True"


def validate_enums(name, label, value, enums):
    if enums:
        if value not in enums.keys():
            msg = '{0}{1}的值验证失败，{2}不在取值范围: {3}！'
            return msg.format(label, name, value, str(enums))
    return "True"


def validate_regular(name, label, value, validate):
    if validate:
        if not re.match(validate, value):
            msg = '{0}{1}的值验证失败，{2}不符合正则表达式：{3}！'
            return msg.format(label, name, value, validate)
    return "True"


def test_validate():
    print('test_validate')
    r = validate_value('name', '名称', 'String', ' ', {'nullable': False})
    print('validate_nullable=' + str(r))

    r = validate_value('length', '长度', 'Integer', 'none', {'nullable': True})
    print('validate_number=' + str(r))

    r = validate_value('datetime', '时间', 'Datetime', '2018',
                       {'nullable': False})
    print('validate_datetime=' + str(r))

    params = {'nullable': False, 'validate': 'PhoneNumber'}
    r = validate_value('phone', '电话号码', 'String', '0513-66699811', params)
    print('validate_phonenumber=' + str(r))

    params = {'nullable': False, 'validate': 'MobilePhone'}
    r = validate_value('mobile', '手机号', 'String', '18621987990', params)
    print('validate_mobile=' + str(r))

    params = {'nullable': False, 'validate': 'Email'}
    r = validate_value('email', 'Email', 'String', 'zxx@qq.com', params)
    print('validate_email=' + str(r))

    params = {'nullable': False, 'validate': 'Enum',
              'enums': {'1': '男', '2': '女'}}
    r = validate_value('sex', '性别', 'String', '1', params)
    print('validate_enums=' + str(r))

    params = {'nullable': False,
              'validate': '^((\\(\\d{2}\\)|\\d{2})[ -]?)?1[3458]\\d{9}$'}
    r = validate_value('regx', '正则表达式', 'String', '186219879990', params)
    print('validate_regular=' + str(r))
