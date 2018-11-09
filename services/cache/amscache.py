
from __future__ import absolute_import

from config import mdb
from log import logger
from models.mdb.ams.amscso import amscsos
from models.mdb.ams.amssso import amsssos

from sqlalchemy.sql import select


class AmsCache:

    def __init__(self):
        self._ssodata = {}
        self._csodata = {}

    def init_cache(self):
        """
        初始化组织机构缓存
        """
        logger.info('<init_cache> start....')
        mdb.connect()
        c = amscsos.alias('t')
        query = select([c.c.comCode, c.c.comName])
        rows = mdb.execute(query).fetchall()
        for r in rows:
            self._csodata[r[0]] = r[1]

        s = amsssos.alias('t')
        query = select([s.c.ssoCode, s.c.ssoName])
        rows = mdb.execute(query).fetchall()
        for r in rows:
            self._ssodata[r[0]] = r[1]
        mdb.close()
        logger.info('<init_cache> end!')

    def getCSOName(self, code, default=None):
        if code is not None:
            return self._csodata.get(code, default)
        else:
            return default

    def getSSOName(self, code, default=None):
        if code is not None:
            return self._ssodata.get(code, default)
        else:
            return default
