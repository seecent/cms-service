from __future__ import absolute_import

from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime, Enum
from sqlalchemy import types, Table
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.selectable import Alias
from hashids import Hashids


Base = declarative_base()
ID_LEN = 128
RAW_TYPE = (sqltypes.Integer, sqltypes.Boolean, sqltypes.Numeric)
hashids = Hashids(salt='leads_ms#1', min_length=4)


def _get_table_column(table, name):
    for c in table.c:
        if c.name == name:
            return c
    return None


def _check_value(col, value):
    coltype = col.type
    if isinstance(coltype, types.Integer):
        return int(value)
    elif isinstance(coltype, types.Numeric):
        return float(value)
    # elif isinstance(coltype, types.Enum):
    #     t, v = value.split(".")
    #     print(enums[t][v])
    #     return enums[t][v]
    else:
        return value


def _col_val(col, value):
    coltype = col.type
    if isinstance(coltype, DateTime):
        return str(value)
    elif isinstance(coltype, Enum):
        return str(value)
    else:
        return value


def _check_includes(name, includes):
    for e in includes:
        if name == e:
            return True
    return False


def _check_excludes(name, excludes):
    for e in excludes:
        if name == e:
            return True
    return False


def _exchange_key_value(mappign):
        new_dict = {}
        for k, v in mappign.items():
            new_dict[v] = k
        return new_dict


def bind_dict(table, body):
    data = {}
    for c in table.c:
        if c.name == 'id':
            pass
        elif c.name == 'created_date':
            data['created_date'] = datetime.now()
        elif c.name == 'date_created':
            data['date_created'] = datetime.now()
        else:
            v = body.pop(c.name, None)
            if v:
                v = _check_value(c, v)
                data[c.name] = v
    return data


def change_dict(table, data, body, excludes=set()):
    d = {}
    if 'created_date' in data.keys():
        data.pop('created_date')
    if 'date_created' in data.keys():
        data.pop('date_created')
    for c in table.c:
        if c.name == 'id':
            d['id'] = data['id']
        elif c.name == 'created_date':
            pass
        elif c.name == 'date_created':
            pass
        elif c.name == 'last_modifed':
            data['last_modifed'] = datetime.now()
        elif c.name == 'last_updated':
            data['last_updated'] = datetime.now()
        else:
            if not _check_excludes(c.name, excludes):
                ov = data.get(c.name)
                nv = body.pop(c.name, None)
                if nv:
                    nv = _check_value(c, nv)
                    if nv != ov:
                        d[c.name] = nv
                else:
                    d[c.name] = None
    return d


def rows2dict(rs, selects, excludes=set()):
    """将查询数据库结果转换为字典，单表查询，不支持关联查询。
            :param rs: 查询结果集（list）
            :param selects: 查找对象，selects可以是数据库表
                            (sqlalchemy.Table类型对象)
                            或者是数据库表字段列表
                            (sqlalchemy.Column列表)
            :param excludes: 排除字段名称（set）
            :param mappign: 字段名称映射（dict）
            :retrun : 查询结果行数据字典（list)
        """
    datas = []
    for r in rs:
        datas.append(row2dict(r, selects, excludes))
    return datas


def row2dict(r, selects, excludes=set()):
    """将查询数据库结果，行数据转换为字典。
            :param r: 查询结果行数据
            :param selects: 查找对象，selects可以是数据库表
                            (sqlalchemy.Table类型对象)
                            或者是数据库表字段列表
                            (sqlalchemy.Column列表)
            :param excludes: 排除字段名称（set）
            :param mapping: 字段名称映射（dict）
            :retrun : 查询结果行数据字典（dict)
        """
    d = {}
    cols = []
    mapping = None
    s_type = type(selects)
    if s_type == Table or s_type == Alias:
        for c in selects.c:
            cols.append(c)
    elif s_type == list:
        cols = selects
    else:
        cols = selects['select']
        mapping = selects.get('mapping')

    if mapping is not None:
        mapping = _exchange_key_value(mapping)
        i = 0
        for c in cols:
            if not _check_excludes(c.name, excludes):
                name = mapping.get(c.name)
                if name is not None:
                    d[name] = _col_val(c, r[i])
                else:
                    d[c.name] = _col_val(c, r[i])
            i = i + 1
    else:
        i = 0
        for c in cols:
            if not _check_excludes(c.name, excludes):
                d[c.name] = _col_val(c, r[i])
            i = i + 1
    return d


def rows2data(rs, table, joins, excludes=set()):
    datas = []
    for r in rs:
        datas.append(row2data(r, table, joins, excludes))
    return datas


def row2data(r, table, joins, excludes=set()):
    d = {}
    cols = []
    a = table.alias('a')
    for c in a.c:
        cols.append(c)
    i = 0
    for c in cols:
        if not _check_excludes(c.name, excludes):
            d[c.name] = _col_val(c, r[i])
        i = i + 1

    for (k, v) in joins.items():
        jt = v['table']    # 关联表
        js = v['select']    # 关联表查询字段
        m = {}
        if js:
            if isinstance(js, str):
                for c in jt.c:
                    if c.name == js:
                        m = _col_val(c, r[i])
                        i = i + 1
                        break
            elif isinstance(js, list):
                for n in js:
                    c = _get_table_column(jt, n)
                    if c is not None:
                        m[n] = _col_val(c, r[i])
                        i = i + 1
        else:
            for c in jt.c:
                if not _check_excludes(c.name, excludes):
                    m[c.name] = _col_val(c, r[i])
                i = i + 1
        if isinstance(js, str):
            d[k] = m
        else:
            if 'id' in m and m['id'] is None:
                d[k] = None
            else:
                d[k] = m

    return d


def handle_secrecy_data(data, name, start=None, end=None):
    if name in data.keys():
        data[name] = handle_secrecy_value(data[name], start, end)


def handle_secrecy_value(value, start=None, end=None):
    if value and type(value) == str:
        ss = list(value)
        c = len(value)
        if start is not None and end is not None:
            if start < (c - end) and end < c:
                for i in range(start, c - end):
                    ss[i] = '*'
        elif end is not None:
            if end < c:
                for i in range(c - end, c):
                    ss[i] = '*'
        elif start is not None:
            if start < c:
                for i in range(start, c):
                    ss[i] = '*'
        return ''.join(ss)
    else:
        return value


def hash_encode(*values):
    return hashids.encode(*values)


def hash_decode(hashid):
    return hashids.decode(hashid)
