
from __future__ import absolute_import

import codecs
import json
from api.errorcode import ErrorCode
from config import setting
from datetime import datetime
from log import logger
from services.cache.progresscache import ProgressCache
from services.collect.import_base import CollectImportBase
from services.collect.merge import merge_datalist, merge_rows
from services.collect.validate import validate_value


# CSV文件导入
class CollectCSVImportService(CollectImportBase):

    def __init__(self, validate_type='Filter', merge_type='Filter'):
        self.validate_type = validate_type
        self.merge_type = merge_type
        self.sep = ","
        self.channel_id = None
        self.progresscache = ProgressCache()

    def set_validate_type(self, validate_type):
        """
        设置导入验证处理类型，validate_type设置为'Filter'时数据
        校验不通过，该条导入记录将被过滤，不保存到数据库。
        validate_type设置为'Mark'时数据校验不通过，该条导入记录将
        有效标识字段effective标记为2无效并保存到数据库。

        :param validate_type: 值可设置为'Filter'或着'Mark'。
        """
        self.validate_type = validate_type

    def set_merge_type(self, merge_type):
        self.merge_type = merge_type

    def set_csv_separator(self, sep):
        logger.info('<set_csv_separator> sep=' + str(sep))
        if sep is not None:
            self.sep = sep

    def set_channel_id(self, channel_id):
        logger.info('<set_channel_id> channel_id=' + str(channel_id))
        self.channel_id = channel_id

    # 从CSV文件导入数据
    def import_from_csv_file(self, cid, filename, config,
                             validate, merge=True):
        logger.info('<import_from_csv_file> cid=' + str(cid) +
                    ', filename=' + filename)
        start_time = datetime.now()
        filename = setting['upload'] + filename
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            # 1. 解析导入CSV文件标题
            titles = self.get_csv_file_titles(filename)
            if titles is None:
                raise Exception("解析CSV文件标题错误！")

            name = config['name']
            uni_keys = config['uniquekeys']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')
            # 2. 检测不允许为空列在CSV文件标题中都存在
            result = self._check_titles(cid, filename, titles, columns,
                                        components, jointables)
            code = result['code']
            if code == ErrorCode.OK.value:
                cols = result['columns']
                # 3. 解析导入CSV文件
                r = self.parse_csv_file_datas(filename, uni_keys, False)
                datas = r['list']
                source_count = len(datas)
                self.progresscache.start(cid, source_count)
                if validate:
                    # 4. 验证值是否有效并根据数据类型转换值
                    r = self._validate_csv_datas(cid, cols, titles, datas)
                    datas = r['valid_datas']
                else:
                    datas = self._convert_csv_datas(cid, cols, titles, datas)

                if merge:
                    datas = self.merge_csv_datas(cid, uni_keys, titles, datas)

                com_datas = {}
                jt_datas = {}

                # 导入关联表数据
                if jointables is not None:
                    jt_datas = self._import_jointables_datas(cid, jointables,
                                                             titles, datas)
                # 导入子表数据
                if components is not None:
                    com_datas = self._import_components_datas(cid, components,
                                                              titles, datas)
                # 导入主表数据
                r = self._import_main_table_datas(cid, name, columns, titles,
                                                  datas,
                                                  com_datas, jt_datas,
                                                  validate, merge)
                collect_count = r['collect_count']
                fail_count = source_count - collect_count
                result['source_count'] = source_count
                result['collect_count'] = collect_count
                result['fail_count'] = fail_count
                logger.info('<import_from_csv_file> cid=' + str(cid) +
                            ', source_count=' + str(source_count) +
                            ', collect_count=' + str(collect_count) +
                            ', fail_count=' + str(fail_count))
                self.progresscache.end(cid, source_count)
        except Exception as e:
            logger.exception('<import_from_csv_file> error: ')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        end_time = datetime.now()
        cost_time = (end_time - start_time).microseconds / 1000
        result['cost_time'] = cost_time
        logger.info('<import_from_csv_file> end! costtime=' +
                    str(cost_time) + 'ms')
        return result

    # 预览CSV文件数据
    def preview_csv_file_datas(self, filename, offset, limit, total):
        logger.info('<preview_csv_file_datas> filename=' + filename +
                    ', offset=' + str(offset) + ", limit=" + str(limit))
        filename = setting['upload'] + filename
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        r = None
        try:
            r = self.page_parse_csv_file(filename, offset, limit,
                                         total, 'utf-8', self.sep)
        except Exception:
            r = self.page_parse_csv_file(filename, offset, limit,
                                         total, 'GBK', self.sep)
        try:
            titles = r.get('titles')
            rows = r.get('list')
            if titles is not None and rows is not None:
                datas = []
                for r in rows:
                    data = {}
                    data['no'] = r['rowid']
                    d = r['data']
                    i = 0
                    for t in titles:
                        data[t] = d[i]
                        i += 1
                    datas.append(data)
                result['titles'] = titles
                result['datas'] = datas
        except Exception as e:
            logger.exception('<preview_csv_file_datas> errors=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 创建导入模板文件
    def create_template_csv_file(self, filename, config):
        logger.info('<create_template_csv_file> filename=' + filename)
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')
            columns_names = []
            for c in columns:
                mapping = c.get('mapping')
                if mapping is not None:
                    columns_names.append(mapping)

            if components is not None:
                for com in components:
                    cols = com['columns']
                    for c in cols:
                        columns_names.append(c.get('mapping'))

            if jointables is not None:
                for jt in jointables:
                    cols = jt['columns']
                    for c in cols:
                        columns_names.append(c.get('mapping'))

            template_filename = setting['upload'] + filename
            with open(template_filename, 'w') as f:
                f.write(','.join(columns_names))
                f.close()
        except Exception as e:
            logger.exception('<create_template_csv_file> error: ')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 2. 检测不允许为空列在CSV文件标题中都存在
    def _check_titles(self, cid, filename, titles, columns,
                      components, jointables):
        logger.info('<_check_titles> cid=' + str(cid) +
                    ', filename=' + filename)
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        msg = 'CSV文件中不存在字段名为{}的列，该导入字段不允许为空！'
        errors = []
        all_columns = []
        if components is not None:
            for com in components:
                cols = com['columns']
                for c in cols:
                    mapping = c.get('mapping')
                    label = c.get('label')
                    if mapping in titles:
                        all_columns.append(c)
                    elif label in titles:
                        all_columns.append(c)
                    else:
                        nullable = c.get('nullable')
                        if nullable is not None and nullable:
                            errors.append(msg.format(mapping))

        if jointables is not None:
            for jt in jointables:
                cols = jt['columns']
                for c in cols:
                    mapping = c.get('mapping')
                    label = c.get('label')
                    if mapping in titles:
                        all_columns.append(c)
                    elif label in titles:
                        all_columns.append(c)
                    else:
                        nullable = c.get('nullable')
                        if nullable is not None and nullable:
                            errors.append(msg.format(mapping))

        for c in columns:
            mapping = c.get('mapping')
            label = c.get('label')
            if mapping is not None:
                if mapping in titles:
                    all_columns.append(c)
                elif label in titles:
                    all_columns.append(c)
                else:
                    nullable = c.get('nullable')
                    if nullable is not None and nullable:
                        errors.append(msg.format(mapping))

        if len(errors) > 0:
            logger.error('<_check_titles> cid=' + str(cid) +
                         ', filename=' + filename +
                         ', errors=' + str(errors))
            result = {'code': ErrorCode.PARSE_CSV_ERROR.value,
                      'message': ErrorCode.PARSE_CSV_ERROR.name,
                      'errors': errors}
        else:
            result['columns'] = all_columns
        return result

    # 导入主表数据
    def _import_main_table_datas(self, cid, table_name, columns, titles, rows,
                                 component_datas, join_table_datas,
                                 validate, merge):
        logger.info('<_import_main_table_datas> cid=' + str(cid) +
                    ', name=' + table_name +
                    ', validate=' + str(validate) + ', merge=' + str(merge))
        r = None
        if validate:
            r = self._validate_main_columns_datas(cid, columns, titles, rows,
                                                  component_datas,
                                                  join_table_datas)
        else:
            r = self._handle_main_columns_datas(cid, columns, titles, rows,
                                                component_datas,
                                                join_table_datas)
        valid_datas = r['valid_datas']
        error_datas = r['error_datas']
        if merge:
            valid_datas = self._merge_table_datas(table_name, columns,
                                                  valid_datas)
        self.insert_main_table_datas(cid, table_name, columns, valid_datas)
        collect_count = len(valid_datas)
        fail_count = len(error_datas)
        logger.info('<import_main_table_datas> cid=' + str(cid) +
                    ', collect_count=' + str(collect_count) +
                    ', fail_count=' + str(fail_count))
        if fail_count > 0 and fail_count < 50:
            logger.info('<import_main_table_datas> cid=' + str(cid) +
                        ', error_datas=' + str(error_datas))
        result = {'collect_count': collect_count,
                  'fail_count': fail_count}
        return result

    # 导入子表数据
    def _import_components_datas(self, cid, components, titles, rows,
                                 merge=False):
        logger.info('<_import_components_datas> cid=' + str(cid) +
                    ', merge=' + str(merge))
        result = {}
        for com in components:
            name = com['name']
            columns = com['columns']
            datas = self._handle_columns_datas(cid, name, columns, titles,
                                               rows)
            if merge:
                datas = self._merge_table_datas(name, columns, datas)
            r = self.insert_components_datas(cid, name, columns, datas)
            collect_count = len(datas)
            logger.info('<_import_components_datas> cid=' + str(cid) +
                        ', name=' + name +
                        ', collect_count=' + str(collect_count))
            code = r['code']
            if code == ErrorCode.OK.value:
                id_dict = r.get('id_dict')
                if id_dict is not None:
                    result[name] = id_dict
        return result

    # 导入关联表数据
    def _import_jointables_datas(self, cid, jointables, titles, rows,
                                 merge=True):
        logger.info('<_import_jointables_datas> cid=' + str(cid) +
                    ', merge=' + str(merge))
        result = {}
        for jt in jointables:
            name = jt['name']
            columns = jt['columns']
            d = self._get_jointables_unique_column_values(columns, titles,
                                                          rows)
            uni_key = d['unique_key']
            ucv_dict = d['ucv_dict']
            datas = self._handle_columns_datas(cid, name, columns, titles,
                                               rows)
            if merge:
                datas = self._merge_table_datas(name, columns, datas)
            collect_count = len(datas)
            logger.info('<_import_jointables_datas> cid=' + str(cid) +
                        ', name=' + name +
                        ', collect_count=' + str(collect_count) +
                        ', datas=' + str(datas))
            r = self.insert_jointables_datas(cid, name, uni_key, datas)
            code = r['code']
            if code == ErrorCode.OK.value:
                id_dict = r.get('id_dict')
                if id_dict is not None:
                    refs_dict = {}
                    for k, v in ucv_dict.items():
                        refs_dict[k] = id_dict[v]
                    result[name] = refs_dict
        return result

    def _get_jointables_unique_column_values(self, columns, titles, rows):
        ucv_dict = {}
        unique_key = None
        index = -1
        for c in columns:
            keys = c.keys()
            if 'unique' in keys:
                is_unique = c['unique']
                if is_unique and 'mapping' in keys:
                    unique_key = c['name']
                    mapping = c['mapping']
                    if mapping in titles:
                        index = titles.index(mapping)
                        break
        if index != -1:
            for r in rows:
                rowid = r['rowid']
                data = r['data']
                ucv_dict[rowid] = data[index]
        return {'unique_key': unique_key, 'ucv_dict': ucv_dict}

    # 将导入文件行数据转换为字典数据并进行数据类型转换
    def _handle_main_columns_datas(self, cid, columns, titles, rows,
                                   component_datas, join_table_datas):
        logger.info('<_handle_main_columns_datas> columns=' + str(columns))
        valid_datas = []
        components = []
        joinTables = []
        for c in columns:
            keys = c.keys()
            if 'component' in keys:
                components.append(c)
            elif 'joinTable' in keys:
                joinTables.append(c)

        self._handle_columns_index(columns, titles)

        for r in rows:
            rowid = r['rowid']
            data = {'no': rowid}
            if cid is not None:
                data['collection_id'] = cid
            d = r['data']
            other_columns = self._handle_json_columns_datas(columns,
                                                            data, d)
            for c in other_columns:
                k = c['name']
                index = c['index']
                if index != -1:
                    data[k] = d[index]
            # 设置导入渠道
            channel_id = data.get('channel_id')
            if channel_id is None:
                data['channel_id'] = self.channel_id
            valid_datas.append(data)

        if len(components) > 0:
            for d in valid_datas:
                rowid = d['no']
                for c in components:
                    name = c['name']
                    com = c['component']
                    jc = c['joinColumn']
                    d[name] = self._get_component_value(rowid, com, jc,
                                                        component_datas)

        if len(joinTables) > 0:
            for d in valid_datas:
                rowid = d['no']
                for c in joinTables:
                    name = c['name']
                    jt = c['joinTable']
                    jc = c['joinColumn']
                    d[name] = self._get_jointable_value(rowid, jt, jc,
                                                        join_table_datas)

        return {'valid_datas': valid_datas, 'error_datas': []}

    # 将导入文件行数据转换为字典数据并对数据进行验证
    def _validate_main_columns_datas(self, cid, columns, titles, rows,
                                     component_datas, join_table_datas):
        logger.info('<_validate_main_columns_datas> columns=' + str(columns))
        valid_datas = []
        error_datas = []

        self._handle_columns_index(columns, titles)
        for r in rows:
            rowid = r['rowid']
            d = r['data']
            data = {'no': rowid, 'collection_id': cid}
            rd = self._validate_json_columns_datas(columns, data, d)
            validate_pass = rd['validate_pass']
            validate_errors = rd['validate_errors']
            other_columns = rd['other_columns']

            for c in other_columns:
                k = c['name']
                index = c['index']
                if index != -1:
                    data[k] = d[index]
                else:
                    v = None
                    com = c.get('component')
                    if com is not None:
                        jc = c['joinColumn']
                        v = self._get_component_value(rowid, com, jc,
                                                      component_datas)
                    else:
                        jt = c.get('joinTable')
                        if jt is not None:
                            jc = c['joinColumn']
                            v = self._get_jointable_value(rowid, jt, jc,
                                                          join_table_datas)
                    data[k] = v
                    if v is None:
                        nullable = c.get('nullable')
                        if nullable is not None and not nullable:
                            validate_pass = False
                            msg = '{}的值验证失败，找不到关联数据！'
                            validate_errors.append(msg.format(k))
            # 设置导入渠道
            channel_id = data.get('channel_id')
            if channel_id is None:
                data['channel_id'] = self.channel_id

            if validate_pass:
                if self.validate_type == 'Mark':
                    data['effective'] = r.get('effective', 1)
                    data['err_msg'] = r.get('err_msg', None)
                valid_datas.append(data)
            else:
                if self.validate_type == 'Mark':
                    data['effective'] = 2
                    data['err_msg'] = str(validate_errors)
                    valid_datas.append(data)
                error_datas.append({'no': rowid,
                                    'validate_result': validate_errors})
        return {'valid_datas': valid_datas, 'error_datas': error_datas}

    # 将name相同的字段值构造为json数据存储，当导入字段未在数据库表中定义时，
    # 可以构造为json格式数据存储在扩展字段中。
    def _handle_json_columns_datas(self, columns, data, values):
        other_columns = []
        count_dict = {}
        for c in columns:
            name = c['name']
            count = count_dict.get(name)
            if count is None:
                count_dict[name] = 1
            else:
                count_dict[name] = count + 1

        # 找出需要构造json值的字段
        json_columns_names = []
        for k, v in count_dict.items():
            if v > 1:
                json_columns_names.append(k)

        # 处理json值的字段赋值
        json_data = {}
        for c in columns:
            k = c['name']
            t = c['type']
            if k in json_columns_names:
                m = c['mapping']
                logger.debug('<_handle_json_columns_datas> name: ' + k +
                             ', mapping: ' + m)
                index = c['index']
                if index != -1:
                    d = json_data.get(k)
                    if d is None:
                        d = {}
                        d[m] = values[index]
                        json_data[k] = d
                    else:
                        d[m] = values[index]
            elif t == 'Json':
                index = c['index']
                if index != -1:
                    # 如果最后一列为Json类型
                    data[k] = self._get_json_value(name, index, values)
            else:
                other_columns.append(c)

        for k, v in json_data.items():
            data[k] = json.dumps(v, ensure_ascii=False)

        # 返回为处理字段
        return other_columns

    # 将name相同的字段值构造为json数据存储，当导入字段未在数据库表中定义时，
    # 可以构造为json格式数据存储在扩展字段中。
    def _validate_json_columns_datas(self, columns, data, values):
        validate_pass = True
        validate_errors = []
        other_columns = []
        count_dict = {}
        for c in columns:
            name = c['name']
            count = count_dict.get(name)
            if count is None:
                count_dict[name] = 1
            else:
                count_dict[name] = count + 1

        # 找出需要构造json值的字段
        json_columns_names = []
        for k, v in count_dict.items():
            if v > 1:
                json_columns_names.append(k)

        # 处理json值的字段赋值
        json_data = {}
        for c in columns:
            k = c['name']
            t = c['type']
            if k in json_columns_names:
                n = c['label']
                m = c['mapping']
                logger.debug('<_handle_json_columns_datas> name: ' + k +
                             ', mapping: ' + m)
                index = c['index']
                v = None
                if index != -1:
                    d = json_data.get(k)
                    if d is None:
                        d = {}
                        v = values[index]
                        d[m] = v
                        json_data[k] = d
                    else:
                        v = values[index]
                        d[m] = v
                vr = validate_value(m, n, t, v, c)
                if vr['code'] != 0:
                    validate_pass = False
                    validate_errors.append(vr['message'])
            elif t == 'Json':
                index = c['index']
                if index != -1:
                    # 如果最后一列为Json类型
                    data[k] = self._get_json_value(name, index, values)
                else:
                    n = c['label']
                    m = c['mapping']
                    msg = '{0}{1}的值验证失败，值不允许为空！'
                    validate_pass = False
                    validate_errors.append(msg.format(n, m))
            else:
                other_columns.append(c)

        for k, v in json_data.items():
            data[k] = json.dumps(v, ensure_ascii=False)

        # 返回为处理字段
        return {'validate_pass': validate_pass,
                'validate_errors': validate_errors,
                'other_columns': other_columns}

    def _get_json_value(self, name, index, values):
        logger.debug('<_get_json_value> name: ' + name +
                     ', index: ' + str(index))
        try:
            return values[index]
        except Exception:
            logger.exception('<_get_json_value> errors=')
        return ''

    def _get_component_value(self, rowid, component, join_column,
                             component_datas):
        datas = component_datas.get(component)
        if datas is not None:
            data = datas.get(rowid)
            if type(data) == dict:
                return data.get(join_column)
            else:
                return data
        return None

    def _get_jointable_value(self, k, join_table, join_column,
                             join_table_datas):
        datas = join_table_datas.get(join_table)
        if datas is not None:
            data = datas.get(k)
            if data is not None:
                if type(data) == dict:
                    return data.get(join_column)
                else:
                    return data
        return None

    # 匹配字段对应标题序号
    def _handle_columns_index(self, columns, titles):
        for c in columns:
            index = -1
            keys = c.keys()
            if 'mapping' in keys:
                mapping = c['mapping']
                if mapping in titles:
                    index = titles.index(mapping)
                if index == -1:
                    if 'label' in keys:
                        label = c['label']
                        if label in titles:
                            index = titles.index(label)
            c['index'] = index

    # 将导入文件行数据转换为字典数据并进行数据类型转换
    def _handle_columns_datas(self, cid, name, columns, titles, rows):
        logger.debug('<_handle_columns_data> name=' + name +
                     ', columns=' + str(columns))
        datas = []
        self._handle_columns_index(columns, titles)
        for r in rows:
            data = {'no': r['rowid']}
            if cid is not None:
                data['collection_id'] = cid
            d = r['data']
            for c in columns:
                k = c['name']
                index = c['index']
                if index != -1:
                    data[k] = d[index]
            datas.append(data)
        return datas

    # 验证值是否有效并根据数据类型转换值
    def _validate_csv_datas(self, cid, columns, titles, rows):
        logger.info('<_validate_csv_datas> cid=' + str(cid) +
                    ', columns=' + str(columns))
        valid_datas = []
        error_datas = []
        self._handle_columns_index(columns, titles)
        for r in rows:
            validate_pass = True
            validate_errors = []
            rowid = r['rowid']
            d = r['data']
            for c in columns:
                k = c['name']
                n = c['label']
                t = c['type']
                m = c.get('mapping')
                index = c['index']
                if index != -1:
                    v = d[index]
                    # 验证数据值是否有效
                    vr = validate_value(m, n, t, v, c)
                    if vr['code'] == 0:
                        # 根据数据类型转换数据
                        nv = self.transform_value(k, t, v, c)
                        d[index] = nv
                    else:
                        validate_pass = False
                        # d[index] = None
                        validate_errors.append(vr['message'])
                else:
                    if m is not None:
                        vr = validate_value(m, n, t, None, c)
                        validate_pass = False
                        validate_errors.append(vr['message'])

            if validate_pass:
                if self.validate_type == 'Mark':
                    r['effective'] = 1
                valid_datas.append(r)
            else:
                if self.validate_type == 'Mark':
                    r['effective'] = 2
                    r['err_msg'] = str(validate_errors)
                    valid_datas.append(r)
                error_datas.append({'no': rowid,
                                    'validate_result': validate_errors})
                # error_datas.append(data)
        error_count = len(error_datas)
        valid_count = len(rows) - error_count
        logger.info('<_validate_csv_datas> cid=' + str(cid) +
                    ', valid_count=' + str(valid_count) +
                    ', error_count=' + str(error_count))
        if error_count > 0 and error_count < 50:
            logger.info('<_validate_csv_datas> cid=' + str(cid) +
                        ', error_datas=' + str(error_datas))
        return {'valid_datas': valid_datas, 'error_datas': error_datas}

    # 根据数据类型转换值
    def _convert_csv_datas(self, cid, columns, titles, rows):
        logger.info('<_convert_csv_datas> cid=' + str(cid) +
                    ', columns=' + str(columns))
        self._handle_columns_index(columns, titles)
        for r in rows:
            d = r['data']
            for c in columns:
                k = c['name']
                t = c['type']
                index = c['index']
                if index != -1:
                    v = d[index]
                    d[index] = self.transform_value(k, t, v, c)
        return rows

    # 合并导入数据
    def merge_csv_datas(self, cid, unique_keys, titles, datas):
        datas_count = len(datas)
        if len(unique_keys) > 0 and datas_count > 0:
            merged_datas = merge_rows(unique_keys, titles, datas)
            merged_count = len(merged_datas)
            logger.info('<merge_csv_datas> cid=' + str(cid) +
                        ', unique_keys=' + str(unique_keys) +
                        ', datas_count=' + str(datas_count) +
                        ', merged_count=' + str(merged_count))
            return merged_datas
        return datas

    # 合并导入数据
    def _merge_table_datas(self, name, columns, datas):
        datas_count = len(datas)
        if datas_count > 0:
            uni_keys = []
            for c in columns:
                unique = c.get('unique')
                if unique is not None and unique:
                    uni_keys.append(c['name'])
            if len(uni_keys) > 0:
                merged_datas = merge_datalist(uni_keys, datas)
                merged_count = len(merged_datas)
                logger.info('<_merge_table_datas> name=' + name +
                            ', unique_keys=' + str(uni_keys) +
                            ', datas_count=' + str(datas_count) +
                            ', merged_count=' + str(merged_count))
                return merged_datas
        return datas

    # 解析csv文件数据
    def parse_csv_file_datas(self, filename, unique_keys, merge):
        logger.info('<parse_csv_file_datas> filename=' + filename +
                    ', merge=' + str(merge))
        r = None
        try:
            if merge and unique_keys is not None:
                r = self.merge_parse_csv_file(filename, unique_keys, 'utf-8',
                                              self.sep)
            else:
                r = self.parse_csv_file(filename, 'utf-8', self.sep)
        except Exception:
            if merge and unique_keys is not None:
                r = self.merge_parse_csv_file(filename, unique_keys, 'GBK',
                                              self.sep)
            else:
                r = self.parse_csv_file(filename, 'GBK', self.sep)
        return r

    # 解析CSV文件标题
    def get_csv_file_titles(self, filename, relative=False):
        logger.info('<get_csv_file_titles> filename=' + filename)
        titles = None
        if relative:
            filename = setting['upload'] + filename
        try:
            titles = self.parse_csv_file_titles(filename, 'utf-8', self.sep)
        except Exception:
            titles = self.parse_csv_file_titles(filename, 'GBK', self.sep)
        return titles

    # 解析CSV文件标题
    def parse_csv_file_titles(self, filename, chartset, sep=','):
        logger.info('<parse_csv_file_titles> filename=' + filename +
                    ', sep=' + sep)
        titles = []
        for rid, line in enumerate(codecs.open(filename, 'r', chartset)):
            ts = self._strip_line(line).split(sep)
            for t in ts:
                titles.append(self._strip(t))
            break
        logger.info('<parse_csv_file_titles> filename=' + filename +
                    ', titles=' + str(titles))
        return titles

    # 解析CSV文件
    def parse_csv_file(self, filename, chartset, sep=','):
        logger.info('<parse_csv_file> filename=' + filename +
                    ', sep=' + sep)
        datas = []
        titles = []
        flag = True
        titles_count = 0
        split_num = 1
        for rid, line in enumerate(codecs.open(filename, 'r', chartset)):
            if flag:
                flag = False
                ts = self._strip_line(line).split(sep)
                for t in ts:
                    titles.append(self._strip(t))
                titles_count = len(titles)
                split_num = titles_count - 1
            else:
                if sep not in line:
                    continue
                line = self._strip_line(line)
                data = line.split(sep, split_num)
                if len(data) >= titles_count:
                    datas.append({'rowid': rid,
                                  'data': self._strip_data(data)})
                else:
                    logger.warning('<parse_csv_file> rowid: ' + str(rid + 1) +
                                   ', error data: ' + line)
        total = len(datas)
        logger.info('<parse_csv_file> filename=' + filename +
                    ', titles=' + str(titles) + ', datas total=' + str(total))
        return {'filename': filename, 'total': total,
                'titles': titles, 'list': datas}

    # 解析CSV文件，根据unique_keys去除重复数据
    def merge_parse_csv_file(self, filename, unique_keys, chartset, sep=','):
        logger.info('<merge_parse_csv_file> filename=' + filename +
                    ', unique_keys=' + str(unique_keys) + ', sep=' + sep)
        datas = []
        titles = []

        flag = True
        m_map = {}
        count = 0
        split_num = 1
        titles_count = 0
        for rid, line in enumerate(codecs.open(filename, 'r', chartset)):
            count += 1
            if flag:
                flag = False
                ts = self._strip_line(line).split(sep)
                for t in ts:
                    titles.append(self._strip(t))
                titles_count = len(titles)
                split_num = titles_count - 1
            else:
                if sep not in line:
                    continue
                line = self._strip_line(line)
                data = line.split(sep, split_num)
                if len(data) < titles_count:
                    logger.warning('<parse_csv_file> rowid: ' + str(rid + 1) +
                                   ', error data: ' + line)
                else:
                    data = self._strip_data(data)
                    i = 0
                    m_key = ''
                    for k in titles:
                        if k in unique_keys:
                            v = self._strip(data[i])
                            m_key = m_key + '@' + v
                        i += 1
                    if m_key not in m_map.keys():
                        datas.append({'rowid': rid, 'data': data})
                        m_map[m_key] = 1
        total = len(datas)
        logger.info('<merge_parse_csv_file> filename=' + filename +
                    ', titles=' + str(titles) + ', datas total=' + str(total))
        return {'filename': filename, 'total': count,
                'titles': titles, 'list': datas}

    # 分页解析CSV文件
    def page_parse_csv_file(self, filename, offset, limit, total,
                            chartset, sep=','):
        logger.info('<page_parse_csv_file> filename=' + filename +
                    ', offset=' + str(offset) + ', limit=' + str(limit) +
                    ', total=' + str(total))
        datas = []
        titles = []

        flag = True
        split_num = 1
        titles_count = 0
        offset = offset + 1
        end = offset + limit
        for index, line in enumerate(codecs.open(filename, 'r', chartset)):
            if flag:
                flag = False
                ts = self._strip_line(line).split(sep)
                for t in ts:
                    titles.append(self._strip(t))
                titles_count = len(titles)
                split_num = titles_count - 1
            else:
                if index >= offset:
                    if index < end:
                        if sep in line:
                            line = self._strip_line(line)
                            data = line.split(sep, split_num)
                            if len(data) < titles_count:
                                logger.warning('<parse_csv_file> rowid: ' +
                                               str(index + 1) +
                                               ', error data: ' + line)
                            else:
                                datas.append({'rowid': index, 'data': data})
                    else:
                        break

        return {'filename': filename, 'total': total,
                'titles': titles, 'list': datas}

    # 根据列索引获取数据值
    def _get_data_v(self, index, data, length):
        if index < length:
            return data[index]
        else:
            return None

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

    # 行数据数组转字典
    def rows2dict(slef, titles, rows):
        datas = []
        for r in rows:
            d = {'rowid': r['rowid']}
            data = r['data']
            i = 0
            for k in titles:
                d[k] = data[i]
                i += 1
            datas.append(d)
        return datas

    # 统计CSV文件行数
    def count_csv_file_lines(self, filename, relative=True):
        total = 0
        if relative:
            filename = setting['upload'] + filename
        try:
            f = codecs.open(filename, 'r', 'utf-8')
            total = sum(1 for x in enumerate(f))
        except Exception:
            f = codecs.open(filename, 'r', 'GBK')
            total = sum(1 for x in enumerate(f))
        if total > 0:
            total = total - 1
        return total
