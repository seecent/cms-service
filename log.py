import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import setting

# 创建一个logger
logger = logging.getLogger('cmslogger')
logger.setLevel(logging.INFO)

logs_home = setting['cms_logs_home']['cms-service']
# 创建一个handler，用于写入日志文件
# log_file = 'D:\\dev\\git\\lms\\lms-service\\logs\\lms-service.log'
log_file = os.path.join(logs_home, 'cms-service.log')
# fh = logging.FileHandler(log_file)
# 每天一个文件
fh = TimedRotatingFileHandler(log_file, 'midnight', 1)
fh.setLevel(logging.INFO)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# 定义handler的输出格式
formatter = logging.Formatter('[%(asctime)s][%(thread)d][%(filename)s][line: %(lineno)d][%(levelname)s] %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)
