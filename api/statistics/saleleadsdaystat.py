
from __future__ import absolute_import
import hug

from api.ext.dateutil import DateUtil
from config import db, mdb
from datetime import datetime, timedelta
from log import logger
from models.mdb.ams.amssales import amssales
from models.leads.activeleads import activeleads
from models.statistics.saleleadsdaystat import saleleadsdaystats
from sqlalchemy.sql import select


@hug.object.urls('')
class SaleLeadsDayStats(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        saleno = request.params.get('saleNo')
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        t = saleleadsdaystats.alias('c')
        query = select([t.c.stat_date,
                        t.c.year,
                        t.c.month,
                        t.c.day,
                        t.c.saleno,
                        t.c.lead_count,
                        t.c.call_count,
                        t.c.visit_count,
                        t.c.order_count])
        if saleno:
            query = query.where(t.c.saleno == saleno)
        if begin_date and end_date:
            begin_time = begin_date
            end_time = end_date
            query = query.where(t.c.stat_date.between(begin_time, end_time))
        else:
            stat_dates = DateUtil.thisMonthStatRange()
            begin_time = stat_dates[0]
            end_time = stat_dates[1]
            query = query.where(t.c.stat_date.between(begin_time, end_time))
        rows = db.execute(query.order_by(t.c.stat_date.asc()))
        data_list = []
        for r in rows:
            data_list.append({'stat_date': r[0], 'lead_count': r[5]})
        return {'sale_no': saleno, 'list': data_list}


def init_test_data():
    logger.info('<init_test_data> start...')
    db.connect()
    count = db.count(saleleadsdaystats)
    if count == 0:
        sales_nos = []
        t = amssales.alias('t')
        query = select([t.c.staffNo, t.c.name])
        query = query.where(t.c.agStatus == 1)
        mdb.connect()
        rs = mdb.execute(query)
        for r in rs:
            sales_nos.append(r[0])
        mdb.close()
        now = datetime.now()
        for i in range(1, 7):
            stat_date = now + timedelta(days=-i)
            init_day_test_data(db, sales_nos, stat_date)
    db.close()
    logger.info('<init_test_data> end!')


def init_day_test_data(db, sales_nos, stat_date):
    logger.info('<init_day_test_data> stat_date: ' + str(stat_date))
    datetimes = DateUtil.getDayBetween(stat_date)
    begin_time = datetimes[0]
    end_time = datetimes[1]
    query = select([activeleads.c.mdb_agent_code,
                    activeleads.c.lead_status])
    query = query.where(activeleads.c.createtime.between(begin_time, end_time))
    rs = db.execute(query).fetchall()
    stat_dict = {}
    if rs:
        for r in rs:
            sales_no = r[0]
            status = r[1]
            stat_data = stat_dict.get(sales_no)
            if stat_data is None:
                stat_data = {'lead_count': 0,
                             'call_count': 0,
                             'visit_count': 0,
                             'order_count': 0}
                stat_data = handle_stat_data(status, stat_data)
                stat_dict[sales_no] = stat_data
            else:
                stat_data = handle_stat_data(status, stat_data)

    for sales_no in sales_nos:
        lead_count = 0
        call_count = 0
        visit_count = 0
        order_count = 0
        stat_data = stat_dict.get(sales_no)
        if stat_data is not None:
            lead_count = stat_data['lead_count']
            call_count = stat_data['call_count']
            visit_count = stat_data['visit_count']
            order_count = stat_data['order_count']

        d = {'stat_date': DateUtil.getStatDate(stat_date),
             'year': stat_date.year,
             'month': stat_date.month,
             'day': stat_date.day,
             'saleno': sales_no,
             'lead_count': lead_count,
             'call_count': call_count,
             'visit_count': visit_count,
             'order_count': order_count}

        db.execute(saleleadsdaystats.insert(), d)


def handle_stat_data(status, stat_data):
    if status < 12:
        stat_data['lead_count'] = stat_data['lead_count'] + 1
    elif status == 12:
        stat_data['call_count'] = stat_data['call_count'] + 1
    elif status == 13:
        stat_data['visit_count'] = stat_data['visit_count'] + 1
    elif status == 100:
        stat_data['order_count'] = stat_data['order_count'] + 1
    return stat_data
