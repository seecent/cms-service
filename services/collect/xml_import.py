
from __future__ import absolute_import

import codecs
from api.errorcode import ErrorCode
from config import setting
from datetime import datetime
from log import logger
from services.collect.import_base import CollectImportBase
from services.collect.merge import merge_datalist
from services.collect.validate import validate_value
import xml.etree.ElementTree as ET


# XML文件导入
class CollectXMLImportService(CollectImportBase):

    def __init__(self, validate_type='Filter', merge_type='Filter'):
        self.validate_type = validate_type
        self.merge_type = merge_type

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

    # 从XML文本导入数据，用于XML导入实时接口
    def import_from_xml(self, cid, xml, config, validate, merge=True):
        logger.info('<import_from_xml> cid=' + str(cid) +
                    ', xml=' + xml)
        start_time = datetime.now()
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            name = config['name']
            tag = config['tag']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')

            # 1. 解析导入XML文件
            result = self._parse_xml(xml, name, tag, columns,
                                     components, jointables)

            code = result['code']
            if code == ErrorCode.OK.value:
                datas = result['list']
                result = self._import_datas(cid, name, columns, components,
                                            jointables, datas, validate, merge)
        except Exception as e:
            logger.exception('<import_from_xml_file> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        end_time = datetime.now()
        cost_time = (end_time - start_time).microseconds / 1000
        result['cost_time'] = cost_time
        logger.info('<import_from_xml_file> end! costtime=' +
                    str(cost_time) + 'ms')
        return result

    # 从XML文件导入数据
    def import_from_xml_file(self, cid, filename, config,
                             validate, merge=True):
        logger.info('<import_from_xml_file> cid=' + str(cid) +
                    ', filename=' + filename)
        start_time = datetime.now()
        filename = setting['upload'] + filename
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            name = config['name']
            tag = config['tag']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')

            # 1. 解析导入XML文件
            result = self._parse_xml_file(filename, name, tag, columns,
                                          components, jointables)
            code = result['code']
            if code == ErrorCode.OK.value:
                datas = result['list']
                result = self._import_datas(cid, name, columns, components,
                                            jointables, datas, validate, merge)
        except Exception as e:
            logger.exception('<import_from_xml_file> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        end_time = datetime.now()
        cost_time = (end_time - start_time).microseconds / 1000
        result['cost_time'] = cost_time
        logger.info('<import_from_xml_file> end! costtime=' +
                    str(cost_time) + 'ms')
        return result

    # 预览XML文件数据
    def preview_xml_file_datas(self, filename, config, offset, limit):
        logger.info('<preview_xml_file_datas> filename=' + filename +
                    ', offset=' + str(offset) + ", limit=" + str(limit))
        filename = setting['upload'] + filename
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            name = config['name']
            tag = config['tag']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')

            # 1. 解析导入XML文件
            result = self._page_parse_xml_file(filename, name, tag,
                                               offset, limit, columns,
                                               components, jointables)
        except Exception as e:
            logger.exception('<preview_xml_file_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 获取XML文件标题
    def get_xml_file_titles(self, filename, config):
        logger.info('<get_xml_file_titles> filename=' + filename)
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            name = config['name']
            tag = config['tag']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')
            titles = self._parse_xml_file_titles(name, tag, columns,
                                                 components, jointables)
            result['titles'] = titles
        except Exception as e:
            logger.exception('<get_xml_file_titles> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 获取XML文件标题
    def _parse_xml_file_titles(self, name, tag, columns,
                               components, jointables):
        titles = []
        for c in columns:
            mapping = c.get('mapping')
            if mapping is not None:
                title = {}
                name = c['name']
                title['dataIndex'] = name
                title['key'] = name
                title['name'] = mapping
                titles.append(title)

        if components is not None:
            for com in components:
                com_name = com['name']
                com_tag = com['tag']
                columns = com['columns']
                for c in columns:
                    title = {}
                    name = c['name']
                    mapping = c['mapping']
                    title['dataIndex'] = com_name + '.' + name
                    title['key'] = name
                    title['name'] = mapping
                    title['group'] = com_name
                    title['groupTitle'] = com_tag
                    titles.append(title)

        if jointables is not None:
            for jt in jointables:
                jt_name = jt['name']
                jt_tag = jt['tag']
                columns = jt['columns']
                for c in columns:
                    title = {}
                    name = c['name']
                    mapping = c['mapping']
                    title['dataIndex'] = jt_name + '.' + name
                    title['key'] = name
                    title['name'] = jt_tag + ' ' + mapping
                    title['group'] = jt_name
                    title['groupTitle'] = jt_tag
                    titles.append(title)

        return titles

    # 创建导入模板文件
    def create_template_xml_file(self, filename, config):
        logger.info('<create_template_xml_file> filename=' + filename)
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            tag = config['tag']
            columns = config['columns']
            components = config.get('components')
            jointables = config.get('jointables')
            root = ET.Element(tag + 'List')
            node = ET.SubElement(root, tag)
            for c in columns:
                mapping = c.get('mapping')
                if mapping is not None:
                    ET.SubElement(node, mapping)

            if components is not None:
                for com in components:
                    cnode = ET.SubElement(node, com['tag'])
                    cols = com['columns']
                    for c in cols:
                        ET.SubElement(cnode, c.get('mapping'))

            if jointables is not None:
                for jt in jointables:
                    cnode = ET.SubElement(node, jt['tag'])
                    cols = jt['columns']
                    for c in cols:
                        ET.SubElement(cnode, c.get('mapping'))

            template_filename = setting['upload'] + filename
            # root.write(template_filename, encoding='utf-8')
            xml = ET.tostring(root, encoding='utf-8', method='xml')
            print(bytes.decode(xml))
            f = codecs.open(template_filename, 'w', 'utf-8')
            f.write(xml.decode('utf-8'))
            f.close()
        except Exception as e:
            logger.exception('<create_template_xml_file> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 导入具体业务逻辑实现
    def _import_datas(self, cid, name, columns, components,
                      jointables, datas, validate, merge=True):
        source_count = len(datas)
        logger.info('<_import_datas> cid=' + str(cid) +
                    ', name=' + name + ', datas size=' + str(source_count))
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name,
                  'source_count': source_count}
        try:
            if validate:
                # 2. 校验数据
                r = self._validate_datas(cid, name, columns, components,
                                         jointables, datas)
                datas = r['valid_datas']

            # if merge:
            #     # 3. 合并数据
            #     unique_keys = config['uniquekeys']
            #     if unique_keys is not None:
            #         datas = self.validate_datas(unique_keys, datas)

            # 4. 根据数据类型转换数据
            datas = self._convert_datas(name, columns, components,
                                        jointables, datas)

            unique_keys = {}
            com_datas = {}
            jt_datas = {}

            # 5. 实现数据导入数据库
            # 5.1 导入关联表数据
            if jointables is not None:
                unique_keys = self._get_jointables_unique_keys(jointables)
                jt_datas = self._import_jointables_datas(cid, jointables,
                                                         datas, validate)
            # 5.2 导入子表数据
            if components is not None:
                com_datas = self._import_components_datas(cid, components,
                                                          datas, validate)
            # 5.3 导入主表数据
            r = self._import_main_table_datas(cid, name, columns, datas,
                                              com_datas, jt_datas,
                                              unique_keys, validate,
                                              merge)

            collect_count = r['collect_count']
            fail_count = source_count - collect_count
            logger.info('<_import_datas> cid=' + str(cid) +
                        ', source_count=' + str(source_count) +
                        ', collect_count=' + str(collect_count) +
                        ', fail_count=' + str(fail_count))

            result['collect_count'] = collect_count
            result['fail_count'] = fail_count
        except Exception as e:
            logger.exception('<_import_datas> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 导入主表数据
    def _import_main_table_datas(self, cid, table_name, columns, datas,
                                 component_datas, join_table_datas,
                                 unique_keys, validate, merge):
        logger.info('<_import_main_table_datas> cid=' + str(cid) +
                    ', name=' + table_name +
                    ', validate=' + str(validate) + ', merge=' + str(merge))

        valid_datas = []
        error_datas = []
        components = []
        joinTables = []
        for c in columns:
            keys = c.keys()
            if 'component' in keys:
                components.append(c)
            elif 'joinTable' in keys:
                joinTables.append(c)

        if len(components) > 0:
            for d in datas:
                validate_pass = True
                validate_errors = []
                rowid = d['no']
                for c in components:
                    name = c['name']
                    com = c['component']
                    jc = c['joinColumn']
                    v = self._get_component_value(rowid, com, jc,
                                                  component_datas)
                    d[name] = v
                    if v is None:
                        nullable = c.get('nullable')
                        if nullable is not None and not nullable:
                            validate_pass = False
                            msg = '{}的值验证失败，找不到关联数据！'
                            validate_errors.append(msg.format(name))
                if validate_pass:
                    d['collection_id'] = cid
                    valid_datas.append(d)
                else:
                    if self.validate_type == 'Mark':
                        d['effective'] = 2
                        d['collection_id'] = cid
                        d['err_msg'] = self._to_err_msg(validate_errors)
                        valid_datas.append(d)
                    error_datas.append({'no': rowid,
                                        'validate_result': validate_errors})

        if len(joinTables) > 0:
            for d in datas:
                rowid = d['no']
                for c in joinTables:
                    name = c['name']
                    jt = c['joinTable']
                    jc = c['joinColumn']
                    uni_key = unique_keys[jt]
                    jt_data = d.pop(jt)
                    k = jt_data.get(uni_key)
                    if k is not None:
                        d[name] = self._get_jointable_value(k, jt, jc,
                                                            join_table_datas)
        self.insert_main_table_datas(cid, table_name, columns, valid_datas)
        collect_count = len(valid_datas)
        fail_count = len(error_datas)
        logger.info('<_import_main_table_datas> cid=' + str(cid) +
                    ', collect_count=' + str(collect_count) +
                    ', fail_count=' + str(fail_count))
        if fail_count > 0:
            logger.info('<_import_main_table_datas> cid=' + str(cid) +
                        ', error_datas=' + str(error_datas))
        result = {'collect_count': collect_count,
                  'fail_count': fail_count}
        return result

    def _get_component_value(self, rowid, component, join_column,
                             component_datas):
        datas = component_datas.get(component)
        if datas is not None:
            data = datas.get(rowid)
            if data is not None:
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

    # 导入子表数据
    def _import_components_datas(self, cid, components, datas, validate,
                                 merge=False):
        logger.info('<_import_components_datas> cid=' + str(cid) +
                    ', validate=' + str(validate) + ', merge=' + str(merge))
        result = {}
        for com in components:
            name = com['name']
            new_datas = []
            if validate:
                for d in datas:
                    data = d.get(name)
                    if data is not None:
                        data['collection_id'] = cid
                        new_datas.append(data)
            else:
                for d in datas:
                    if name in d.keys():
                        data = d[name]
                        data['collection_id'] = cid
                        new_datas.append(data)
            # 保存到数据库
            r = self.insert_components_datas(cid, name, None, new_datas)
            collect_count = len(new_datas)
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
    def _import_jointables_datas(self, cid, jointables, datas, validate,
                                 merge=True):
        logger.info('<_import_jointables_datas> cid=' + str(cid) +
                    ', validate=' + str(validate) + ', merge=' + str(merge))
        result = {}
        for jt in jointables:
            name = jt['name']
            columns = jt['columns']
            uni_key = self._get_jointable_unique_key(columns)
            new_datas = []
            if validate:
                for d in datas:
                    new_datas.append(d[name])
            else:
                for d in datas:
                    if name in d.keys():
                        new_datas.append(d[name])

            if merge:
                new_datas = self._merge_import_datas(name, columns,
                                                     new_datas)

            logger.info('<_import_jointables_datas> cid=' + str(cid) +
                        ', name=' + name +
                        ', datas=' + str(new_datas))
            # 保存到数据库
            r = self.insert_jointables_datas(cid, name, uni_key, new_datas)
            collect_count = len(new_datas)
            logger.info('<_import_jointables_datas> cid=' + str(cid) +
                        ', name=' + name +
                        ', collect_count=' + str(collect_count))
            code = r['code']
            if code == ErrorCode.OK.value:
                id_dict = r['id_dict']
                result[name] = id_dict
        return result

    # 合并导入数据
    def _merge_import_datas(self, name, columns, datas):
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
                logger.info('<_merge_import_datas> name=' + name +
                            ', unique_keys=' + str(uni_keys) +
                            ', datas_count=' + str(datas_count) +
                            ', merged_count=' + str(merged_count))
                return merged_datas
        return datas

    def _get_jointables_unique_keys(self, jointables):
        unique_keys = {}
        for jt in jointables:
            name = jt['name']
            columns = jt['columns']
            uni_key = self._get_jointable_unique_key(columns)
            unique_keys[name] = uni_key
        return unique_keys

    def _get_jointable_unique_key(self, columns):
        unique_key = None
        for c in columns:
            unique = c.get('unique')
            if unique is not None and unique:
                unique_key = c['name']
                break
        return unique_key

    # 验证数据
    def _validate_datas(self, cid, name, columns, components, jointables,
                        datas):
        logger.info('<_validate_datas> name=' + name + ', datas size=' +
                    str(len(datas)))
        valid_datas = []
        error_datas = []
        for d in datas:
            rowid = d['no']
            validate_pass = True
            validate_errors = {}
            for c in columns:
                k = c['name']
                if k in d.keys():
                    t = c['type']
                    v = d[k]
                    n = c.get('label', '')
                    # 验证数据值是否有效
                    vr = validate_value(k, n, t, v, c)
                    if vr['code'] != 0:
                        validate_pass = False
                        validate_errors[k] = vr['message']
                else:
                    nullable = True
                    if 'nullable' in c.keys():
                        nullable = c['nullable']
                    if not nullable:
                        if 'component' in c.keys():
                            com = c['component']
                            if com not in d.keys():
                                msg = '{}的值验证失败，值不允许为空！'
                                validate_pass = False
                                validate_errors[k] = msg.format(k)
                        elif 'joinTable' in c.keys():
                            jt = c['joinTable']
                            if jt not in d.keys():
                                msg = '{}的值验证失败，值不允许为空！'
                                validate_pass = False
                                validate_errors[k] = msg.format(k)
            # 验证关联表字段值是否有效
            r = self._validate_jointables_data(components, rowid, d)
            if len(r) > 0:
                validate_pass = False
                for k, v in r.items():
                    validate_errors[k] = v
            r = self._validate_jointables_data(jointables, rowid, d)
            if len(r) > 0:
                validate_pass = False
                for k, v in r.items():
                    validate_errors[k] = v
            if validate_pass:
                if self.validate_type == 'Mark':
                    d['effective'] = 1
                    d['err_msg'] = None
                valid_datas.append(d)
            else:
                if self.validate_type == 'Mark':
                    d['effective'] = 2
                    d['err_msg'] = self._to_err_msg(validate_errors)
                    valid_datas.append(d)
                error_datas.append({'no': rowid,
                                    'validate_errors': validate_errors})

        error_count = len(error_datas)
        valid_count = len(datas) - error_count
        logger.info('<_validate_datas> cid=' + str(cid) +
                    ', valid_count=' + str(valid_count) +
                    ', error_count=' + str(error_count))
        if error_count > 0 and error_count < 50:
            logger.info('<_validate_datas> cid=' + str(cid) +
                        ', error_datas=' + str(error_datas))
        return {'valid_datas': valid_datas, 'error_datas': error_datas}

    def _to_err_msg(self, validate_errors):
        err_msg = ''
        try:
            if type(validate_errors) == dict:
                errors = []
                for k, v in validate_errors.items():
                    errors.extend(v)
                err_msg = str(errors)
            else:
                err_msg = str(validate_errors)
        except Exception as e:
            logger.exception('<_to_err_msg> error=')
        return err_msg

    def _validate_jointables_data(self, jointables, no, data):
        result = {}
        if jointables is not None:
            for jt in jointables:
                name = jt['name']
                if name in data.keys():
                    validate_errors = []
                    d = data[name]
                    columns = jt['columns']
                    for c in columns:
                        k = c['name']
                        if k in d.keys():
                            t = c['type']
                            v = d[k]
                            n = c.get('label', '')
                            # 验证数据值是否有效
                            vr = validate_value(k, n, t, v, c)
                            if vr['code'] != 0:
                                validate_errors.append(vr['message'])
                    if len(validate_errors) > 0:
                        result[name] = validate_errors

        return result

    # 根据数据类型转换数据
    def _convert_datas(self, name, columns, components, jointables, datas):
        logger.info('<_convert_datas> name=' + name + ', datas size=' +
                    str(len(datas)))
        for d in datas:
            for c in columns:
                k = c['name']
                if k in d.keys():
                    t = c['type']
                    v = d[k]
                    # 根据数据类型转换数据
                    d[k] = self.transform_value(k, t, v, c)
            # 根据数据类型转换数据(关联表)
            self._convert_jointables_data(components, d)
            self._convert_jointables_data(jointables, d)
        return datas

    def _convert_jointables_data(self, jointables, data):
        if jointables is not None:
            for jt in jointables:
                name = jt['name']
                if name in data.keys():
                    d = data[name]
                    columns = jt['columns']
                    for c in columns:
                        k = c['name']
                        if k in d.keys():
                            t = c['type']
                            v = d[k]
                            # 根据数据类型转换数据
                            d[k] = self.transform_value(k, t, v, c)
        return data

    # 解析XML文件
    def _parse_xml_file(self, filename, name, tag, columns,
                        components, jointables):
        logger.info('<_parse_xml_file> filename=' + filename)
        datas = []
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            root_tag = tag + 'List'
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag != root_tag:
                return {'code': ErrorCode.PARSE_XML_ERROR.value,
                        'message': ErrorCode.PARSE_XML_ERROR.name}
            no = 0
            for c in root:
                no = no + 1
                data = self._parse_xml_node(name, tag, no, c, columns,
                                            components, jointables)
                datas.append(data)

            total = len(datas)
            logger.info('<_parse_xml_file> filename=' + filename +
                        ', datas total=' + str(total))
            result['filename'] = filename
            result['total'] = total
            result['list'] = datas
        except Exception as e:
            logger.exception('<_parse_xml_file> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 分页解析XML文件
    def _page_parse_xml_file(self, filename, name, tag, offset, limit,
                             columns, components, jointables):
        logger.info('<_page_parse_xml_file> filename=' + filename +
                    ', offset=' + str(offset) + ', limit=' + str(limit))
        datas = []
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            root_tag = tag + 'List'
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag != root_tag:
                return {'code': ErrorCode.PARSE_XML_ERROR.value,
                        'message': ErrorCode.PARSE_XML_ERROR.name}

            end = offset + limit
            no = 0
            for c in root:
                if no >= offset and no < end:
                    no = no + 1
                    data = self._parse_xml_node(name, tag, no, c, columns,
                                                components, jointables)
                    datas.append(data)

            total = len(datas)
            logger.info('<_page_parse_xml_file> filename=' + filename +
                        ', datas total=' + str(total))
            result['filename'] = filename
            result['total'] = total
            result['list'] = datas
        except Exception as e:
            logger.exception('<_page_parse_xml_file> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 解析XML文本
    def _parse_xml(self, xml, name, tag, columns, components, jointables):
        logger.info('<_parse_xml> xml=' + xml)
        datas = []
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            root_tag = tag + 'List'
            root = ET.fromstring(xml)
            if root.tag != root_tag:
                return {'code': ErrorCode.PARSE_XML_ERROR.value,
                        'message': ErrorCode.PARSE_XML_ERROR.name}
            no = 0
            for c in root:
                no = no + 1
                data = self._parse_xml_node(name, tag, no, c, columns,
                                            components, jointables)
                datas.append(data)

            total = len(datas)
            logger.info('<_parse_xml> datas total=' + str(total))
            result['total'] = total
            result['list'] = datas
        except Exception as e:
            logger.exception('<_parse_xml> error=')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    def _parse_xml_node(self, name, tag, no, node, columns,
                        components, jointables):
        logger.info('<_parse_xml_node> name=' + name + ', tag=' + tag +
                    ', no=' + str(no))
        data = self._parse_xml_columns_data(no, node, columns, True)
        if components is not None:
            for com in components:
                com_tag = com['tag']
                n = node.find(com_tag)
                if n is not None:
                    com_name = com['name']
                    d = self._parse_xml_columns_data(no, n, com['columns'])
                    data[com_name] = d

        if jointables is not None:
            for jt in jointables:
                jt_tag = jt['tag']
                n = node.find(jt_tag)
                if n is not None:
                    jt_name = jt['name']
                    d = self._parse_xml_columns_data(None, n, jt['columns'])
                    data[jt_name] = d
        return data

    def _parse_xml_columns_data(self, no, node, columns, check_mapping=False):
        data = {}
        if no is not None:
            data['no'] = no
        if check_mapping:
            for c in columns:
                mapping = c.get('mapping')
                if mapping is not None:
                    n = node.find(mapping)
                    if n is not None:
                        name = c['name']
                        data[name] = n.text
        else:
            for c in columns:
                mapping = c['mapping']
                n = node.find(mapping)
                if n is not None:
                    name = c['name']
                    data[name] = n.text

        return data

    # 统计XML文件数据总数
    def count_xml_datas_total(self, filename, tag):
        total = 0
        try:
            filename = setting['upload'] + filename
            root_tag = tag + 'List'
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag == root_tag:
                for c in root:
                    if c.tag == tag:
                        total = total + 1
        except Exception as e:
            logger.exception('<count_xml_datas_total> error=')

        return total
