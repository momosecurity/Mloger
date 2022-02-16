#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from pymongo import MongoClient


# 本地mongo配置
LOCAL_MONGO_HOST = "127.0.0.1"
LOCAL_MONGO_PORT = 27017
LOCAL_MONGO_USER = "mloger"
LOCAL_MONGO_PWD = "mloger_pwd"
LOCAL_MONGO_DB = "mloger"

# 线上mongo配置
MLOGER_REPLSET_MONGO_HOST = [
    "mongo",
]
MONGO_REPLSET_PORT = 27017
MONGO_REPLSET_DB = "mloger"
MONGO_REPLSET_USER = "mloger"
MONGO_REPLSET_PWD = "mloger_pwd"
timezone = 8

MONGO_REPLSET_POOL = None
MONGO_REPLSET_POOL_SIZE = 40
MONGO_REPLSET_MAX_IDLE_TIME = 1 * 60 * 1000  # 最大空闲时长,1分钟
MONGO_REPLSET_SOCKET_TIMEOUT = 60 * 1000  # socket超时,60秒
MONGO_REPLSET_MAX_WAITING_TIME = 20 * 1000  # 最大等待时间,20秒
MONGO_REPLSET_READ_PREFERENCE = "secondaryPreferred"

local = os.getenv('PROJECT_ENV', 'prod') == 'local'


def get_mongo_client(local=local):
    global MONGO_REPLSET_POOL
    if local:
        if not MONGO_REPLSET_POOL:
            MONGO_REPLSET_POOL = MongoClient(host=LOCAL_MONGO_HOST,
                                             port=LOCAL_MONGO_PORT,
                                             connect=False)
            MONGO_REPLSET_POOL[LOCAL_MONGO_DB].authenticate(LOCAL_MONGO_USER, LOCAL_MONGO_PWD)
        db = MONGO_REPLSET_POOL[LOCAL_MONGO_DB]
    else:
        if not MONGO_REPLSET_POOL:
            MONGO_REPLSET_POOL = MongoClient(host=MLOGER_REPLSET_MONGO_HOST,
                                             port=MONGO_REPLSET_PORT,
                                             maxPoolSize=MONGO_REPLSET_POOL_SIZE,
                                             socketKeepAlive=True,
                                             maxIdleTimeMS=MONGO_REPLSET_MAX_IDLE_TIME,
                                             waitQueueTimeoutMS=MONGO_REPLSET_MAX_WAITING_TIME,
                                             socketTimeoutMS=MONGO_REPLSET_SOCKET_TIMEOUT, w=1, j=False,
                                             readPreference=MONGO_REPLSET_READ_PREFERENCE)
            MONGO_REPLSET_POOL[MONGO_REPLSET_DB].authenticate(MONGO_REPLSET_USER, MONGO_REPLSET_PWD)
        db = MONGO_REPLSET_POOL[MONGO_REPLSET_DB]
    return db
