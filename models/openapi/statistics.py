from sqlalchemy import Column, BigInteger, Integer, Table
from models import Base


openapilogdaystats = Table('cms_open_api_day_stats', Base.metadata,
                           Column('stat_date', Integer, primary_key=True),
                           Column('year', Integer),
                           Column('month', Integer),
                           Column('day', Integer),
                           Column('api_id', BigInteger, primary_key=True),
                           Column('access_count', Integer, default=0),
                           Column('success_count', Integer, default=0),
                           Column('fail_count', Integer, default=0)
                           )

openapiloghourstats = Table('cms_open_api_hour_stats', Base.metadata,
                            Column('stat_time', Integer, primary_key=True),
                            Column('year', Integer),
                            Column('month', Integer),
                            Column('day', Integer),
                            Column('hour', Integer),
                            Column('api_id', BigInteger, primary_key=True),
                            Column('access_count', Integer, default=0),
                            Column('success_count', Integer, default=0),
                            Column('fail_count', Integer, default=0)
                            )
