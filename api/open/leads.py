from __future__ import absolute_import

import hug
import json

from api.errorcode import ErrorCode
from config import db, setting
from datetime import datetime
from log import logger
from models.leads.activeleads import activeleads
from models.saleschannel import saleschannels
# from models.leads.tracepolicy import tracepolicy
# from models.leads.traceaction import traceactions
from services.signtool import check_sign
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func


@hug.object.urls('')
class Leads(object):
    @hug.object.get()
    def get(self, request, response):
        sign = request.params.get('sign')
        logger.info('<get_all_lead_list> sign=' + str(sign))
        if not sign:
            return {'code': ErrorCode.MISS_SIGN_PARAM.value,
                    'message': '缺少sign参数！'}
        begin_date = request.params.get('begin_time')
        if not begin_date:
            return {'code': ErrorCode.MISS_PARAM_BEGIN_TIME.value,
                    'message': '缺少begin_time参数！'}
        end_date = request.params.get('end_time')
        if not end_date:
            return {'code': ErrorCode.MISS_PARAM_END_TIME.value,
                    'message': '缺少end_time参数！'}
        offset = request.params.get('offset', 0)
        limit = request.params.get('limit', 100)

        params = {'begin_time': begin_date, 'end_time': end_date,
                  'offset': offset, 'limit': limit}
        logger.info('<get_all_lead_list> params=' + str(params))

        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            # 校验安全校验字符串
            # sign_key = setting['xyt_api_sign_key']
            # if not check_sign(params, sign_key, sign):
            #     return {'code': ErrorCode.SIGN_VALIDATION_FAILURE.value,
            #             'message': '验证签名sign参数失败！'}

            sc = saleschannels.alias('sc')
            q = select([sc.c.id, sc.c.code, sc.c.name])
            q = q.where(sc.c.code == 'XYT')
            sales_channel = db.execute(q).fetchone()
            if sales_channel is None:
                return {'code': ErrorCode.NOT_FOUND.value,
                        'message': '信易通渠道不存在！'}

            channel_id = sales_channel[0]
            logger.info('<get_all_lead_list> channel_id=' + str(channel_id))
            al = activeleads.alias('a')
            q = select([al.c.mdb_agent_code,
                        al.c.mdb_customerid,
                        al.c.mdb_name,
                        al.c.mdb_sex,
                        al.c.mdb_birthdate,
                        al.c.offer_product_code,
                        al.c.offer_product_name,
                        al.c.offer_resolution_code,
                        al.c.offer_resolution_name,
                        al.c.customer_json])
            c = select([func.count('1')])
            if begin_date and end_date:
                df = "%Y%m%d%H%M%S"
                begin_time = datetime.strptime(begin_date, df)
                end_time = datetime.strptime(end_date, df)
                c = c.where(al.c.mdb_channel == channel_id)
                c = c.where(al.c.createtime.between(begin_time, end_time))
                q = q.where(al.c.mdb_channel == channel_id)
                q = q.where(al.c.createtime.between(begin_time, end_time))
            total = db.count(c)
            rows = db.execute(q.offset(offset).limit(limit))
            leads = []
            if rows:
                for r in rows:
                    cus_json = self._check_json_data(r[9])
                    d = {'lead_seqid': r[0],
                         'agent_code': self._check_value(r[1]),
                         'agent_name': cus_json.get('AgentName',),
                         'customer_id': cus_json.get('CustomerID'),
                         'customer_name': self._check_value(r[3]),
                         'sex': self._check_sex(r[4]),
                         'birth_day': r[5],
                         'policies_total': cus_json.get('PoliciesTotal'),
                         'ape': cus_json.get('APE'),
                         'score': cus_json.get('Score'),
                         'contact_point': cus_json.get('ContactPoint'),
                         'suggest_reasons': cus_json.get('SuggestReasons'),
                         'recommend_product': cus_json.get('RecommendProduct'),
                         'recommend_reasons': cus_json.get('RecommendReasons')}
                    leads.append(d)
            return {'total': total, 'offset': offset,
                    'limit': limit, 'leads': leads}
        except Exception as e:
            logger.exception('<get_all_lead_list> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = "服务器内部异常！"

        return result

    def _check_value(self, v):
            if v is None:
                return ''
            return v

    def _check_sex(self, v):
        if v == 'M':
            return 'M'
        elif v == 'F':
            return 'F'
        elif v == '1':
            return 'M'
        elif v == '2':
            return 'F'
        return '0'

    def _check_json_data(self, v):
        data = {}
        try:
            if v is not None:
                if v != '':
                    data = json.loads(v)
        except Exception:
            pass
        return data
