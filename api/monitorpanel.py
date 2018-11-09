
from __future__ import absolute_import
import hug

from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func

from api.auth.user import check_sysadmin, query_current_user
from config import db
from datetime import datetime
from models.collection import collections
from models.saleschannel import saleschannels
from models.campaign import campaigns
from models.monitorchart import monitorcharts
from models.rawleads import rawleads

DF = "%Y-%m-%d %H:%M:%S"


@hug.object.urls('')
class MonitorPanels(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        mid = request.params.get('id')
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        u = query_current_user(request)
        mc = monitorcharts.alias('m')
        sc = saleschannels.alias('s')
        ca = campaigns.alias('ca')
        cl = collections.alias('c')
        q = select([mc.c.id,
                    mc.c.name,
                    mc.c.status,
                    mc.c.channel_id,
                    sc.c.name,
                    mc.c.campaign_id,
                    ca.c.name,
                    mc.c.collection_id,
                    cl.c.code,
                    mc.c.begin_date,
                    mc.c.end_date,
                    mc.c.collect_count,
                    mc.c.viable_count,
                    mc.c.merge_count])
        c = select([func.count(mc.c.id)])
        join = mc.outerjoin(sc, mc.c.channel_id == sc.c.id)
        join = join.outerjoin(cl, mc.c.collection_id == cl.c.id)
        join = join.outerjoin(ca, mc.c.campaign_id == ca.c.id)
        q = q.select_from(join)
        c = c.select_from(join)
        q = q.where(mc.c.status == 'Open')
        c = c.where(mc.c.status == 'Open')
        if mid:
            q = q.where(mc.c.id == mid)
            c = c.where(mc.c.id == mid)
        if u and not check_sysadmin(u):
            q = db.filter_by_user(mc, q, u)
            c = db.filter_by_user(mc, c, u)
        count = db.count(c)
        q = q.order_by(mc.c.created_date.desc())
        rows = db.execute(q).fetchall()
        data = []
        for r in rows:
            d = {}
            d['id'] = r[0]
            d['name'] = r[1]
            d['status'] = str(r[2])
            d['channel_id'] = r[3]
            d['channel'] = r[4]
            d['campaign_id'] = r[5]
            d['campaign'] = r[6]
            d['collection_id'] = r[7]
            d['collection'] = r[8]
            d['begin_date'] = str(r[9])
            d['end_date'] = str(r[10])
            d['collect_count'] = count_leads(db, 0, d, begin_date, end_date)
            d['viable_count'] = count_leads(db, 1, d, begin_date, end_date)
            d['merge_count'] = count_leads(db, 2, d, begin_date, end_date)
            data.append(d)

        response.set_header('X-Total-Count', str(count))
        return data


def count_leads(db, effective, monitorchart, begin_date, end_date):
    rl = rawleads.alias('l')
    c = select([func.count(rl.c.id)])
    cid = monitorchart['collection_id']
    channel_id = monitorchart['channel_id']
    campaign_id = monitorchart['campaign_id']
    if effective == 1:
        c = c.where(rl.c.effective == 1)
    if effective == 2:
        c = c.where(rl.c.effective == 1)
        c = c.where(rl.c.merge_status == 1)
    if cid:
        c = c.where(rl.c.collection_id == cid)
    if channel_id:
        c = c.where(rl.c.channel_id == channel_id)
    if campaign_id:
        c = c.where(rl.c.campaign_id == campaign_id)
    if begin_date and end_date:
        begin_time = datetime.strptime(begin_date + " 00:00:00", DF)
        end_time = datetime.strptime(end_date + " 23:59:59", DF)
        c = c.where(rl.c.created_date.between(begin_time, end_time))
    else:
        begin_date = monitorchart['begin_date']
        end_date = monitorchart['end_date']
        if begin_date != 'None' and end_date != 'None':
            begin_date = begin_date.split(' ')[0]
            end_date = end_date.split(' ')[0]
            begin_time = datetime.strptime(begin_date + " 00:00:00", DF)
            end_time = datetime.strptime(end_date + " 23:59:59", DF)
            c = c.where(rl.c.created_date.between(begin_time, end_time))

    count = db.count(c)
    return count
