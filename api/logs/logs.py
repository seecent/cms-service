
from __future__ import absolute_import
import hug
import os
from falcon import HTTPInternalServerError
from config import setting
from log import logger

#
# Created by ghu on 2018/8/23.
#


@hug.object.urls('/{dirname}/{filename}')
class Logs(object):
    @hug.object.get()
    def get(self, request, response, dirname: str=None, filename: str=None):
        try:
            logdata = []
            len = 50
            start = request.params.get('start')
            if start is not None:
                start = int(start)
            else:
                start = 0
            if start != 0:
                beginLine = -start
                endLine = -(start + len)
            else:
                beginLine = None
                endLine = -len
            filepath = _get_validate_filepath(dirname, filename)
            logFile = open(filepath, 'r')
            rowCount = 0
            for row in logFile.readlines()[endLine:beginLine]:
                logdata.append(row)
                rowCount += 1
            return {
                'logdata': logdata,
                'hasMore': rowCount == len,
                'start': start,
                'len': len
            }
        except Exception:
            logger.exception('<get> error: ')
            raise HTTPInternalServerError(title="server_error")


@hug.object.http_methods('/list')
class LogsList(object):
    def get(self):
        try:
            filedirs = _get_filedirs()
            fileDict = {}
            for dirname, filedir in filedirs.items():
                fileList = []
                for root, dirs, files in os.walk(filedir):
                    for file in files:
                        fileList.append(file)
                fileDict[dirname] = fileList
            return fileDict
        except Exception:
            logger.exception('<get> error: ')
            raise HTTPInternalServerError(title="server_error")


@hug.object.http_methods('/download', output=hug.output_format.file)
class LogsDownload(object):
    def get(self, request, response):
        filename = request.params.get('filename')
        dirname = request.params.get('dirname')
        filepath = _get_validate_filepath(dirname, filename)
        response.set_header('Content-Type', 'application/octet-stream')
        response.set_header(
            'Content-Disposition', 'attachment;filename="{}"'.format(filename))
        return filepath


def _get_filedirs():
    filedirs = setting['lms_logs_home']
    return filedirs


def _get_validate_filepath(dirname, filename):
    filedirs = _get_filedirs()
    filedir = filedirs[dirname]
    if filename is None:
        raise HTTPInternalServerError(
            title="invalid_log_file_path", description=filename)
    filepath = os.path.join(filedir, filename)  # denied access to other path
    if os.path.dirname(filepath) != filedir:
        raise HTTPInternalServerError(
            title="invalid_log_file_path", description=filename)
    return filepath
