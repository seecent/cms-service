
from __future__ import absolute_import

# import redis
from log import logger


class ProgressCache:

    def __init__(self):
        try:
            self._data = {}
            # self.pool = redis.ConnectionPool(host='192.168.0.115', port=6379,
            #                                  password='admin',
            #                                  decode_responses=True)
            # self.redis = redis.Redis(connection_pool=self.pool)
        except Exception as e:
            logger.exception('<__init__> error: ')

    def init_cache(self):
        logger.info('<init_cache> start....')
        logger.info('<init_cache> end!')

    def get(self, key, default=None):
        try:
            if key is not None:
                return self._data.get(key, default)
                # return self.redis.hgetall(key)
            else:
                return default
        except Exception as e:
            logger.exception('<get> error: ')
        return default

    def exists(self, key):
        try:
            return key in self._data
        except Exception as e:
            logger.exception('<exists> error: ')
        return False

    def set(self, key, data):
        try:
            self._data[key] = data
            # self.redis.hmset(key, data)
        except Exception as e:
            logger.exception('<set> error: ')

    def delete(self, key):
        try:
            if key in self._data:
                del self._data[key]
            # self.redis.hdel(key)
        except Exception as e:
            logger.exception('<delete> error: ')

    def start(self, key, total):
        try:
            # self._data[key] = {'step': 'start',
            #                    'current': 0,
            #                    'total': total}
            # data = {'step': 'start',
            #         'current': 0,
            #         'total': total}
            # self.redis.hmset(key, data)
            pass
        except Exception as e:
            logger.exception('<start> error: ')

    def update(self, key, step, current):
        try:
            # data = self._data[key]
            # data['step'] = step
            # data['current'] = current
            # self.redis.hset(key, "step", step)
            # self.redis.hset(key, "current", current)
            pass
        except Exception as e:
            logger.exception('<update> error: ')

    def end(self, key, total):
        try:
            # self._data[key] = {'step': 'end',
            #                    'current': total,
            #                    'total': total}
            # data = {'step': 'end',
            #         'current': total,
            #         'total': total}
            # self.redis.hmset(key, data)
            pass
        except Exception as e:
            logger.exception('<end> error: ')
