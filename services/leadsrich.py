
from __future__ import absolute_import

import re

from cache import locationcache
from config import db
from datetime import datetime
from log import logger
from models.rawleads import rawleads, rawcontacts
from models.viableleads import viablecontacts
from sqlalchemy.sql import select

REGX = r'^\d{17}(\d{1}|x|X)$'
BD_REGX = r'^\d{8}$'
BD2_REGX = r'^\d{4}-\d{2}-\d{2}$'


class LeadsRichService:
    def rich_raw_leads(self, cid: int):
        logger.info('<rich_raw_leads> cid: ' + str(cid))
        try:
            db.connect()
            rl = rawleads.alias('l')
            rc = rawcontacts.alias('c')
            q = select([rc.c.id,
                        rc.c.gender,
                        rc.c.age,
                        rc.c.birth_date,
                        rc.c.birth_year,
                        rc.c.birth_month,
                        rc.c.birth_day,
                        rc.c.id_type,
                        rc.c.id_number,
                        rc.c.province_code,
                        rc.c.province_name,
                        rc.c.city_code,
                        rc.c.city_name,
                        rl.c.collection_id,
                        rl.c.contact_id,
                        rl.c.merge_status])
            join = rl.outerjoin(rc, rl.c.contact_id == rc.c.id)
            q = q.select_from(join).where(rl.c.collection_id == cid)
            q = q.where(rl.c.merge_status == 1)
            datas = []
            rows = db.execute(q).fetchall()
            for r in rows:
                datas.append({'id': r[0],
                              'gender': r[1],
                              'age': r[2],
                              'birth_date': r[3],
                              'birth_year': r[4],
                              'birth_month': r[5],
                              'birth_day': r[6],
                              'id_type': r[7],
                              'id_number': r[8],
                              'province_code': r[9],
                              'province_name': r[10],
                              'city_code': r[11],
                              'city_name': r[12]})
            for d in datas:
                self.rich_data(db, rawcontacts, d)
            db.close()
        except Exception as e:
            logger.exception('<rich_raw_leads> cid: ' + str(cid) + ', error=')

    def rich_viable_leads(self, cid):
        logger.info('<rich_viable_leads> cid: ' + str(cid))
        try:
            db.connect()
            vc = viablecontacts.alias('c')
            q = select([vc.c.id,
                        vc.c.gender,
                        vc.c.age,
                        vc.c.birth_date,
                        vc.c.birth_year,
                        vc.c.birth_month,
                        vc.c.birth_day,
                        vc.c.id_type,
                        vc.c.id_number,
                        vc.c.province_code,
                        vc.c.province_name,
                        vc.c.city_code,
                        vc.c.city_name,
                        vc.c.collection_id])
            q = q.where(vc.c.collection_id == cid)
            datas = []
            rows = db.execute(q).fetchall()
            for r in rows:
                datas.append({'id': r[0],
                              'gender': r[1],
                              'age': r[2],
                              'birth_date': r[3],
                              'birth_year': r[4],
                              'birth_month': r[5],
                              'birth_day': r[6],
                              'id_type': r[7],
                              'id_number': r[8],
                              'province_code': r[9],
                              'province_name': r[10],
                              'city_code': r[11],
                              'city_name': r[12]})
            for d in datas:
                self.rich_data(db, viablecontacts, d)
            db.close()
        except Exception as e:
            logger.exception('<rich_viable_leads> cid: ' + str(cid) +
                             ', error=')

    def rich_data(self, db, table, data):
        try:
            change = self._rich_data_by_idnumber(data)
            if change:
                self._rich_data_birth(data)
            else:
                change = self._rich_data_birth(data)
            if change:
                logger.info('<rich_data> table: ' + table.name +
                            ', data: ' + str(data))
                db.update(table, data)
        except Exception as e:
            logger.exception('<rich_data> error=')

    # 判断是否为合法身份证号码
    def _check_idnumber(self, idnumber):
        try:
            if idnumber is not None:
                if len(idnumber) == 18:
                    return re.match(REGX, idnumber)
        except Exception as e:
            logger.exception('<_check_idnumber> error=')
        return False

    def _rich_data_by_idnumber(self, data):
        change = False
        try:
            id_number = data['id_number']
            if self._check_idnumber(id_number):
                # gender = id_number[17]
                birth_date = data.get('birth_date')
                province_code = data.get('province_code')
                city_code = data.get('city_code')
                if birth_date is None or birth_date == '':
                    change = True
                    data['birth_date'] = id_number[6:14]
                if province_code is None or province_code == '':
                    change = True
                    provincecode = id_number[0:2] + '0000'
                    province_name = data.get('province_name')
                    data['province_code'] = provincecode
                    data['province_name'] = locationcache.get(provincecode,
                                                              province_name)
                if city_code is None or city_code == '':
                    change = True
                    citycode = id_number[0:4] + '00'
                    city_name = data.get('city_name')
                    data['city_code'] = citycode
                    data['city_name'] = locationcache.get(citycode, city_name)
        except Exception as e:
            logger.exception('<_rich_data_by_idnumber> error=')
        return change

    # 判断是否为合法出生日期
    def _split_birth_date(self, birth_date):
        try:
            bd_len = len(birth_date)
            if bd_len == 8:
                if re.match(BD_REGX, birth_date):
                    return [birth_date[0:4],
                            birth_date[4:6],
                            birth_date[6:8]]
            elif bd_len == 11:
                if re.match(BD2_REGX, birth_date):
                    return birth_date.split('-')
        except Exception as e:
            logger.exception('<_check_birth_date> error=')
        return None

    def _rich_data_birth(self, data):
        change = False
        try:
            age = data.get('age')
            birth_date = data.get('birth_date')
            birth_year = data.get('birth_year')
            if birth_year is not None:
                if birth_date is None or birth_date == '':
                    birth_date = str(birth_year)
                    birth_month = data.get('birth_month')
                    if birth_month is not None:
                        birth_date += str(birth_month)
                        birth_day = data.get('birth_day')
                        if birth_day is not None:
                            birth_date += str(birth_day)
                    change = True
                    data['birth_date'] = birth_date
                if age is None:
                    change = True
                    now = datetime.now()
                    data['age'] = now.year - birth_year
            elif birth_date is not None:
                bds = self._split_birth_date(birth_date)
                if bds is not None:
                    change = True
                    data['birth_year'] = bds[0]
                    data['birth_month'] = bds[1]
                    data['birth_day'] = bds[2]
        except Exception as e:
            logger.exception('<_rich_data_birth> error=')
        return change
