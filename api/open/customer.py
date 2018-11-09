from __future__ import absolute_import

import hug

from api.errorcode import ErrorCode
from api.ext.output_format import output_xml
from config import db
from log import logger

# from models.rawleads import rawleads, rawcontacts
from models.mdb.cm.customerprofile import customerprofile
from models.mdb.cm.customertag import customertag
from models.mdb.cm.contactlist import contactlist
from models.mdb.cm.fiveelementsunion import fiveelementsunion
from models.mdb.ods.ldcode import ldcode
from models.mdb.ods.lccont import lccont
from sqlalchemy.sql import select, or_, text

import xml.etree.ElementTree as ET

cityItem = {}


@hug.get('/getCustomerProfile', output=output_xml)
def get_customer_profile(request, response):
    sign = request.params.get('sign')
    logger.info('<get_customer_profile> sign=' + str(sign))
    if not sign:
        return build_error_xml(ErrorCode.MISS_PARAM_SIGN.value,
                               'miss parameter sign')
    customer_id = request.params.get('id')
    if not customer_id:
        return build_error_xml(ErrorCode.MISS_PARAM.value, 'miss parameter id')

    params = {'id': customer_id}

    # 校验安全校验字符串
    # sign_key = setting['ams_api_sign_key']
    # if not check_sign(params, sign_key, sign):
    #     return build_error_xml(ErrorCode.SIGN_VALIDATION_FAILURE.value,
    #                            ErrorCode.SIGN_VALIDATION_FAILURE.name)

    cp = customerprofile.alias('c')
    feu = fiveelementsunion.alias('f')
    ld = ldcode.alias('d')
    lcc = lccont.alias('p')
    cl = contactlist.alias('i')

    cpQuery = select([cp.c.fiveUnionID, cp.c.mobileUnionID, cp.c.mobilePhone])
    cpQuery = cpQuery.where(cp.c.id == customer_id)
    cpResult = db.fetch_one(cpQuery)
    if not cpResult:
        return build_error_xml(4001, "customer not found")

    # clQuery=select([cl.c.policyNo])
    # clQuery=clQuery.where(cl.c.mobileUnionID==cpResult[1] and cl.c.fiveUnionID==cpResult[0])
    # clResult=db.fetch_one(clQuery)

    feuQuery = select([feu.c.name, feu.c.sex, feu.c.birthDate, feu.c.certType, feu.c.certNo])
    feuQuery = feuQuery.where(feu.c.fiveUnionID == cpResult[0])
    feuResult = db.fetch_one(feuQuery)

    lccQuery = select([lcc.c.companyCode, lcc.c.province, lcc.c.city, lcc.c.county])
    lccQuery = lccQuery.where(
        lcc.c.appntName == feuResult[0] and lcc.c.appntSex == feuResult[1] and lcc.c.appntBirthDate == feuResult[
            2] and lcc.c.appntCertType == feuResult[3] and lcc.c.appntCertNo == feuResult[4])
    lccResult = db.fetch_one(lccQuery)

    if not cityItem:
        ldQuery = select([ld.c.code, ld.c.codeName])
        ldQuery = ldQuery.where(or_(ld.c.codeType == 'pr_circpopedomcode', ld.c.codeType == 'pr_sitecode'))
        lcResult = db.execute(ldQuery)
        for item in lcResult:
            cityItem[item[0]] = item[1]
    # q = select([
    #             cp.c.id,
    #             lc1.c.companyCode,
    #             lc1.c.province,
    #             lc1.c.city,
    #             lc1.c.county,
    #             feu.c.certType,
    #             feu.c.name,
    #             feu.c.certNo,
    #             feu.c.birthDate,
    #             feu.c.sex,
    #             ])
    # join = cp.outerjoin(feu, feu.c.fiveUnionID == cp.c.fiveUnionID)
    # q = q.select_from(join)
    # q = q.where(cp.c.id == customer_id)

    # r = db.fetch_one(q)
    r = [lccResult[0], lccResult[1], cityItem[lccResult[1]], lccResult[2],
         cityItem[lccResult[2]], lccResult[3], cityItem[lccResult[3]], customer_id,
         feuResult[3], feuResult[4], feuResult[0], feuResult[1], feuResult[2], cpResult[2]]
    xml = build_customer_profile_xml(customer_id, r)

    return xml


# 获取指定ID客户信息返回XML报文
# <?xml version="1.0" encoding="UTF-8"?>
# <GETCUSTOMERPROFILE>
#     <CUSTOMER>
#         <CO_CODE>201</CO_CODE>
#         <PROVINCE_CODE>GD</PROVINCE_CODE>
#         <PROVINCE_NAME>广东</PROVINCE_NAME>
#         <CITY_CODE>SZ</CITY_CODE>
#         <CITY_NAME>深圳</CITY_NAME>
#         <DISTRICT_CODE>NS</DISTRICT_CODE>
#         <DISTRICT_NAME>南山区</DISTRICT_NAME>
#         <ID>100001</ID>
#         <IDTYPE>1</IDTYPE>
#         <IDNUM>36031119870923XXXX</IDNUM>
#         <NAME>张昱珩</NAME>
#         <SEX>1</CUSTOM_SEX>
#         <BIRTH>19870923</BIRTH>
#         <PHONE>18621987999</PHONE>
#     </CUSTOMER>
# </GETCUSTOMERPROFILE>
def build_customer_profile_xml(customer_id, r):
    root = ET.Element('GETCUSTOMERPROFILE')
    cus_node = ET.SubElement(root, 'CUSTOMER')
    ET.SubElement(cus_node, 'CO').text = str(r[0])
    ET.SubElement(cus_node, 'PROVINCE_CODE').text = str(r[1])
    ET.SubElement(cus_node, 'PROVINCE_NAME').text = str(r[2])
    ET.SubElement(cus_node, 'CITY_CODE').text = str(r[3])
    ET.SubElement(cus_node, 'CITY_NAME').text = str(r[4])
    ET.SubElement(cus_node, 'DISTRICT_CODE').text = str(r[5])
    ET.SubElement(cus_node, 'DISTRICT_NAME').text = str(r[6])
    ET.SubElement(cus_node, 'ID').text = str(r[7])
    ET.SubElement(cus_node, 'IDTYPE').text = str(r[8])
    ET.SubElement(cus_node, 'IDNUM').text = str(r[9])
    ET.SubElement(cus_node, 'NAME').text = str(r[10])
    ET.SubElement(cus_node, 'SEX').text = str(r[11])
    ET.SubElement(cus_node, 'BIRTH').text = str(r[12])
    ET.SubElement(cus_node, 'PHONE').text = str(r[13])

    xml = ET.tostring(root, encoding='utf-8', method='xml')

    return bytes.decode(xml)


def build_error_xml(code, message):
    root = ET.Element('ERROR')
    ET.SubElement(root, 'CODE').text = str(code)
    ET.SubElement(root, 'MESSAGE').text = message
    xml = ET.tostring(root, encoding='utf-8', method='xml')
    return bytes.decode(xml)
