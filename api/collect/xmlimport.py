
from __future__ import absolute_import
import hug
import os
import uuid

from api.errorcode import ErrorCode
from api.exceptions import ErrorCodeError, NotFoundException
from api.auth.user import query_current_user
from config import db, setting
from datetime import datetime
from log import logger
from models import row2dict
from models.collection import collections, CollectionType, CollectionStatus
from models.operationlog import OperResult
from models.template import templates
from models.rawleads import rawleads
from models.transformtask import transformtasks
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import func
from services.collect.config import CollectConfigService
from services.collect.xml_import import CollectXMLImportService
from services.leadsmerge import LeadsMergeService
from services.oprationlog import OprationLogService


DF = "%Y-%m-%d %H:%M:%S"
# 导入配置服务
ccs = CollectConfigService()
# CSV文件导入服务
cxis = CollectXMLImportService()
# 数据库操作日志服务
log = OprationLogService()
# 销售线索去重服务
leadsMergeService = LeadsMergeService()


# 异步导入
def execute_import(cid, user, client_ip, total, config):
    logger.info('<execute_import> cid=' + str(cid) +
                ', username=' + user.get('username') +
                ', client_ip=' + client_ip +
                ', total=' + str(total))
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name,
              'source_count': total,
              'collect_count': 0,
              'success_count': 0,
              'fail_count': 0}
    try:
        task_id = None
        db.connect()
        row = db.get(collections.alias('c'), cid)
        if row:
            c = row2dict(row, collections)
            source_count = c['source_count']
            xml_file = c['save_file']
            validate = config.get('validate', True)
            merge = config.get('merge', False)
            r = cxis.import_from_xml_file(cid, xml_file, config,
                                          validate, merge)
            db.connect()
            query = select([func.count(rawleads.c.id)]).\
                where(rawleads.c.collection_id == cid)
            success_count = db.count(query)
            fail_count = source_count - success_count
            c.pop('created_date')
            c['collect_count'] = success_count
            c['fail_count'] = fail_count
            c['type'] = CollectionType.ImportXML
            if r['code'] == ErrorCode.OK.value:
                c['status'] = CollectionStatus.Success
            else:
                c['status'] = CollectionStatus.Fail
            c['error_code'] = r['code']
            c['error_msg'] = r['message']
            c['last_modifed'] = datetime.now()
            db.update(collections, c)

            detail = '上传文件：{0}, 保存文件：{1}。'
            detail = detail.format(c['source'], c['save_file'])
            # 导入成功，创建清洗和去重任务
            if r['code'] == ErrorCode.OK.value:
                task_id = save_transform_task(db, cid, c['template_id'])
                detail = '销售线索导入成功！任务编号：' + c['code'] + '，' + detail
                log.collect(user, client_ip, '手工导入销售线索XML文件', detail,
                            OperResult.Success, cid, db)
            else:
                detail = '销售线索导入失败，错误消息：' + r['message'] + '！' + detail
                log.collect(user, client_ip, '手工导入销售线索XML文件', detail,
                            OperResult.Fail, cid, db)

            result['code'] = r['code']
            result['message'] = r['message']
            result['collect_count'] = success_count
            result['success_count'] = success_count
            result['fail_count'] = fail_count

        db.close()

        if task_id is not None:
            leadsMergeService.merge(task_id)
    except Exception as e:
        logger.exception('<execute_import> error: ')
        result['code'] = ErrorCode.EXCEPTION.value
        result['message'] = str(e)
    return result


# 创建清洗和去重任务
def save_transform_task(db, cid, template_id):
    now = datetime.now()
    transformtask = {'collection_id': cid,
                     'template_id': template_id,
                     'created_date': now,
                     'last_modifed': now}
    tid = db.insert(transformtasks, transformtask)
    return tid


