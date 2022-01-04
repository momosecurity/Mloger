#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import time

from db.mongo_db import get_mongo_client
from db.redis_db import get_redis_client
from utils.common import replaceD
from utils.log import logger


def add2apis():
    logger.warning('start add2apis')
    db = get_mongo_client()
    rc = get_redis_client()
    # sub一个频道然后处理
    ps = rc.pubsub()
    ps.subscribe('mloger:logger_request')

    while 1:
        message = ps.get_message(ignore_subscribe_messages=True, timeout=0.01)
        if message:
            req = json.loads(message['data'])
        else:
            continue
        if "path" not in req:
            continue
        req['gparams'] = req["path"].split('?')[1] if '?' in req["path"] else ''
        req['path'] = req["path"].split('?')[0]
        req['rd_path'] = replaceD(req['path'])
        if not db['apis'].find_one(
                {"scheme": req["scheme"], "host": req["host"], "port": req["port"], "rd_path": req['rd_path']}):
            req.pop('_id')
            db['apis'].insert_one(req)
            # req['_id'] = str(req.pop('_id'))
            # rc.lpush("mloger:security_scan_targets", json.dumps(req))
        time.sleep(0.01)


def timeout_for_ip():
    rc = get_redis_client()
    REDIS_KEY = "mloger:mitmproxy:auth:hash"
    data = rc.hgetall(REDIS_KEY)
    for ip in data:
        info = json.loads(data[ip])
        if int(time.time()) - info.get('dt', 0) > 180:
            rc.hdel(REDIS_KEY, ip)
            if info.get('status', 1):
                logger.debug("{user}授权的{client_ip}已超时，授权失效".format(user=info.get('name', ''), client_ip=ip))


def timeout_for_ip_acl():
    logger.warning('start timeout_for_ip_acl')
    while 1:
        timeout_for_ip()
        time.sleep(2)