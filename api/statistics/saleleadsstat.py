
from __future__ import absolute_import
import hug

from api.ext.dateutil import DateUtil
from config import db
from datetime import datetime
from log import logger
from models.mdb.ams.amssales import amssales
from models.leads.activeleads import activeleads
from models.statistics.saleleadsstat import saleleadsstats
from services.db import bulk_insert_datas
from sqlalchemy.sql import select, func, and_


@hug.object.urls('')
class SaleLeadsStats(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        stat_sales_active_leads(datetime.now())
        sale_no = request.params.get('saleno')
        t = saleleadsstats.alias('c')
        query = select([t.c.saleno,
                        t.c.daily_lead_count,
                        t.c.week_lead_count,
                        t.c.month_lead_count,
                        t.c.month_call_count,
                        t.c.month_visit_count,
                        t.c.month_order_count])
        rows = db.execute(query)
        data_list = []
        for r in rows:
            data_list.append({'daily_lead_count': r[1]})
        return {'sale_no': sale_no, 'list': data_list}
        # return datas


def stat_sales_active_leads(db, salesno, stat_datetime):
    logger.debug('<stat_sales_active_leads> salesno=' + salesno +
                 ', stat_date=' + str(stat_datetime))
    stat_data = {'saleno': salesno,
                 'daily_lead_count': 0,
                 'week_lead_count': 0,
                 'month_lead_count': 0,
                 'month_call_count': 0,
                 'month_visit_count': 0,
                 'month_order_count': 0}
    try:
        dlc = stat_daily_lead_count(db, salesno, stat_datetime)
        wlc = stat_week_lead_count(db, salesno, stat_datetime)
        mlc = stat_month_lead_count(db, salesno)
        mcc = stat_month_lead_count(db, salesno, 12)
        mvc = stat_month_lead_count(db, salesno, 13)
        moc = stat_month_lead_count(db, salesno, 100)

        stat_data = {'saleno': salesno,
                     'daily_lead_count': dlc,
                     'week_lead_count': wlc,
                     'month_lead_count': mlc,
                     'month_call_count': mcc,
                     'month_visit_count': mvc,
                     'month_order_count': moc,
                     'create_time': datetime.now()}
        db.execute(saleleadsstats.delete().where(
            and_(saleleadsstats.c.saleno == salesno)))
        db.insert(saleleadsstats, stat_data)
    except Exception:
        logger.exception('<stat_sales_active_leads> error: ')

    return stat_data


def stat_daily_lead_count(db, salesno, stat_datetime, state=None):
    datetimes = DateUtil.getDayBetween(stat_datetime)
    t = activeleads.alias('al')
    query = select([func.count(t.c.mdb_agent_code)])
    query = query.where(t.c.mdb_agent_code == salesno)
    if state is not None:
        query = query.where(t.c.lead_status == state)
    query = query.where(t.c.createtime.between(datetimes[0], datetimes[1]))
    return db.count(query)


def stat_week_lead_count(db, salesno, stat_datetime, state=None):
    datetimes = DateUtil.getDayBetween(stat_datetime)
    t = activeleads.alias('al')
    query = select([func.count(t.c.mdb_agent_code)])
    query = query.where(t.c.mdb_agent_code == salesno)
    if state is not None:
        query = query.where(t.c.lead_status == state)
    query = query.where(t.c.createtime.between(datetimes[0], datetimes[1]))
    return db.count(query)


def stat_month_lead_count(db, salesno, state=None):
    datetimes = DateUtil.thisMonthRange()
    t = activeleads.alias('al')
    query = select([func.count(t.c.mdb_agent_code)])
    query = query.where(t.c.mdb_agent_code == salesno)
    if state is not None:
        query = query.where(t.c.lead_status == state)
    query = query.where(t.c.createtime.between(datetimes[0], datetimes[1]))
    return db.count(query)


def init_saleleadsstats():
    logger.info('<init_saleleadsstats> start...')
    try:
        db.connect()
        count = db.count(saleleadsstats)
        if count > 0:
            return 0
        query = select([amssales.c.staffNo])
        rs = db.execute(query).fetchall()
        stat_datas = []
        for r in rs:
            sales_no = r[0]
            stat_data = {'saleno': sales_no,
                         'daily_lead_count': 0,
                         'week_lead_count': 0,
                         'month_lead_count': 0,
                         'month_call_count': 0,
                         'month_visit_count': 0,
                         'month_order_count': 0,
                         'create_time': datetime.now()}
            stat_datas.append(stat_data)
        stat_datas_count = len(stat_datas)
        if stat_datas_count > 0:
            bulk_insert_datas(db, saleleadsstats, stat_datas)
        db.close()
    except Exception:
        logger.exception('<init_saleleadsstats> error: ')
    logger.info('<init_saleleadsstats> end!')
