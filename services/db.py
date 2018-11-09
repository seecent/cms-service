
from __future__ import absolute_import

from log import logger


def bulk_insert_datas(db, table, data_list, batch=5000):
    try:
        total = len(data_list)
        logger.info('<bulk_insert_datas> total=' + str(total) +
                    ', batch=' + str(batch))
        if total > batch:
            begin = 0
            end = 0
            pages = int(total / batch)
            for n in range(0, pages):
                logger.info('<bulk_insert_datas> pages=' + str(pages) +
                            ', n=' + str(n))
                begin = n * batch
                end = begin + batch
                page_datas = data_list[begin:end]
                db.bulk_insert(table, page_datas)

            if end < (total - 1):
                begin = end
                end = total
                page_datas = data_list[begin:end]
                db.bulk_insert(table, page_datas)
        else:
            db.bulk_insert(table, data_list)
    except Exception:
        logger.exception('<bulk_insert_datas> error=')
