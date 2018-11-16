
from __future__ import absolute_import
import hug
import os
import time
import uuid

from api.errorcode import ErrorCode
from api.auth.user import check_sysadmin, check_admin, query_current_user
from cache import locationcache
from config import db, setting
from log import logger
from models import handle_secrecy_value
from models.collection import collections, CollectionType
from models.campaign import campaigns
from models.company import companies
from models.operationlog import operationlogs, OperType, OperResult
from models.product import products
# from models.location import locations
from models.rawleads import rawleads, rawcontacts
from models.transformtask import transformtasks
from models.template import templates
from services.leadscollect import LeadsCollectService
from services.file import count_file_lines_csv, parse_file_csv,\
    page_parse_file_csv, count_file_lines_xml, parse_file_xml,\
    page_parse_file_xml
from datetime import datetime
from sqlalchemy.sql import select, or_
from sqlalchemy.sql.expression import func


collect = LeadsCollectService()


@hug.object.urls('')
class RawLeads(object):
    @hug.object.get()
    def get(self, request, response, q: str=None):
        offset = int(request.params.get('offset', 0))
        limit = int(request.params.get('limit', 15))
        cid = request.params.get('collection_id')
        ccode = request.params.get('collection_code')
        ctype = request.params.get('collection_type')
        name = request.params.get('name')
        effective = request.params.get('effective')
        merge_status = request.params.get('merge_status')
        campaign = request.params.get('campaign')
        begin_date = request.params.get('begin_date')
        end_date = request.params.get('end_date')
        sorts = request.params.get('sort', [])
        sorts = sorts if isinstance(sorts, list) else [sorts]
        u = query_current_user(request)
        rl = rawleads.alias('l')
        rc = rawcontacts.alias('c')
        co = collections.alias('co')
        ca = campaigns.alias('ca')
        cp = companies.alias('cp')
        pd = products.alias('p')
        q = select([rl.c.id,
                    rl.c.name,
                    rl.c.effective,
                    rl.c.merge_status,
                    rl.c.budget,
                    rl.c.need,
                    rl.c.authority,
                    rl.c.time_frame,
                    rl.c.premiun,
                    rl.c.created_date,
                    rl.c.last_modifed,
                    rl.c.collection_id,
                    co.c.code,
                    rl.c.campaign_id,
                    ca.c.name.label('campaign_name'),
                    rl.c.company_id,
                    cp.c.name.label('company_name'),
                    rl.c.product_id,
                    pd.c.name.label('product_name'),
                    rc.c.en_name,
                    rc.c.first_name,
                    rc.c.last_name,
                    rc.c.full_name,
                    rc.c.gender,
                    rc.c.age,
                    rc.c.id_type,
                    rc.c.id_number,
                    rc.c.marriage,
                    rc.c.num_of_childs,
                    rc.c.education,
                    rc.c.income,
                    rc.c.job_title,
                    rc.c.vip_flag,
                    rc.c.mobile_phone,
                    rc.c.home_phone,
                    rc.c.work_phone,
                    rc.c.email,
                    rc.c.qq,
                    rc.c.weixin,
                    rc.c.ip_address,
                    rc.c.province_code,
                    rc.c.province_name,
                    rc.c.city_code,
                    rc.c.city_name,
                    cp.c.memo.label('company_memo'),
                    rl.c.err_msg])
        c = select([func.count(rl.c.id)])
        join = rl.outerjoin(rc, rl.c.contact_id == rc.c.id)
        join = join.outerjoin(co, rl.c.collection_id == co.c.id)
        join = join.outerjoin(ca, rl.c.campaign_id == ca.c.id)
        join = join.outerjoin(cp, rl.c.company_id == cp.c.id)
        join = join.outerjoin(pd, rl.c.product_id == pd.c.id)
        q = q.select_from(join)
        c = c.select_from(join)
        if cid:
            c = c.where(co.c.id == int(cid))
            q = q.where(co.c.id == int(cid))
        if u and not check_sysadmin(u):
            filter_by_user = False
            if check_admin(u):
                orgid = u.get('organization_id')
                if str(orgid) != '1':
                    org = u.get('org')
                    if org is not None:
                        com_code = org.get('ccode')
                        if com_code is not None:
                            c = filter_by_user_org(co, cp, c, u, com_code)
                            q = filter_by_user_org(co, cp, q, u, com_code)
                        else:
                            filter_by_user = True
                    else:
                        filter_by_user = True
            else:
                filter_by_user = True
            if filter_by_user:
                c = db.filter_by_user(co, c, u)
                q = db.filter_by_user(co, q, u)
        if effective:
            c = c.where(rl.c.effective == int(effective))
            q = q.where(rl.c.effective == int(effective))
        if merge_status:
            c = c.where(rl.c.merge_status == int(merge_status))
            q = q.where(rl.c.merge_status == int(merge_status))
        if ccode:
            c = c.where(co.c.code == ccode)
            q = q.where(co.c.code == ccode)
        if ctype:
            c = c.where(co.c.type == ctype)
            q = q.where(co.c.type == ctype)
        if name:
            q = q.where(rl.c.name.like('%' + name + '%'))
            c = c.where(rl.c.name.like('%' + name + '%'))
        if campaign:
            q = q.where(ca.c.name.like('%' + campaign + '%'))
            c = c.where(ca.c.name.like('%' + campaign + '%'))
        if begin_date and end_date:
            df = "%Y-%m-%d %H:%M:%S"
            begin_time = datetime.strptime(begin_date + " 00:00:00", df)
            end_time = datetime.strptime(end_date + " 23:59:59", df)
            c = c.where(rl.c.created_date.between(begin_time, end_time))
            q = q.where(rl.c.created_date.between(begin_time, end_time))
        count = db.count(c)
        q = q.order_by(rl.c.id.desc())

        q = db.paginate(q, offset, limit)
        rows = db.execute(q)
        data = []
        for r in rows:
            d = {}
            d['id'] = r[0]
            d['name'] = r[1]
            d['effective'] = r[2]
            d['merge_status'] = r[3]
            d['budget'] = r[4]
            d['need'] = r[5]
            d['authority'] = r[6]
            d['time_frame'] = r[7]
            d['premiun'] = r[8]
            d['created_date'] = str(r[9])
            d['last_modifed'] = str(r[10])
            d['collection_id'] = r[11]
            d['collection_code'] = r[12]
            d['campaign_id'] = r[13]
            d['campaign'] = r[14]
            d['company_id'] = r[15]
            d['company'] = r[16]
            d['product_id'] = r[17]
            d['product'] = r[18]
            d['en_name'] = r[19]
            d['first_name'] = r[20]
            d['last_name'] = r[21]
            d['full_name'] = r[22]
            d['gender'] = r[23]
            d['age'] = r[24]
            d['id_type'] = r[25]
            d['id_number'] = handle_secrecy_value(r[26], 4, 3)
            d['marriage'] = r[27]
            d['num_of_childs'] = r[28]
            d['education'] = r[29]
            d['income'] = r[30]
            d['job_title'] = r[31]
            d['vip_flag'] = r[32]
            d['mobile_phone'] = handle_secrecy_value(r[33], None, 4)
            d['home_phone'] = r[34]
            d['work_phone'] = r[35]
            d['email'] = r[36]
            d['qq'] = r[37]
            d['weixin'] = r[38]
            d['ip_address'] = r[39]
            d['province_code'] = r[40]
            d['province_name'] = locationcache.get(r[40], r[41])
            d['city_code'] = r[42]
            d['city_name'] = locationcache.get(r[42], r[43])
            d['errMsg'] = r[45]
            data.append(d)

        response.set_header('X-Total-Count', str(count))
        return data

    @hug.get('/gen_code')
    def gen_collection_code():
        code = 'M' + time.strftime('%Y%m%d%H%M%S')
        return {'code': code}

    @hug.post('/upload')
    def upload_file(body):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            filename = body['file_name']
            file_text = body['file']
            uid = str(uuid.uuid1())
            filename_str = bytes.decode(filename)
            save_filename = uid + filename_str[filename_str.find('.'):]
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
        uid = request.params.get('uid')
        filename = request.params.get('file_name')
        offset = int(request.params.get('offset', 0))
        limit = int(request.params.get('limit', 15))
        total = int(request.params.get('total', 0))
        filetype = filename[filename.find('.'):]
        if (filetype == '.csv'):
            if total == 0:
                total = count_file_lines_csv(uid)
            data = None
            try:
                data = page_parse_file_csv(uid, offset, limit, total, 'utf-8')
            except Exception:
                data = page_parse_file_csv(uid, offset, limit, total, 'GBK')
            return data
        else:
            if total == 0:
                total = count_file_lines_xml(uid)
            data = page_parse_file_xml(uid, offset, limit, total)
            return data

    @hug.post('/importCsvFile')
    def importCsvFile(request, response, body):
        u = query_current_user(request)
        if not u:
            return {'code': 40001,
                    'message': 'Authentication token failure',
                    'collect_count': 0,
                    'success_count': 0,
                    'fail_count': 0}

        code = body['code']
        query = select([collections.c.source_count,
                        collections.c.collect_count,
                        collections.c.fail_count])
        query = query.where(collections.c.code == code)
        row = db.fetch_one(query)
        if row:
            return {'code': 1,
                    'message': 'OK',
                    'collect_count': row[0],
                    'success_count': row[1],
                    'fail_count': row[2]}

        uid = body['uid']
        filename = body['file_name']
        name = body.pop("name", None)
        tid = body['template_id']
        user_id = u['id']
        data = None
        try:
            data = parse_file_csv(uid, 'utf-8')
        except Exception:
            data = parse_file_csv(uid, 'GBK')

        rows = data['list']
        count = len(rows)
        now = datetime.now()
        s = select([templates]).where(templates.c.id == int(tid))
        row = db.fetch_one(s)
        if not row:
            return {'code': 1, 'message': 'Error',
                    'collect_count': count,
                    'success_count': 0, 'fail_count': 0}

        channel = row['channel_id']
        save_file = uid + '.csv'
        collection = {'code': code,
                      'name': name,
                      'source': filename,
                      'save_file': save_file,
                      'type': CollectionType.ImportCSV,
                      'channel_id': channel,
                      'template_id': int(tid),
                      'source_count': count,
                      'collect_count': count,
                      'user_id': user_id,
                      'created_date': now, 'last_modifed': now}
        cid = db.insert(collections, collection)

        success_count = collect.insert_file_leads(db.conn, cid, channel, rows)
        fail_count = count - success_count

        now = datetime.now()
        update = {'id': cid,
                  'collect_count': success_count,
                  'fail_count': fail_count,
                  'status': 'Success',
                  'last_modifed': now}
        db.update(collections, update)

        save_transform_task(db.conn, cid, int(tid))
        detail = '销售线索导入, 上传文件：' + filename + ', 保存文件：' + save_file
        save_log(db.conn, user_id, cid, '销售线索导入', detail)
        return {'code': 1, 'message': 'OK', 'collect_count': count,
                'success_count': success_count, 'fail_count': fail_count}

    @hug.get('/importProgress')
    def importProgress(request, response):
        code = request.params.get('code')
        query = select([collections.c.id,
                        collections.c.source_count])
        query = query.where(collections.c.code == code)
        row = db.fetch_one(query)
        if row:
            total = row[1]
            if total > 0:
                query = select([func.count(rawleads.c.id)]).\
                    where(rawleads.c.collection_id == row[0])
                current = db.count(query)
                progress = (current * 100) / total
                return {'total': total,
                        'current': current,
                        'progress': progress}
        return {'total': 0, 'current': 0, 'progress': 0}

    @hug.post('/importXmlFile')
    def importXmlFile(request, response, body):
        u = query_current_user(request)
        if not u:
            return {'code': 40001,
                    'message': 'Authentication token failure',
                    'collect_count': 0,
                    'success_count': 0,
                    'fail_count': 0}
        uid = body['uid']
        filename = body['file_name']
        code = body['code']
        name = body.pop("name", None)
        tid = body['template_id']
        user_id = u['id']
        data = parse_file_xml(uid)

        rows = data['list']
        count = len(rows)
        now = datetime.now()
        s = select([templates]).where(templates.c.id == int(tid))
        result = db.execute(s)
        row = result.fetchone()
        if not row:
            return {'code': 1, 'message': 'Error',
                    'collect_count': count,
                    'success_count': 0, 'fail_count': 0}

        channel = row['channel_id']
        save_file = uid + '.xml'
        collection = {'code': code,
                      'name': name,
                      'source': filename,
                      'save_file': save_file,
                      'type': CollectionType.ImportXML,
                      'channel_id': channel,
                      'template_id': int(tid),
                      'source_count': count,
                      'collect_count': count,
                      'user_id': user_id,
                      'created_date': now, 'last_modifed': now}
        rs = db.execute(collections.insert(), collection)
        cid = rs.inserted_primary_key[0]

        success_count = collect.insert_file_leads(db.conn, cid, rows, now,
                                                  channel)
        fail_count = count - success_count

        save_transform_task(db.con, cid, int(tid))
        detail = '销售线索导入, 上传文件：' + filename + ', 保存文件：' + save_file
        save_log(db.conn, user_id, cid, '销售线索导入', detail)
        return {'code': 1, 'message': 'OK', 'collect_count': count,
                'success_count': success_count, 'fail_count': fail_count}


