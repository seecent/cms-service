import enum
from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    Enum, DateTime, ForeignKey
from models import Base


class OrgStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


class OrgType(enum.IntEnum):
    GroupCompany = 0
    Company = 1
    Branch = 2
    Department = 3


organizations = Table('cms_organizations', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(20), nullable=False),
    Column('name', String(256), nullable=False),
    Column('short_name', String(64)),
    Column('org_type', Enum(OrgType), default=OrgType.Department),
    Column('telephone', String(32)),
    Column('mobilephone', String(32)),
    Column('fax', String(32)),
    Column('email', String(64)),
    Column('province', String(32)),
    Column('city', String(32)),
    Column('postcode', String(32)),
    Column('address', String(256)),
    Column('memo', String(512)),
    Column('parent_id', None, ForeignKey('cms_organizations.id',
                                         ondelete="set null")),
    Column('location_id', None, ForeignKey('cms_locations.id')),
    Column('org_order', Integer, default=1),
    Column('status', Enum(OrgStatus), default=OrgStatus.Active),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
