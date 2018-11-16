from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    DateTime, Text, ForeignKey
from models import Base


historypages = Table('cms_history_pages', Base.metadata,
                     Column('id', BigInteger, primary_key=True),
                     Column('version', String(50), nullable=False),
                     Column('name', String(50), nullable=False),
                     Column('title', String(128)),
                     Column('digest', String(256)),
                     Column('author', String(256)),
                     Column('content', Text),
                     Column('image_url', String(512)),
                     Column('show_cover_pic', Integer, default=0),
                     Column('file_size', BigInteger),
                     Column('file_path', String(512)),
                     Column('page_id', None, ForeignKey(
                         'cms_pages.id', ondelete="set null")),
                     Column('category_id', None, ForeignKey(
                         'cms_categories.id', ondelete="set null")),
                     Column('owner_id', None, ForeignKey(
                         'cms_users.id', ondelete="set null")),
                     Column('is_public', Integer, default=0),
                     Column('pubdate', DateTime),
                     Column('created_date', DateTime, nullable=False),
                     Column('last_modifed', DateTime)
                     )
