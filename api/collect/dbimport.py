
from __future__ import absolute_import
import hug
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
from threading import Thread

# 异步导入限制，当导入数据量大于5万是采用异步导入
ASYN_THRESHOLD = 50000
# 导入配置服务
ccs = CollectConfigService()
# CSV文件导入服务
ccis = CollectCSVImportService()
# 数据库操作日志服务
log = OprationLogService()


# 异步导入
def execute_import(cid, user_id, total, config):
    logger.info('<execute_import> cid=' + str(cid) +
                ', user_id=' + str(user_id) +
                ', total=' + str(total))
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name,
              'source_count': total,
              'collect_count': 0,
              'success_count': 0,
              'fail_count': 0}
    try:
        db.connect()
        row = db.get(collections.alias('c'), cid)
        if row:
            c = row2dict(row, collections)
            source_count = c['source_count']
            csv_file = c['save_file']
            r = ccis.import_from_csv_file(cid, csv_file, config, True, False)
            query = select([func.count(rawleads.c.id)]).\
                where(rawleads.c.collection_id == cid)
            success_count = db.count(query)
            fail_count = source_count - success_count
            c['collect_count'] = success_count
            c['fail_count'] = fail_count
            c['last_modifed'] = datetime.now()
            if result['code'] == ErrorCode.OK.code:
                c['status'] = CollectionStatus.Success
            else:
                c['status'] = CollectionStatus.Fail
            c['error_code'] = r['code']
            c['error_msg'] = r['message']
            db.update(collections, c)

            detail = '上传文件：{0}, 保存文件：{1}。'
            detail = detail.format(c['source'], c['save_file'])
            # 导入成功，创建清洗和去重任务
            if r['code'] == ErrorCode.OK.value:
                save_transform_task(db, cid, c['template_id'])
                detail = '销售线索导入成功！' + detail
                log.collect(user_id, '', '销售线索手工CSV文件导入', detail,
                            OperResult.Success, cid, db)
            else:
                detail = '销售线索导入失败，错误消息：' + r['message'] + '！' + detail
                log.collect(user_id, '', '销售线索手工CSV文件导入', detail,
                            OperResult.Fail, cid, db)

            result['code'] = r['code']
            result['message'] = r['message']
            result['collect_count'] = success_count
            result['success_count'] = r['success_count']
            result['fail_count'] = r['fail_count']
        db.close()
    except Exception as e:
        logger.exception('<execute_import> error=')
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
    db.insert(transformtasks, transformtask)


@hug.object.urls('')
class DBImport(object):

    @hug.post('/upload')
    def upload_file(body):
        filename = body['file_name']
        file_text = body['file']
        uid = str(uuid.uuid1())
        save_filename = uid + '.csv'
        upload_filename = setting['upload'] + save_filename
        with open(upload_filename, 'wb') as f:
            f.write(file_text)
            f.close()

        return {'uid': uid, 'fileName': filename}

    @hug.get('/upload_preview')
    def upload_preview(request, response):
        uid = request.params.get('uid')
        filename = request.params.get('file_name')
        offset = int(request.params.get('offset', 0))
        limit = int(request.params.get('limit', 15))
        total = int(request.params.get('total', 0))
        csv_file = uid + '.csv'
        if total == 0:
            total = ccis.count_csv_file_lines(csv_file)
        r = ccis.preview_csv_file_datas(csv_file, offset, limit, total)
        titles = []
        datas = []
        code = r['code']
        message = r['message']
        if code == ErrorCode.OK.value:
            titles = r['titles']
            datas = r['datas']

        return {'code': code, 'message': message,
                'uid': uid, 'fileName': filename,
                'total': total, 'titles': titles, 'list': datas}

    @hug.post('/importCsvFile')
    def importCsvFile(request, response, body):
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
        try:
            u = query_current_user(request)
            if not u:
                raise ErrorCodeError(
                    ErrorCode.TOKEN_VALIDATION_FAILURE.name)

            tid = body['template_id']
            template = db.get(templates, int(tid))
            config = None
            if template:
                configFileName = "rawleads_csv_collect_config.xml"
                r = ccs.parse_config("RawLeads", configFileName)
                if r['code'] == ErrorCode.OK.value:
                    config = r['config']
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

            save_file = uid + '.csv'
            user_id = u['id']
            now = datetime.now()
            collection = {'code': code,
                          'name': name,
                          'source': filename,
                          'save_file': save_file,
                          'type': CollectionType.ImportCSV,
                          'channel_id': template['channel_id'],
                          'template_id': int(tid),
                          'source_count': total,
                          'user_id': user_id,
                          'collect_count': 0,
                          'created_date': now, 'last_modifed': now}
            cid = db.insert(collections, collection)
            if total > ASYN_THRESHOLD:
                thread = Thread(target=execute_import(cid, user_id, total,
                                                      config))
                thread.start()
            else:
                result = execute_import(cid, user_id, total, config)
            result['collection_id'] = cid
        except ErrorCodeError as e:
            logger.exception('<importCsvFile> error=')
            result['code'] = e.code
            result['message'] = e.message
        except Exception as e:
            logger.exception('<importCsvFile> error=')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result

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
            status = row[2]
            code = row[3]
            message = row[4]
            current = total
            progress = 100
            if CollectionStatus.Collecting.name in str(status):
                if total > 0:
                    query = select([func.count(rawleads.c.id)]).\
                        where(rawleads.c.collection_id == cid)
                    current = db.count(query)
                    progress = (current * 100) / total
            return {'code': code, 'message': message,
                    'total': total, 'current': current,
                    'progress': progress}
        else:
            return {'code': ErrorCode.NOT_FOUND.value,
                    'message': ErrorCode.NOT_FOUND.name,
                    'total': 0, 'current': 0, 'progress': 0}
