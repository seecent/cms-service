
from __future__ import absolute_import

import sys
from services.security import SecurityService


if __name__ == '__main__':
    security = SecurityService()
    print('encrypted password=' + security.encrypt(sys.argv[1]).strip())
