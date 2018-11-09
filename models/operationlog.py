import enum

from sqlalchemy import Column, BigInteger, String, DateTime,\
    Enum, Table, ForeignKey
from models import Base


class OperType(enum.Enum):
    Login = 1
    Logout = 2
    Create = 3
    Update = 4
    Delete = 5
    Import = 6
    Upload = 7
    Download = 8


class OperResult(enum.IntEnum):
    Success = 1
    PartialSucess = 2
    Fail = 3


operationlogs = Table('cms_operation_logs', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(128)),
    Column('detail', String(4000)),
    Column('object_id', BigInteger),
    Column('object', String(128)),
    Column('type', Enum(OperType), default=OperType.Login),
    Column('result', Enum(OperResult), default=OperResult.Success),
    Column('ip_address', String(50)),
    Column('user_id', None, ForeignKey('cms_users.id', ondelete="set null")),
    Column('username', String(128)),
    Column('created_date', DateTime, nullable=False)
)
