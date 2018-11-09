from sqlalchemy import Column, String, Table, DateTime, BigInteger
from models import Base


fiveelementsunion = Table('FIVEELEMENTSUNION', Base.metadata,
                          Column('fiveUnionID', BigInteger, primary_key=True),
                          Column('name', String(120)),
                          Column('sex', String(1)),
                          Column('birthDate', DateTime),
                          Column('certType', String(3)),
                          Column('certNo', String(50))
                          )
