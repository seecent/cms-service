import enum

from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    DateTime, ForeignKey
from models import Base


class PermissionType(enum.Enum):
    View = 1
    Create = 2
    Update = 3
    Delete = 4
    Import = 5
    Export = 6
    Upload = 7
    Download = 8
    ChangeStatus = 9
    Assign = 10


menus = Table('cms_menus', Base.metadata,
              Column('id', BigInteger, primary_key=True),
              Column('code', String(32), nullable=False, unique=True),
              Column('name', String(128), nullable=False),
              Column('parent_id', None, ForeignKey('cms_menus.id')),
              Column('path', String(1024), nullable=False),
              Column('icon', String(128)),
              Column('url', String(1024)),
              Column('url_params', String(128)),
              Column('grade', Integer, default=0),
              Column('order_no', Integer, default=0),
              Column('permissions', String(512)),
              Column('memo', String(512)),
              Column('target', String(20)),
              Column('created_date', DateTime, nullable=False),
              Column('last_modifed', DateTime)
              )
