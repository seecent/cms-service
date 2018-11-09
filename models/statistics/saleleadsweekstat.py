from sqlalchemy import Column, String, Table, Integer, Index
from models import Base

saleleadsweekstats = Table('lms_saleleads_weekstat', Base.metadata,
                           Column('stat_date', Integer),
                           Column('saleno', String(32)),
                           Column('year', Integer),
                           Column('month', Integer),
                           Column('week_of_year', Integer),  # 每年第几周，
                           Column('week_of_month', Integer),  # 月份的第几周
                           Column('lead_count', Integer),
                           Column('call_count', Integer),
                           Column('visit_count', Integer),
                           Column('order_count', Integer)
                           )

Index('idx_lms_saleleads_weekstat_stat_date', saleleadsweekstats.c.stat_date)
Index('idx_lms_saleleads_weekstat_saleno', saleleadsweekstats.c.saleno)
