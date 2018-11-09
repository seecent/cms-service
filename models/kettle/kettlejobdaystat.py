from sqlalchemy import Column, Integer, Table
from models import Base


kettlejobdaystats = Table('lms_kettle_job_day_stats', Base.metadata,
    Column('stat_date', Integer, primary_key=True),
    Column('year', Integer),
    Column('month', Integer),
    Column('day', Integer),
    Column('run_count', Integer, default=0),
    Column('success_count', Integer, default=0),
    Column('fail_count', Integer, default=0)
)
