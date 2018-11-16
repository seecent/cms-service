import enum
from sqlalchemy import Column, BigInteger, Integer, String, Table,\
    Enum, DateTime, ForeignKey
from models import Base


class FileType(enum.Enum):
    IMAGE = 1
    VIDEO = 2
    VOICE = 3
    TXT = 4
    CSV = 4
    EXCEL = 6
    WORD = 7
    PPT = 8
    PDF = 9


files = Table('cms_files', Base.metadata,
              Column('id', BigInteger, primary_key=True),
              Column('uuid', String(256), nullable=False),
              Column('name', String(256), nullable=False),
              Column('original_filename', String(256)),
              Column('description', String(256)),
              Column('file_size', BigInteger),
              Column('file_path', String(512)),
              Column('type', Enum(FileType), default=FileType.IMAGE),
              Column('folder_id', None, ForeignKey(
                  'cms_folders.id', ondelete="set null")),
              Column('owner_id', None, ForeignKey(
                  'cms_users.id', ondelete="set null")),
              Column('is_public', Integer, default=0),
              Column('created_date', DateTime, nullable=False),
              Column('last_modifed', DateTime)
              )
