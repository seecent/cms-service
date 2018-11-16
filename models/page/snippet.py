import enum
from sqlalchemy import Column, BigInteger, String, Table,\
    Enum, DateTime, Text
from models import Base


class SnippetType(enum.Enum):
    Title = 1
    Content = 2
    Image = 3
    Images = 4
    Separate = 5
    ChapterNo = 6
    StartTag = 7
    EndTag = 8


snippets = Table('cms_page_snippets', Base.metadata,
                 Column('id', BigInteger, primary_key=True),
                 Column('name', String(50), nullable=False),
                 Column('color', String(50)),
                 Column('description', String(256)),
                 Column('content', Text),
                 Column('type', Enum(SnippetType), default=SnippetType.Title),
                 Column('created_date', DateTime, nullable=False),
                 Column('last_modifed', DateTime)
                 )
