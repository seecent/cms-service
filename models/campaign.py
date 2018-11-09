from sqlalchemy import Column, BigInteger, String, Table, DateTime
from models import Base


campaigns = Table('lms_campaigns', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(50)),
    Column('name', String(100)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
