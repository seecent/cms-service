from sqlalchemy import Column, BigInteger, Integer, String,\
    DateTime, ForeignKey, Table
from models import Base


wxusers = Table('wx_users', Base.metadata,
                Column('id', BigInteger, primary_key=True),
                Column('openid', String(64), nullable=False),
                Column('unionid', String(64)),
                Column('nickname', String(64)),
                Column('name', String(32)),
                Column('sex', Integer, default=0),
                Column('language', String(32)),
                Column('city', String(64)),
                Column('province', String(64)),
                Column('country', String(64)),
                Column('headimgurl', String(512)),
                Column('remark', String(512)),
                Column('phone', String(32)),
                Column('mobile', String(32)),
                Column('email', String(256)),
                Column('tags', String(256)),
                Column('subscribe', Integer, default=0),
                Column('subscribe_time', BigInteger),
                Column('subscribe_scene', String(32)),
                Column('qr_scene', Integer),
                Column('qr_scene_str', String(256)),
                # Column('group_id', None, ForeignKey(
                #     'wx_user_groups.id', ondelete="set null")),
                Column('account_id', None, ForeignKey(
                    'wx_accounts.id', ondelete="set null")),
                Column('created_date', DateTime, nullable=False),
                Column('last_modifed', DateTime)
                )
