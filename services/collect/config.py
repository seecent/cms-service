
from __future__ import absolute_import

from api.errorcode import ErrorCode
from config import setting
from log import logger
import os.path
import xml.etree.ElementTree as ET


class CollectConfigService:
    # 解析导入配置XML文件
    def parse_config(self, name, filename):
        logger.info('<parse_config> filename=' + filename)
        result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
        try:
            config = {}
            filename = setting['lms_home'] + os.path.sep +\
                "conf" + os.path.sep + filename
            tree = ET.parse(filename)
            root = tree.getroot()
            if root.tag != name:
                return {'code': ErrorCode.PARSE_XML_ERROR.value,
                        'message': ErrorCode.PARSE_XML_ERROR.name}
            config = self._check_node_attrib_value(root.attrib)
            config['tag'] = root.tag
            for c in root:
                if c.tag == 'Columns':
                    config['columns'] = self._parse_columns(c)
                elif c.tag == 'Components':
                    config['components'] = self._parse_components(c)
                elif c.tag == 'JoinTables':
                    config['jointables'] = self._parse_jointables(c)
                elif c.tag == 'UniqueKeys':
                    config['uniquekeys'] = self._parse_uniquekeys(c)
                    config['mergekeys'] = self._parse_mergekeys(c)
                elif c.tag == 'UniqueDateRange':
                    config['mergedays'] = self._parse_mergedays(c)
                elif c.tag == 'Separator':
                    config['separator'] = self._parse_separator(c)
            result = self.validate_config(name, filename, config)
        except Exception as e:
            logger.exception('<parse_config> error: ')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result

    # 验证导入配置XML文件是否正确
    def validate_config(self, name, filename, config):
        logger.info('<validate_config> filename=' + filename)
        errors = []
        components = config.get('components')
        jointables = config.get('jointables')
        columns = config['columns']
        for c in columns:
            com = c.get('component')
            if com is not None:
                r = self._validate_component(com, components)
                if not r:
                    m = '{0} Column component[{1}] 没有在 Components 中配置！'
                    errors.append(m.format(name, com))
            jt = c.get('joinTable')
            if jt is not None:
                r = self._validate_jointable(jt, jointables)
                if not r:
                    m = '{0} Column joinTable[{1}] 没有在 JoinTables 中配置！'
                    errors.append(m.format(name, jt))

        if jointables is not None:
            errors += self._check_jointables_unique_key(jointables)
        result = None
        if len(errors) > 0:
            logger.error('<validate_config> filename=' + filename +
                         ', errors: ' + str(errors))
            result = {'code': ErrorCode.PARSE_XML_ERROR.value,
                      'message': ErrorCode.PARSE_XML_ERROR.name,
                      'errors': errors}
        else:
            logger.info('<validate_config> filename=' + filename +
                        ', config is correct!')
            result = {'code': ErrorCode.OK.value,
                      'message': ErrorCode.OK.name,
                      'config': config}
        return result

    def _validate_component(self, component, components):
        if components is None:
            return False
        for c in components:
            if c['name'] == component:
                return True
        return False

    def _validate_jointable(self, jointable, jointables):
        if jointables is None:
            return False
        for jt in jointables:
            if jt['name'] == jointable:
                return True
        return False

    # 检测jointable唯一值字段是否存在
    # jointable必须有且有一个唯一值字段用于和主表关联
    def _check_jointables_unique_key(self, jointables):
        errors = []
        for jt in jointables:
            name = jt['name']
            columns = jt['columns']
            check_pass = False
            for c in columns:
                unique = c.get('unique')
                if unique is not None and unique:
                    check_pass = True
                    break
            if not check_pass:
                m = 'JoinTables [{}] 没有设置唯一值列, 要求有且有一个Column的unique属性值为true！'
                errors.append(m.format(name))
        return errors

    def _parse_uniquekeys(self, node):
        uniquekeys = []
        for c in node:
            uniquekeys.append(c.attrib['mapping'])
        return uniquekeys

    def _parse_mergekeys(self, node):
        mergekeys = []
        for c in node:
            mergekeys.append(c.attrib['name'])
        return mergekeys

    def _parse_mergedays(self, node):
        merge_days = 30
        try:
            days = node.attrib['days']
            if days and days != '':
                merge_days = int(days)
        except Exception as e:
            pass
        return merge_days

    def _parse_separator(self, node):
        separator = ","
        try:
            sep = node.attrib['sep']
            if sep is not None:
                separator = sep
        except Exception as e:
            pass
        return separator

    def _parse_columns(self, node):
        columns = []
        for c in node:
            columns.append(self._check_column_attrib_value(c.attrib))
        return columns

    def _parse_components(self, node):
        components = []
        for c in node:
            data = c.attrib
            data['tag'] = c.tag
            data['columns'] = self._parse_columns(c)
            components.append(data)
        return components

    def _parse_jointables(self, node):
        jointables = []
        for c in node:
            data = c.attrib
            data['tag'] = c.tag
            data['columns'] = self._parse_columns(c)
            jointables.append(data)
        return jointables

    def _check_node_attrib_value(self, attrib):
        d = {}
        for k, v in attrib.items():
            if k == 'validate':
                d[k] = self._check_boolean_value(k, v)
            elif k == 'merge':
                d[k] = self._check_boolean_value(k, v)
            else:
                d[k] = v
        return d

    def _check_column_attrib_value(self, attrib):
        d = {}
        for k, v in attrib.items():
            if k == 'unique':
                d[k] = self._check_boolean_value(k, v)
            elif k == 'nullable':
                d[k] = self._check_boolean_value(k, v)
            elif k == 'length':
                d[k] = int(v.strip())
            elif k == 'enums':
                d[k] = self._value2dict(v.strip())
            elif k == 'transform':
                d[k] = self._value2dict(v.strip())
            else:
                d[k] = v
        return d

    def _check_boolean_value(self, name, value):
        if value == 'true':
            return True
        else:
            return False

    def _value2dict(self, v):
        d = {}
        if v != '':
            for s in v.split(','):
                splits = s.split(':')
                k = splits[0]
                d[k] = splits[1]
        return d
