from __future__ import absolute_import
import hug
import os

from api.errorcode import ErrorCode
from config import setting
from log import logger


@hug.post('')
def upload_file(body):
    result = {'code': ErrorCode.OK.value,
              'message': ErrorCode.OK.name}
    try:
        filename = body['file_name']
        file_name = bytes.decode(filename)
        logger.info('<upload_file> file_name: ' + file_name)
        file_text = body['file']
        config = setting['collect_config']
        upload_path = config['upload_path']
        filter_list = config['filter_list']
        if file_name not in filter_list:
            save_file_name = upload_path + file_name
            with open(save_file_name, 'wb') as f:
                f.write(file_text)
                f.close()
        result['fileName'] = file_name
    except Exception as e:
        logger.exception('<upload_file> error: ')
    return result


@hug.get('/list')
def get_file_list(request):
    file_list = []
    try:
        config = setting['collect_config']
        upload_path = config['upload_path']
        for root, dirs, files in os.walk(upload_path):
            for file in files:
                file_list.append(file)
    except Exception:
        logger.exception('<get_file_list> error: ')
    return {'fileList': file_list}


@hug.get('/load')
def load_file(request):
    file_name = request.params.get('filename')
    editable = True
    load_file_str = ''
    try:
        config = setting['collect_config']
        upload_path = config['upload_path']
        filter_list = config['filter_list']
        file_path = upload_path + file_name
        load_file = open(file_path, 'rb')
        load_file_str = load_file.read()
        load_file.close()
        if file_name in filter_list:
            editable = False
    except Exception:
            logger.exception('<load_file> error: ')
    return {
        'xmlString': load_file_str,
        'xmlName': file_name,
        'xmlEditable': editable
    }
