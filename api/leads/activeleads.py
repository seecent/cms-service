
# coding=utf-8
from __future__ import absolute_import

import hug
import random

from api.ext.dbutil import DBUtil
from api.auth.user import query_current_user, check_sysadmin
from cache import amscache, orgcache, locationcache
from config import db, mdb, campaign_db as cdb
from datetime import datetime, timedelta
from falcon import HTTPNotFound
from log import logger
from models.product import products
from models.leads.activeleads import activeleads, activeleads_mapping
from models.leads.assignment import assignment
from models.leads.traceaction import traceactions
from models.leads.tracepolicy import tracepolicy
from models.mdb.ams.amssales import amssales
from models import row2dict, rows2dict, handle_secrecy_data
from services.collect.config import CollectConfigService
from services.collect.db_import import CollectDBImportService
from sqlalchemy import select, func

IGNORES = {'createTime', 'updateTime'}


class ActiveLeadMixin(object):

    def get_activeLead(self, id):
        t = activeleads.alias('a')
        column_names = DBUtil.get_column_names(
            activeleads_mapping, None, 'lead_seqid')
        select = DBUtil.get_selects(t, column_names)
        selects = {'select': select, 'mapping': activeleads_mapping}
        query = db.query(selects, {'seqId': id})
        row = db.fetch_one(query)
        if row:
            return row2dict(row, selects)
        else:
            raise HTTPNotFound(title="no_active_lead")


