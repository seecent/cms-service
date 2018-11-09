
from __future__ import absolute_import
import hug

from api.errorcode import ErrorCode
from config import db
from log import logger
from models.rawleads import rawleads, rawcontacts
from models.collection import collections
# from services.cache.progresscache import ProgressCache
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func


@hug.object.urls('')
class Progress(object):
    @hug.get('/importProgress')
    def importProgress(request, response):
        code = request.params.get('code')
        query = select([collections.c.id,
                        collections.c.source_count,
                        collections.c.status,
                        collections.c.error_code,
                        collections.c.error_msg,
                        ])
        query = query.where(collections.c.code == code)
        row = db.fetch_one(query)
        if row:
            cid = row[0]
            total = row[1]
            status = str(row[2])
            # error_code = row[3]
            message = row[4]
            current = total
            progress = 100
            if 'Collecting' not in status:
                logger.info("<importProgress> code: " + code +
                            ", status: " + status)
                return {'code': 0, 'message': message,
                        'total': total, 'current': total,
                        'progress': 100}
            elif total > 0:
                query = select([func.count(rawleads.c.id)]).\
                    where(rawleads.c.collection_id == cid)
                current = db.count(query)
                if current < 1:
                    query = select([func.count(rawcontacts.c.id)]).\
                        where(rawcontacts.c.collection_id == cid)
                    current = db.count(query)
                    progress = int((current * 50) / total)
                elif current == total:
                    progress = 100
                else:
                    progress = 50 + int((current * 50) / total)
                # progresscache = ProgressCache()
                # data = progresscache.get(cid)
                # logger.info("<importProgress> cid: " + str(cid) +
                #             ", data: " + str(data))
                # if data is not None:
                #     step = data['step']
                #     if step == 'end':
                #         current = 0
                #         progress = 0
                #     elif step == 'end':
                #         current = total
                #         progress = 100
                #     else:
                #         current = int(data['current'])
                #         if step == 'lms_raw_contacts':
                #             progress = int((current * 50) / total)
                #         elif step == 'lms_raw_leads':
                #             progress = 50 + int((current * 50) / total)
                #         else:
                #             progress = int((current * 50) / total)
                # else:
                #     current = 0
                #     progress = 0
            return {'code': 0, 'message': message,
                    'total': total, 'current': current,
                    'progress': progress}
        else:
            return {'code': ErrorCode.NOT_FOUND.value,
                    'message': ErrorCode.NOT_FOUND.name}
