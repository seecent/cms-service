from sqlalchemy import Column, BigInteger, Integer, String,\
    Table, Index
from models import Base


amssales = Table('AMS_AMSSALES', Base.metadata,
    Column('staffNo', String(32), primary_key=True),
    Column('name', String(64)),
    Column('sex', String(4)),
    Column('birthday', String(16)),
    Column('idno', String(32)),
    Column('phone', String(16)),
    Column('email', String(64)),
    Column('address', String(225)),
    Column('channel', String(8)),
    Column('comCode', String(8)),
    Column('ssoCode', String(8)),
    Column('dutyDeg', String(8)),
    Column('dutyName', String(64)),
    Column('joinDate', BigInteger),
    Column('agStatus', Integer),
    Column('startMthnum', Integer),
    Column('quafNo', String(32)),
    Column('quafStartDate', BigInteger),
    Column('quafEndDate', BigInteger),
    Column('abossnum', String(32)),
    Column('bbossnum', String(32)),
    Column('cbossnum', String(32)),
    Column('dbossnum', String(32)),
    Column('ibossnum', String(32))
)

Index('idx_amssales_comcode', amssales.c.comCode)
Index('idx_amssales_ssocode', amssales.c.ssoCode)