def create_upload_dir():
    try:
        upload_dir = setting['upload']
        if not os.path.exists(upload_dir):
            logger.info('<create_upload_dir> upload_dir: ' + upload_dir)
            os.makedirs(upload_dir)
    except Exception as e:
        logger.exception('<create_upload_dir> error: ')


def filter_by_user_org(co, cp, q, user, com_code):
    user_id = user.get('id')
    if user_id is not None:
        q = q.where(or_(co.c.user_id == user_id,
                        cp.c.memo.like(com_code + '%')))
    elif user.get('username') is not None:
        q = q.where(or_(co.c.username == user.get('username'),
                        cp.c.memo.like(com_code + '%')))
    return q


def save_transform_task(conn, collection_id, template_id):
    now = datetime.now()
    transformtask = {'collection_id': collection_id,
                     'template_id': template_id,
                     'created_date': now,
                     'last_modifed': now}
    conn.execute(transformtasks.insert(), transformtask)


def save_log(conn, user_id, cid, name, detail):
    operationlog = {'name': name,
                    'detail': detail,
                    'object_id': cid,
                    'object': 'Collection',
                    'type': OperType.Import,
                    'result': OperResult.Success,
                    'user_id': user_id,
                    'created_date': datetime.now()}
    conn.execute(operationlogs.insert(), operationlog)
