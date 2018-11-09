
from __future__ import absolute_import

from api.errorcode import ErrorCode
from config import db
from datetime import datetime
from log import logger
from models.campaign import campaigns
from models.company import companies
from models.product import products
from models.rawleads import rawleads, rawcontacts
from models.viableleads import viableleads, viablecontacts
from models.saleschannel import saleschannels
from models.leads.activeleads import activeleads
# mdb ams
from models.mdb.ams.amscso import amscsos
from models.mdb.ams.amssso import amsssos
from models.mdb.ams.amssales import amssales
from services.cache.progresscache import ProgressCache
from sqlalchemy.sql import select


class CollectImportBase:

    def __init__(self):
        self.progresscache = ProgressCache()

    def _get_table(self, name):
        table_dict = {'campaigns': campaigns,
                      'companies': companies,
                      'products': products,
                      'rawleads': rawleads,
                      'rawcontacts': rawcontacts,
                      'viableleads': viableleads,
                      'viablecontacts': viablecontacts,
                      'activeleads': activeleads,
                      'saleschannels': saleschannels,
                      'amscsos': amscsos,
                      'amsssos': amsssos,
                      'amssales': amssales}
        if name in table_dict.keys():
            return table_dict[name]
        return None

    # 插入主表导入数据
    def insert_main_table_datas(self, cid, table_name, columns, datas):
        total = len(datas)
        logger.info('<insert_main_table_datas> cid=' + str(cid) +
                    ', table_name=' + table_name +
                    ', datas size=' + str(total))
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        if total == 0:
            return result
        try:
            table = self._get_table(table_name)
            if table is not None:
                # 批量入库
                db.connect()
                self.set_created_date(table, datas, datetime.now())
                self.bulk_insert_datas(db, cid, table, datas)
                db.close()
            else:
                logger.error(
                    '<insert_main_table_datas> not table: ' + table_name)
                msg = 'not table: ' + table_name
                result = {'code': ErrorCode.EXCEPTION.value,
                          'message': msg}
        except Exception as e:
            logger.exception('<insert_main_table_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}
        return result

    # 插入子表导入数据
    def insert_components_datas(self, cid, table_name, columns, datas):
        total = len(datas)
        logger.info('<insert_components_datas> cid=' + str(cid) +
                    ', table_name=' + table_name +
                    ', datas size=' + str(total))
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        if total == 0:
            return result
        try:
            table = self._get_table(table_name)
            if table is not None:
                # 批量入库
                db.connect()
                self.set_created_date(table, datas, datetime.now())
                self.bulk_insert_datas(db, cid, table, datas)
                # 查询入库数据ID
                params = {'collection_id': cid}
                query = self.query(table, ['id', 'no'], params)
                rows = db.execute(query)
                id_dict = {}
                if rows:
                    for r in rows:
                        k = r[1]
                        id_dict[k] = {'id': r[0]}
                result['id_dict'] = id_dict
                db.close()
            else:
                logger.error('<insert_components_datas> not table: ' +
                             table_name)
                msg = 'not table: ' + table_name
                result = {'code': ErrorCode.EXCEPTION.value, 'message': msg}
        except Exception as e:
            logger.exception('<insert_components_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}
        return result

    # 插入关联表导入数据
    def insert_jointables_datas(self, cid, table_name, unique_key, datas):
        total = len(datas)
        logger.info('<insert_jointables_datas> cid=' + str(cid) +
                    ', table_name=' + table_name +
                    ', datas size=' + str(total))
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        if total == 0:
            return result
        try:
            table = self._get_table(table_name)
            if table is not None:
                db.connect()
                query = self.query(table, ['id', unique_key])
                rows = db.execute(query)
                id_dict = {}
                if rows:
                    for r in rows:
                        k = r[1]
                        d = {'id': r[0]}
                        d[unique_key] = k
                        id_dict[k] = d
                # 保存新增数据
                self.set_created_date(table, datas, datetime.now())
                for d in datas:
                    k = d[unique_key]
                    if id_dict.get(k) is None:
                        nid = db.insert(table, d)
                        id_dict[k] = nid
                        logger.info('<insert_jointables_datas> table_name=' +
                                    table_name + ', data=' + str(d) +
                                    ', nid=' + str(nid))
                result['id_dict'] = id_dict
                db.close()
            else:
                logger.error('<insert_jointables_datas> not table: ' +
                             table_name)
                msg = 'not table: ' + table_name
                result = {'code': ErrorCode.EXCEPTION.value, 'message': msg}
        except Exception as e:
            logger.exception('<insert_jointables_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}
        return result

    # 批量插入数据
    def bulk_insert_datas(self, db, cid, table, data_list):
        total = len(data_list)
        logger.info('<bulk_insert_datas> table=' + table.name +
                    ', data_list size=' + str(total))
        if total > 0:
            batch = 5000
            logger.info('<bulk_insert_datas> total=' + str(total) +
                        ', batch=' + str(batch))

            if total > batch:
                begin = 0
                end = 0
                pages = int(total / batch)
                for n in range(0, pages):
                    logger.info('<bulk_insert_datas> table=' + table.name +
                                ', pages=' + str(pages) + ', n=' + str(n))
                    begin = n * batch
                    end = begin + batch
                    page_datas = data_list[begin:end]
                    db.bulk_insert(table, page_datas)
                    self.progresscache.update(cid, table.name, end)
                if end < (total - 1):
                    begin = end
                    end = total
                    page_datas = data_list[begin:end]
                    db.bulk_insert(table, page_datas)
                    self.progresscache.update(cid, table.name, end)
            else:
                db.bulk_insert(table, data_list)
                self.progresscache.update(cid, table.name, total)

    # 设置创建和修改时间字段值
    def set_created_date(self, table, data_list, now):
        col = self._get_column(table, 'created_date')
        if col is not None:
            for data in data_list:
                data['created_date'] = now
        col = self._get_column(table, 'last_modifed')
        if col is not None:
            for data in data_list:
                data['last_modifed'] = now
        return data_list

    def query(self, table, column_names, params={}):
        cols = []
        for n in column_names:
            col = self._get_column(table, n)
            if col is not None:
                cols.append(col)
        query = select(cols)
        if params:
            for k, v in params.items():
                col = self._get_column(table, k)
                if col is not None:
                    query = query.where(col == v)
        return query

    def _get_column(self, table, name):
        for c in table.c:
            if c.name == name:
                return c
        return None

    # 根据类型转换数据
    def convert_value(self, name, data_type, value, params):
        try:
            if data_type == 'String':
                return value
            else:
                if self._check_none(value):
                    return None
                else:
                    if data_type == 'Integer':
                        return int(value)
                    elif data_type == 'BigInteger':
                        return int(value)
                    elif data_type == 'Datetime':
                        if 'format' in params.keys():
                            df = params['format']
                            if df is not None:
                                return datetime.strptime(value, df)
                    else:
                        return value
        except Exception as e:
            logger.exception('<convert_value> name=' + name +
                             ', type=' + data_type +
                             ', value=' + str(value) + ', error=')
            return None
        return None

    # 根据类型转换数据
    def transform_value(self, name, data_type, value, params):
        try:
            logger.debug('<transform_value> name=' + name +
                         ', type=' + data_type +
                         ', value=' + str(value) +
                         ', params=' + str(params))
            if data_type == 'String':
                return value
            else:
                if self._check_none(value):
                    return None
                else:
                    if 'transform' in params.keys():
                        transform = params['transform']
                        if value in transform.keys():
                            value = transform[value]
                        else:
                            logger.error('<transform_value> transform error' +
                                         ', name=' + name +
                                         ', type=' + data_type +
                                         ', value=' + str(value) +
                                         ', transform=' + str(transform))
                            return None

                    if data_type == 'Integer':
                        return int(value)
                    elif data_type == 'BigInteger':
                        return int(value)
                    elif data_type == 'Datetime':
                        if 'format' in params.keys():
                            df = params['format']
                            if df is not None:
                                return datetime.strptime(value, df)
                    else:
                        return value
        except Exception as e:
            logger.exception('<transform_value> name=' + name +
                             ', type=' + data_type +
                             ', value=' + str(value) + ', error=')
            return None
        return None

    # 判断空值
    def _check_none(self, value):
        if value is None:
            return True
        if type(value) == str:
            if value == '':
                return True
            elif value.lower() == 'null' or value.lower() == 'none':
                return True
            else:
                return False
        else:
            return False
