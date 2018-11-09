from sqlalchemy import Column, BigInteger, Integer, String, DateTime,\
    Table
from models import Base


traceactions = Table('LMS_TRACEACTION', Base.metadata,
    Column('seqId', BigInteger, primary_key=True),
    Column('lead_seqId', BigInteger),
    Column('actionCode', String(32)),
    Column('actionType', Integer),
    Column('actionName', String(32)),
    Column('actionStartTime', DateTime),
    Column('actionEndTime', DateTime),
    Column('actionExecTime', DateTime),
    Column('actionResult', String(32)),
    Column('createTime', DateTime),
    Column('updateime', DateTime)
)
