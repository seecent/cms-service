
from __future__ import absolute_import
import _thread
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
from services.collect.csv_import import CollectCSVImportService
from services.oprationlog import OprationLogService
from services.leadsmerge import LeadsMergeService

DF = "%Y-%m-%d %H:%M:%S"
# 异步导入限制，当导入数据量大于5万是采用异步导入
ASYN_THRESHOLD = 5000
# 导入配置服务
ccs = CollectConfigService()
# CSV文件导入服务
ccis = CollectCSVImportService()
# 数据库操作日志服务
log = OprationLogService()
# 销售线索去重服务
leadsMergeService = LeadsMergeService()


# 异步导入
async def async_execute_import(cid, user, client_ip, total, config):
    logger.info('<async_execute_import> cid=' + str(cid) +
                ', username=' + user.get('username') +
                ', client_ip=' + client_ip +
                ', total=' + str(total))
    execute_import(cid, user, client_ip, total, config)


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
        db.connect()
        task_id = None
        row = db.get(collections.alias('c'), cid)
        if row:
            c = row2dict(row, collections)
            source_count = c['source_count']
            csv_file = c['save_file']
            validate = config.get('validate', True)
            merge = config.get('merge', False)
            ccis.set_csv_separator(config.get('separator', ','))
            r = ccis.import_from_csv_file(cid, csv_file, config,
                                          validate, merge)
            db.connect()
            query = select([func.count(rawleads.c.id)]).\
                where(rawleads.c.collection_id == cid)
            success_count = db.count(query)
            fail_count = source_count - success_count
            c.pop('created_date')
            c['collect_count'] = success_count
            c['fail_count'] = fail_count
            c['type'] = CollectionType.ImportCSV
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
                log.collect(user, client_ip, '手工导入销售线索CSV文件', detail,
                            OperResult.Success, cid, db)
            else:
                detail = '销售线索导入失败，错误消息：' + r['message'] + '！' + detail
                log.collect(user, client_ip, '手工导入销售线索CSV文件', detail,
                            OperResult.Fail, cid, db)

            result['code'] = r['code']
            result['message'] = r['message']
            result['collect_count'] = success_count
            result['success_count'] = success_count
            result['fail_count'] = fail_count

        db.close()

        if task_id is not None:
            _thread.start_new_thread(merge_leads, (cid, task_id))
    except Exception as e:
        logger.exception('<execute_import> error: ')
        result['code'] = ErrorCode.EXCEPTION.value
        result['message'] = str(e)


def merge_leads(cid, task_id):
    leadsMergeService.merge(task_id)


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
class CsvImport(object):

    @hug.post('/upload')
    def upload_file(body):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            filename = body['file_name']
            file_text = body['file']
            uid = str(uuid.uuid1())
            save_filename = uid + '.csv'
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
            tid = request.params.get('tid')
            filename = request.params.get('file_name')
            offset = int(request.params.get('offset', 0))
            limit = int(request.params.get('limit', 15))
            total = int(request.params.get('total', 0))
            csv_file = uid + '.csv'
            if total == 0:
                total = ccis.count_csv_file_lines(csv_file)
            config = {}
            if tid is not None:
                # 解析导入配置模板
                row = db.get(templates, int(tid))
                if row:
                    template = row2dict(row, templates)
                    default_file = 'rawleads_csv_collect_config.xml'
                    configFileName = template.get('template_file',
                                                  default_file)
                    configFileName = "collect" + os.path.sep + configFileName
                    r = ccs.parse_config("RawLeads", configFileName)
                    if r['code'] == ErrorCode.OK.value:
                        config = r['config']
            # 设置CSV文件解析分隔符
            ccis.set_csv_separator(config.get("separator", ','))
            # 预览导入数据
            r = ccis.preview_csv_file_datas(csv_file, offset, limit, total)
            titles = []
            datas = []
            code = r['code']
            message = r['message']
            if code == ErrorCode.OK.value:
                titles = r['titles']
                datas = r['datas']

            result = {'code': code, 'message': message,
                      'uid': uid, 'fileName': filename,
                      'total': total, 'titles': titles, 'list': datas}
        except Exception as e:
            logger.exception('<upload_preview> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    @hug.post('/importCSVFile')
    def importCSVFile(request, response, body):
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
        logger.info('<importCSVFile> code=' + code + ', uid=' + uid +
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
                default_file = 'rawleads_csv_collect_config.xml'
                configFileName = template.get('template_file', default_file)
                configFileName = "collect" + os.path.sep + configFileName
                r = ccs.parse_config("RawLeads", configFileName)
                if r['code'] == ErrorCode.OK.value:
                    config = r['config']
                    if template.get('clean_rule_id') is None:
                        ccis.set_validate_type('Mark')
                    else:
                        config['validate'] = False
                    if template.get('merge_rule_id') is None:
                        ccis.set_merge_type('Mark')
                    else:
                        config['merge'] = False
            else:
                raise NotFoundException(ErrorCode.NOT_FOUND.name)

            query = select([collections.c.id,
                            collections.c.source_count,
                            collections.c.collect_count,
                            collections.c.fail_count])
            query = query.where(collections.c.code == code)
            row = db.fetch_one(query)
            if row:
                return {'code': ErrorCode.OK.value,
                        'message': ErrorCode.OK.name,
                        'collection_id': row[0],
                        'source_count': row[1],
                        'collect_count': row[1],
                        'success_count': row[2],
                        'fail_count': row[3]}

            save_file = uid + '.csv'
            now = datetime.now()
            channel_id = template['channel_id']
            collection = {'code': code,
                          'name': name,
                          'source': filename,
                          'save_file': save_file,
                          'type': CollectionType.ImportCSV,
                          'channel_id': channel_id,
                          'template_id': int(tid),
                          'source_count': total,
                          'user_id': u.get('id'),
                          'username': u.get('username'),
                          'collect_count': 0,
                          'status': CollectionStatus.Collecting,
                          'created_date': now, 'last_modifed': now}
            cid = db.insert(collections, collection)
            # 设置导入渠道
            ccis.set_channel_id(channel_id)
            if total > ASYN_THRESHOLD:
                logger.info('<importCSVFile> new thread import total=' +
                            str(total))
                _thread.start_new_thread(execute_import, (cid, u, client_ip,
                                                          total, config))
            else:
                logger.info('<importCSVFile> execute import total=' +
                            str(total))
                execute_import(cid, u, client_ip, total, config)
            result['collection_id'] = cid
        except ErrorCodeError as e:
            logger.exception('<importCSVFile> error: ')
            result['code'] = e.code
            result['message'] = e.message
        except Exception as e:
            logger.exception('<importCSVFile> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

    @hug.get('/show_result')
    def show_result(request, response):
        code = request.params.get('code')
        total = int(request.params.get('total'))
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name,
                  'source_count': total,
                  'collect_count': 0,
                  'success_count': 0,
                  'fail_count': 0}
        try:
            cid = None
            query = select([collections.c.id])
            query = query.where(collections.c.code == code)
            row = db.fetch_one(query)
            if row:
                cid = row[0]
            if cid is not None:
                query = select([func.count(rawleads.c.id)]).\
                    where(rawleads.c.collection_id == int(cid))
                success_count = db.count(query)
                fail_count = total - success_count
                result['collect_count'] = success_count
                result['success_count'] = success_count
                result['fail_count'] = fail_count
        except Exception as e:
            logger.exception('<show_result> error: ')
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
