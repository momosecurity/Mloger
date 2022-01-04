import json
import time
import socket

import netaddr
from cachetools import cached, TTLCache
from mitmproxy import websocket

from db.mongo_db import get_mongo_client
from db.redis_db import get_redis_client
from utils.common import *

# mongo 查询句柄
db = get_mongo_client()
rc = get_redis_client()

# redis 代理收到的客户端ip的key
REDIS_KEY = "mloger:mitmproxy:auth:hash"


@cached(cache=TTLCache(maxsize=1024, ttl=5))
def client_ip_is_allowed(ip) -> bool:
    """
    判断ip是否允许连接mitproxy
    :param ip:
    :return:
    """
    status = 0
    user_name = ''
    data = rc.hget(REDIS_KEY, ip)
    if data:
        status = json.loads(data).get('status', 0)
        user_name = json.loads(data).get('user_name', '')
    rc.hset(REDIS_KEY, ip, json.dumps({'dt': int(time.time()), 'status': status, 'user_name': user_name}))
    return status == 1


@cached(cache=TTLCache(maxsize=1024, ttl=5))
def get_user_name_by_ip_for_redis(ip) -> str:
    """
    获取授权ip的用户名
    :param ip:
    :return:
    """
    user = ''
    data = rc.hget(REDIS_KEY, ip)
    if data:
        user = json.loads(data).get('user_name', '')
    return user


@cached(cache=TTLCache(maxsize=100, ttl=60))
def get_domain_rules_list():
    domain_rules_list = list(db['rules'].find({'remove': None, 'client_ip': {'$ne': None}}))
    return domain_rules_list


@cached(cache=TTLCache(maxsize=100, ttl=5))
def get_logger_black(user_name):
    data = list(db['user_logger_black'].find({'user_name': user_name}))
    return data


@cached(cache=TTLCache(maxsize=100, ttl=60))
def get_logger_black_by_ip(ip):
    user_name = get_user_name_by_ip_for_redis(ip)
    black_rules_list = get_logger_black(user_name)
    return black_rules_list


def domain_is_intranet(domain):
    try:
        ip = socket.getaddrinfo(domain, None)[0][4][0]
        if netaddr.IPAddress(ip).is_private():
            return True
    except:
        pass
    return False


def get_client_ip(flow):
    try:
        client_ip = netaddr.IPAddress(flow.client_conn.address[0]).ipv4().__str__()
    except Exception as e:
        flow.kill()
        raise e
    return client_ip


def flow_is_black(flow) -> bool:
    client_ip = get_client_ip(flow)
    if not client_ip_is_allowed(client_ip):
        flow.kill()
        return True
    if flow.websocket is not None:
        return False
    if flow.request.host in domain_black_list or flow.request.path.split('?')[0].endswith(file_type_black_list):
        return True
    black_rules_list = get_logger_black_by_ip(client_ip)
    for rule in black_rules_list:
        if flow.request.host.endswith(rule['host']) and flow.request.path.startswith(rule['path']):
            return True
    return False


def get_client_ip_list():
    data = rc.hgetall(REDIS_KEY)
    return data
