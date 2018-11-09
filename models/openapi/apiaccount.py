from sqlalchemy import Column, BigInteger, Integer, String,\
    Enum, DateTime, ForeignKey, Table
from models import Base
import enum


class APIAccountStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


class APIStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


apiaccounts = Table('cms_api_accounts', Base.metadata,
                    Column('id', BigInteger, primary_key=True),
                    Column('clent_id', String(16), nullable=False),
                    Column('clent_secret', String(32), nullable=False),
                    Column('name', String(32), nullable=False),
                    Column('description', String(256)),
                    Column('status', Enum(APIAccountStatus),
                           default=APIAccountStatus.Active),
                    Column('created_date', DateTime, nullable=False),
                    Column('last_modifed', DateTime)
                    )

accountopenapis = Table('cms_account_open_apis', Base.metadata,
                        Column('id', BigInteger, primary_key=True),
                        Column('account_id', None, ForeignKey(
                            'lms_api_accounts.id')),
                        Column('api_id', None, ForeignKey('lms_open_apis.id')),
                        Column('frequency_limit ', Integer, default=10),
                        Column('day_call_quotas', Integer, default=300),
                        Column('total_call_quotas', Integer, default=10000),
                        Column('status', Enum(APIStatus),
                               default=APIStatus.Active),
                        Column('created_date', DateTime, nullable=False),
                        Column('last_modifed', DateTime)
                        )
