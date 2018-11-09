from sqlalchemy import Column, BigInteger, String, DateTime, Table, ForeignKey
from models import Base


templates = Table('lms_import_templates', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100)),
    Column('template_file', String(100)),
    Column('channel_id', None, ForeignKey('lms_sales_channels.id')),
    Column('clean_rule_id', None, ForeignKey('lms_transform_rules.id')),
    Column('merge_rule_id', None, ForeignKey('lms_transform_rules.id')),
    Column('description', String(1024)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
