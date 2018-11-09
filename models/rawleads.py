from sqlalchemy import Column, BigInteger, Integer, String, DateTime,\
    Table, ForeignKey, Index
from models import Base


rawleads = Table('lms_raw_leads', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('no', Integer, default=0),
    Column('name', String(100)),
    Column('budget', Integer),
    Column('need', String(100)),
    Column('authority', String(100)),
    Column('time_frame', String(100)),
    Column('premiun', Integer),
    Column('effective', Integer, default=0),
    Column('merge_status', Integer, default=0),
    Column('channel_id', None, ForeignKey('lms_sales_channels.id')),
    Column('campaign_id', None, ForeignKey('lms_campaigns.id')),
    Column('company_id', None, ForeignKey('lms_companies.id')),
    Column('contact_id', None, ForeignKey('lms_raw_contacts.id')),
    Column('collection_id', None, ForeignKey('lms_collections.id')),
    Column('product_id', None, ForeignKey('lms_products.id')),
    Column('description', String(1024)),
    Column('customer_type', Integer, default=0),
    Column('customer_json', String(2048)),
    Column('family_json', String(2048)),
    Column('agentcode', String(50)),
    Column('err_msg', String(4000)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)

Index('idx_lms_rawleads_created_date', rawleads.c.created_date)

rawcontacts = Table('lms_raw_contacts', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('no', Integer, default=0),
    Column('collection_id', None, ForeignKey('lms_collections.id')),
    Column('en_name', String(50)),
    Column('first_name', String(20)),
    Column('last_name', String(20)),
    Column('full_name', String(50)),
    Column('gender', Integer),
    Column('age', Integer),
    Column('birth_date', String(20)),
    Column('birth_year', Integer),
    Column('birth_month', Integer),
    Column('birth_day', Integer),
    Column('id_type', Integer),
    Column('id_number', String(50)),
    Column('marriage', Integer),
    Column('num_of_childs', Integer),
    Column('education', Integer),
    Column('income', Integer),
    Column('job_title', String(100)),
    Column('vip_flag', String(100)),
    Column('mobile_phone', String(20)),
    Column('home_phone', String(20)),
    Column('work_phone', String(20)),
    Column('email', String(50)),
    Column('qq', String(20)),
    Column('weixin', String(50)),
    Column('open_id', String(50)),
    Column('ip_address', String(50)),
    Column('country_code', String(10)),
    Column('country_name', String(64)),
    Column('province_code', String(10)),
    Column('province_name', String(50)),
    Column('city_code', String(10)),
    Column('city_name', String(50)),
    Column('district_code', String(10)),
    Column('district_name', String(50)),
    Column('address', String(200)),
    # Column('location_id', None, ForeignKey('lms_locations.id')),
    # Column('company_id', None, ForeignKey('lms_contact_company.id')),
    Column('created_date', DateTime, nullable=False)
)