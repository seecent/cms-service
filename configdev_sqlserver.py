import os
from api.ext.db import SQLAlchemy
from services.store import InMemoryStore

# lms db
db = SQLAlchemy()
# mdb
mdb = SQLAlchemy()
# cmapign db
campaign_db = SQLAlchemy()

# store
store = InMemoryStore()

true_values = {1, '1', 'True', 'true', 't', 'y', 'yes'}
_default = {
    "lms_home": "D:\\dev\\git\\lms\\lms-service\\",  # lms-service 主目录
    "upload": "D:\\dev\\git\\lms\\upload\\",         # 上传文件保存目录
    "sqlalchemy.url": "mssql+pymssql://lms:lms_line@192.168.0.114:1433/lmsdb?charset=utf8",
    "secret_key": "sc62ko&m&3g*rx8r3j2pinf6ae1%#=m5#g&hho2mu_tea-#&us",
    "ams_api_sign_key": "TqhjhdGA639o6OAT",
    "xyt_api_sign_key": "TqhjhdGA639o6OAT",
    "lms_debug": 1,
    "lms_logs_home": {  # 注意:最后没有路径分割符\\
        "lms-service": "D:\\dev\\git\\lms\\lms-service\\logs",
        "lms-crontab": "D:\\dev\\git\\lms\\lms-crontab\\logs"
    },
    "collect_config": {
        "upload_path": "D:\\dev\\git\\lms\\lms-service\\conf\\collect\\",
        "filter_list": [  # 禁止修改导入配置文件清单
            "rawleads_csv_collect_config.xml",
            "rawleads_db_collect_config.xml",
            "rawleads_xml_collect_config.xml"
        ]
    }
}


def get_env(key):
    env_key = key.replace('.', '_')
    return os.environ.get(env_key, _default[key])


setting = {
    "lms_home": get_env("lms_home"),
    "upload": get_env("upload"),
    "sqlalchemy.url": get_env("sqlalchemy.url"),
    "secret_key": get_env("secret_key"),
    "ams_api_sign_key": get_env("ams_api_sign_key"),
    "xyt_api_sign_key": get_env("xyt_api_sign_key"),
    "lms_debug": get_env("lms_debug") in true_values,
    "lms_logs_home": get_env("lms_logs_home"),
    "collect_config": get_env("collect_config"),
}

# 数据库连接信息配置
dataSources = {
    "lmsdb": {"username": "lms",                       # lmsdb数据库用户名
              "password": "6+TMOoz00SWZK71LgB4olQ==",  # lmsdb数据库用户密码（加密）
              "type": "mssql+pymssql",                    # lmsdb数据库类型
              "host": "192.168.0.114",                     # lmsdb数据库服务器域名或IP
              "port": 1433,                            # lmsdb数据库端口
              "database": "lmsdb",                     # lmsdb数据库名称
              "charset": "utf8"},                      # lmsdb数据库字符集
    "mdb": {"username": "lms",                         # mdb数据库用户名
            "password": "6+TMOoz00SWZK71LgB4olQ==",    # mdb数据库用户密码（加密）
            "type": "mssql+pymssql",                      # mdb数据库类型
            "host": "192.168.0.114",                       # mdb数据库服务器域名或IP
            "port": 1433,                              # mdb数据库端口
            "database": "mdb",                       # mdb数据库名称
            "charset": "utf8"},                        # mdb数据库字符集
    "campaigndb": {"username": "lms",                       # campaigndb数据库用户名
                   "password": "6+TMOoz00SWZK71LgB4olQ==",  # campaigndb数据库用户密码（加密）
                   "type": "mssql+pymssql",                    # campaigndb数据库类型
                   "host": "192.168.0.114",                     # campaigndb数据库服务器域名或IP
                   "port": 1433,                            # campaigndb数据库端口
                   "database": "campaign",                     # campaigndb数据库名称
                   "charset": "utf8"},                      # campaigndb数据库字符集
}