@hug.object.urls('')
class ActiveLeads(object):

    @hug.object.get()
    def get(self, request, response, q: str=None):
        displays = request.params.get('displays')
        t = activeleads.alias('a')
        column_names = DBUtil.get_column_names(
            activeleads_mapping, displays, 'lead_seqid')
        select = DBUtil.get_selects(t, column_names)
        selects = {'select': select, 'mapping': activeleads_mapping}
        query = db.filter(selects, request, ['-createtime'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            org_id = u.get('organization_id')
            dcodes = orgcache.get_dcodes(org_id)
            if dcodes and len(dcodes) > 0:
                query = query.where(t.c.mdb_ssocode.in_(dcodes))
            else:
                ccodes = orgcache.get_ccodes(org_id)
                if ccodes and len(ccodes) > 0:
                    query = query.where(t.c.mdb_companycode.in_(ccodes))
        if q:
            query = query.where(t.c.lead_name.like('%' + q + '%'))
        query = db.filter_by_date(t.c.createtime, query, request)
        rows = db.paginate_data(query, request, response)
        datas = rows2dict(rows, selects)
        return map_active_leads_data(mdb, column_names, datas)


@hug.object.http_methods('/{id}')
class ActiveLeadInst(ActiveLeadMixin, object):

    def get(self, id: int):
        a = self.get_activeLead(id)
        return a


@hug.object.http_methods('/detail/{id}')
class ActiveLeadDetail(ActiveLeadMixin, object):

    def get(self, id: int):
        query = db.query(traceactions).where(traceactions.c.lead_seqId == id)
        query = query.order_by(traceactions.c.createTime.asc())
        rs = db.execute(query).fetchall()
        traceactions_list = rows2dict(rs, traceactions)

        query = db.query(assignment).where(assignment.c.lead_seqId == id)
        rs = db.execute(query).fetchall()
        assignment_list = rows2dict(rs, assignment)
        for ag in assignment_list:
            companyCode = ag['mdb_companyCode']
            ssoCode = ag['mdb_ssoCode']
            saleNo = ag['mdb_agent_code']
            build_assignment_data(mdb, ag, companyCode, ssoCode, saleNo)

        query = db.query(tracepolicy).where(tracepolicy.c.lead_seqId == id)
        rs = db.execute(query).fetchall()
        tracepolicy_list = rows2dict(rs, tracepolicy)

        return {
            'traceactions': traceactions_list,
            'assignments': assignment_list,
            'tracepolicies': tracepolicy_list,
        }


def map_active_leads_data(mdb, column_names, datas):
    for d in datas:
        if 'mdb_name' in column_names:
            handle_secrecy_data(d, 'customerName', 1)
        if 'mdb_mobilephone' in column_names:
            handle_secrecy_data(d, 'mobilePhone', 3, 3)
        if 'mdb_certno' in column_names:
            handle_secrecy_data(d, 'certno', 5, 3)
        if 'mdb_ssocode' in column_names:
            d['ssoCode'] = amscache.getSSOName(d['ssoCode'], '')
        if 'mdb_companycode' in column_names:
            d['companyCode'] = amscache.getCSOName(d['companyCode'], '')
        if 'mdb_agent_code' in column_names:
            d['agentCode'] = get_sales_name(mdb, d['agentCode'])
        if 'mdb_province' in column_names:
            d['provinceName'] = locationcache.get(d['province'])
        if 'mdb_city' in column_names:
            d['cityName'] = locationcache.get(d['city'])
        if 'mdb_county' in column_names:
            d['countyName'] = locationcache.get(d['county'])
    return datas


def build_assignment_data(mdb, assignment_data, companyCode, ssoCode, saleNo):
    assignment_data['companyName'] = amscache.getCSOName(companyCode, '')
    assignment_data['ssoName'] = amscache.getSSOName(ssoCode, '')
    assignment_data['saleName'] = get_sales_name(mdb, saleNo)
    return assignment_data


def get_sales_name(mdb, saleNo):
    saleName = ''
    if saleNo:
        q = select([amssales.c.name]).where(amssales.c.staffNo == saleNo)
        row = mdb.fetch_one(q)
        if row:
            saleName = row[0]
    return saleName


def init_activeleads():
    ccs = CollectConfigService()
    config_name = "activeleads_db_collect_config.xml"
    r = ccs.parse_config("ActiveLeads", config_name)
    config = r['config']
    cdis = CollectDBImportService()
    cdis.import_from_db(3, 'postgresql://lms:lms_line@localhost/lmsdb',
                        'raw_leads_view', config, True, False,
                        {'offset': 1, 'limit': 200})


def init_test_data():
    logger.info('<init_test_data> start...')
    db.connect()
    count = db.count(activeleads)
    if count > 0:
        logger.info('<init_test_data> end!')
        return 0

    campaign_list = []

    mdb.connect()
    t = amssales.alias('as')
    q = select([t.c.staffNo, t.c.comCode, t.c.ssoCode])
    q = q.where(t.c.agStatus == 1)
    sales_list = []
    rs = mdb.execute(q).fetchall()
    for r in rs:
        sales_list.append({'staffNo': r[0], 'comCode': r[1], 'ssoCode': r[2]})
    mdb.close()

    rs = db.fetch_all(products, ['Name'])
    product_list = []
    for r in rs:
        product_list.append({'id': r[0], 'code': r[1], 'name': r[2]})

    locations = [['440000', '广东', '440300', '深圳', '440305', '南山区'],
                 ['440000', '广东', '440100', '广州', '440104', '越秀区'],
                 ['310000', '上海', '310000', '上海', '310200', '浦东新区'],
                 ['330000', '浙江', '330100', '杭州', '360103', '西湖区'],
                 ['110000', '北京', '110000', '北京', '110001', '西城区']]

    status = [0, 1, 2, 10, 11, 12, 13, 14, 100, 101]
    for i in range(0, 7):
        create_time = datetime.now() + timedelta(days=-i)
        active_leads = init_active_leads_test_data(db, create_time,
                                                   campaign_list,
                                                   sales_list, product_list,
                                                   locations, status)

        init_test_data_detail(db, active_leads, create_time)
    db.close()
    logger.info('<init_test_data> end!')


def init_active_leads_test_data(db, createtime, campaign_list,
                                sales_list, product_list,
                                locations, status):
    logger.info('<init_active_leads_test_data> createtime: ' + str(createtime))
    active_leads = []
    sales_total = len(sales_list) - 1
    product_count = len(product_list)
    max_id = 0
    query = select([func.max(activeleads.c.lead_seqid)])
    row = db.fetch_one(query)
    if row:
        max_v = row[0]
        if max_v is not None:
            max_id = row[0]
    no = max_id
    for c in campaign_list:
        uni_dict = {}
        end = random.randint(8, 36)
        for i in range(1, end):
            no += 1
            pi = random.randint(0, product_count - 1)
            product = product_list[pi]
            mobilePhone = '1862198' + str(random.randint(1000, 1999))
            certNo = '37032219870329' + str(random.randint(1000, 5000))
            marriageStatus = random.randint(0, 1)
            childNum = 0
            if marriageStatus == 1:
                childNum = random.randint(0, 3)
            loc = locations[random.randint(0, 4)]
            source_type = random.randint(0, 4)
            source_id = no
            campaign_code = c['code']
            uni_key = str(source_type) + '@' + str(no) + '@' + campaign_code
            if uni_key in uni_dict.keys():
                continue
            else:
                uni_dict[uni_key] = 1

            sales_index = random.randint(0, sales_total)
            sales = sales_list[sales_index]
            d = {'lead_seqid': no, 'lead_name': product['name'],
                 'lead_source_type': source_type,
                 'lead_source_id': source_id,
                 'lead_campaign_code': campaign_code, 'lead_lifecycle': True,
                 'createtime': createtime,
                 'endtime': createtime, 'lead_details': product['name'],
                 'lead_status': status[random.randint(0, 9)],
                 'lead_size_of_opportunity': random.randint(0, 100),
                 'lead_decision_level': '', 'lead_timeFrame': '',
                 'lead_wants_to_be_contacted': 1, 'lead_competitors': '',
                 'lead_import_userId': None,
                 'offer_product_code': product['code'],
                 'offer_product_name': product['name'],
                 'offer_resolution_code': product['code'],
                 'offer_resolution_name': product['name'],
                 'unica_campaigncode': c['code'],
                 'unica_campaignname': c['name'],
                 'unica_treatmentcode': None,
                 'mdb_customertype': 0, 'mdb_customerid': 50800000 + no,
                 'mdb_mobilephone': mobilePhone,
                 'mdb_name': '客户' + str(no),
                 'mdb_birthdate': '1987' + str(random.randint(1000, 1230)),
                 'mdb_sex': random.randint(1, 2),
                 'mdb_certtype': random.randint(1, 5),
                 'mdb_certno': certNo,
                 'mdb_province': loc[0], 'mdb_provincename': loc[1],
                 'mdb_city': loc[2], 'mdb_cityname': loc[3],
                 'mdb_county': loc[4], 'mdb_countyname': loc[5],
                 'mdb_marriagestatus': str(marriageStatus),
                 'mdb_childNum': str(childNum),
                 'mdb_channel': random.randint(1, 2),
                 'mdb_companycode': sales['comCode'],
                 'mdb_ssocode': sales['ssoCode'],
                 'mdb_agent_code': sales['staffNo']}
            active_leads.append(d)
            db.execute(activeleads.insert(), d)
    return active_leads


def init_test_data_detail(db, active_leads, createtime):
    logger.info('<init_test_data_detail> start...')
    actionNames = [
        '销售线索创建', '首次电话确认', '完成首次拜访', '完成建议书提交', '完成保单'
    ]

    for a in active_leads:
        id = a['lead_seqid']
        end = random.randint(0, 4)
        for i in range(0, end):
            action_dict = {
                'lead_seqId': id,
                'actionCode': i,
                'actionType': i,
                'actionName': actionNames[i],
                'actionStartTime': datetime.now(),
                'actionEndTime': datetime.now(),
                'actionExecTime': datetime.now(),
                'actionResult': None,
                'createTime': createtime
            }
            db.execute(traceactions.insert(), action_dict)

        pno = createtime.strftime('%Y%m%d%H%M%S')
        policy_dict = {
            'seqId': pno,
            'lead_seqId': id,
            'policyNo': 'P' + pno,
            'premium': random.randint(1000, 5000),
            'createTime': createtime,
            'updateTime': createtime,
        }
        db.execute(tracepolicy.insert(), policy_dict)

        assignment_dict = {
            'lead_seqId': id,
            'mdb_companyCode': a['mdb_companycode'],
            'mdb_ssoCode': a['mdb_ssocode'],
            'mdb_channel': a['mdb_channel'],
            'mdb_agent_code': a['mdb_agent_code'],
            'createTime': createtime,
            'updateTime': createtime,
        }
        db.execute(assignment.insert(), assignment_dict)
    logger.info('<init_test_data_detail> end!')
