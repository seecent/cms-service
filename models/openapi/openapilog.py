from sqlalchemy import Column, BigInteger, Integer, String,\
    Enum, DateTime, Table, ForeignKey
from models import Base
import enum


class APIResult(enum.IntEnum):
    Success = 1
    Fail = 2
    Error = 3


openapilogs = Table('cms_open_api_logs', Base.metadata,
                    Column('id', BigInteger, primary_key=True),
                    Column('api_id', None, ForeignKey('lms_open_apis.id')),
                    Column('api_result', Enum(APIResult),
                           default=APIResult.Success),
                    Column('clent_id', None, ForeignKey(
                        'lms_api_accounts.id')),
                    Column('clent_ip', String(50)),
                    Column('detail', String(4000)),
                    Column('call_date', DateTime, nullable=False),
                    Column('end_date', DateTime),
                    Column('cost_time', Integer),
                    Column('created_date', DateTime, nullable=False)
                    )
