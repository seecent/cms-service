from sqlalchemy import Column, String, Table, BigInteger
from models import Base


contactlist = Table('CONTACTLIST', Base.metadata,
                    Column('mobileUnionID', BigInteger),
                    Column('fiveUnionID', BigInteger),
                    Column('customerSource', String(20)),
                    Column('customerType', String(2)),
                    Column('customerNo', String(50)),
                    Column('policyNo', String(50)),
                    Column('leadsNo', String(50)),
                    Column('name', String(120)),
                    Column('certNo', String(50)),
                    Column('mobilePhone', String(30))
                    )
