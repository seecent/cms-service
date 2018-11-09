from sqlalchemy import Column, BigInteger, String, DateTime, Table
from models import Base


products = Table('lms_products', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(100)),
    Column('name', String(100)),
    Column('prod_category', String(100)),
    Column('memo', String(512)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
