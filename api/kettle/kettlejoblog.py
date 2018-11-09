from __future__ import absolute_import
import hug
from api.ext.dateutil import DateUtil
from config import db
from models.kettle.kettlejob import kettlejobs
from models.kettle.kettlejoblog import kettlejoblogs
from models import rows2data

IGNORES = {'startdate', 'enddate'}


@hug.object.urls('')
class KettleJobLogs(object):

    @hug.object.get()
    def get(self, request, response):
        log_date = request.params.get('logDate')
        t = kettlejoblogs.alias('k')
        j = kettlejobs.alias('j')
        joins = {'job': {
                 'column': t.c.jobname,
                 'select': ['id', 'name', 'job_module',
                            'job_schedule', 'update_mode',
                            'description'],
                 'table': j,
                 'join_column': j.c.name}}
        query = db.filter_join(t, joins, request, ['-logdate'])
        if log_date:
            dates = DateUtil.getDayBetween(log_date)
            query = query.where(t.c.logdate.between(dates[0], dates[1]))
        else:
            query = db.filter_by_date(t.c.logdate, query, request)
        rs = db.paginate_data(query, request, response)
        return rows2data(rs, t, joins)
