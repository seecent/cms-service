from sqlalchemy import Column, BigInteger, String,\
    DateTime, ForeignKey, Table
from models import Base


wxusertags = Table('wx_user_tags', Base.metadata,
                   Column('id', BigInteger, primary_key=True),
                   Column('tag_id', BigInteger, nullable=False),
                   Column('name', String(32), nullable=False),
                   Column('account_id', None, ForeignKey(
                       'wx_accounts.id', ondelete="set null")),
                   Column('created_date', DateTime, nullable=False),
                   Column('last_modifed', DateTime)
                   )
