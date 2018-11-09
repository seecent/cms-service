
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from models import row2dict, rows2dict, bind_dict, change_dict
from models.saleschannel import saleschannels

IGNORES = {'created_date', 'last_modifed'}


class SaleschannelsMixin(object):
    def get_saleschannel(self, id):
        row = db.get(saleschannels, id)
        if row:
            return row2dict(row, saleschannels)
        else:
            raise HTTPNotFound(title="no_saleschannel")


@hug.object.urls('')
class SalesChannels(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = saleschannels.alias('c')
        query = db.filter(t, request)
        if q:
            query = query.where(t.c.name.like('%' + q + '%'))
        rs = db.paginate_data(query, request, response)
        return rows2dict(rs, saleschannels)

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        saleschannel = bind_dict(saleschannels, body)
        saleschannel['last_modifed'] = datetime.now()
        d = db.save(saleschannels, saleschannel)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(saleschannels, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class SalesChannelsInst(SaleschannelsMixin, object):
    def get(self, id: int):
        t = self.get_saleschannel(id)
        return t

    def patch(self, id: int, body):
        t = self.get_saleschannel(id)
        if t:
            t = change_dict(saleschannels, t, body)
            db.update(saleschannels, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        db.delete(saleschannels, id)


def init_sales_channels():
    now = datetime.now()
    channel1 = {'code': 'YB',
                'name': '银保渠道',
                'type': '银保',
                'created_date': now,
                'last_modifed': now}
    channel2 = {'code': 'XYT',
                'name': '信易通渠道',
                'type': '信易通',
                'created_date': now,
                'last_modifed': now}
    channel3 = {'code': 'EXX',
                'name': 'E行销渠道',
                'type': 'E行销',
                'created_date': now,
                'last_modifed': now}
    db.connect()
    count = db.count(saleschannels)
    if count == 0:
        db.insert(saleschannels, channel1)
        db.insert(saleschannels, channel2)
        db.insert(saleschannels, channel3)
    db.close()
