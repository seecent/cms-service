
from __future__ import absolute_import
import hug

from config import db, store
from models.auth.user import users, parse_token
from sqlalchemy.sql import select


@hug.get('/current-info')
def current_info(request):
    def user_info(username='admin', name='管理员', userid=1):
        if name is None or name == '':
            name = username
        return dict(username=username, name=name, avatar='',
                    userid=userid, notifyCount=0)
    token = request.get_header('apikey')
    if token:
        try:
            u = store.get(token)
            if u is not None:
                return user_info(u['username'], u['fullname'], u['user_id'])
            else:
                u = {}
                username = parse_token(token)
                query = select([users.c.id,
                                users.c.username,
                                users.c.enname,
                                users.c.fullname,
                                users.c.usertype,
                                users.c.department])
                query = query.where(users.c.username == username)
                row = db.fetch_one(query)
                if row:
                    user_id = row[0]
                    username = row[1]
                    fullname = row[3]
                    u['user_id'] = user_id
                    u['username'] = username
                    u['fullname'] = fullname
                    u['usertype'] = row[4]
                    u['department'] = row[5]
                    return user_info(username, fullname, user_id)
                else:
                    return user_info()
        except Exception as e:
            return user_info()
    else:
        return user_info()
