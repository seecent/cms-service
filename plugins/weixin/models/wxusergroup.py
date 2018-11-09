from sqlalchemy import Column, BigInteger, String,\
    DateTime, ForeignKey, Table
from models import Base


wxusergroups = Table('wx_user_groups', Base.metadata,
                     Column('id', BigInteger, primary_key=True),
                     Column('name', String(32), nullable=False),
                     Column('description', String(256)),
                     Column('account_id', None, ForeignKey(
                         'wx_accounts.id', ondelete="set null")),
                     Column('created_date', DateTime, nullable=False),
                     Column('last_modifed', DateTime)
                     )
