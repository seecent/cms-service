
from __future__ import absolute_import
import hug

from api.ext.dateutil import DateUtil
from config import db
from models.statistics.uacampaigndaystat import uacampaigndaystats
from sqlalchemy.sql import select


@hug.object.urls('')
class UaCampaignStats(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        campaign_id = request.params.get('campaignId')
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        t = uacampaigndaystats.alias('c')
        query = select([t.c.stat_date,
                        t.c.year,
                        t.c.month,
                        t.c.day,
                        t.c.campaign_name,
                        t.c.active_leads_count])
        if campaign_id:
            query = query.where(t.c.campaign_id == campaign_id)
        if begin_date and end_date:
            begin_time = int(begin_date)
            end_time = int(end_date)
            query = query.where(t.c.stat_date.between(begin_time, end_time))
        else:
            stat_dates = DateUtil.thisMonthStatRange()
            begin_time = stat_dates[0]
            end_time = stat_dates[1]
            query = query.where(t.c.stat_date.between(begin_time, end_time))
        rows = db.execute(query.order_by(t.c.stat_date.asc()))
        datas = []
        for r in rows:
            month = r[2]
            day = r[3]
            datas.append({'x': '{0}-{1}'.format(month, day), 'y': r[5]})
        return datas
