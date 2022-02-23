# !/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import json
import time
import base64
import traceback

import mitmproxy.http
from mitmproxy import http, ctx
from mitmproxy.script import concurrent

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from db.mongo_db import get_mongo_client
from db.redis_db import get_redis_client
from utils.proxypriv import client_ip_is_allowed, get_user_name_by_ip_for_redis, domain_is_intranet, flow_is_black, get_client_ip
from utils.common import *
from utils.log import logger

db = get_mongo_client()
rc = get_redis_client()

db['connections'].update({'type': 'websocket', 'live': True}, {'$set': {'live': False, 'timestamp_end': time.time()}},
                         multi=True)
websocket_conns_dict = {}
req_id_dict = {}
intercept_req_id_dict = {}


def handle_crypto(host, path, content):
    crypto = False
    crypto_data = None
    return crypto, crypto_data


@concurrent
def request(flow: http.HTTPFlow) -> None:
    in_black = flow_is_black(flow)
    client_ip = get_client_ip(flow)
    if not in_black:
        try:
            if flow.request:
                user_name = get_user_name_by_ip_for_redis(client_ip)
                raw_content = flow.request.get_content(strict=False)
                content = raw_content.decode('latin-1')
                crypto, crypto_data = handle_crypto(flow.request.host, flow.request.path, content)
                data = {
                    "method": flow.request.method,
                    "scheme": flow.request.scheme,
                    "host": flow.request.host,
                    "port": flow.request.port,
                    "path": flow.request.path,
                    "http_version": flow.request.http_version,
                    "headers": dict(flow.request.headers),
                    "content": raw_content.decode("utf-8", "ignore"),
                    "timestamp_start": flow.request.timestamp_start,
                    "timestamp_end": flow.request.timestamp_end,
                    "client_ip": client_ip,
                    "exclude": in_black,
                    "crypto": crypto,
                    "crypto_data": crypto_data,
                    "user_name": user_name,
                }
                req_id = db['request_data'].insert_one(data).inserted_id
                req_id_dict[data['host'] + '_' + data['path'] + '_' + str(data['timestamp_start']) + '_' + str(
                    data['timestamp_end'])] = req_id
                data['_id'] = str(req_id)
                if in_black:
                    return
                if crypto:
                    rc.lpush("mloger:request_data", json.dumps(data))
                elif not in_black:
                    rc.publish("mloger:logger_request", json.dumps(data))
                # 判断拦截条件，看是否修改数据
                intercept = rc.get('mloger:intercept:request:' + client_ip)
                if intercept:
                    db['request_data'].update_one({'_id': req_id}, {
                        "$set": {'intercept': True}})
                    ps = rc.pubsub()
                    ps.subscribe('intercept')
                    t = 0
                    intercept_data = None
                    while t < 3000:
                        message = ps.get_message(ignore_subscribe_messages=True, timeout=0.1)
                        if message:
                            intercept_data = json.loads(message['data'])
                            if intercept_data.get('flow_id', '') == str(req_id):
                                break
                        else:
                            time.sleep(0.1)
                        t += 1
                    ps.close()

                    if intercept_data and intercept_data['forward']:
                        if intercept_data['edited']:
                            flow.request.content = intercept_data['request_edited'].encode()
                            crypto, crypto_data = handle_crypto(flow.request.host, flow.request.path,
                                                                intercept_data['request_edited'])
                            data = {
                                "method": flow.request.method,
                                "scheme": flow.request.scheme,
                                "host": flow.request.host,
                                "port": flow.request.port,
                                "path": flow.request.path,
                                "http_version": flow.request.http_version,
                                "headers": dict(flow.request.headers),
                                "content": intercept_data['request_edited'].encode().decode("utf-8", "ignore"),
                                "timestamp_start": flow.request.timestamp_start,
                                "timestamp_end": flow.request.timestamp_end,
                                "client_ip": client_ip,
                                "exclude": in_black,
                                "crypto": crypto,
                                "crypto_data": crypto_data,
                                "user_name": user_name,
                            }
                            req_id = db['request_data'].insert_one(data).inserted_id
                            if intercept_data['wait_response']:
                                intercept_req_id_dict[
                                    data['host'] + '_' + data['path'] + '_' + str(data['timestamp_start']) + '_' + str(
                                        data['timestamp_end'])] = req_id
                            data['_id'] = str(req_id)
                            rc.lpush("mloger:request_data", json.dumps(data))
                    else:
                        flow.kill()
        except Exception as e:
            logger.debug(traceback.print_exc())
            pass
        finally:
            pass
    else:
        if domain_is_intranet(flow.request.host):
            flow.kill()


