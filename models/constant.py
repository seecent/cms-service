from sqlalchemy import Column, Integer, String, DateTime, Table
from models import Base


constants = Table('cms_constants', Base.metadata,
    Column('code', String(20), nullable=False, primary_key=True),
    Column('const_type', String(32), nullable=False, primary_key=True),
    Column('const_type_label', String(100)),
    Column('name', String(100), nullable=False),
    Column('const_alias', String(100)),
    Column('order_no', Integer),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
