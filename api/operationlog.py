
from __future__ import absolute_import
import hug

from config import db
from api.auth.user import check_sysadmin, query_current_user
from models.operationlog import operationlogs
from models.auth.user import users
from models import rows2data
from sqlalchemy.sql import or_
IGNORES = {'last_modifed'}


@hug.object.urls('')
class OperationLogs(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = operationlogs.alias('o')
        joins = {'user': {
                 'select': ['id', 'username'],
                 'table': users.alias('u')}}
        query = db.filter_join(t, joins, request, ['-created_date'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            query = db.filter_by_user(t, query, u)
        if q:
            q = '%{}%'.format(q)
            filters = or_(t.c.name.like(q),
                          t.c.detail.like(q),
                          t.c.username.like(q))
            query = query.where(filters)
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)

        return rows2data(rows, operationlogs, joins, IGNORES)
