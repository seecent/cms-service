
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from models.campaign import campaigns
from models import rows2dict, row2dict, change_dict, bind_dict
from falcon import HTTPNotFound, HTTP_201, HTTP_204

IGNORES = {'created_date', 'last_modifed'}


class CampaignMixin(object):
    def get_campaign(self, id):
        row = db.get(campaigns, id)
        if row:
            return row2dict(row, campaigns)
        else:
            raise HTTPNotFound(title="no_campaign")


@hug.object.urls('')
class Campaigns(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        try:
            t = campaigns.alias('c')
            query = db.filter(campaigns, request, ['name'])
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            rs = db.paginate_data(query, request, response)
            return rows2dict(rs, campaigns)
        except Exception as e:
            return {'code': 1, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        campaign = bind_dict(campaigns, body)
        d = db.save(campaigns, campaign)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(campaigns, ids)
        return {'code': 0, 'message': 'OK'}


@hug.object.http_methods('/{id}')
class CampaignInst(CampaignMixin, object):
    def get(self, id: int):
        t = self.get_campaign(id)
        return t

    def patch(self, id: int, body):
        t = self.get_campaign(id)
        if t:
            t = change_dict(campaigns, t, body)
            db.update(campaigns, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        db.delete(campaigns, id)


def query_all_campaigns():
    rs = db.fetch_all(campaigns, ['name'])
    campaign_dict = {}
    for r in rs:
        code = r[1]
        campaign_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return campaign_dict


def init_campaigns():
    now = datetime.now()
    campaign1 = {'code': '1', 'name': '开门红',
                 'created_date': now,
                 'last_modifed': now}
    campaign2 = {'code': '2', 'name': '3月营销活动',
                 'created_date': now,
                 'last_modifed': now}
    db.connect()
    count = db.count(campaigns)
    if count == 0:
        db.insert(campaigns, campaign1)
        db.insert(campaigns, campaign2)
    db.close()
