from sqlalchemy import Column, String, Table, DateTime, Integer, BigInteger
from models import Base


assignment = Table('LMS_ASSIGNMENT', Base.metadata,
                   Column('seqId', BigInteger, primary_key=True),
                   Column('lead_seqId', BigInteger),
                   Column('mdb_companyCode', String(10)),
                   Column('mdb_ssoCode', String(10)),
                   Column('mdb_channel', Integer),
                   Column('mdb_agent_code', String(50)),
                   Column('createTime', DateTime),
                   Column('updateTime', DateTime)
                   )
