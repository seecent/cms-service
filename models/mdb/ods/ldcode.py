from sqlalchemy import Column, String, Table
from models import Base


ldcode = Table('LDCODE', Base.metadata,
               Column('codeType', String(50)),
               Column('code', String(600)),
               Column('codeName', String(120)),
               Column('codeAlias', String(120)),
               Column('comCode', String(10)),
               Column('otherSign', String(10))
               )
