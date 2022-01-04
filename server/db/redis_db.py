#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import redis

LOCAL_REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "password": "redis_password",
    "db": 0,
    "max_connections": 100,
    "socket_timeout": 1,
    "socket_keepalive": True,
    "health_check_interval": 10,
    "decode_responses": True,
}

REDIS_CONFIG = {
    "host": "",
    "port": 6379,
    "max_connections": 100,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "socket_keepalive": True,
    "health_check_interval": 10,
    "decode_responses": True,
    "db": 0,
}

REDIS_POOL = None

local = os.getenv('PROJECT_ENV', 'prod') == 'local'


def get_redis_client(local=local):
    global REDIS_POOL
    if local and not REDIS_POOL:
        REDIS_POOL = redis.ConnectionPool(**LOCAL_REDIS_CONFIG)
    if not REDIS_POOL:
        REDIS_POOL = redis.ConnectionPool(**REDIS_CONFIG)
    redis_client = redis.Redis(connection_pool=REDIS_POOL)
    return redis_client


def get_redis_client_for_flask(local=local):
    if local:
        FLASK_CONFIG = LOCAL_REDIS_CONFIG
    else:
        FLASK_CONFIG = REDIS_CONFIG
    FLASK_CONFIG['decode_responses'] = False
    redis_client = redis.Redis(**FLASK_CONFIG)
    return redis_client


def get_redis_url(local=local):
    conf = REDIS_CONFIG
    if local:
        conf = LOCAL_REDIS_CONFIG
    if "password" in conf:
        redis_url = f'redis://:{conf.get("password","")}@{conf["host"]}:{conf["port"]}/'
    else:
        redis_url = f'redis://{conf["host"]}:{conf["port"]}/'
    return redis_url

