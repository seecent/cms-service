from sqlalchemy import Column, BigInteger, Integer, String, Table
from models import Base


images = Table('cms_images', Base.metadata,
               Column('id', BigInteger, primary_key=True),
               Column('img_height', Integer),
               Column('img_width', Integer),
               Column('author', String(256)),
               Column('default_alt_text', String(256))
               )
