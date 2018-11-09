
from __future__ import absolute_import

from config import db
from log import logger
from models.location import locations

from sqlalchemy.sql import select


class LocationCache:

    def __init__(self):
        self._data = {}

    def init_cache(self):
        """
        初始化组织机构缓存
        """
        logger.info('<init_cache> start....')
        db.connect()
        t = locations.alias('t')
        query = select([t.c.id, t.c.code, t.c.name])
        rows = db.execute(query).fetchall()
        for r in rows:
            self._data[r[1]] = r[2]
        db.close()
        logger.info('<init_cache> end!')

    def get(self, key, default=None):
        if key is not None:
            return self._data.get(key, default)
        else:
            return default

    def exists(self, key):
        """Return whether key exists or not."""
        return key in self._data

    def set(self, key, data):
        """Set data object for given store key."""
        self._data[key] = data

    def delete(self, key):
        """Delete data for given store key."""
        if key in self._data:
            del self._data[key]
