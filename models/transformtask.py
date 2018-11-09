import enum
from sqlalchemy import Column, BigInteger, String, DateTime,\
    Enum, Table, ForeignKey
from models import Base


class TransformTaskStatus(enum.Enum):
    Created = 1
    Cleaning = 2
    CleanSuccess = 3
    CleanFail = 4
    Merging = 5
    MergeSuccess = 6
    MergeFail = 7


transformtasks = Table('lms_transform_tasks', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('collection_id', None, ForeignKey('lms_collections.id')),
    Column('template_id', None, ForeignKey('lms_import_templates.id')),
    Column('status', Enum(TransformTaskStatus), default=TransformTaskStatus.Created),
    Column('error_msg', String(1024)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
