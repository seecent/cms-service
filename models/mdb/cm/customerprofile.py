from sqlalchemy import Column, String, Table, BigInteger
from models import Base


customerprofile = Table('CUSTOMERPROFILE', Base.metadata,
                        Column('id', BigInteger, primary_key=True),
                        Column('mobileUnionID', BigInteger),
                        Column('fiveUnionID', BigInteger),
                        Column('name', String(120)),
                        Column('certNo', String(50)),
                        Column('mobilePhone', String(30))
                        )
