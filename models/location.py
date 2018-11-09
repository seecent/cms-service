import enum
from sqlalchemy import Column, BigInteger, String, Table,\
    Enum, DateTime, ForeignKey
from models import Base


class LocationType(enum.Enum):
    Country = 1
    Province = 2
    City = 3
    District = 4


locations = Table('cms_locations', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(10), nullable=False),
    Column('name', String(50), nullable=False),
    Column('short_name', String(50)),
    Column('type', Enum(LocationType), default=LocationType.Country),
    Column('parent_id', None, ForeignKey('cms_locations.id')),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
