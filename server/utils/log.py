import logging.config

logging.config.fileConfig("./config/log.conf")
logger = logging.getLogger('log')