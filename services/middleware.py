
from __future__ import absolute_import

from api.exceptions import Unauthorized, ValidateTokenFailure
from config import store


class AuthMiddleware(object):
    __slots__ = ('auth_key', 'exclude_urls')

    def __init__(self, auth_key='apikey', exclude_urls=[]):
        self.auth_key = auth_key
        self.exclude_urls = exclude_urls

    def process_request(self, request, response):
        """validate api key"""
        for exclude in self.exclude_urls:
            if request.relative_uri == exclude:
                return True

        api_key = request.get_header(self.auth_key)
        if api_key:
            if store.exists(api_key):
                # user = store.get(api_key)
                return True
            else:
                raise ValidateTokenFailure('Validate token failure')
        else:
            raise Unauthorized('Invalid Authentication')

    def process_response(self, request, response, resource):
        pass
