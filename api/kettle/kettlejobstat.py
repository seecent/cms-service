
from __future__ import absolute_import
import hug

from api.ext.dateutil import DateUtil
from config import db
from models.kettle.kettlejobdaystat import kettlejobdaystats
from sqlalchemy.sql import select


@hug.object.urls('')
class KettleJobStats(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        t = kettlejobdaystats.alias('t')
        query = select([t.c.stat_date,
                        t.c.year,
                        t.c.month,
                        t.c.day,
                        t.c.run_count,
                        t.c.success_count,
                        t.c.fail_count])
        if begin_date and end_date:
            begin_time = int(begin_date)
            end_time = int(end_date)
            query = query.where(t.c.stat_date.between(begin_time, end_time))
        else:
            date_range = DateUtil.last15DaysStatRange()
            query = query.where(t.c.stat_date.between(
                date_range[0], date_range[1]))
        rows = db.execute(query.order_by(t.c.stat_date.asc()))
        datas = []
        for r in rows:
            year = r[1]
            month = r[2]
            day = r[3]
            date = '{0}-{1}-{2}'.format(year, month, day)
            datas.append({'x': date, 'y1': r[5], 'y2': r[6]})
        return datas
