import enum

from sqlalchemy import Column, BigInteger, Integer, String,\
    DateTime, Enum, Table, Index
from models import Base


class JobResult(enum.IntEnum):
    Success = 1
    PartialSucess = 2
    Fail = 3


joblogs = Table('cms_job_logs', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(128)),
    Column('params', String(256)),
    Column('begin_time', DateTime),
    Column('end_time', DateTime),
    Column('page_offset', Integer),
    Column('page_limit', Integer),
    Column('source_count', Integer, default=0),
    Column('insert_count', Integer, default=0),
    Column('update_count', Integer, default=0),
    Column('code', Integer, default=0),
    Column('message', String(1024)),
    Column('result', Enum(JobResult), default=JobResult.Fail),
    Column('run_date', DateTime, nullable=False)
)

Index('idx_joblogs_name', joblogs.c.name)
