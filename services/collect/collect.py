
from __future__ import absolute_import

import codecs
import os.path
from config import setting
from datetime import datetime
from log import logger


class CollectService:
    def import_from_csv(self, filename, db, table, unique_keys,
                        mapping=None, filedir='upload'):
        logger.info('<import_from_csv> filedir=' + filedir +
                    ', filename=' + filename + ', table=' + table.name +
                    ', unique_keys=' + str(unique_keys) +
                    ', mapping=' + str(mapping))
        data = None
        if filedir == 'conf':
            filename = setting['lms_home'] + os.path.sep +\
                "conf" + os.path.sep + filename
        else:
            filename = setting['upload'] + filename
        try:
            data = self.parse_csv_file_datas(filename, unique_keys)
            data_list = data['list']
            if mapping:
                self.bulk_insert_csvdatas(db, table, data_list, mapping)
            else:
                self.bulk_insert_datas(db, table, data_list)
        except Exception:
            logger.exception('<import_from_csv> error: ')
        logger.info('<import_from_csv> end!')

    # 解析csv文件数据
    def parse_csv_file_datas(self, filename, unique_keys):
        logger.info('<parse_csv_file_datas> filename=' + filename)
        r = None
        try:
            r = self.parse_csv_file(filename, unique_keys, 'utf-8')
        except Exception:
            r = self.parse_csv_file(filename, unique_keys, 'GBK')
        return r

    def bulk_insert_csvdatas(self, db, table, data_list, mapping):
        total = len(data_list)
        batch = 5000
        logger.info('<bulk_insert_csvdatas> total=' + str(total) +
                    ', batch=' + str(batch))
        if total > batch:
            begin = 0
            end = 0
            pages = int(total / batch)
            for n in range(0, pages):
                logger.info('<bulk_insert_csvdatas> pages=' + str(pages) +
                            ', n=' + str(n))
                begin = n * batch
                end = begin + batch
                page_datas = data_list[begin:end]
                db.bulk_insert(table, self._convert_csvdata(page_datas,
                                                            mapping))

            if end < (total - 1):
                begin = end
                end = total
                page_datas = data_list[begin:end]
                db.bulk_insert(table, self._convert_csvdata(page_datas,
                                                            mapping))
        else:
            db.bulk_insert(table, self._convert_csvdata(data_list, mapping))

    def bulk_insert_datas(self, db, table, data_list):
        total = len(data_list)
        batch = 5000
        logger.info('<bulk_insert_datas> total=' + str(total) +
                    ', batch=' + str(batch))
        if total > batch:
            begin = 0
            end = 0
            pages = int(total / batch)
            for n in range(0, pages):
                logger.info('<bulk_insert_datas> pages=' + str(total) +
                            ', n=' + str(n))
                begin = n * batch
                end = begin + batch
                page_datas = data_list[begin:end]
                db.bulk_insert(table, page_datas)

            if end < (total - 1):
                begin = end
                end = total
                page_datas = data_list[begin:end]
                db.bulk_insert(table, page_datas)
        else:
            db.bulk_insert(table, data_list)

    # 解析CSV文件，根据unique_keys去除重复数据
    def parse_csv_file(self, filename, unique_keys, chartset, sep=','):
        logger.info('<parse_csv_file> filename=' + filename +
                    ', unique_keys=' + str(unique_keys) + ', sep=' + sep)
        datas = []
        titles = []

        flag = True
        m_map = {}
        count = 0
        for rid, line in enumerate(codecs.open(filename, 'r', chartset)):
            count += 1
            if flag:
                flag = False
                ts = self._strip_line(line).split(sep)
                for t in ts:
                    titles.append(self._strip(t))
            else:
                vals = self._strip_line(line).split(sep)
                vals = self._strip_data(vals)
                i = 0
                data = {'no': count}
                m_key = ''
                if len(titles) != len(vals):
                    continue
                for k in titles:
                    if k in unique_keys:
                        v = self._strip(vals[i])
                        data[k] = v
                        m_key = m_key + '@' + v
                    else:
                        v = self._strip(vals[i])
                        data[k] = v
                    i += 1
                if m_key not in m_map.keys():
                    datas.append(data)
                    m_map[m_key] = 1
        total = len(datas)
        logger.info('<parse_csv_file> filename=' + filename +
                    ', titles=' + str(titles) + ', datas total=' + str(total))
        return {'filename': filename, 'total': count,
                'titles': titles, 'list': datas}

    # 去除特殊字符
    def _strip_line(self, line):
        return line.strip("\n").strip("\r").strip("\ufeff")

    # 去除两端特殊字符
    def _strip_data(self, data):
        new_data = []
        for v in data:
            new_data.append(self._strip(v))
        return new_data

    # 去除两端特殊字符
    def _strip(self, value):
        return value.strip('"').strip()

    # 转换数据类型，根据mapping设置将csv文件导入数据转换为数据库字段对应类型
    # mapping name: 数据库表字段名称，title: CSV文件字段标题名称，type：数据类型
    # mapping 样例：
    # mapping = [{'name': 'name', 'title': 'Name', 'type': 'Text'},
    #            {'name': 'joinDate', 'title': 'JoinDate',
    #             'type': 'DateTime', 'format': '%Y-%m-%d %H:%M:%S'},
    #            {'name': 'agStatus', 'title': 'AgStatus', 'type': 'Number'}]
    def _convert_csvdata(self, rows, mapping):
        datas = []
        for r in rows:
            d = {}
            for m in mapping:
                n = m['name']
                k = m.get('title')
                if k is not None:
                    if k in r.keys():
                        t = m['type']
                        v = r[k]
                        if t == 'Text':
                            d[n] = v
                        elif t == 'Number':
                            d[n] = self._convert2number(t, v)
                        elif t == 'DateTime':
                            d[n] = self._convert2datetime(t, v, m['format'])
                        else:
                            d[n] = v
                    else:
                        d[n] = None
                else:
                    d[n] = m.get('default_value')
            datas.append(d)
        return datas

    def _convert_value(self, t, v, f=None):
        if t == 'Text':
            return v
        else:
            v = v.strip()
            if v != '':
                if t == 'Number':
                    return int(v)
                elif t == 'DateTime':
                    return datetime.strptime(v, f)
        return None

    def _convert2number(self, t, v):
        v = v.strip()
        if v != '':
            return int(v)
        return None

    def _convert2datetime(self, t, v, f):
        v = v.strip()
        if v != '':
            if len(v) == 10:
                return datetime.strptime(v, f)
        return None
