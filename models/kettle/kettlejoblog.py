from sqlalchemy import Column, BigInteger, Integer, String, DateTime, \
    Table, Text
from models import Base

kettlejoblogs = Table('lms_kettle_job_logs', Base.metadata,
                      Column('id_job', Integer, primary_key=True),
                      Column('channel_id', String(255)),
                      Column('jobname', String(255)),
                      Column('status', String(15)),
                      Column('lines_read', BigInteger),
                      Column('lines_written', BigInteger),
                      Column('lines_updated', BigInteger),
                      Column('lines_input', BigInteger),
                      Column('lines_output', BigInteger),
                      Column('lines_rejected', BigInteger),
                      Column('errors', BigInteger),
                      Column('startdate', DateTime),
                      Column('enddate', DateTime),
                      Column('logdate', DateTime),
                      Column('depdate', DateTime),
                      Column('replaydate', DateTime),
                      Column('log_field', Text),
                      Column('executing_server', String(255), default=None),
                      Column('executing_user', String(255), default=None),
                      Column('start_job_entry', String(255), default=None),
                      Column('client', String(255)),
                      Column('start_time', DateTime),
                      Column('cost_time', Integer)
                      )
