from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Table
from models import Base


transformrules = Table('lms_transform_rules', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100)),
    Column('type', Integer),  # 0：清洗规则，1：去重规则
    Column('dir', String(256)),  # 存放全路径
    Column('status', String(100)),
    Column('description', String(1024)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
