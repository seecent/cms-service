
from __future__ import absolute_import
import hug
import time

from api.errorcode import ErrorCode
from api.auth.user import check_sysadmin, check_admin, query_current_user
from config import db
from falcon import HTTPNotFound, HTTP_204, HTTPForbidden,\
    HTTPInternalServerError
from log import logger
from models.collection import collections
from models.saleschannel import saleschannels
from models.template import templates
from models.transformtask import transformtasks
from models.rawleads import rawleads, rawcontacts
from models.viableleads import viableleads, viablecontacts
from models import rows2data, row2dict

IGNORES = {'last_modifed'}


class CollectionMixin(object):
    def get_collection(self, id):
        row = db.get(collections, id)
        if row:
            return row2dict(row, collections)
        else:
            raise HTTPNotFound(title="no_collection")


@hug.object.urls('')
class Collections(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        cname = request.params.get('cname')
        t = collections.alias('c')
        joins = {'channel': {
                 'select': ['id', 'name'],
                 'table': saleschannels.alias('s')},
                 'template': {
                 'select': ['id', 'name'],
                 'table': templates.alias('t')}}
        query = db.filter_join(t, joins, request, ['-created_date'])
        u = query_current_user(request)
        if u and not check_sysadmin(u):
            if not check_admin(u):
                query = db.filter_by_user(t, query, u)
        if q:
            query = query.where(t.c.code.like('%' + q + '%'))
        if cname:
            query = query.where(t.c.name.like('%' + cname + '%'))
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)
        datas = rows2data(rows, collections, joins, IGNORES)
        if u:
            if check_sysadmin(u):
                for c in datas:
                    c['deletable'] = True
            else:
                username = u['username']
                for c in datas:
                    if c['username'] == username:
                        c['deletable'] = True
                    else:
                        c['deletable'] = False

        return datas

    @hug.get('/gen_code')
    def gen_collection_code():
        code = 'M' + time.strftime('%Y%m%d%H%M%S')
        return {'code': code}


@hug.object.http_methods('/{id}')
class CollectionInst(CollectionMixin, object):

    def get(self, id: int):
        c = self.get_collection(id)
        return c

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        cid = str(id)
        logger.info('<delete> collection: ' + cid)
        current_user = query_current_user(request)
        if current_user is None:
            return {'code': ErrorCode.UNAUTHORIZED.value,
                    'message': ErrorCode.UNAUTHORIZED.name}
        collection = self.get_collection(id)
        if collection:
            if not check_sysadmin(current_user):
                username = current_user['username']
                logger.info('<delete> user[' + username +
                            '] delete collection: ' + cid)
                if collection['username'] != username:
                    raise HTTPForbidden(title='not_allow_delete')
            try:
                tx = db.begin()
                db.execute(rawleads.delete().where(
                    rawleads.c.collection_id == id))
                db.execute(rawcontacts.delete().where(
                    rawcontacts.c.collection_id == id))
                db.execute(viableleads.delete().where(
                    viableleads.c.collection_id == id))
                db.execute(viablecontacts.delete().where(
                    viablecontacts.c.collection_id == id))
                db.execute(transformtasks.delete().where(
                    transformtasks.c.collection_id == id))
                db.execute(collections.delete().where(
                    collections.c.id == id))
                tx.commit()
                return {'code': 0, 'message': 'OK'}
            except Exception:
                logger.exception('<delete> collection[' + cid + '] error: ')
                tx.rollback()
                raise HTTPInternalServerError(title='delete_collection_error')


@hug.get('/enableForeignKeys')
def enable_foreign_keys(request, response):
    try:
        logger.info('<enable_foreign_keys> start...')
        print(db.check_db_type('sqlserver'))
        if db.check_db_type('sqlserver'):
            logger.info('<enable_foreign_keys> table: lms_raw_leads')
            db.execute("alter table lms_raw_leads CHECK constraint all")
            logger.info('<enable_foreign_keys> table: lms_raw_contacts')
            db.execute("alter table lms_raw_contacts CHECK constraint all")
            logger.info('<enable_foreign_keys> table: lms_viable_leads')
            db.execute("alter table lms_viable_leads CHECK constraint all")
            logger.info('<enable_foreign_keys> table: lms_viable_contacts')
            db.execute("alter table lms_viable_contacts CHECK constraint all")
        logger.info('<enable_foreign_keys> end!')
    except BaseException:
        logger.exception('<enable_foreign_keys> error: ')
    return {'code': 0, 'message': 'OK'}


@hug.get('/disableForeignKeys')
def disable_foreign_keys(request, response):
    try:
        logger.info('<disable_foreign_keys> start...')
        if db.check_db_type('sqlserver'):
            logger.info('<disable_foreign_keys> table: lms_raw_leads')
            db.execute("alter table lms_raw_leads NOCHECK constraint all")
            logger.info('<disable_foreign_keys> table: lms_raw_contacts')
            db.execute("alter table lms_raw_contacts NOCHECK constraint all")
            logger.info('<disable_foreign_keys> table: lms_viable_leads')
            db.execute("alter table lms_viable_leads NOCHECK constraint all")
            logger.info('<disable_foreign_keys> table: lms_viable_contacts')
            db.execute("alter table lms_viable_contacts NOCHECK constraint all")
        logger.info('<disable_foreign_keys> end!')
    except BaseException:
        logger.exception('<disable_foreign_keys> error: ')
    return {'code': 0, 'message': 'OK'}
