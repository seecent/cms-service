
from __future__ import absolute_import
from api.errorcode import ErrorCode


class ErrorCodeError(Exception):
    def __init__(self, error_code, message: None):
        Exception.__init__(self)
        self.code = error_code.value
        self.name = error_code.name
        if message is not None:
            self.message = message
        else:
            self.message = error_code.name


class Unauthorized(ErrorCodeError):
    def __init__(self, message):
        Exception.__init__(self)
        self.code = ErrorCode.UNAUTHORIZED.value
        self.name = ErrorCode.UNAUTHORIZED.name
        self.message = message


class ValidateTokenFailure(ErrorCodeError):
    def __init__(self, message):
        Exception.__init__(self)
        self.code = ErrorCode.TOKEN_VALIDATION_FAILURE.value
        self.name = ErrorCode.TOKEN_VALIDATION_FAILURE.name
        self.message = message


class NotFoundException(ErrorCodeError):
    def __init__(self, message):
        Exception.__init__(self)
        self.code = ErrorCode.NOT_FOUND.value
        self.name = ErrorCode.NOT_FOUND.name
        self.message = message
