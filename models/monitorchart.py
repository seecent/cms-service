import enum

from sqlalchemy import Column, BigInteger, Integer, String, DateTime,\
    Enum, Table, ForeignKey
from models import Base


class MonitorStatus(enum.Enum):
    Open = 1
    Closed = 2


monitorcharts = Table('cms_monitor_charts', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100), nullable=False),
    Column('collect_count', Integer),
    Column('viable_count', Integer),
    Column('merge_count', Integer),
    Column('channel_id', None, ForeignKey('lms_sales_channels.id')),
    Column('collection_id', None, ForeignKey('lms_collections.id')),
    Column('campaign_id', None, ForeignKey('lms_campaigns.id')),
    Column('begin_date', DateTime),
    Column('end_date', DateTime),
    Column('user_id', None, ForeignKey('cms_users.id', ondelete="set null")),
    Column('username', String(128)),
    Column('status', Enum(MonitorStatus), default=MonitorStatus.Open),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
