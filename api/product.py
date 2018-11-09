
from __future__ import absolute_import
import hug

from config import db
from datetime import datetime
from models.product import products
from models import rows2dict

IGNORES = {'created_date', 'last_modifed'}


@hug.object.urls('')
class Products(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = products.alias('p')
        query = db.filter(t, request)
        if q:
            query = query.where(t.c.name.like('%' + q + '%'))
        rs = db.paginate_data(query, request, response)
        return rows2dict(rs, products)


def query_all_products():
    rs = db.fetch_all(products, ['name'])
    product_dict = {}
    for r in rs:
        code = r[1]
        product_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return product_dict


def init_product():
    now = datetime.now()
    product1 = {'code': '1001',
                'name': '中信保诚「宝贝护航」意外保障计划',
                'created_date': now,
                'last_modifed': now}
    product2 = {'code': '1002',
                'name': '中信保诚「暖宝保」医疗保险',
                'created_date': now,
                'last_modifed': now}
    db.connect()
    db.insert(products, product1)
    db.insert(products, product2)
    db.close()
