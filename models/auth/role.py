from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    DateTime, ForeignKey
from models import Base


roles = Table('cms_roles', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('version', Integer, default=1),
    Column('authority', String(255), nullable=False, unique=True),
    Column('code', String(32), nullable=False),
    Column('name', String(255), nullable=False),
    Column('description', String(512)),
    Column('date_created', DateTime, nullable=False),
    Column('last_updated', DateTime)
)


rolemenus = Table('cms_role_menu', Base.metadata,
    Column('role_id', None, ForeignKey('cms_roles.id')),
    Column('menu_id', None, ForeignKey('cms_menus.id')),
    Column('permissions', String(512)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)


userroles = Table('cms_user_role', Base.metadata,
    Column('user_id', None, ForeignKey('cms_users.id')),
    Column('role_id', None, ForeignKey('cms_roles.id')),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
