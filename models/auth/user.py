from __future__ import absolute_import

from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
import enum
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import Column, BigInteger, Integer, Boolean, String,\
    DateTime, Enum, Table, ForeignKey
from models import Base, ID_LEN
from config import setting


cms_secret = setting['secret_key']


def _kdf_derive(salt, msg):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                      iterations=100000, backend=default_backend()
                      ).derive(msg.encode())


def gen_password(password_txt):
    salt = Fernet.generate_key()
    key = urlsafe_b64encode(_kdf_derive(salt, cms_secret))
    f = Fernet(key)
    return (salt.decode(), f.encrypt(password_txt.encode()).decode())


def get_password(salt, password_encrypt):
    key = urlsafe_b64encode(_kdf_derive(salt.encode(), cms_secret))
    f = Fernet(key)
    return f.decrypt(password_encrypt.encode()).decode()


def generate_token(info):
    key = urlsafe_b64encode(_kdf_derive(b'', cms_secret))
    f = Fernet(key)
    return f.encrypt(info.encode()).decode()


def parse_token(token):
    key = urlsafe_b64encode(_kdf_derive(b'', cms_secret))
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()


class UserType(enum.Enum):
    SysAdmin = 1
    Admin = 2
    Sales = 3


class UserStatus(enum.IntEnum):
    Active = 1
    Locked = 2
    Removed = 3


users = Table('cms_users', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('version', Integer, default=1),
    Column('username', String(ID_LEN), nullable=False, unique=True),
    Column('password', String(128)),
    Column('firstname', String(64)),
    Column('lastname', String(128)),
    Column('enname', String(128)),
    Column('fullname', String(128)),
    Column('mobile', String(32), nullable=False, unique=True),
    Column('phone', String(32)),
    Column('email', String(256)),
    Column('hashed_password', String(128), nullable=False),
    Column('salt', String(64)),
    Column('employee_no', String(32)),
    Column('status', Enum(UserStatus), default=UserStatus.Active),
    Column('usertype', Enum(UserType), default=UserType.Sales),
    Column('organization_id', None,
           ForeignKey('cms_organizations.id', ondelete="set null")),
    Column('department', String(128)),
    Column('account_expired', Boolean, default=False),
    Column('account_locked', Boolean, default=False),
    Column('password_expired', Boolean, default=False),
    Column('password_errors', Integer, default=0),
    Column('enabled', Boolean, default=True),
    Column('date_created', DateTime, nullable=False),
    Column('last_updated', DateTime)
)


preferences = Table('cms_user_preferences', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('language', String(30)),
    Column('timezone', String(64)),
    Column('memo', String(512)),
    Column('user_id', None, ForeignKey('cms_users.id')),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)


memberships = Table('cms_user_auth_memberships', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('provider', String(30)),
    Column('provider_userid', String(128)),
    Column('user_id', None, ForeignKey('cms_users.id')),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)


class TokenAction(enum.Enum):
    API = 1
    FEEDS = 2
    RECOVERY = 3
    AUTOLOGIN = 4


tokens = Table('cms_user_tokens', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    # UniqueConstraint('user_id', 'action', name='uni_token_action'), ),
    Column('action', Enum(TokenAction), default=TokenAction.API),
    Column('value', String(200)),
    Column('user_id', None, ForeignKey('cms_users.id')),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)


departments = Table('cms_departments', Base.metadata,
    Column('id', BigInteger, primary_key=True),
    Column('code', String(20), nullable=False),
    Column('name', String(64), nullable=False),
    Column('description', String(512)),
    Column('created_date', DateTime, nullable=False),
    Column('last_modifed', DateTime)
)
