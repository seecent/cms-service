from sqlalchemy import Column, BigInteger, String, DateTime, Table
from models import Base


contactcompanies = Table('lms_contact_company', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(100), nullable=False),
    Column('name', String(100), nullable=False),
    Column('short_name', String(32)),
    Column('business_type', String(100)),
    Column('memo', String(512)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
