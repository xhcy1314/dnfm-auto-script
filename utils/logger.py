import logging
from utils.path_manager import PathManager
from logging import handlers
import logging.config
import os

MSG = '''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

# '''
# 指定保存日志的文件路径，日志级别，以及调用文件
# 将日志存入到指定的文件中，当天的日志存在一个txt文件，不同月份，用目录区分
# '''


# 获取日志保存的路劲
logs_path = PathManager.LOG_PATH + PathManager.PROJECT_NAME + '.log'
if os.path.exists(PathManager.LOG_PATH) is False:
    os.mkdir(PathManager.LOG_PATH)
if os.path.exists(logs_path) is False:
    file = open(logs_path, 'w')
    file.write(MSG)
# 创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 创建日志输入端，fh输入到日志文件，ch输出到控制台，定义日志级别为info
th = handlers.TimedRotatingFileHandler(filename=logs_path, when='MIDNIGHT', backupCount=30, encoding='utf-8')
ch = logging.StreamHandler()

ch.setLevel(logging.INFO)
# 定义handler的输出格式
formatter_fh = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s[line:%(lineno)d] - %(message)s')
ch.setFormatter(formatter_fh)
th.setFormatter(formatter_fh)
# 给logger添加handler
logger.addHandler(ch)
logger.addHandler(th)
# logger.addHandler(logstash.TCPLogstashHandler(elastic_host,5000,version=1))
