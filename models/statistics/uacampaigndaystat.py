from sqlalchemy import Column, BigInteger, Integer, String,\
    Table
from models import Base


uacampaigndaystats = Table('lms_uacampaign_day_stats', Base.metadata,
                           Column('stat_date', Integer, primary_key=True),
                           Column('year', Integer),
                           Column('month', Integer),
                           Column('day', Integer),
                           Column('campaign_id', BigInteger, primary_key=True),
                           Column('campaign_code', String(32)),
                           Column('campaign_name', String(64)),
                           Column('active_leads_count', Integer, default=0)
                           )
