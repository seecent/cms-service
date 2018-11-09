from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    DateTime, ForeignKey
from models import Base


folders = Table('cms_folders', Base.metadata,
                Column('id', BigInteger, primary_key=True),
                Column('code', String(50), nullable=False),
                Column('name', String(50), nullable=False),
                Column('description', String(256)),
                Column('level', Integer, default=1),
                Column('parent_id', None, ForeignKey(
                    'cms_folders.id', ondelete="set null")),
                Column('owner_id', None, ForeignKey(
                    'cms_users.id', ondelete="set null")),
                Column('created_date', DateTime, nullable=False),
                Column('last_modifed', DateTime)
                )
