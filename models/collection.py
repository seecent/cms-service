import enum
from sqlalchemy import Column, BigInteger, Integer, String, DateTime,\
    Table, Enum, ForeignKey
from models import Base


class CollectionType(enum.Enum):
    ImportCSV = 1
    ImportDB = 2
    ImportXML = 3
    CronImport = 4


class CollectionStatus(enum.Enum):
    Collecting = 1
    Fail = 2
    Success = 3
    Cleaned = 4
    Merged = 5


collections = Table('lms_collections', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(100)),
    Column('name', String(100)),
    Column('type', Enum(CollectionType), default=CollectionType.ImportCSV),
    Column('source', String(100)),
    Column('save_file', String(100)),
    Column('source_count', Integer),
    Column('fail_count', Integer, default=0),
    Column('collect_count', Integer),
    Column('viable_count', Integer),
    Column('merge_count', Integer),
    Column('channel_id', None, ForeignKey('lms_sales_channels.id')),
    Column('template_id', None, ForeignKey('lms_import_templates.id')),
    Column('user_id', None, ForeignKey('cms_users.id', ondelete="set null")),
    Column('username', String(128)),
    Column('cost_time', BigInteger),
    Column('error_code', String(10), default='0'),
    Column('error_msg', String(1024), default='OK'),
    Column('status',
           Enum(CollectionStatus), default=CollectionStatus.Fail),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
