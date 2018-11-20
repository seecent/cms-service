
from __future__ import absolute_import
import hug

from api.errorcode import ErrorCode
from config import db, setting
from datetime import datetime
from falcon import HTTPNotFound, HTTP_201, HTTP_204
from log import logger
from models.media.file import files
from models import row2dict, rows2dict, bind_dict, change_dict
from services.media.file import FileService
from sqlalchemy.sql import select

IGNORES = {'uuid', 'path', 'last_modifed'}
fileservice = FileService()


class FileMixin(object):

    def get_file(self, id):
        row = db.get(files, id)
        if row:
            return row2dict(row, files)
        else:
            raise HTTPNotFound(title="no_file")


@hug.object.urls('')
class Files(object):
    '''文件管理REST API
    '''
    @hug.object.get()
    def get(self, request, response, q: str=None):
        '''文件
        '''
        try:
            folder_id = request.params.get('folderId')
            t = files.alias('f')
            query = db.filter(t, request)
            if folder_id:
                query = query.where(t.c.folder_id == folder_id)
            if q:
                query = query.where(t.c.name.like('%' + q + '%'))
            query = db.filter_by_date(t.c.created_date, query, request)
            rs = db.paginate_data(query, request, response)
            files_list = rows2dict(rs, files, IGNORES)
            media_url = setting['media_url']
            for f in files_list:
                f['name'] = f.pop('original_filename')
                f['url'] = media_url + f.pop('file_path')
            return files_list
        except Exception as e:
            logger.exception('<get> error: ')
            return {'code': ErrorCode.EXCEPTION.value, 'message': 'error'}

    @hug.object.post(status=HTTP_201)
    def post(self, body):
        '''
        文件REST API Post接口
        :param: id int 文件ID
        :return: json
        '''
        file = bind_dict(files, body)
        d = db.save(files, file)
        return d

    @hug.object.delete(status=HTTP_204)
    def delete(self, request, response):
        ids = request.params.get('ids')
        db.bulk_delete(files, ids)
        return {'code': 0, 'message': 'OK'}

    @hug.post('/upload')
    def upload_file(body):
        result = {'code': ErrorCode.OK.value,
                  'message': ErrorCode.OK.name}
        try:
            folder_id = body['folder_id']
            file_name = body['file_name']
            file_content = body['file']
            if folder_id:
                folder_id = folder_id.decode(encoding="utf-8")
                file_name = file_name.decode(encoding="utf-8")
                result = fileservice.create(
                    db, folder_id, file_name, file_content)
                print(result)
            else:
                result['code'] = ErrorCode.MISS_PARAM.value
                result['message'] = "miss param folder_id!"
        except Exception as e:
            logger.exception('<upload_file> error: ')
            result['code'] = ErrorCode.EXCEPTION.value
            result['message'] = str(e)
        return result


@hug.object.http_methods('/{id}')
class FileInst(FileMixin, object):

    def get(self, id: int):
        t = self.get_file(id)
        return t

    def patch(self, id: int, body):
        t = self.get_file(id)
        if t:
            t = change_dict(files, t, body)
            db.update(files, t)
        return t

    @hug.object.delete(status=HTTP_204)
    def delete(self, id: int):
        '''
        删除文件
        :param: id int 文件ID
        :return:
        '''
        db.delete(files, id)


@hug.get('/getAllFiles')
def get_all_files():
    datas = []
    t = files.alias('d')
    query = select([t.c.id, t.c.code, t.c.name])
    rows = db.execute(query).fetchall()
    for r in rows:
        datas.append({'id': r[0], 'code': r[1], 'name': r[2]})
    return datas


def query_all_files():
    rs = db.fetch_all(files, ['name'])
    file_dict = {}
    for r in rs:
        code = r[1]
        file_dict[code] = {'id': r[0], 'code': code, 'name': r[2]}
    return file_dict


def init_files():
    db.connect()
    count = db.count(files)
    if count > 1:
        db.close()
        return
    now = datetime.now()
    dept1 = {'code': '1001', 'name': '销售部',
             'created_date': now,
             'last_modifed': now}
    dept2 = {'code': '1002', 'name': '银保部',
             'created_date': now,
             'last_modifed': now}
    dept3 = {'code': '1003', 'name': '收展部',
             'created_date': now,
             'last_modifed': now}
    dept4 = {'code': '1004', 'name': '数字创新',
             'created_date': now,
             'last_modifed': now}
    db.insert(files, dept1)
    db.insert(files, dept2)
    db.insert(files, dept3)
    db.insert(files, dept4)
    db.close()
