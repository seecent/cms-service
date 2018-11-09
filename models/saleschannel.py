from sqlalchemy import Column, BigInteger, String, Table, DateTime
from models import Base


saleschannels = Table('lms_sales_channels', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(50)),
    Column('name', String(100)),
    Column('type', String(100)),
    Column('memo', String(512)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime, nullable=False)
)
