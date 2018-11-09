# -*- coding: utf-8 -*-
import hug
from datetime import datetime
from sqlalchemy import create_engine, types, Table
from sqlalchemy.sql import select, and_, text
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.selectable import Alias
from services.security import SecurityService

security = SecurityService()


class SQLAlchemy:

    def __init__(self):
        self.engine = None
        self.conn = None
        self._conn_str = None

    def connect(self, **settings):
        """
        建立数据库链接。
        """
        self.conn = self.engine.connect()

    def _get_select_columns(self, selects):
        """
        获取查询字段列表。
        Parameters
        ----------
        selects : sqlalchemy.Table or sqlalchemy.Column list
          查找对象，selects可以是数据库表(sqlalchemy.Table类型对象)
          或者是数据库表字段列表(sqlalchemy.Column列表)
         
        Returns
        -------
        list
          查询字段列表
         
        Raises
        ------
        OtherError
          when an other error
        """
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

        return [cols, mapping]

    def _get_column(self, cols, name, mapping=None):
        """
        根据名称获取数据库表映射字段。
        Parameters
        ----------
        cols :
          数据库表字段列表(sqlalchemy.Column列表)
        name : str
          名称
        mapping : dict
          字段名称映射
         
        Returns
        -------
        list
          数据库表映射字段(sqlalchemy.Column类型)。
        """
        if mapping is not None:
            col_name = mapping.get(name)
            for c in cols:
                if c.name == col_name:
                    return c
        else:
            for c in cols:
                if c.name == name:
                    return c
        return None

    def _get_table_column(self, table, name):
        """
        根据名称获取数据库表映射字段。

        :param table: 数据库表(sqlalchemy.Table类型对象)
        :param name: 名称（str 类型）
        :retrun : 数据库表映射字段(sqlalchemy.Column类型)
        """
        for c in table.c:
            if c.name == name:
                return c
        return None

    def _filters(self, cols, params, mapping=None):
        """
        根据http请求参数构造数据库查询过滤条件，不支持关联查询。

        :param cols: 数据库表字段列表(sqlalchemy.Column列表)
        :param params: http请求参数字典（dict）
        :param mapping: 字段名称映射（dict）
        :retrun : 数据库查询表达式列表（list）
        """
        filters = []
        for k, v in params.items():
            if '.' not in k:
                n = k
                like = False
                if k.startswith('l_'):
                    n = k[2:]
                    like = True
                col = self._get_column(cols, n, mapping)
                if col is not None:
                    if like:
                        filters.append(col.like('%' + v + '%'))
                    elif isinstance(v, list):
                        filters.append(col.in_(
                            [self._check_value(col, i) for i in v]))
                    else:
                        filters.append(col == self._check_value(col, v))

        return filters

    def _prefix_filters(self, table, prefix, params):
        """
        根据http请求参数构造数据库查询过滤条件，支持关联查询。

        :param table: 数据库表(sqlalchemy.Table类型对象)
        :param prefix: 数据库关联查询关联表名称 (str 类型)
        :param params: http请求参数字典（dict）
        :retrun : 数据库查询表达式列表（list）
        """
        filters = []
        for k, v in params.items():
            if prefix + '.' in k:
                splits = k.split('.')
                n = splits[1]
                like = False
                if n.startswith('l_'):
                    n = k[2:]
                    like = True
                col = self._get_table_column(table, n)
                if col is not None:
                    if like:
                        filters.append(col.like('%' + v + '%'))
                    elif isinstance(v, list):
                        filters.append(col.in_(
                            [self._check_value(col, i) for i in v]))
                    else:
                        filters.append(col == self._check_value(col, v))

        return filters

    def _check_value(self, col, value):
        """
        检查数据值，根据col数据类型转换数据值。

        :param col: 数据库表字段(sqlalchemy.Column)
        :param value: 数据值
        :retrun : 根据col数据类型转换后数据值
        """
        coltype = col.type
        if isinstance(coltype, types.Integer):
            return self._check_int_value(value)
        elif isinstance(coltype, types.BigInteger):
            return self._check_int_value(value)
        elif isinstance(coltype, types.Numeric):
            return float(value)
        # elif isinstance(coltype, types.Enum):
        #     t, v = value.split(".")
        #     print(enums[t][v])
        #     return enums[t][v]
        else:
            if ',' in value:
                return value.split(',')
            else:
                return value

    def _check_int_value(self, value):
        if type(value) == str:
            if ',' in value:
                v_list = []
                for s in value.split(','):
                    v_list.append(int(s.strip()))
                return v_list
            else:
                return int(value)
        else:
            return value

    def _sort(self, col, is_desc):
        return col.desc() if is_desc else col.asc()
        # SQl Server nullslast 报错
        # return col.desc().nullslast() if is_desc else col.asc().nullslast()

    def _sorts(self, cols, sorts, mapping=None):
        """
        构造排序，不支持关联表字段排序。

        :param cols: 数据库表字段列表(sqlalchemy.Column列表)
        :param sorts: 排序字段名称（list）
        :param mapping: 字段名称映射（dict）
        :retrun : 排序列表（list）
        """
        orders = []
        for name in sorts:
            is_desc = name[0] == '-'
            if is_desc:
                name = name[1:]
            col = self._get_column(cols, name, mapping)
            if col is not None:
                orders.append(self._sort(col, is_desc))

        return orders

    def _prefix_sorts(self, table, prefix, sorts):
        """
        构造排序，支持关联查询按照关联表字段进行排序。

        :param table: 数据库表(sqlalchemy.Table类型对象)
        :param prefix: 数据库关联查询关联表名称（str 类型）
        :param params: http请求参数字典（dict）
        :retrun : 排序列表（list）
        """
        orders = []
        for name in sorts:
            if prefix + '.' in name:
                is_desc = name[0] == '-'
                if is_desc:
                    name = name[1:]
                splits = name.split('.')
                name = splits[1]
                col = self._get_table_column(table, name)
                if col is not None:
                    orders.append(self._sort(col, is_desc))

        return orders

    def query(self, selects, params=None):
        """
        根据 sqlalchemy 数据库表或者查询字段列表和 request 请求参数构造 query 查询对象。\n
        单表查询，不支持关联表查询。\n
        举例：\n
          1）查询数据库表所有字段 db.query(users, params)。\n
          2）查询指定字段 db.query([users.c.name, users.c.type], params)。

        :param selects: 查询数据库表(sqlalchemy.Table)或查询字段列表(sqlalchemy.Column list)。
        :param params: 查询参数字典。
        :returns: Sqlalchemy query查询对象。
        """
        sc = self._get_select_columns(selects)
        q = select(sc[0])
        if params is not None:
            filters = self._filters(sc[0], params, sc[1])
            if filters:
                q = q.where(and_(*filters))

        return q

    def order_by(self, selects, q, sorts):
        """
        排序，单表排序，不支持按照关联表字段排序。
        举例：\n
          1）db.order_by([users.c.name, users.c.type], query, ['name'])。\n
          2）db.order_by(users, query, sorts=['-user.name'])。

        :param selects: 查询数据库表(sqlalchemy.Table)或查询字段列表(sqlalchemy.Column list)。
        :param q: Sqlalchemy query查询对象。
        :param sorts: 排序字段名称列表，默认按照升序进行排序，降序排序在名称前面加上“-”符号。\n
          举例：\n
          1）按照name字段升序排序，sorts=['name']。\n
          2）按照name字段降序排序，sorts=['-name']。\n
          3）按照关联表user的name字段升序排序，sorts=['user.name']。\n
          4）按照关联表user的name字段降序排序，sorts=['-user.name']。\n
        :returns: Sqlalchemy query查询对象。
        """
        sc = self._get_select_columns(selects)
        sorts = sorts if isinstance(sorts, list) else [sorts]
        orders = self._sorts(sc[0], sorts, sc[1])
        if orders:
            q = q.order_by(*orders)

        return q

    def paginate(self, q, offset, limit):
        """
        分页查询, 举例：db.paginate(query, 0, 10)

        :param query: Sqlalchemy query查询对象。
        :param offset: 查询起始位置（int 类型）。
        :param limit: 每次查询记录数（int 类型）。
        :returns: Sqlalchemy query查询对象。
        """
        return q.offset(offset).limit(limit)

    def filter(self, selects, request, default_sort=[]):
        """
        根据sqlalchemy数据库表或者表字段列表和request请求参数构造query查询对象。\n
        单表查询，不支持关联表查询。举例：\n
            1）查询数据库表所有字段。\n
                query = db.filter(users, request)\n
            2）查询指定字段。\n
                query = db.filter([users.c.name, users.c.type], request)\n
            3）查询指定字段, 前端界面字段和数据库字段不一致，通过mapping进行字段映射。
                selects = {'select': [users.c.name, users.c.type],\n
                           'mapping': {'name': 'db_name', 'type': 'db_type'}}\n
                query = db.filter(selects, request)\n

        :param selects: 查询数据库表(sqlalchemy.Table)或查询字段列表(sqlalchemy.Column list)。
        :param request: HTTP请求 request 对象。
        :param default_sort: 默认排序字段列表 list, 降序排序在名称前面加上“-”符号。举例：\n
            1）按照name字段升序排序，sorts=['name']。\n
            2）按照name字段降序排序，sorts=['-name']。\n
        :returns: sqlalchemy.query 查询对象。
        """
        sorts = request.params.get('sort', default_sort)
        q = self.query(selects, request.params)
        q = self.order_by(selects, q, sorts)
        return q

    def filter_join(self, selects, joins, request, default_sort=[]):
        """
        根据sqlalchemy数据库表或者表字段列表和request请求参数构造query查询对象，\n
        支持关联表查询。举例：\n
            1）主表指定查询字段\n
                c = collections.alias('c')\n
                s = saleschannels.alias('s')\n
                selects = {'table': c, 'select': ['id', 'name']}\n
                joins = {'channel': {\n
                       'select': ['id', 'name'],\n
                       'table': s}}\n
                query = db.filter_join(selects, joins, request)\n
            2）主表指定查询字段, 前端界面字段和数据库字段不一致，通过mapping进行字段映射。\n
                c = collections.alias('c')\n
                s = saleschannels.alias('s')\n
                selects = {'table': c,\n
                         'select': [users.c.name, users.c.type],\n
                         'mapping': {'name': 'db_name',\n
                                     'type': 'db_type'}\n
                        }\n
                joins = {'channel': {\n
                       'select': ['id', 'name'],\n
                       'table': s}}\n
                query = db.filter_join(selects, joins, request)\n
            3）主表查询全部字段，使用默认关联字段（collections表字段channel_id与\n
                saleschannels表id字段关联）。\n
                c = collections.alias('c')\n
                s = saleschannels.alias('s')\n
                joins = {'channel': {\n
                       'select': name,\n
                       'table': s}}\n
                query = db.filter_join(c, joins, request)\n
            4）主表查询全部字段，指定关联字段，指定关联表查询字段。\n
                c = collections.alias('c')\n
                s = saleschannels.alias('s')\n
                joins = {'channel': {
                       'column': c.c.channel_id,\n
                       'select': ['id', 'name']\n
                       'table': s,\n
                       'join_column': s.c.id}}\n
                query = db.filter_join(c, joins, request)\n

        :param selects: 查询数据库表(sqlalchemy.Table)或查询字段列表(sqlalchemy.Column list)。
        :param joins: 关联表查询参数 (dict)。
        :param request: HTTP请求 request 对象。
        :param default_sort: 默认排序字段列表 list, 降序排序在名称前面加上“-”符号。举例：\n
            1）按照name字段升序排序，sorts=['name']。\n
            2）按照name字段降序排序，sorts=['-name']。\n
            3）按照关联表user的name字段升序排序，sorts=['user.name']。\n
            4）按照关联表user的name字段降序排序，sorts=['-user.name']。\n
        :returns: sqlalchemy.query 查询对象。
        """
        table = None
        mapping = None
        # 构造查询字段
        cols = []
        if type(selects) == dict:
            table = selects['table']
            cols = selects['select']
            mapping = selects.get('mapping')
        else:
            table = selects
            for c in table.c:
                cols.append(c)

        # 添加关联表查询字段
        for (k, v) in joins.items():
            jt = v['table']
            js = v['select']
            if js:
                if isinstance(js, str):
                    c = self._get_table_column(jt, js)
                    if c is not None:
                        cols.append(c.label(jt.name + '_' + c.name))
                elif isinstance(js, list):
                    for n in js:
                        c = self._get_table_column(jt, n)
                        if c is not None:
                            cols.append(c.label(jt.name + '_' + c.name))
            else:
                for c in jt.c:
                    cols.append(c.label(jt.name + '_' + c.name))

        # 表关联查询
        join = None
        for (k, v) in joins.items():
            jt = v['table']
            if 'column' in v.keys() and 'join_column' in v.keys():
                tc = v['column']
                jc = v['join_column']
                if join is None:
                    join = table.outerjoin(jt, tc == jc)
                else:
                    join = join.outerjoin(jt, tc == jc)
            else:
                fcol = self._get_table_column(table, k + '_id')
                if fcol is not None:
                    if join is None:
                        join = table.outerjoin(jt, fcol == jt.c.id)
                    else:
                        join = join.outerjoin(jt, fcol == jt.c.id)

        q = select(cols)
        if join is not None:
            q = q.select_from(join)

        params = {}
        if request is not None:
            params = request.params
            # 查询条件
            filters = self._filters(cols, params, mapping)
            for (k, v) in joins.items():
                jt = v['table']
                filters.extend(self._prefix_filters(jt, k, params))

            if filters:
                q = q.where(and_(*filters))

        # 排序
        sorts = params.get('sort', default_sort)
        sorts = sorts if isinstance(sorts, list) else [sorts]
        orders = self._sorts(cols, sorts, mapping)
        for (k, v) in joins.items():
            jt = v['table']
            orders.extend(self._prefix_sorts(jt, k, sorts))

        if orders:
            q = q.order_by(*orders)

        return q

    def filter_by_date(self, column, q, request):
        """
        追加日期过滤查询条件, 举例：db.filter_by_date(users.c.created_date, query, request)。

        :param column: 数据库表日期字段，sqlalchemy.Column 类型。
        :param q: sqlalchemy.query 查询对象。
        :param request: HTTP请求 request 对象。
        :returns: sqlalchemy.query 查询对象。
        """
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        if begin_date and end_date:
            df = "%Y-%m-%d %H:%M:%S"
            begin_time = datetime.strptime(begin_date + " 00:00:00", df)
            end_time = datetime.strptime(end_date + " 23:59:59", df)
            q = q.where(column.between(begin_time, end_time))
        return q

    def filter_by_user(self, table, q, user):
        """
        追加所属用户过滤查询条件, 举例：db.filter_by_user(operationlogs, query, user)。

        :param table: 数据库表，sqlalchemy.Table 类型。
        :param q: sqlalchemy.query 查询对象。
        :param user: 用户信息。
        :returns: sqlalchemy.query 查询对象。
        """
        user_id = user.get('id')
        if user_id is not None:
            q = q.where(table.c.user_id == user_id)
        elif user.get('username') is not None:
            q = q.where(table.c.username == user.get('username'))
        return q

    def paginate_data(self, q, request, response):
        """
        分页查询, 举例：db.paginate_data(query, request, response)。

        :param q: sqlalchemy.query 查询对象。
        :param request: HTTP请求 request 对象。
        :param response: HTTP相应 response 对象。
        :returns: rows, 数据库查询结果集。
        """
        offset = int(request.params.get('offset', 0))
        limit = min(int(request.params.get('limit', 15)), 100)
        # splits = str(q).split('FROM')
        # c = text('SELECT count(1) FROM ' + splits[1])
        c = select([func.count('1')]).select_from(q.alias('n'))
        count = self.conn.execute(c).scalar()
        response.set_header('X-Total-Count', str(count))
        q = q.offset(offset).limit(limit)
        rows = self.conn.execute(q)
        return rows

    def fetch_all(self, table, sorts=[]):
        """
        获取全部记录, 举例：db.fetch_all(users, ['name'])

        :param table: 查询数据库表，sqlalchemy.Table类型。
        :param sorts: 排序字段名称列表，默认按照升序进行排序，降序排序在名称前面加上“-”符号。
        :returns: rows, 数据库查询结果集。
        """
        q = select([table])
        if sorts:
            orders = self._sorts(table.c, sorts)
            if orders:
                q = q.order_by(*orders)
        rows = self.conn.execute(q).fetchall()
        return rows

    def fetch_one(self, query):
        """
        获取一条记录, 举例：db.fetch_one(query)

        :param query: 查询query对象，sqlalchemy.query类型。
        :returns: 数据库查询结果。
        """
        return self.conn.execute(query).fetchone()

    def count(self, query, where=None):
        """
        查询记录数量。举例：\n
          1）查询用户表总记录数 db.count(users)。\n
          2）查询语句查询记录数: db.count(select([func.count('1')]).select_from(users))。

        :param query: 查询query对象(sqlalchemy.query)或数据库表(sqlalchemy.Table)。
        :returns: 查询结果数量。
        """
        if type(query) == Table:
            q = select([func.count('1')]).select_from(query.alias('t'))
            if where is not None:
                q = q.where(where)
            return self.conn.execute(q).scalar()
        else:
            return self.conn.execute(query).scalar()

    def get(self, table, id):
        """
        获取指定id数据库表记录, 举例：db.get(users, 1)。

        :param table: 查询数据库表，sqlalchemy.Table类型。
        :returns: 数据库查询结果。
        """
        cols = []
        a = table.alias('a')
        for c in a.c:
            cols.append(c)
        q = select(cols).where(a.c.id == id)
        return self.conn.execute(q).fetchone()

    def insert(self, table, data):
        """
        插入记录, 举例：db.insert(users, {'username': 'test', 'created_date': now})。

        :param table: 数据库表，sqlalchemy.Table类型。
        :returns: 插入记录主键值。
        """
        tx = self.conn.begin()
        try:
            r = self.conn.execute(table.insert(), data)
            tx.commit()
            return r.inserted_primary_key[0]
        except BaseException:
            tx.rollback()
            raise

    def bulk_insert(self, table, datas):
        """
        批量插入记录, 举例：db.insert(users, [{'name': 'test1'}, {'name': 'test2'}])。

        :param table: 数据库表，sqlalchemy.Table类型。
        :param data: 插入数据dict。
        :returns: 插入记录主键值。
        """
        tx = self.conn.begin()
        try:
            r = self.conn.execute(table.insert(), datas)
            tx.commit()
            return r
        except BaseException:
            tx.rollback()
            raise

    def save(self, table, data):
        """
        保存记录, 举例：db.save(users, {'username': 'test', 'created_date': now})。

        :param table: 数据库表，sqlalchemy.Table类型。
        :param data: 保存数据dict。
        :returns: data, data['id'] = 插入记录主键值。
        """
        tx = self.conn.begin()
        try:
            r = self.conn.execute(table.insert(), data)
            tx.commit()
            data['id'] = r.inserted_primary_key[0]
            return data
        except BaseException:
            tx.rollback()
            raise

    def update(self, table, data):
        """
        修改记录, 举例：db.update(users, {'id': 1, 'name': 'test2'})。

        :param table: 数据库表，sqlalchemy.Table类型。
        :param data: 修改数据dict。
        :returns: 修改结果，True or False。
        """
        tx = self.conn.begin()
        try:
            id = data.pop('id')
            stmt = table.update().where(table.c.id == id).values(data)
            self.conn.execute(stmt)
            tx.commit()
        except BaseException as e:
            tx.rollback()
            raise e

    def set_null_on_delete(self, table, col_name, id):
        """
        修改记录, 举例：db.set_null_on_delete(operlog, operlog.user_id, 2)

        :param table: 数据库表，sqlalchemy.Table类型。
        :param col_name: 外键字段名称。
        :param id：外键值。
        :returns: 修改结果，True or False。
        """
        col = self._get_table_column(table, col_name)
        if col is not None:
            stmt = table.update().where(col == id).values({col_name: None})
            self.conn.execute(stmt)

    def delete(self, table, id):
        """
        删除指定id数据库表记录, 举例：db.delete(users, 1)。

        :param table: 数据库表，sqlalchemy.Table类型。
        :param id: 需要删除记录的id。
        :returns: 删除结果，True or False。
        """
        tx = self.conn.begin()
        try:
            self.conn.execute(table.delete().where(table.c.id == id))
            tx.commit()
        except BaseException as e:
            tx.rollback()
            raise e

    def bulk_delete(self, table, ids):
        """
        批量数据库表记录, 举例：db.delete(users, [1, 2, 3])。

        :param table: 数据库表，sqlalchemy.Table类型。
        :param id: 需要删除记录的id列表。
        :returns: 删除结果，True or False。
        """
        tx = self.conn.begin()
        try:
            if type(ids) == str:
                ids = ids.split(',')
            self.conn.execute(table.delete().where(table.c.id.in_(ids)))
            tx.commit()
        except BaseException as e:
            tx.rollback()
            raise e

    def execute(self, stmt, params=None):
        """
        执行数据库语句, 举例：db.execute(users.insert(), {'username': 'test'})。

        :param stmt: 数据库语句，sqlalchemy.query类型。
        :param params: 参数dict。
        """
        if params is not None:
            return self.conn.execute(stmt, params)
        else:
            return self.conn.execute(stmt)

    def begin(self):
        """
        开始事物。

        :returns: 事物对象。
        """
        return self.conn.begin()

    def close(self):
        """
        关闭数据库链接。
        """
        self.conn.close()

    def check_db_type(self, db_type):
        if db_type == self.db_type:
            return True
        elif db_type in self.db_type:
            return True
        elif db_type == 'sqlserver':
            if 'mssql' in self.db_type:
                return True
        return False

    def init_app(self, app, datasource):
        """
        该方法在app.py中调用，hug启动运行进行db初始化。

        :param app: hug app。
        :param conn_str: 数据库链接字符串。
        """
        conn_str = '{0}://{1}:{2}@{3}:{4}/{5}'
        db_type = datasource['type']
        username = datasource['username']
        password = security.decrypt(datasource['password'])
        host = datasource['host']
        port = datasource['port']
        database = datasource['database']
        charset = datasource.get('charset', None)
        conn_str = conn_str.format(db_type, username, password,
                                   host, str(port), database)
        if charset is not None and db_type != 'postgresql':
            conn_str += '?charset=' + charset
        self.db_type = db_type
        self._conn_str = conn_str
        self.engine = create_engine(self._conn_str, echo=False,
                                    encoding='utf-8', convert_unicode=True)

        @hug.request_middleware(api=app)
        def process_req_data(request, response):
            self.connect()

        @hug.response_middleware(api=app)
        def process_res_data(request, response, resource):
            self.close()

        return app
