import os
from api.ext.db import SQLAlchemy
from services.store import InMemoryStore

# cms db
db = SQLAlchemy()
# mdb
mdb = SQLAlchemy()
# cmapign db
campaign_db = SQLAlchemy()

# store
store = InMemoryStore()

true_values = {1, '1', 'True', 'true', 't', 'y', 'yes'}
_default = {
    "cms_home": "D:\\dev\\github\\seecent\\cms-service\\",  # cms-service 主目录
    "upload": "D:\\dev\\github\\seecent\\upload\\",         # 上传文件保存目录
    "media_root": "D:\\dev\\github\\seecent\\media",      # 素材文件保存目录
    "media_url": "http://localhost/media/",                 # 素材访问根URL
    "sqlalchemy.url": "postgresql://lms:lms_line@localhost/cmsdb",
    "secret_key": "sc62ko&m&3g*rx8r3j2pinf6ae1%#=m5#g&hho2mu_tea-#&us",
    "ams_api_sign_key": "TqhjhdGA639o6OAT",
    "xyt_api_sign_key": "TqhjhdGA639o6OAT",
    "weixin_api_url": "https://api.weixin.qq.com/cgi-bin/",
    "cms_debug": 1,
    "cms_logs_home": {
        "cms-service": "D:\\dev\\github\\seecent\\cms-service\\logs",
        "cms-crontab": "D:\\dev\\github\\seecent\\cms-crontab\\logs"
    },
    "collect_config": {
        "upload_path": "D:\\dev\\github\\seecent\\cms-service\\conf\\collect\\",
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
    "cms_home": get_env("cms_home"),
    "media_root": get_env("media_root"),
    "media_url": get_env("media_url"),
    "upload": get_env("upload"),
    "sqlalchemy.url": get_env("sqlalchemy.url"),
    "secret_key": get_env("secret_key"),
    "weixin_api_url": get_env("weixin_api_url"),
    "ams_api_sign_key": get_env("ams_api_sign_key"),
    "xyt_api_sign_key": get_env("xyt_api_sign_key"),
    "cms_debug": get_env("cms_debug") in true_values,
    "cms_logs_home": get_env("cms_logs_home"),
    "collect_config": get_env("collect_config"),
}

# 数据库连接信息配置
dataSources = {
    "cmsdb": {"username": "lms",                       # cmsdb数据库用户名
              "password": "6+TMOoz00SWZK71LgB4olQ==",  # cmsdb数据库用户密码（加密）
              "type": "postgresql",                    # cmsdb数据库类型
              "host": "localhost",                     # cmsdb数据库服务器域名或IP
              "port": 5432,                            # cmsdb数据库端口
              "database": "cmsdb",                     # cmsdb数据库名称
              "charset": "utf8"},                      # cmsdb数据库字符集
    "mdb": {"username": "lms",                         # mdb数据库用户名
            "password": "6+TMOoz00SWZK71LgB4olQ==",    # mdb数据库用户密码（加密）
            "type": "postgresql",                      # mdb数据库类型
            "host": "localhost",                       # mdb数据库服务器域名或IP
            "port": 5432,                              # mdb数据库端口
            "database": "cmsdb",                       # mdb数据库名称
            "charset": "utf8"},                        # mdb数据库字符集
    "campaigndb": {"username": "lms",                       # campaigndb数据库用户名
                   "password": "6+TMOoz00SWZK71LgB4olQ==",  # campaigndb数据库用户密码（加密）
                   "type": "postgresql",                    # campaigndb数据库类型
                   "host": "localhost",                     # campaigndb数据库服务器域名或IP
                   "port": 5432,                            # campaigndb数据库端口
                   "database": "cmsdb",                     # campaigndb数据库名称
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
    "app_id": "cms",                                   # cms 在 UAMS 中的应用ID
    "app_secret": "arwwfCEWvzhoHasd6Yt2aP",            # Token 密钥
    "api_url": "http://localhost:8080/cms-sso/api",    # 单点登录 API URL
    "auth_url": "http://localhost:8080/cms-sso/auth",  # 单点登录 认证 URL
    "sso_url": "http://localhost:8080/cms-sso/sso"     # 单点登录 登录 URL
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
