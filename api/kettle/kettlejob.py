
from __future__ import absolute_import
import hug

from config import db, setting
from datetime import datetime
from models.kettle.kettlejob import kettlejobs
from models import rows2dict
from log import logger
from sqlalchemy.sql import select

import os.path
import xml.etree.ElementTree as ET

IGNORES = {'created_date', 'last_modifed'}


@hug.object.urls('')
class Kettlejobs(object):
    @hug.object.get()
    def get(self, request, response):
        t = kettlejobs.alias('k')
        query = db.filter(t, request, ['name'])
        query = db.filter_by_date(t.c.created_date, query, request)
        rs = db.paginate_data(query, request, response)
        return rows2dict(rs, kettlejobs)


def init_kettle_jobs():
    db.connect()
    t = kettlejobs.alias('k')
    query = select([t.c.id, t.c.name])
    rows = db.execute(query)
    job_dict = {}
    for r in rows:
        job_dict[r[1]] = r[0]

    jobs = []
    filename = setting['lms_home'] + os.path.sep +\
        "conf" + os.path.sep + 'kettle_jobs_config.xml'
    logger.info('<init_kettle_jobs> filename=' + filename)
    tree = ET.parse(filename)
    root = tree.getroot()
    if root.tag == 'KettleJobs':
        for kj in root:
            if kj.tag == 'KettleJob':
                job = {}
                for c in kj:
                    if c.tag == 'Name':
                        job['name'] = c.text
                    elif c.tag == 'Module':
                        job['job_module'] = c.text
                    elif c.tag == 'TargetDataBase':
                        job['target_db'] = c.text
                    elif c.tag == 'TargetTable':
                        job['target_table'] = c.text
                    elif c.tag == 'TargetTableCnName':
                        job['target_table_cnname'] = c.text
                    elif c.tag == 'SourceDataBase':
                        job['source_db'] = c.text
                    elif c.tag == 'SourceTable':
                        job['source_table'] = c.text
                    elif c.tag == 'Schedule':
                        job['job_schedule'] = c.text
                    elif c.tag == 'UpdateMode':
                        job['update_mode'] = c.text
                    elif c.tag == 'Description':
                        job['description'] = c.text
                jobs.append(job)

    now = datetime.now()
    for job in jobs:
        job_name = job['name']
        job_id = job_dict.get(job_name)
        if job_id is None:
            logger.info('<init_kettle_jobs> insert kettlejobs=' + str(job))
            job['created_date'] = now
            job['last_modifed'] = now
            db.insert(kettlejobs, job)
        else:
            job['id'] = job_id
            logger.info('<init_kettle_jobs> update kettlejobs=' + str(job))
            job['last_modifed'] = now
            db.update(kettlejobs, job)

    db.close()
