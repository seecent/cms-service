from __future__ import absolute_import


class DBUtil:
    @staticmethod
    def get_selects(table, column_names: list):
        """
        根据字段名获取 table 查询 column 列表。

        :param table: 数据库表（sqlalchemy.Table类型）。
        :param column_names: 查询字段名称列表（list）。
        :retruns: 查询字段列表（list）。
        """
        cols = []
        for c in table.c:
            if c.name in column_names:
                cols.append(c)
        return cols

    @staticmethod
    def get_column_names(mapping, indexs, key):
        """
        根据序号获取查询字段名称列表，处理过程：\n
           1）根据展示字段生成一个二进制字符串，如果第n个字段在表格\n
              中展示将二进制字符串第n位字符设置为1，否则设置为0.\n
           2）将二进制字符串转换为整数传到后台。\n
           3）将整数解析为二进制字符串。\n
           4）根据二进制字符串和mappgin字段进行匹配，遍历mapping,如\n
              果字段对应序号在二进制字符串中的字符为1,将字段添加到查\n
              询字段名称列表，否则不添加。\n
           5）返回查询字段名称列表。\n
           举例：get_column_names(mapping, indexs)。

        :param mapping: 数据库表字段名称映射（dict）。
        :param indexs: 字段序号（str）。
        :param key: 主键字段（str）。
        :retruns: 查询字段名称列表（list）。
        """
        column_names = [key]
        if indexs is not None:
            count = len(indexs)
            if count > 0:
                end = count - 1
                if count > len(mapping):
                    end = len(mapping) - 1
                indexs_dict = {}
                for i in range(0, end):
                    if indexs[i] == '1':
                        indexs_dict[i] = indexs[i]
                n = 0
                for k, v in mapping.items():
                    if indexs_dict.get(n) is not None:
                        column_names.append(v)
                    n += 1
        else:
            for k, v in mapping.items():
                column_names.append(v)
        return column_names

    @staticmethod
    def exchange_key_value(mapping):
        new_dict = {}
        for k, v in mapping.items():
            new_dict[v] = k
        return new_dict