def handle_res_crypto(host, content):
    crypto = False
    crypto_data = None
    if not crypto:
        crypto_data = content.decode('utf-8', 'ignore')
    return crypto, crypto_data


@concurrent
def response(flow: http.HTTPFlow) -> None:
    in_black = flow_is_black(flow)
    client_ip = get_client_ip(flow)
    if not in_black:
        try:
            if flow.response:
                user_name = get_user_name_by_ip_for_redis(client_ip)
                req_id = req_id_dict.pop(
                    flow.request.host + '_' + flow.request.path + '_' + str(flow.request.timestamp_start) + '_' + str(
                        flow.request.timestamp_end), None)
                content = flow.response.get_content(strict=False)
                if len(content) > 1048576 or flow.request.path.endswith(file_type_black_list):
                    content = b'Large response or binary files are not stored.'
                crypto, crypto_data = handle_res_crypto(flow.request.host, content)
                data = {
                    "req_id": req_id,
                    "http_version": flow.response.http_version,
                    "status_code": flow.response.status_code,
                    "reason": flow.response.reason,
                    "headers": dict(flow.response.headers),
                    "content": crypto_data,
                    "timestamp_start": flow.response.timestamp_start,
                    "timestamp_end": flow.response.timestamp_end,
                    "client_ip": client_ip,
                    "exclude": in_black,
                    "crypto": crypto,
                    "crypto_data": crypto_data if crypto else None,
                    "user_name": user_name,
                }
                res_id = db['response_data'].insert_one(data).inserted_id
                db['request_response_map'].insert_one({'req_id': data['req_id'], 'res_id': res_id})
                data['_id'] = str(res_id)
                data['req_id'] = str(data['req_id'])
                if in_black:
                    return
                if crypto:
                    rc.lpush("mloger:response_data", json.dumps(data))
                else:
                    try:
                        data['content'] = json.dumps(json.loads(data['content']), indent=4).encode().decode(
                            'unicode_escape')
                    except:
                        pass
                    rc.publish("mloger:logger_request", json.dumps(data))
                intercept = rc.get('mloger:intercept:wait_response:' + str(req_id))
                if intercept:
                    req_id = intercept_req_id_dict.pop(flow.request.host + '_' + flow.request.path + '_' + str(
                        flow.request.timestamp_start) + '_' + str(flow.request.timestamp_end), None)
                    ps = rc.pubsub()
                    ps.subscribe('intercept')
                    t = 0
                    intercept_data = None
                    while t < 3000:
                        message = ps.get_message(ignore_subscribe_messages=True, timeout=0.1)
                        if message:
                            intercept_data = json.loads(message['data'])
                            if intercept_data.get('flow_id', '') == str(res_id):
                                break
                        else:
                            time.sleep(0.1)
                        t += 1
                    ps.close()
                    if intercept_data and intercept_data['forward']:
                        if intercept_data['edited']:
                            if intercept_data.get('b64', False):
                                flow.response.content = base64.b64decode(intercept_data['response_edited'])
                            elif type(intercept_data['response_edited']) is str:
                                flow.response.content = intercept_data['response_edited'].encode()
                            else:
                                flow.response.content = intercept_data['response_edited']
                            content = flow.response.get_content(strict=False)
                            crypto, crypto_data = handle_res_crypto(flow.request.host, content)
                            data = {
                                "req_id": req_id,
                                "http_version": flow.response.http_version,
                                "status_code": flow.response.status_code,
                                "reason": flow.response.reason,
                                "headers": dict(flow.response.headers),
                                "content": crypto_data,
                                "timestamp_start": flow.response.timestamp_start,
                                "timestamp_end": flow.response.timestamp_end,
                                "client_ip": client_ip,
                                "exclude": in_black,
                                "crypto": crypto,
                                "crypto_data": crypto_data if crypto else None,
                                "user_name": user_name,
                            }
                            res_id = db['response_data'].insert_one(data).inserted_id
                            data['_id'] = str(res_id)
                            data['req_id'] = str(data['req_id'])
                            rc.lpush("mloger:response_data", json.dumps(data))
                    else:
                        flow.kill()
        except Exception as e:
            logger.debug(traceback.print_exc())
        finally:
            pass


