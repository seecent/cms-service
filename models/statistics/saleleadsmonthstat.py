from sqlalchemy import Column, String, Table, Integer, Index
from models import Base

saleleadsmonthstats = Table('lms_saleleads_monthstat', Base.metadata,
                            Column('stat_date', Integer),
                            Column('saleno', String(32)),
                            Column('year', Integer),
                            Column('month', Integer),
                            Column('lead_count', Integer),
                            Column('call_count', Integer),
                            Column('visit_count', Integer),
                            Column('order_count', Integer)
                            )

Index('idx_lms_saleleads_monthstat_stat_date', saleleadsmonthstats.c.stat_date)
Index('idx_lms_saleleads_monthstat_saleno', saleleadsmonthstats.c.saleno)
