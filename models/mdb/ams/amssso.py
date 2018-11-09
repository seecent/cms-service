from sqlalchemy import Column, String, Table, Index
from models import Base


amsssos = Table('AMS_AMSSSO', Base.metadata,
    Column('ssoCode', String(32), primary_key=True),
    Column('ssoName', String(225)),
    Column('comCode', String(8)),
)

Index('idx_amssso_comcode', amsssos.c.comCode)
