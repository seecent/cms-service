
from __future__ import absolute_import

from hug.exceptions import StoreKeyNotFound


class InMemoryStore:
    """
    Naive store class which can be used for the session middleware
    and unit tests. It is not thread-safe and no data will survive
    the lifecycle of the hug process. Regard this as a blueprint for
    more useful and probably more complex store implementations, for
    example stores which make use of databases like Redis, PostgreSQL
    or others.
    """

    def __init__(self):
        self._data = {}

    def get(self, key):
        """Get data for given store key.
        Raise hug.exceptions.StoreKeyNotFound if key does not exist."""
        try:
            data = self._data.get(key)
        except KeyError:
            raise StoreKeyNotFound(key)
        return data

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
