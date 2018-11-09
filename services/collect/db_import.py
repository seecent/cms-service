from __future__ import absolute_import


from datetime import datetime
from log import logger
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from api.errorcode import ErrorCode
from sqlalchemy.sql import select
from services.collect.validate import validate_value
from services.collect.import_base import CollectImportBase
from services.collect.merge import merge_datalist, merge_rows


# 从数据库导入
class CollectDBImportService(CollectImportBase):

    # 从数据库导入
    def import_from_db(self, cid, db_url, view_name, config,
                       validate, merge=True, params={}):
        logger.info('<import_from_db> cid=' + str(cid) +
                    ', view_name=' + view_name +
                    ', validate=' + str(validate) + ', merge=' + str(merge))
        start_time = datetime.now()
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            # 1. 读取配置文件conf/*_config.xml
            name = config.get('name')
            uni_keys = config.get('uniquekeys', [])
            columns = config.get('columns')
            components = config.get('components')
            jointables = config.get('jointables')

            # 2. 检测不允许为空列在导入源数据库视图中是否都存在
            engine = create_engine(
                db_url, echo=False, encoding='utf-8', convert_unicode=True)
            conn = engine.connect()
            source_count = self.fetch_source_db_datas_count(conn, cid,
                                                            view_name)
            print(source_count)
            titles = self.get_source_db_view_column_names(conn, cid,
                                                          view_name)
            result = self._check_source_db_view_column_names(cid, view_name,
                                                             titles,
                                                             columns,
                                                             components,
                                                             jointables)
            cols = result.get('columns')
            if result['code'] == ErrorCode.OK.value:
                # 2. 读取源数据库导入数据
                result = self.fetch_source_db_datas(conn, cid, view_name,
                                                    params)

            if result['code'] == ErrorCode.OK.value:
                datas = result['datas']
                source_count = len(datas)
                if validate:
                    # 4. 验证值是否有效并根据数据类型转换值
                    r = self._validate_db_datas(cid, cols, titles, datas)
                    datas = r['valid_datas']
                else:
                    datas = self._convert_db_datas(cid, cols, titles, datas)

                if merge:
                    datas = self.merge_db_datas(cid, uni_keys, titles, datas)

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
                logger.info('<import_from_db> cid=' + str(cid) +
                            ', source_count=' + str(source_count) +
                            ', collect_count=' + str(collect_count) +
                            ', fail_count=' + str(fail_count))
        except Exception as e:
            logger.exception('<import_from_db> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        end_time = datetime.now()
        cost_time = (end_time - start_time).microseconds / 1000
        result['cost_time'] = cost_time
        logger.info('<import_from_db> end! costtime=' +
                    str(cost_time) + 'ms')
        return result

    # 获取源数据库带入数据
    def fetch_source_db_datas(self, conn, cid, view_name, params=None):
        logger.info('<fetch_source_db_datas> cid=' + str(cid) +
                    ', view_name=' + view_name + ', params=' + str(params))
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            query = select([text('*')]).select_from(text(view_name))
            if params is not None:
                offset = params.pop('offset')
                limit = params.pop('limit')
                if offset is not None and limit is not None:
                    query = query.offset(offset).limit(limit)
            logger.info('<fetch_source_db_datas> cid=' + str(cid) +
                        ', view_name=' + view_name + ', sql=' + str(query))
            rs = conn.execute(query)
            cursor = rs.cursor
            desc = cursor.description
            column_names = [col[0] for col in desc]
            datas = []
            rows = cursor.fetchall()
            for index, row in enumerate(rows, start=1):
                datas.append({'rowid': index, 'data': list(row)})
            result['titles'] = column_names
            result['datas'] = datas
        except Exception as e:
            logger.exception('<fetch_source_db_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 获取源数据库导入视图列名
    def get_source_db_view_column_names(self, conn, cid, view_name):
        logger.info('<get_source_db_view_column_names> cid=' + str(cid) +
                    ', view_name=' + view_name)
        column_names = []
        try:
            sql = 'SELECT * FROM ' + view_name
            query = text(sql)
            rs = conn.execute(query)
            cursor = rs.cursor
            desc = cursor.description
            column_names = [col[0] for col in desc]
        except Exception as e:
            logger.exception('<get_source_db_view_column_names> error=')

        return column_names

    # 获取源数据库带入数据数量
    def fetch_source_db_datas_count(self, conn, cid, view_name, params=None):
        sql = 'SELECT count(1) FROM ' + view_name
        return conn.execute(text(sql)).scalar()

    # 2. 检测不允许为空列在导入源数据库视图中是否都存在
    def _check_source_db_view_column_names(self, cid, view_name, view_columns,
                                           columns, components, jointables):
        logger.info('<_check_source_db_view_column_names> cid=' + str(cid) +
                    ', view_name=' + view_name +
                    ', view_columns=' + str(view_columns))
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        msg = '源数据库导入视图{0}中不存在字段名为{1}的列！'
        errors = []
        all_columns = []
        if components is not None:
            for com in components:
                cols = com['columns']
                for c in cols:
                    mapping = c.get('mapping')
                    if mapping in view_columns:
                        all_columns.append(c)
                    else:
                        nullable = c.get('nullable')
                        if nullable is not None and nullable:
                            errors.append(msg.format(view_name, mapping))

        if jointables is not None:
            for jt in jointables:
                cols = jt['columns']
                for c in cols:
                    mapping = c.get('mapping')
                    if mapping in view_columns:
                        all_columns.append(c)
                    else:
                        nullable = c.get('nullable')
                        if nullable is not None and nullable:
                            errors.append(msg.format(view_name, mapping))

        for c in columns:
            mapping = c.get('mapping')
            if mapping is not None:
                if mapping in view_columns:
                    all_columns.append(c)
                else:
                    nullable = c.get('nullable')
                    if nullable is not None and nullable:
                        errors.append(msg.format(view_name, mapping))

        if len(errors) > 0:
            logger.error('<_check_source_db_view_column_names> cid=' +
                         str(cid) + ', view_name=' + view_name +
                         ', errors=' + str(errors))
            result = {'code': ErrorCode.DB_VIEW_VALIDATION_FAILED.value,
                      'message': ErrorCode.DB_VIEW_VALIDATION_FAILED.name,
                      'errors': errors}
        else:
            result['columns'] = all_columns
        return result

    # 验证值是否有效并根据数据类型转换值
    def _validate_db_datas(self, cid, columns, titles, rows):
        logger.debug('<_validate_db_datas> cid=' +
                     str(cid) + ', columns=' + str(columns))
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
                    if type(v) == str:
                        vr = validate_value(m, n, t, v, c)
                        if vr['code'] == 0:
                            # 根据数据类型转换数据
                            nv = self.convert_value(k, t, v, c)
                            d[index] = nv
                        else:
                            validate_pass = False
                            # d[index] = None
                            validate_errors.append(vr['message'])
                    else:
                        d[index] = v

            if validate_pass:
                valid_datas.append(r)
            else:
                error_datas.append({'no': rowid,
                                    'validate_result': validate_errors})
                # error_datas.append(data)
        valid_count = len(valid_datas)
        error_count = len(error_datas)
        logger.info('<_validate_db> cid=' + str(cid) +
                    ', valid_count=' + str(valid_count) +
                    ', error_count=' + str(error_count))
        if error_count > 0:
            logger.info('<_validate_db_datas> cid=' + str(cid) +
                        ', error_datas=' + str(error_datas))
        return {'valid_datas': valid_datas, 'error_datas': error_datas}

    # 根据数据类型转换值
    def _convert_db_datas(self, cid, columns, titles, rows):
        logger.info('<_convert_db_datas> cid=' + str(cid) +
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
                    d[index] = self.convert_value(k, t, v, c)
        return rows

    # 匹配字段对应标题序号
    def _handle_columns_index(self, columns, titles):
        for c in columns:
            index = -1
            keys = c.keys()
            if 'mapping' in keys:
                mapping = c['mapping']
                if mapping in titles:
                    index = titles.index(mapping)
            c['index'] = index

    # 根据类型转换数据
    def convert_value(self, name, data_type, value, params):
        try:
            if value is None:
                return None
            elif data_type == 'String':
                return str(value)
            else:
                if type(value) == str:
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

    # 合并导入数据
    def merge_db_datas(self, cid, unique_keys, titles, datas):
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
        if fail_count > 0:
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

    # 将导入行数据转换为字典数据并进行数据类型转换
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

    # 将导入行数据转换为字典数据并对数据进行验证
    def _validate_main_columns_datas(self, cid, columns, titles, rows,
                                     component_datas, join_table_datas):
        logger.info('<_validate_main_columns_datas> columns=' + str(columns))
        valid_datas = []
        error_datas = []

        self._handle_columns_index(columns, titles)
        for r in rows:
            validate_pass = True
            validate_errors = []
            rowid = r['rowid']
            d = r['data']
            data = {'no': rowid, 'collection_id': cid}
            for c in columns:
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

            if validate_pass:
                valid_datas.append(data)
            else:
                error_datas.append({'no': rowid,
                                    'validate_result': validate_errors})
                # error_datas.append(data)
        return {'valid_datas': valid_datas, 'error_datas': error_datas}

    # 将导入行数据转换为字典数据并进行数据类型转换
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
            for c in columns:
                k = c['name']
                index = c['index']
                if index != -1:
                    data[k] = d[index]
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

    def _get_component_value(self, rowid, component, join_column,
                             component_datas):
        datas = component_datas.get(component)
        if datas is not None:
            data = datas.get(rowid)
            if data is not None:
                return data.get(join_column)

    def _get_jointable_value(self, k, join_table, join_column,
                             join_table_datas):
        datas = join_table_datas.get(join_table)
        if datas is not None:
            data = datas.get(k)
            if data is not None:
                if isinstance(data, dict):  # 如果data不是字典对象则直接返回其值
                    return data.get(join_column)
                else:
                    return data
        return None

    # endregion
