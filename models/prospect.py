from sqlalchemy import Column, BigInteger, String, DateTime,\
    Table
from models import Base


prospects = Table('lms_prospects', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('company_code', String(30)),
    Column('prospect_id', String(32)),
    Column('name', String(100)),
    Column('phone', String(30)),
    Column('description', String(512)),
    Column('province_code', String(10)),
    Column('province_name', String(50)),
    Column('city_code', String(10)),
    Column('city_name', String(50)),
    Column('district_code', String(10)),
    Column('district_name', String(50)),
    Column('job_log_id', BigInteger),
    Column('created_date', DateTime, nullable=False)
)