# Unica Campaign配置信息
unica_campaign = {
    "name": "Campaign",                       # Campaign 名称
    "host": "localhost",                      # Campaign 服务器域名
    "ip": "127.0.01",                         # Campaign 服务器IP地址
    "protocol": "http",                       # Campaign 部署协议
    "port": 9080,                             # Campaign 端口
    "username": "test",                       # Campaign 登录用户名
    "password": "jfiKikhFRwGRhfYeRD6yZA=="    # Campaign 用户密码（加密）
}

# 单点登录权限集成配置
sso_settings = {
    "app_id": "LMS",                                   # LMS 在 UAMS 中的应用ID
    "app_secret": "arwwfCEWvzhoHasd6Yt2aP",            # Token 密钥
    "api_url": "http://localhost:8080/lms-sso/api",    # 单点登录 API URL
    "auth_url": "http://localhost:8080/lms-sso/auth",  # 单点登录 认证 URL
    "sso_url": "http://localhost:8080/lms-sso/sso"     # 单点登录 登录 URL
}


# 菜单配置
menus = [{
    'name': 'Menu.dashboard',
    'icon': 'dashboard',
    'path': 'dashboard',
    'children': [{
        'name': 'Menu.workplace',
        'path': 'workplace',
        'permissions': [1]
    }, {
        'name': 'Menu.dataCollect',
        'path': 'dataCollect',
        'permissions': [1]
    }, {
        'name': 'Menu.dataIntegration',
        'path': 'dataIntegration',
        'permissions': [1]
    }, {
        'name': 'Menu.activityAPI',
        'path': 'activityAPI',
        'permissions': [1]
    }],
}, {
    'name': 'Menu.collection',
    'icon': 'sync',
    'path': 'collection',
    'children': [{
        'name': 'Menu.collection.list',
        'path': 'list',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.monitorList',
        'path': 'monitorList',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.monitorPanel',
        'path': 'monitorPanel',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.importTemplate',
        'path': 'importTemplate',
        'permissions': [1, 2, 3, 4]
    }],
}, {
    'name': 'Menu.recognition',
    'icon': 'filter',
    'path': 'recognition',
    'children': [{
        'name': 'Menu.recognition.hot',
        'path': 'hot',
        'permissions': [1]
    }, {
        'name': 'Menu.recognition.common',
        'path': 'common',
        'permissions': [1]
    }, {
        'name': 'Menu.recognition.key',
        'path': 'key',
        'permissions': [1]
    }, {
        'name': 'Menu.recognition.campaign',
        'path': 'campaign',
        'permissions': [1]
    }],
}, {
    'name': 'Menu.distribution',
    'icon': 'share-alt',
    'path': 'distribution',
    'children': [{
        'name': 'Menu.distribution.amssales',
        'path': 'amssales',
        'permissions': [1]
    }],
}, {
    'name': 'Menu.tracking',
    'icon': 'paper-clip',
    'path': 'tracking',
    'children': [{
        'name': 'Menu.tracking.activityVolume',
        'path': 'http://www.citic-prudential.com.cn',
        'target': '_blank',
        'permissions': [1]
    }, {
        'name': 'Menu.tracking.leadsConversion',
        'path': 'http://www.citic-prudential.com.cn/',
        'target': '_blank',
        'permissions': [1]
    }],
}, {
    'name': 'Menu.system',
    'icon': 'setting',
    'path': 'system',
    'children': [{
        'name': 'Menu.user',
        'path': 'users',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.role',
        'path': 'role',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.menus',
        'path': 'menus',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.organization',
        'path': 'organizations',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.department',
        'path': 'department',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.salesChannel',
        'path': 'salesChannel',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.constant',
        'path': 'constant',
        'permissions': [1, 2, 3, 4]
    }, {
        'name': 'Menu.operationLog',
        'path': 'operationLog',
        'permissions': [1]
    }, {
        'name': 'Menu.kettleJobLog',
        'path': 'kettleJobLogs',
        'permissions': [1]
    }, {
        'name': 'Menu.campaignServer',
        'path': 'campaignServer',
        'permissions': [1]
    }, {
        'name': 'Menu.uaUser',
        'path': 'uaUser',
        'permissions': [1]
    }],
}]
