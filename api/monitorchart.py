
from __future__ import absolute_import
import hug

from api.auth.user import check_sysadmin, check_current_user, query_current_user
from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201,\
    HTTPInternalServerError
from log import logger
from models.collection import collections
from models.saleschannel import saleschannels
from models.campaign import campaigns
from models.monitorchart import monitorcharts
from models import bind_dict, change_dict, row2dict, rows2data

IGNORES = {'last_modifed'}


class MonitorChartMixin(object):
    def get_monitor_chart(self, id):
        t = monitorcharts.alias('m')
        row = db.get(t, id)
        if row:
            return row2dict(row, monitorcharts)
        else:
            raise HTTPNotFound(title="no_monitor_chart")


@hug.object.urls('')
class MonitorCharts(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = monitorcharts.alias('m')
        joins = {'channel': {
                 'select': 'name',
                 'table': saleschannels.alias('ch')},
                 'campaign': {
                 'select': 'name',
                 'table': campaigns.alias('ca')},
                 'collection': {
                 'select': 'code',
                 'table': collections.alias('c')}
                 }
        query = db.filter_join(t, joins, request, ['-created_date'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            query = db.filter_by_user(t, query, u)
        if q:
            query = query.where(t.c.name.like('%' + q + '%'))
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)

        return rows2data(rows, monitorcharts, joins, IGNORES)

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            begin_date = body.pop("begin_date", None)
            end_date = body.pop("end_date", None)
            if begin_date and end_date:
                df = "%Y-%m-%d %H:%M:%S"
                begin_date = datetime.strptime(begin_date + " 00:00:00", df)
                end_date = datetime.strptime(end_date + " 23:59:59", df)
            mc = bind_dict(monitorcharts, body)
            current_user = result['user']
            logger.info('<post> user[' + current_user['username'] +
                        '] create monitorchart: ' + str(mc))
            mc['user_id'] = current_user.get('id')
            mc['username'] = current_user.get('username')
            mc['begin_date'] = begin_date
            mc['end_date'] = end_date
            d = db.save(monitorcharts, mc)
            return d
        except Exception:
            logger.exception('<post> error: ')
            raise HTTPInternalServerError(title='create_monitorchart_error')

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(monitorcharts, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class MonitorChartInst(MonitorChartMixin, object):
    def get(self, id: int):
        mc = self.get_monitor_chart(id)
        return mc

    def patch(self, request, response, id: int, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            mc = self.get_monitor_chart(id)
            if mc:
                begin_date = body.pop("begin_date", None)
                end_date = body.pop("end_date", None)
                if begin_date and end_date:
                    df = "%Y-%m-%d %H:%M:%S"
                    begin_date = datetime.strptime(
                        begin_date + " 00:00:00", df)
                    end_date = datetime.strptime(end_date + " 23:59:59", df)
                excludes = ['collect_count', 'viable_count', 'merge_count',
                            'user_id', 'username']
                mc = change_dict(monitorcharts, mc, body, excludes)
                mc['begin_date'] = begin_date
                mc['end_date'] = end_date
                current_user = result['user']
                logger.info('<patch> user[' + current_user['username'] +
                            '] update monitorchart: ' + str(mc))
                db.update(monitorcharts, mc)
            return mc
        except Exception:
            logger.exception('<patch> monitorchart[' + str(id) + '] error: ')
            raise HTTPInternalServerError(title='update_monitorchart_error')

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            current_user = result['user']
            logger.info('<delete> user[' + current_user['username'] +
                        '] delete monitorchart[' + str(id) + ']')
            db.delete(monitorcharts, id)
        except Exception:
            logger.exception('<delete> monitorchart[' + str(id) + '] error: ')
            raise HTTPInternalServerError(title='delete_monitorchart_error')
