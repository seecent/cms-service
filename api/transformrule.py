
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from models.transformrule import transformrules
from models import rows2dict


IGNORES = {'description', 'last_modifed'}


@hug.object.urls('')
class TransformRules(object):
    @hug.object.get()
    def get(self, request, response):
        t = transformrules.alias('t')
        q = db.query(t, request.params)
        q = q.where(t.c.status == 'save')
        q = db.order_by(t, q, ['name'])
        rs = db.execute(q)
        data = rows2dict(rs, transformrules, IGNORES)
        response.set_header('X-Total-Count', str(len(data)))
        return data


def init_transformrule():
    now = datetime.now()
    rule1 = {'name': '测试清洗规则',
             'type': 0,
             'description': '测试清洗规则',
             'status': 'save',
             'created_date': now,
             'last_modifed': now}
    rule2 = {'name': '测试去重规则',
             'type': 1,
             'description': '测试去重规则',
             'status': 'save',
             'created_date': now,
             'last_modifed': now}
    db.connect()
    db.insert(transformrules, rule1)
    db.insert(transformrules, rule2)
    db.close()
