# -*- coding: utf-8 -*-
# @Time    : 2018/8/8 10:46
# @Author  : zjm
# @Version : 1.0.1

from __future__ import absolute_import
import hug
import os

from api.auth.user import check_current_user
from config import db, setting
from datetime import datetime
from falcon import HTTPNotFound, HTTP_204, HTTP_201,\
    HTTPInternalServerError
from log import logger
from models.template import templates
from models.transformrule import transformrules
from models.saleschannel import saleschannels
from models import bind_dict, change_dict, row2dict, rows2data
from services.oprationlog import OprationLogService

IGNORES = {'last_modifed'}
log = OprationLogService()


class TemplateMixin(object):
    def get_template(self, id):
        row = db.get(templates, id)
        if row:
            return row2dict(row, templates)
        else:
            raise HTTPNotFound(title="no_template")


@hug.object.urls('')
class Templates(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        t = templates.alias('t')
        joins = {'channel': {
                 'select': ['name'],
                 'table': saleschannels.alias('ch')},
                 'clean_rule': {
                 'select': ['name'],
                 'table': transformrules.alias('c')},
                 'merge_rule': {
                 'select': ['name'],
                 'table': transformrules.alias('m')}
                 }
        query = db.filter_join(t, joins, request)
        if q:
            query = query.where(t.c.name.like('%' + q + '%'))
        query = db.filter_by_date(t.c.created_date, query, request)
        rows = db.paginate_data(query, request, response)
        return rows2data(rows, templates, joins, IGNORES)

    @hug.object.post(status=HTTP_201)
    def post(self, request, response, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            template = bind_dict(templates, body)
            current_user = result['user']
            logger.info('<post> user[' + current_user['username'] +
                        '] create template: ' + str(template))
            d = db.save(templates, template)
            log.create(current_user, request, d.get('id'),
                       'templates', template, db)
            return d
        except Exception:
            logger.exception('<post> error: ')
            raise HTTPInternalServerError(title='create_template_error')


@hug.object.http_methods('/{id}')
class TemplateInst(TemplateMixin, object):
    def get(self, id: int):
        t = self.get_template(id)
        return t

    def patch(self, request, response, id: int, body):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            t = self.get_template(id)
            if t:
                data = change_dict(templates, t, body)
                current_user = result['user']
                logger.info('<patch> user[' + current_user['username'] +
                            '] update template: ' + str(data))
                db.update(templates, data)
                log.update(current_user, request, id,
                           'templates', t, data, db)
            return t
        except Exception:
            logger.exception('<patch> template[' + str(id) + '] error: ')
            raise HTTPInternalServerError(title='update_template_error')

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response, id: int):
        result = check_current_user(request)
        if result['code'] != 0:
            return result
        try:
            current_user = result['user']
            logger.info('<delete> user[' + current_user['username'] +
                        '] delete template[' + str(id) + ']')
            db.delete(templates, id)
            log.delete(current_user, request, id, 'templates', db)
        except Exception:
            logger.exception('<delete> template[' + str(id) + '] error: ')
            raise HTTPInternalServerError(title='delete_template_error')


@hug.get('/getTemplateFiles')
def template_files(request, response):
    file_names = []
    try:
        conf_dir = setting['lms_home'] + os.path.sep +\
            "conf" + os.path.sep + "collect"
        for root, dirs, files in os.walk(conf_dir):
            for file_name in files:
                file_names.append(file_name)
    except Exception as e:
        logger.exception('<template_files> error=')

    return file_names


def init_templates():
    now = datetime.now()
    template1 = {'channel_id': 1,
                 'name': '银保CSV导入模板',
                 'template_file': 'rawleads_csv_collect_config.xml',
                 'created_date': now,
                 'last_modifed': now}
    template2 = {'channel_id': 2,
                 'name': '信易通XML导入模板',
                 'template_file': 'rawleads_xml_collect_config.xml',
                 'created_date': now,
                 'last_modifed': now}
    db.connect()
    count = db.count(templates)
    if count == 0:
        db.insert(templates, template1)
        db.insert(templates, template2)
    db.close()