@hug.object.urls('')
class XMLImport(object):

    @hug.post('/upload')
    def upload_file(body):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            filename = body['file_name']
            file_text = body['file']
            uid = str(uuid.uuid1())
            save_filename = uid + '.xml'
            upload_filename = setting['upload'] + save_filename
            with open(upload_filename, 'wb') as f:
                f.write(file_text)
                f.close()

            result['uid'] = uid
            result['fileName'] = filename
        except FileNotFoundError as e:
            logger.exception('<upload_file> error: ')
            create_upload_dir()
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        except Exception as e:
            logger.exception('<upload_file> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    @hug.get('/upload_preview')
    def upload_preview(request, response):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            uid = request.params.get('uid')
            filename = request.params.get('file_name')
            offset = int(request.params.get('offset', 0))
            limit = int(request.params.get('limit', 15))
            total = int(request.params.get('total', 0))
            titles = []
            datas = []
            xml_file = uid + '.xml'
            if total == 0:
                total = cxis.count_xml_datas_total(xml_file, 'RawLeads')

            default_file = 'rawleads_xml_collect_config.xml'
            configFileName = "collect" + os.path.sep + default_file
            r = ccs.parse_config("RawLeads", configFileName)
            if r['code'] == ErrorCode.OK.value:
                config = r['config']
                r = cxis.get_xml_file_titles(xml_file, config)
                if r['code'] == ErrorCode.OK.value:
                    titles = r['titles']
                    r = cxis.preview_xml_file_datas(
                        xml_file, config, offset, limit)
                    if r['code'] == ErrorCode.OK.value:
                        datas = r.get('list')

            code = r['code']
            message = r['message']
            result = {'code': code, 'message': message,
                      'uid': uid, 'fileName': filename,
                      'total': total, 'titles': titles, 'list': datas}
        except Exception as e:
            logger.exception('<upload_preview> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    @hug.post('/importXMLFile')
    def importXMLFile(request, response, body):
        uid = body['uid']
        filename = body['file_name']
        code = body['code']
        name = body.pop("name", None)
        total = body['total']
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name,
                  'source_count': total,
                  'collect_count': total,
                  'success_count': total,
                  'fail_count': 0}
        client_ip = request.remote_addr
        logger.info('<importXMLFile> code=' + code + ', uid=' + uid +
                    ', client_ip=' + client_ip)
        try:
            u = query_current_user(request)
            if not u:
                raise ErrorCodeError(
                    ErrorCode.TOKEN_VALIDATION_FAILURE.name)

            tid = body['template_id']
            template = db.get(templates, int(tid))
            config = None
            if template:
                template = row2dict(template, templates)
                default_file = 'rawleads_xml_collect_config.xml'
                configFileName = template.get('template_file', default_file)
                configFileName = "collect" + os.path.sep + configFileName
                r = ccs.parse_config("RawLeads", configFileName)
                if r['code'] == ErrorCode.OK.value:
                    config = r['config']
                    if template.get('clean_rule_id') is None:
                        cxis.set_validate_type('Mark')
                    else:
                        config['validate'] = False
                    if template.get('merge_rule_id') is None:
                        cxis.set_merge_type('Mark')
                    else:
                        config['merge'] = False
            else:
                raise NotFoundException(ErrorCode.NOT_FOUND.name)

            query = select([collections.c.source_count,
                            collections.c.collect_count,
                            collections.c.fail_count])
            query = query.where(collections.c.code == code)
            row = db.fetch_one(query)
            if row:
                return {'code': ErrorCode.OK.value,
                        'message': ErrorCode.OK.name,
                        'source_count': row[0],
                        'collect_count': row[0],
                        'success_count': row[1],
                        'fail_count': row[2]}

            save_file = uid + '.xml'
            now = datetime.now()
            collection = {'code': code,
                          'name': name,
                          'source': filename,
                          'save_file': save_file,
                          'type': CollectionType.ImportXML,
                          'channel_id': template['channel_id'],
                          'template_id': int(tid),
                          'source_count': total,
                          'user_id': u.get('id'),
                          'username': u.get('username'),
                          'collect_count': 0,
                          'status': CollectionStatus.Collecting,
                          'created_date': now, 'last_modifed': now}
            cid = db.insert(collections, collection)
            result = execute_import(cid, u, client_ip, total, config)
            result['collection_id'] = cid
        except ErrorCodeError as e:
            logger.exception('<importXMLFile> error: ')
            result['code'] = e.code
            result['message'] = e.message
        except Exception as e:
            logger.exception('<importXMLFile> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result


def create_upload_dir():
    try:
        upload_dir = setting['upload']
        if not os.path.exists(upload_dir):
            logger.info('<create_upload_dir> upload_dir: ' + upload_dir)
            os.makedirs(upload_dir)
    except Exception as e:
        logger.exception('<create_upload_dir> error: ')
