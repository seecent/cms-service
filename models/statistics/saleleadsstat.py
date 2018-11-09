from sqlalchemy import Column, String, Table, DateTime, Integer
from models import Base

saleleadsstats = Table('lms_saleleads_stat', Base.metadata,
                       Column('saleno', String(32), primary_key=True),
                       Column('daily_lead_count', Integer),
                       Column('week_lead_count', Integer),
                       Column('month_lead_count', Integer),
                       Column('month_call_count', Integer),
                       Column('month_visit_count', Integer),
                       Column('month_order_count', Integer),
                       Column('create_time', DateTime)
                       )
