
from __future__ import absolute_import

import os

from api.errorcode import ErrorCode
from api.ext.dateutil import DateUtil
from config import db
from datetime import datetime
from log import logger
from models import row2dict
from models.collection import collections, CollectionType, CollectionStatus
from models.template import templates
from models.rawleads import rawleads, rawcontacts
from models.viableleads import viableleads, viablecontacts
from models.transformtask import transformtasks, TransformTaskStatus
from services.collect.config import CollectConfigService
from sqlalchemy.sql import select, text


# 导入配置服务
ccs = CollectConfigService()


class LeadsMergeService:
    def merge(self, task_id):
        logger.info('<merge> task_id: ' + str(task_id))
        try:
            db.connect()
            query = select([transformtasks.c.id,
                            transformtasks.c.collection_id,
                            transformtasks.c.template_id,
                            transformtasks.c.status])
            query = query.where(transformtasks.c.id == task_id)
            row = db.fetch_one(query)
            if row:
                collection_id = row[1]
                template_id = row[2]
                status = row[3]
                logger.info('<merge> task_id: ' + str(task_id) +
                            ', collection_id: ' + str(collection_id) +
                            ', template_id: ' + str(template_id) +
                            ', status: ' + str(status))
                template = db.get(templates, int(template_id))
                template = row2dict(template, templates)
                merge_rule_id = template.get('merge_rule_id')
                if merge_rule_id is not None:
                    logger.info('<merge> task_id: ' + str(task_id) +
                                ', template_id: ' + str(template_id) +
                                ', merge_rule_id: ' + str(merge_rule_id))
                    return True

                if status == TransformTaskStatus.Created:
                    ctype = self._get_collection(db, collection_id)
                    merge_rs = self._get_merge_keys_and_days(ctype, template)
                    merge_keys = merge_rs[0]
                    merge_days = merge_rs[1]
                    logger.info('<merge> task_id: ' + str(task_id) +
                                ', merge_keys: ' + str(merge_keys) +
                                ', merge_days: ' + str(merge_days))
                    date_ranges = DateUtil.getLastDaysBetween(merge_days)
                    start_time = date_ranges[0]
                    end_time = date_ranges[1]
                    filter_dict = self._get_viableleads_dict(db,
                                                             merge_keys,
                                                             start_time,
                                                             end_time)
                    rs = self._merge_rawleleads(db, collection_id,
                                                merge_keys, filter_dict)
                    rawleads_ids = rs[0]
                    filter_ids = rs[1]
                    viable_count = rs[2]
                    self._update_rawleads_merge_status(db, task_id,
                                                       collection_id,
                                                       rawleads_ids,
                                                       filter_ids,
                                                       viable_count)

                    self._copy_rawleads_to_viableleads(db, collection_id,
                                                       len(rawleads_ids))
            else:
                logger.error('<merge> task_id: ' + str(task_id) +
                             ', error: transformtasks not found!')
            db.close()
        except Exception as e:
            logger.exception('<merge> task_id: ' + str(task_id) + ', error: ')

    def _get_merge_keys_and_days(self, collection_type, template):
        merge_keys = ['mobile_phone']
        merge_days = 30
        try:
            template_file = template['template_file']
            if template_file is not None:
                configFileName = "collect" + os.path.sep + template_file
                r = ccs.parse_config("RawLeads", configFileName)
                if r['code'] == ErrorCode.OK.value:
                    config = r['config']
                    merge_keys = config['mergekeys']
                    merge_days = config.get('mergedays', 30)
        except Exception as e:
            logger.exception('<_get_merge_keys_and_days> error: ')
        return (merge_keys, merge_days)

    def _get_collection(self, db, collection_id):
        query = select([collections.c.id,
                        collections.c.type])
        query = query.where(collections.c.id == collection_id)
        row = db.fetch_one(query)
        if row:
            return row[1]
        return CollectionType.ImportCSV

    def _merge_rawleleads(self, db, collection_id, merge_keys,
                          filter_dict):
        logger.info('<_merge_rawleleads> collection_id: ' +
                    str(collection_id) + ', merge_keys: ' + str(merge_keys))
        rawleads_ids = []
        filter_ids = []
        rl = rawleads.alias('l')
        rc = rawcontacts.alias('c')
        cols = [rl.c.id, rl.c.collection_id]
        for name in merge_keys:
            col = self._get_table_column(rl, name)
            if col is not None:
                cols.append(col)
            else:
                col = self._get_table_column(rc, name)
                if col is not None:
                    cols.append(col)

        query = select(cols)
        join = rl.outerjoin(rc, rl.c.contact_id == rc.c.id)
        query = query.select_from(join)
        query = query.where(rl.c.collection_id == collection_id)
        query = query.where(rl.c.effective == 1)
        query = query.order_by(rl.c.created_date.desc())
        rows = db.execute(query).fetchall()
        logger.info('<_merge_rawleleads> collection_id: ' +
                    str(collection_id) + ', rawleads count: ' +
                    str(len(rows)))
        end = len(cols)
        viable_count = len(rows)
        for r in rows:
            rid = r[0]
            vs = []
            for i in range(2, end):
                vs.append(str(r[i]))
            key = '@'.join(vs)
            if filter_dict.get(key) is None:
                filter_dict[key] = 1
                rawleads_ids.append(rid)
            else:
                filter_ids.append(rid)
        return (rawleads_ids, filter_ids, viable_count)

    def _update_rawleads_merge_status(self, db, task_id,
                                      collection_id,
                                      rawleads_ids,
                                      filter_ids,
                                      viable_count):
        rawleads_count = len(rawleads_ids)
        filter_count = len(filter_ids)
        logger.info('<_update_rawleads_merge_status> collection_id: ' +
                    str(collection_id) + ', merge count: ' +
                    str(rawleads_count) + ', filter count: ' +
                    str(filter_count) + ', viable count: ' +
                    str(viable_count))
        now = datetime.now()
        data = None
        if rawleads_count > filter_count:
            data = {'merge_status': 2, 'last_modifed': now}
        else:
            data = {'merge_status': 1, 'last_modifed': now}
        db.execute(rawleads.update().where(
            rawleads.c.collection_id == collection_id).values(data))

        if rawleads_count > filter_count:
            for rid in rawleads_ids:
                db.update(rawleads, {'id': rid, 'merge_status': 1})
        else:
            for rid in filter_ids:
                db.update(rawleads, {'id': rid, 'merge_status': 2})

        db.update(collections, {'id': collection_id,
                                'viable_count': viable_count,
                                'merge_count': rawleads_count,
                                'status': CollectionStatus.Merged,
                                'last_modifed': now})

        db.update(transformtasks, {'id': task_id,
                                   'status': TransformTaskStatus.MergeSuccess,
                                   'last_modifed': now})

    def _get_viableleads_dict(self, db, merge_keys, start_time, end_time):
        logger.info('<_get_viableleads_dict> start_time: ' +
                    str(start_time) + ', end_time: ' + str(end_time))
        viableleads_dict = {}
        rl = viableleads.alias('l')
        rc = viablecontacts.alias('c')
        cols = []
        for name in merge_keys:
            col = self._get_table_column(rl, name)
            if col is not None:
                cols.append(col)
            else:
                col = self._get_table_column(rc, name)
                if col is not None:
                    cols.append(col)

        query = select(cols)
        join = rl.outerjoin(rc, rl.c.contact_id == rc.c.id)
        query = query.select_from(join)
        query = query.where(rl.c.created_date.between(start_time, end_time))
        rows = db.execute(query).fetchall()
        end = len(cols)
        for r in rows:
            vs = []
            for i in range(0, end):
                vs.append(str(r[i]))
            viableleads_dict['@'.join(vs)] = 1
        return viableleads_dict

    def _get_table_column(self, table, name):
        """
        根据名称获取数据库表映射字段。

        :param table: 数据库表(sqlalchemy.Table类型对象)
        :param name: 名称（str 类型）
        :retrun : 数据库表映射字段(sqlalchemy.Column类型)
        """
        for c in table.c:
            if c.name == name:
                return c
        return None

    def _copy_rawleads_to_viableleads(self, db, collection_id, merge_count):
        logger.info('<_copy_rawleads_to_viableleads> collection_id=' +
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
                qq, weixin, open_id, ip_address, country_code,
                country_name, province_code, province_name,
                city_code, city_name, district_code, district_name,
                address,
                created_date)
                SELECT c.id, c.no, c.collection_id, c.en_name, c.first_name,
                c.last_name, c.full_name, c.gender, c.age, c.birth_date,
                c.birth_year, c.birth_month, c.birth_day, c.id_type, c.id_number,
                c.marriage, c.num_of_childs, c.education, c.income, c.job_title,
                c.vip_flag, c.mobile_phone, c.home_phone, c.work_phone, c.email,
                c.qq, c.weixin, c.open_id, c.ip_address, c.country_code,
                c.country_name, c.province_code, c.province_name,
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
                contact_id, collection_id, product_id,
                customer_type, description, agentcode,
                customer_json, family_json,
                created_date, last_modifed)
                SELECT id, no, budget, need, authority,
                time_frame, premiun, channel_id, campaign_id, company_id,
                contact_id, collection_id, product_id,
                customer_type, description, agentcode,
                customer_json, family_json,
                created_date, last_modifed FROM lms_raw_leads
                WHERE collection_id = :cid and effective = 1
                and merge_status = 1
                """

            db.execute(text(sql), {'cid': collection_id})
        except Exception as e:
            logger.exception('<_copy_rawleads_to_viableleads> error: ')
            result = {'code': ErrorCode.EXCEPTION.value, 'message': str(e)}

        return result
