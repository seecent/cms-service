
from __future__ import absolute_import
import hug

from api.errorcode import ErrorCode
from config import db
from datetime import datetime
from log import logger
from models.collection import collections
from models.rawleads import rawleads
from models.viableleads import viableleads, viablecontacts
from sqlalchemy.sql import select, text
from sqlalchemy.sql.expression import func


@hug.post('/clean')
def clean(collection_id, clean_time):
    logger.info('<clean> collection_id=' + str(collection_id) +
                ', clean_time=' + str(clean_time))
    result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
    try:
        query = select([func.count('1')]).where(rawleads.c.effective == 1)
        query = query.where(rawleads.c.collection_id == collection_id)
        viable_count = db.count(query)
        data = {'id': collection_id,
                'viable_count': viable_count,
                'status': 'Cleaned',
                'last_modifed': datetime.now()}
        db.update(collections, data)
    except Exception as e:
        logger.exception('<clean> error=')
        result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

    return result


@hug.post('/merge')
def merge(collection_id, merge_time):
    logger.info('<merge> collection_id=' + str(collection_id) +
                ', merge_time=' + str(merge_time))
    result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
    try:
        query = select([func.count('1')]).where(rawleads.c.merge_status == 1)
        query = query.where(rawleads.c.collection_id == collection_id)
        merge_count = db.count(query)
        data = {'id': collection_id,
                'merge_count': merge_count,
                'status': 'Merged',
                'last_modifed': datetime.now()}
        db.update(collections, data)
        copy_rawleads_to_viableleads(db, collection_id, merge_count)
    except Exception as e:
        logger.exception('<merge> error=')
        result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

    return result


def copy_rawleads_to_viableleads(db, collection_id, merge_count):
    logger.info('<copy_rawleads_to_viableleads> collection_id=' +
                str(collection_id) + ', merge_count=' + str(merge_count))
    result = {'code': ErrorCode.OK.value, 'message': ErrorCode.OK.name}
    try:
        db.execute(viableleads.delete().where(
            viableleads.c.collection_id == collection_id))
        db.execute(viablecontacts.delete().where(
            viablecontacts.c.collection_id == collection_id))

        sql = """INSERT INTO lms_viable_contacts(id, no, collection_id,
            en_name, first_name,
            last_name, full_name, gender, age, birth_date,
            birth_year, birth_month, birth_day, id_type, id_number,
            marriage, num_of_childs, education, income, job_title,
            vip_flag, mobile_phone, home_phone, work_phone, email,
            qq, weixin, open_id, ip_address, province_code,
            province_name,
            city_code, city_name, district_code, district_name,
            address,
            created_date)
            SELECT c.id, c.no, c.collection_id, c.en_name, c.first_name,
            c.last_name, c.full_name, c.gender, c.age, c.birth_date,
            c.birth_year, c.birth_month, c.birth_day, c.id_type, c.id_number,
            c.marriage, c.num_of_childs, c.education, c.income, c.job_title,
            c.vip_flag, c.mobile_phone, c.home_phone, c.work_phone, c.email,
            c.qq, c.weixin, c.open_id, c.ip_address, c.province_code,
            c.province_name,
            c.city_code, c.city_name, c.district_code, c.district_name,
            c.address,
            c.created_date FROM lms_raw_leads l LEFT OUTER JOIN
            lms_raw_contacts c ON l.contact_id = c.id
            WHERE l.collection_id = :cid AND l.effective = 1
            AND l.merge_status = 1
            """

        db.execute(text(sql), {'cid': collection_id})

        sql = """INSERT INTO lms_viable_leads(
            id, no, budget, need, authority,
            time_frame, premiun, channel_id, campaign_id, company_id,
            contact_id, collection_id, product_id, created_date,
            last_modifed)
            SELECT id, no, budget, need, authority,
            time_frame, premiun, channel_id, campaign_id, company_id,
            contact_id, collection_id, product_id, created_date,
            last_modifed FROM lms_raw_leads
            WHERE collection_id = :cid and effective = 1 and merge_status = 1
            """

        db.execute(text(sql), {'cid': collection_id})
    except Exception as e:
        logger.exception('<copy_rawleads_to_viableleads> error=')
        result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

    return result
