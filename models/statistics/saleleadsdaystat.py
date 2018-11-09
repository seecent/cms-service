from sqlalchemy import Column, String, Table, Integer, Index
from models import Base

saleleadsdaystats = Table('lms_saleleads_daystat', Base.metadata,
                          Column('stat_date', Integer),
                          Column('saleno', String(32)),
                          Column('year', Integer),
                          Column('month', Integer),
                          Column('day', Integer),
                          Column('lead_count', Integer),
                          Column('call_count', Integer),
                          Column('visit_count', Integer),
                          Column('order_count', Integer)
                          )
Index('idx_lms_saleleads_daystat_stat_date', saleleadsdaystats.c.stat_date)
Index('idx_lms_saleleads_daystat_saleno', saleleadsdaystats.c.saleno)
