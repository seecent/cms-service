from sqlalchemy import Column, String, Table, DateTime, BigInteger, Float
from models import Base


tracepolicy = Table('LMS_TRACEPOLICY', Base.metadata,
                    Column('seqId', BigInteger),
                    Column('lead_seqId', BigInteger),
                    Column('policyNo', String(50)),
                    Column('premium', Float),
                    Column('createTime', DateTime),
                    Column('updateTime', DateTime)
                    )
