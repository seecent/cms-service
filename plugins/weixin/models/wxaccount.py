from sqlalchemy import Column, BigInteger, String,\
    Enum, DateTime, Table
from models import Base
import enum


class AccountStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


wxaccounts = Table('wx_accounts', Base.metadata,
                   Column('id', BigInteger, primary_key=True),
                   Column('code', String(64), nullable=False),
                   Column('app_id', String(32), nullable=False),
                   Column('app_secret', String(64), nullable=False),
                   Column('name', String(64), nullable=False),
                   Column('description', String(512)),
                   Column('access_token', String(64)),
                   Column('refresh_time', BigInteger),
                   Column('effective_time', BigInteger),
                   Column('status', Enum(AccountStatus),
                          default=AccountStatus.Active),
                   Column('created_date', DateTime, nullable=False),
                   Column('last_modifed', DateTime)
                   )
