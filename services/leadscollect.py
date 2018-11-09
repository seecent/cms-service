
from __future__ import absolute_import

from config import db
from datetime import datetime
from api.campaign import query_all_campaigns
from api.product import query_all_products
from models.rawleads import rawleads, rawcontacts
from models.campaign import campaigns
from models.product import products
from sqlalchemy.sql import select, text
from sqlalchemy import MetaData, Column,\
    String, Table, DateTime, Boolean, Integer


class LeadsCollectService:
    def get_channel_id(self, channel_code):
        db.connect()
        s = text("SELECT id FROM sales_channels WHERE code = :x")
        result = db.execute(s, x=channel_code)
        id = -1
        if result.rowcount == 1:
            id = result['id']
        db.close()
        return id

    def fetch_view(self, conn, viewname):
        metadata = MetaData()
        view = Table(viewname, metadata,
                     Column('channel_code', String),
                     Column('campaign_code', String),
                     Column('company_code', Integer),
                     Column('en_name', String),
                     Column('first_name', String),
                     Column('last_name', String),
                     Column('full_name', String),
                     Column('id_type', Integer),
                     Column('id_number', String),
                     Column('gender', String),
                     Column('age', String),
                     Column('birth_year', Integer),
                     Column('birth_month', Integer),
                     Column('birth_day', Integer),
                     Column('marriage', Boolean),
                     Column('num_of_childs', Integer),
                     Column('education', Integer),
                     Column('income', Integer),
                     Column('mobile_phone', String),
                     Column('home_phone', String),
                     Column('work_phone', String),
                     Column('email', String),
                     Column('qq', String),
                     Column('weixin', String),
                     Column('open_id', String),
                     Column('ip_address', String),
                     Column('province_code', String),
                     Column('city_code', String),
                     Column('district_code', String),
                     Column('address', String),
                     Column('budget', Integer),
                     Column('need', String),
                     Column('authority', String),
                     Column('time_frame', String),
                     Column('product_code', String),
                     Column('product_name', String),
                     Column('last_modifed', DateTime),
                     )
        s = select([view])
        result = conn.execute(s)
        return result

    def toIntger(self, s):
        if s and s != '':
            return int(s)
        else:
            return None

    def textValue(self, name, d):
        if name in d.keys():
            return d[name]
        return None

    def intValue(self, name, d):
        if name in d.keys():
            v = d[name]
            if v and v != '':
                return int(v)
        return None

    def genderValue(self, name, d):
        if name in d.keys():
            v = d[name]
            if v and v == 'F':
                return 1
            if v and v == 'M':
                return 0
        return None

    def insert_file_leads(self, conn, collection_id, channel, rows):
        campaign_dict = query_all_campaigns()
        product_dict = query_all_products()
        success_count = 0
        total = len(rows)
        batch = 5000
        if total > batch:
            begin = 0
            end = 0
            pages = int(total / batch)
            for n in range(0, pages):
                begin = n * batch
                end = begin + batch
                page_rows = rows[begin:end]
                contact_ids = self.bulk_insert_contacts(conn, collection_id,
                                                        begin, page_rows)
                page_count = self.bulk_insert_leads(conn, collection_id,
                                                    channel, begin,
                                                    page_rows, campaign_dict,
                                                    product_dict, contact_ids)
                success_count = success_count + page_count

            if end < (total - 1):
                begin = end
                end = total
                page_rows = rows[begin:end]
                contact_ids = self.bulk_insert_contacts(conn, collection_id,
                                                        begin, page_rows)
                page_count = self.bulk_insert_leads(conn, collection_id,
                                                    channel, begin,
                                                    page_rows, campaign_dict,
                                                    product_dict, contact_ids)
                success_count = success_count + page_count

        else:
            no = 0
            contact_ids = self.bulk_insert_contacts(conn, collection_id,
                                                    no, rows)
            success_count = self.bulk_insert_leads(conn, collection_id,
                                                   channel, no, rows,
                                                   campaign_dict, product_dict,
                                                   contact_ids)

        return success_count

    def bulk_insert_contacts(self, conn, collection_id, no, rows):
        now = datetime.now()
        contacts = []
        begin = no
        for d in rows:
            contact = {'no': no,
                       'en_name': self.textValue('EnName', d),
                       'full_name': self.textValue('FullName', d),
                       'first_name': self.textValue('FirstName', d),
                       'last_name': self.textValue('LastName', d),
                       'gender': self.genderValue('Gender', d),
                       'age': self.intValue('Age', d),
                       'birth_year': self.intValue('BirthYear', d),
                       'birth_month': self.intValue('BirthMonth', d),
                       'birth_day': self.intValue('BirthDay', d),
                       'id_type': self.intValue('IDType', d),
                       'id_number': self.textValue('IDNumber', d),
                       'marriage': self.intValue('Marriage', d),
                       'num_of_childs': self.intValue('NumOfChilds', d),
                       'education': self.intValue('Education', d),
                       'mobile_phone': self.textValue('MobilePhone', d),
                       'home_phone': self.textValue('HomePhone', d),
                       'work_phone': self.textValue('WorkPhone', d),
                       'email': self.textValue('Email', d),
                       'qq': self.textValue('QQ', d),
                       'weixin': self.textValue('Weixin', d),
                       'open_id': self.textValue('OpenID', d),
                       'province_code': self.textValue('ProvinceCode', d),
                       'city_code': self.textValue('CityCode', d),
                       'district_code': self.textValue('DistrictCode', d),
                       'collection_id': collection_id,
                       'location_id': None,
                       'company_id': None,
                       'created_date': now, 'last_modifed': now}
            contacts.append(contact)
            no = no + 1

        conn.execute(rawcontacts.insert(), contacts)

        end = no
        query = select([rawcontacts.c.id])
        query = query.where(rawcontacts.c.collection_id == collection_id)
        query = query.where(rawcontacts.c.no.between(begin, end))
        rows = conn.execute(query)

        contact_ids = []
        for r in rows:
            contact_ids.append(r[0])

        return contact_ids

    def bulk_insert_leads(self, conn, collection_id, channel, no, rows,
                          campaign_dict, product_dict, contact_ids):
        now = datetime.now()
        leads = []
        batch = len(rows)
        n = 0
        for d in rows:
            cam_id = None
            cam_code = self.textValue('CampaignCode', d)
            cam_name = self.textValue('CampaignName', d)
            if cam_code:
                cam_id = self.save_campaign(conn, cam_code, cam_name,
                                            campaign_dict)

            prod_id = None
            prod_code = self.textValue('ProductCode', d)
            prod_name = self.textValue('ProductName', d)
            if prod_code:
                prod_id = self.save_product(conn, prod_code, prod_name,
                                            product_dict)

            lead = {'no': no + n,
                    'channel_id': channel,
                    'collection_id': collection_id,
                    'contact_id': contact_ids[n],
                    'name': prod_name,
                    'budget': self.intValue('Budget', d),
                    'authority': self.textValue('Authority', d),
                    'need': self.textValue('Need', d),
                    'timeFrame': self.textValue('TimeFrame', d),
                    'campaign_id': cam_id,
                    'company_id': None,
                    'product_id': prod_id,
                    'created_date': now, 'last_modifed': now}
            leads.append(lead)
            n = n + 1

        conn.execute(rawleads.insert(), leads)

        return batch

    def insert_db_leads(self, conn, collection_id, rows, now):
        failed = 0
        for d in rows:
            channelid = self.get_channel_id(d['channel_code'])
            if channelid == -1:
                failed = failed + 1
                continue
            contact = {'en_name': d['en_name'],
                       'full_name': d['full_name'],
                       'first_name': d['first_name'],
                       'last_name': d['last_name'],
                       'gender': self.toIntger(d['gender']),
                       'age': self.toIntger(d['age']),
                       'birth_year': self.toIntger(d['birth_year']),
                       'birth_month': self.toIntger(d['birth_month']),
                       'birth_day': self.toIntger(d['birth_day']),
                       'id_type': self.toIntger(d['id_type']),
                       'id_number': d['id_number'],
                       'marriage': self.toIntger(d['marriage']),
                       'num_of_childs': self.toIntger(d['num_of_childs']),
                       'education': self.toIntger(d['education']),
                       'mobile_phone': d['mobile_phone'],
                       'home_phone': d['home_phone'],
                       'work_phone': d['work_phone'],
                       'email': d['email'],
                       'qq': d['qq'],
                       'weixin': d['weixin'],
                       'open_id': d['open_id'],
                       'province_code': d['province_code'],
                       'city_code': d['city_code'],
                       'district_code': d['district_code'],
                       'collection_id': collection_id,
                       'created_date': now, 'last_modifed': now}
            rs = conn.execute(rawcontacts.insert(), contact)

            lead = {'channel_id': channelid,
                    'collection_id': collection_id,
                    'contact_id': rs.inserted_primary_key[0],
                    'budget': self.toIntger(d['budget']),
                    'need': d['need'],
                    'authority': d['authority'],
                    'timeFrame': d['time_frame'],
                    'created_date': now, 'last_modifed': now}
            rs = conn.execute(rawleads.insert(), lead)
        return failed

    def save_campaign(self, conn, code, name, campaign_dict):
        if code in campaign_dict.keys():
            c = campaign_dict[code]
            return c['id']
        else:
            q = select([campaigns.c.id,
                        campaigns.c.code,
                        campaigns.c.name])
            q = q.where(campaigns.c.code == code)
            row = conn.execute(q).fetchone()
            if row:
                c = {'id': row[0], 'code': code, 'name': row[2]}
                campaign_dict[code] = c
                return c['id']
            else:
                now = datetime.now()
                ins = campaigns.insert()
                rs = conn.execute(ins, code=code, name=name,
                                  created_date=now, last_modifed=now)
                campaign_id = rs.inserted_primary_key[0]
                c = {'id': campaign_id, 'code': code, 'name': name}
                campaign_dict[code] = c
                return campaign_id

    def save_product(self, conn, code, name, product_dict):
        if code in product_dict.keys():
            c = product_dict[code]
            return c['id']
        else:
            q = select([products.c.id,
                        products.c.code,
                        products.c.name])
            q = q.where(products.c.code == code)
            row = conn.execute(q).fetchone()
            if row:
                c = {'id': row[0], 'code': code, 'name': row[2]}
                product_dict[code] = c
                return c['id']
            else:
                now = datetime.now()
                ins = products.insert()
                rs = conn.execute(ins, code=code, name=name,
                                  created_date=now, last_modifed=now)
                product_id = rs.inserted_primary_key[0]
                c = {'id': product_id, 'code': code, 'name': name}
                product_dict[code] = c
                return product_id