@concurrent
def websocket_message(flow: mitmproxy.http.HTTPFlow):
    in_black = flow_is_black(flow)
    client_ip = get_client_ip(flow)
    if not in_black:
        user_name = get_user_name_by_ip_for_redis(client_ip)
        message = flow.websocket.messages[-1]
        print(message)
        if type(message.content) is str:
            message.content = message.content.encode()
        if b'Ping' in message.content or b'Pong' in message.content:
            in_black = True
        data = {
            'client_id': flow.client_conn.id,
            'server_id': flow.server_conn.id,
            'client_host': client_ip,
            'client_port': flow.client_conn.address[1],
            'server_host': flow.server_conn.address[0],
            'server_port': flow.server_conn.address[1],
            'direction': 'send' if message.from_client else 'receive',
            'content': message.content,
            "client_ip": client_ip,
            "exclude": in_black,
            "timestamp_start": flow.client_conn.timestamp_start,
            "conn_id": websocket_conns_dict.get(flow.client_conn.id + flow.server_conn.id, None),
            "user_name": user_name,
        }
        mes_id = db['websocket'].insert_one(data).inserted_id
        data['_id'] = str(mes_id)
        data['type'] = 'websocket'
        if in_black:
            return
        data['content'] = data['content'].decode('utf-8', 'ignore')
        rc.publish("mloger:imws_websocket", json.dumps(data))


def websocket_start(flow: mitmproxy.http.HTTPFlow):
    client_ip = get_client_ip(flow)
    if not client_ip_is_allowed(client_ip):
        flow.kill()
        return
    user_name = get_user_name_by_ip_for_redis(client_ip)
    data = {
        'type': 'websocket',
        'live': True,
        'client_id': flow.client_conn.id,
        'server_id': flow.server_conn.id,
        'client_host': client_ip,
        'client_port': flow.client_conn.address[1],
        'server_host': flow.server_conn.address[0],
        'server_port': flow.server_conn.address[1],
        'timestamp_start': flow.client_conn.timestamp_start,
        'user_name': user_name,
    }
    conn_id = db['connections'].insert_one(data).inserted_id
    websocket_conns_dict[flow.client_conn.id + flow.server_conn.id] = str(conn_id)
    data['_id'] = str(data['_id'])
    rc.publish("mloger:imws_websocket", json.dumps(data))
    asyncio.create_task(inject_websocket(flow))


async def inject_websocket(flow: mitmproxy.http.HTTPFlow):
    # 注入功能
    logger.info('inject_websocket start')
    while db['connections'].find_one({'type': 'websocket',
                                      'live': True,
                                      'client_id': flow.client_conn.id,
                                      'server_id': flow.server_conn.id, }):
        ws_mes = db['inject_repeater'].find_one({'client_id': flow.client_conn.id,
                                                 'server_id': flow.server_conn.id, 'status': None, 'type': 'websocket'})
        if ws_mes:
            to_client = False if ws_mes['direction'] == 'send' else True
            is_text = True
            concurrent_num = int(ws_mes.get('concurrent_num', 0))
            if isinstance(ws_mes['content'], str):
                ws_mes['content'] = ws_mes['content'].encode()
            logger.info(ws_mes['content'])
            if concurrent_num > 0:
                for _ in range(concurrent_num):
                    ctx.master.commands.call("inject.websocket", flow, to_client,  ws_mes['content'], is_text)
            else:
                logger.info("inject.websocket------------")
                ctx.master.commands.call("inject.websocket", flow, to_client, ws_mes['content'], is_text)
            db['inject_repeater'].update_one({'_id': ws_mes['_id']}, {'$set': {'status': 'done'}})
        await asyncio.sleep(0.5)


def websocket_error(flow):
    # 更新websocket连接状态
    data = {
        'type': 'websocket',
        'live': True,
        'client_id': flow.client_conn.id,
        'server_id': flow.server_conn.id,
        'server_host': flow.server_conn.address[0],
        'server_port': flow.server_conn.address[1],
    }
    db['connections'].update_one(data, {'$set': {'live': False, 'timestamp_end': time.time()}})
    data['_id'] = str(websocket_conns_dict.pop(flow.client_conn.id + flow.server_conn.id, ''))
    data['live'] = False
    rc.publish("mloger:imws_websocket", json.dumps(data))


@concurrent
def websocket_end(flow: mitmproxy.http.HTTPFlow):
    # 更新websocket连接状态
    data = {
        'type': 'websocket',
        'live': True,
        'client_id': flow.client_conn.id,
        'server_id': flow.server_conn.id,
        'server_host': flow.server_conn.address[0],
        'server_port': flow.server_conn.address[1],
    }
    db['connections'].update_one(data, {'$set': {'live': False, 'timestamp_end': time.time()}})
    data['_id'] = str(websocket_conns_dict.pop(flow.client_conn.id + flow.server_conn.id, ''))
    data['live'] = False
    rc.publish("mloger:imws_websocket", json.dumps(data))
