import enum
from sqlalchemy import Column, BigInteger, Integer, String,\
    Enum, DateTime, Text, ForeignKey, Table
from models import Base


class MediaType(enum.Enum):
    IMAGE = 1
    VIDEO = 2
    VOICE = 3
    NEWS = 4


wxmedias = Table('wx_medias', Base.metadata,
                 Column('id', BigInteger, primary_key=True),
                 Column('media_id', String(128), nullable=False),
                 Column('file_id', BigInteger),
                 Column('name', String(128)),
                 Column('url', String(1024)),
                 Column('type', Enum(MediaType), default=MediaType.IMAGE),
                 Column('title', String(128)),
                 Column('thumb_media_id', BigInteger),
                 Column('show_cover_pic', Integer, default=0),
                 Column('author', String(64)),
                 Column('digest', String(256)),
                 Column('content', Text),
                 Column('content_source_url', String(1024)),
                 Column('account_id', None, ForeignKey(
                     'wx_accounts.id', ondelete="set null")),
                 Column('update_time', BigInteger),
                 Column('created_date', DateTime, nullable=False),
                 Column('last_modifed', DateTime)
                 )
