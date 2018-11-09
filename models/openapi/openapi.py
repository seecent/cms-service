from sqlalchemy import Column, BigInteger, Integer, String,\
    Enum, DateTime, Table
from models import Base
import enum


class APIType(enum.IntEnum):
    REST = 1
    WebService = 2


class APIStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


openapis = Table('cms_open_apis', Base.metadata,
                 Column('id', BigInteger, primary_key=True),
                 Column('name', String(32), nullable=False),
                 Column('description', String(256)),
                 Column('url', String(256)),
                 Column('config_file', String(32)),
                 Column('config', String(2048)),
                 Column('input_content_type', String(32)),
                 Column('output_content_type', String(32)),
                 Column('api_type', Enum(APIType),
                        default=APIType.REST),
                 Column('status', Enum(APIStatus),
                        default=APIStatus.Active),
                 Column('access_auth', Integer, default=1),
                 Column('enable_api_log', Integer, default=1),
                 Column('created_date', DateTime, nullable=False),
                 Column('last_modifed', DateTime)
                 )
