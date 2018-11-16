import enum
from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    Enum, DateTime, Text, ForeignKey
from models import Base


class PageStatus(enum.Enum):
    Create = 1
    Editing = 2
    Published = 3
    Close = 4
    Removed = 5


pages = Table('cms_pages', Base.metadata,
              Column('id', BigInteger, primary_key=True),
              Column('uuid', String(50), nullable=False),
              Column('name', String(50), nullable=False),
              Column('title', String(128)),
              Column('digest', String(256)),
              Column('author', String(256)),
              Column('content', Text),
              Column('image_url', String(512)),
              Column('show_cover_pic', Integer, default=0),
              Column('file_size', BigInteger),
              Column('file_path', String(512)),
              Column('status', Enum(PageStatus), default=PageStatus.Editing),
              Column('category_id', None, ForeignKey(
                  'cms_categories.id', ondelete="set null")),
              Column('owner_id', None, ForeignKey(
                  'cms_users.id', ondelete="set null")),
              Column('is_public', Integer, default=0),
              Column('pubdate', DateTime),
              Column('created_date', DateTime, nullable=False),
              Column('last_modifed', DateTime)
              )

tags = Table('cms_page_tags', Base.metadata,
             Column('id', BigInteger, primary_key=True),
             Column('name', String(50), nullable=False),
             Column('created_date', DateTime, nullable=False),
             Column('last_modifed', DateTime)
             )

pagetags = Table('cms_page_tag_map', Base.metadata,
                 Column('page_id', None, ForeignKey('cms_pages.id')),
                 Column('tag_id', None, ForeignKey('cms_page_tags.id')),
                 Column('created_date', DateTime, nullable=False)
                 )
