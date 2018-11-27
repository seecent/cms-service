from sqlalchemy import Column, BigInteger, String,\
    Enum, DateTime, Table
from models import Base
import enum


class AccountStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


wxaccounts = Table('wx_accounts', Base.metadata,
                   Column('id', BigInteger, primary_key=True, comment='ID'),
                   Column('code', String(64), nullable=False,
                          comment='微信公众号ID'),
                   Column('app_id', String(32),
                          nullable=False, comment='AppID'),
                   Column('app_secret', String(64),
                          nullable=False, comment='AppSecret'),
                   Column('name', String(64), nullable=False,
                          comment='微信公众号名成'),
                   Column('description', String(512), comment='描述'),
                   Column('access_token', String(512), comment='AccessToken'),
                   Column('refresh_time', BigInteger, comment='刷新时间'),
                   Column('effective_time', BigInteger, comment='Token过期时间'),
                   Column('status', Enum(AccountStatus),
                          default=AccountStatus.Active, comment='状态'),
                   Column('created_date', DateTime,
                          nullable=False, comment='创建时间'),
                   Column('last_modifed', DateTime, comment='修改时间')
                   )
