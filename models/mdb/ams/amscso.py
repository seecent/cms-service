from sqlalchemy import Column, String, Table, DateTime
from models import Base


amscsos = Table('AMS_AMSCSO', Base.metadata,
    Column('comCode', String(32), primary_key=True),
    Column('comName', String(32)),
    Column('comShortName', String(32)),
    Column('phone', String(16)),
    Column('zipCode', String(10)),
    Column('fax', String(16)),
    Column('proviceNo', String(32)),
    Column('cityNo', String(32)),
    Column('address', String(225)),
    Column('datime', DateTime)
)
