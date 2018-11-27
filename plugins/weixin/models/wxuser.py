from sqlalchemy import Column, BigInteger, Integer, String,\
    DateTime, ForeignKey, Table
from models import Base


wxusers = Table('wx_users', Base.metadata,
                Column('id', BigInteger, primary_key=True, comment='ID'),
                Column('openid', String(64), nullable=False, comment='OpenID'),
                Column('unionid', String(64), comment='UnionID'),
                Column('nickname', String(64), comment='昵称'),
                Column('name', String(32), comment='名称'),
                Column('sex', Integer, default=0, comment='性别'),
                Column('language', String(32), comment='语言'),
                Column('city', String(64), comment='城市'),
                Column('province', String(64), comment='省份'),
                Column('country', String(64), comment='国家'),
                Column('headimgurl', String(512), comment='头像'),
                Column('remark', String(512), comment='备注'),
                Column('phone', String(32), comment='电话'),
                Column('mobile', String(32), comment='手机'),
                Column('email', String(256), comment='E-Mail'),
                Column('tags', String(256), comment='标签'),
                Column('subscribe', Integer, default=0, comment='关注状态'),
                Column('subscribe_time', BigInteger, comment='关注时间'),
                Column('subscribe_scene', String(32), comment='关注场景'),
                Column('qr_scene', Integer, comment='OpenID'),
                Column('qr_scene_str', String(256), comment='OpenID'),
                # Column('group_id', None, ForeignKey(
                #     'wx_user_groups.id', ondelete="set null")),
                Column('account_id', None, ForeignKey(
                    'wx_accounts.id', ondelete="set null"), comment='微信公众号'),
                Column('created_date', DateTime,
                       nullable=False, comment='创建时间'),
                Column('last_modifed', DateTime, comment='修改时间')
                )
