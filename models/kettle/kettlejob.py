from sqlalchemy import Column, BigInteger, String,\
    DateTime, Table
from models import Base

kettlejobs = Table('lms_kettle_jobs', Base.metadata,
                   Column('id', BigInteger, primary_key=True),
                   Column('name', String(128)),
                   Column('job_module', String(128)),
                   Column('target_db', String(32)),
                   Column('target_table', String(32)),
                   Column('target_table_cnname', String(32)),
                   Column('source_db', String(32)),
                   Column('source_table', String(128)),
                   Column('source_table_cnname', String(32)),
                   Column('job_schedule', String(32)),
                   Column('update_mode', String(32)),
                   Column('description', String(512)),
                   Column('created_date', DateTime, nullable=False),
                   Column('last_modifed', DateTime)
                   )
