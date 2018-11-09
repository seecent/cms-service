
from __future__ import absolute_import
import hug

from api.ext.output_format import output_xml
from api.errorcode import ErrorCode
from config import setting, db
from log import logger
from models.rawleads import rawleads, rawcontacts

from datetime import datetime
from services.signtool import check_sign
from sqlalchemy.sql import select

import xml.etree.ElementTree as ET


@hug.get('/getAllResponseList', output=output_xml)
def get_all_response_list(request, response):
    sign = request.params.get('sign')
    logger.info('<get_all_response_list> sign=' + str(sign))
    if not sign:
        return build_error_xml(ErrorCode.MISS_PARAM_SIGN.value,
                               'miss parameter sign')
    customer_id = request.params.get('id')
    if not customer_id:
        return build_error_xml(ErrorCode.MISS_PARAM.value, 'miss parameter id')
    begin_date = request.params.get('begin_time')
    if not begin_date:
        return build_error_xml(ErrorCode.MISS_PARAM_BEGIN_TIME.value,
                               'miss parameter begin_time')
    end_date = request.params.get('end_time')
    if not end_date:
        return build_error_xml(ErrorCode.MISS_PARAM_END_TIME.value,
                               'miss parameter end_time')

    params = {'id': customer_id,
              'begin_time': begin_date,
              'end_time': end_date}

    # 校验安全校验字符串
    sign_key = setting['ams_api_sign_key']
    if not check_sign(params, sign_key, sign):
        return build_error_xml(ErrorCode.SIGN_VALIDATION_FAILURE.value,
                               ErrorCode.SIGN_VALIDATION_FAILURE.name)

    rl = rawleads.alias('l')
    rc = rawcontacts.alias('c')
    q = select([rl.c.collection_id,
                rl.c.created_date,
                rl.c.id,
                rl.c.name,
                rl.c.premiun,
                rc.c.province_code,
                rc.c.province_name,
                rc.c.city_code,
                rc.c.city_name,
                rc.c.id,
                rc.c.id_type,
                rc.c.id_number,
                rc.c.full_name,
                rc.c.gender,
                rc.c.age,
                rc.c.mobile_phone])
    join = rl.outerjoin(rc, rl.c.contact_id == rc.c.id)
    q = q.select_from(join)
    q = q.where(rl.c.id < 10)
    if begin_date and end_date:
        df = "%Y%m%d%H%M%S"
        begin_time = datetime.strptime(begin_date, df)
        end_time = datetime.strptime(end_date, df)
        q = q.where(rl.c.created_date.between(begin_time, end_time))
    q = q.order_by(rl.c.created_date.desc())

    rows = db.execute(q)
    xml = build_response_list_xml(customer_id, '', rows, 1)

    return xml


# 获取指定ID客户行为轨迹返回XML报文
# <?xml version="1.0" encoding="UTF-8"?>
# <GETALLRESPONSELIST>
#     <CUSTOM_ID>100001</CUSTOM_ID>
#     <CUSTOM_NAME>张昱珩</CUSTOM_NAME>
#     <TOTAL>6</TOTAL>
#     <LIST>
#        <RESPONSE>
#             <DATETIME>2018-03-10 00:00:00</DATETIME>
#             <TYPE>1</TYPE>
#             <DETAIL>查看中信宝诚[宝贝护航]意外保障计划</DETAIL>
#         </RESPONSE>
#         <RESPONSE>
#            ...
#         </RESPONSE>
#     </LIST>
# </GETALLRESPONSELIST>
def build_response_list_xml(customer_id, customer_name, rows, total):
    root = ET.Element('GETALLRESPONSELIST')
    ET.SubElement(root, 'CUSTOM_ID').text = str(customer_id)
    ET.SubElement(root, 'CUSTOM_NAME').text = customer_name
    ET.SubElement(root, 'TOTAL').text = str(total)
    list_node = ET.SubElement(root, 'LIST')
    for r in rows:
        node = ET.SubElement(list_node, 'RESPONSE')
        ET.SubElement(node, 'DATETIME').text = ''
        ET.SubElement(node, 'TYPE').text = ''
        ET.SubElement(node, 'DETAIL').text = ''

    xml = ET.tostring(root, encoding='utf-8', method='xml')

    return bytes.decode(xml)


def build_error_xml(code, message):
    root = ET.Element('ERROR')
    ET.SubElement(root, 'CODE').text = str(code)
    ET.SubElement(root, 'MESSAGE').text = message
    xml = ET.tostring(root, encoding='utf-8', method='xml')
    return bytes.decode(xml)
