from sqlalchemy import Column, String, Table, BigInteger
from models import Base


mobileunion = Table('MOBILEUNION', Base.metadata,
                    Column('mobileUnionID', BigInteger),
                    Column('mobilePhone', String(30))
                    )
