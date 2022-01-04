from gevent import monkey

from utils.common import replaceD

monkey.patch_all()

import json
import base64
import os
import time
import traceback
from urllib.parse import unquote

from cachetools import TTLCache, cached
from bson import ObjectId
from flask import Flask, request, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
from flask_login import AnonymousUserMixin, LoginManager, login_required, UserMixin, current_user
from flask_session import RedisSessionInterface
from flask_socketio import SocketIO, disconnect, emit, send
from flask_mongoengine import MongoEngine

from db.mongo_db import get_mongo_client
from db.redis_db import get_redis_client, get_redis_client_for_flask, get_redis_url
from utils.ProtocUtil import ParseData, ProtocEncode
from utils.log import logger
from utils.repeater import Repeater
from utils.proxypriv import get_client_ip_list

db = get_mongo_client()
rc = get_redis_client()

template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
template_dir = os.path.join(template_dir, 'front/dist')
app = Flask(__name__, static_folder=template_dir, template_folder=template_dir, static_url_path='')
app.debug = True
app.jinja_env.auto_reload = True
app.secret_key = 'UWlyLon09UEyinBmmrk6hTPcbC4FZjQzvkE1XZVkxQbTkpK'
app.logger = logger


class MlogerDefaultUser(AnonymousUserMixin):
    def __init__(self):
        self.user = {'name': 'admin'}


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.anonymous_user = MlogerDefaultUser
auth = HTTPBasicAuth()

app.session_interface = RedisSessionInterface(get_redis_client_for_flask(), use_signer=True,
                                              key_prefix='flask_session_')
# app.register_blueprint(blue_web)
MongoEngine(app)
socketio = SocketIO(app, path='/api/logerws', cors_allowed_origins='*', engineio_logger=logger, async_mode='gevent',
                    message_queue=get_redis_url())


# 通用函数
@login_manager.user_loader
def load_user(user_id):
    return MlogerDefaultUser()


def get_remote_addr():
    """获取用户ip"""
    return request.headers.get('X-Real-Ip', request.remote_addr)


def pretty_content(content):
    """美化content字段"""
    try:
        result = json.dumps(json.loads(content), indent=4, ensure_ascii=False)
    except:
        try:
            content = base64.b64decode(content, validate=True).decode()
            result = json.dumps(json.loads(content), indent=4, ensure_ascii=False)
            # result = json.dumps(json.loads(content), indent=4).encode().decode(
            #     "unicode_escape")
        except:
            if type(content) is str:
                result = content.encode().decode("unicode_escape")
            else:
                result = content.decode("unicode_escape")
    return result


def get_request(request):
    """把请求转换成要展示的格式"""
    if not request:
        return {}
    request['_id'] = request['_id'].__str__()
    for key in request:
        if type(request[key]) is ObjectId:
            logger.debug('request ObjectId type' + key)
    return request


def get_response(response, pretty=True):
    """把响应转换成要展示的格式"""
    if not response:
        return {}
    response['_id'] = response.get('_id', '').__str__()
    response['req_id'] = response.get('req_id', '').__str__()
    if 'content' not in response or response['content'] is None:
        logger.debug('get_response not found response content ' + response['_id'])
        response['content'] = ''
        return response
    # 优化展示
    if pretty:
        response['content'] = pretty_content(response['content'])
    else:
        try:
            json.loads(response['content'])
            response['content'] = json.dumps(json.loads(response['content']), ensure_ascii=False)
            # response['content'] = response['content'].encode().decode("unicode_escape")
        except:
            try:
                response['content'] = base64.b64decode(response['content'], validate=True).decode()
                response['content'] = response['content'].encode().decode("unicode_escape")
            except:
                if type(response['content']) is str:
                    response['content'] = response['content'].encode().decode("unicode_escape")
                else:
                    response['content'] = response['content'].decode("unicode_escape")
    for key in response:
        if type(response[key]) is ObjectId:
            logger.debug('response ObjectId type' + key)
    return response


def get_message(message):
    """把消息转换成要展示的格式"""
    if not message:
        return {}
    message['_id'] = message.pop('_id').__str__()
    message['conn_id'] = message.pop('conn_id', '').__str__()

    # 转为byte处理一次pb
    if type(message['content']) is str:
        try:
            byte_content = base64.b64decode(message['content'], validate=True)
            message['content'] = byte_content
        except:
            byte_content = message['content'].encode()
        message_format = {}
        succ = ParseData(byte_content, 0, len(byte_content), message_format)
        if succ:
            message['content'] = json.dumps(message_format, indent=4, sort_keys=True, ensure_ascii=False)
            return message
    # pb解析失败再处理bytes
    if type(message['content']) is bytes:
        try:
            message['content'] = message['content'].decode()
        except:
            try:
                message['content'] = message['content'].decode('unicode_escape')
            except:
                message['content'] = message['content'].decode('latin-1')

    return message


# web API接口
@app.route('/', methods=['GET'])
def index():
    # return 'It works'+str(current_user.user)
    return render_template('index.html', username=current_user.user['name'])


# 全局准入代理功能
@app.route('/api/get_client_ip', methods=['POST'])
def get_client_ip():
    """准入代理获取客户端ip列表"""
    data = get_client_ip_list()
    intercept_status = rc.hgetall('mloger:intercept:client')
    for d in data:
        tmp_v = json.loads(data[d])
        tmp_v["intercept_status"] = 1 if intercept_status.get(d, 0) != 0 else 0
        data[d] = json.dumps(tmp_v)
    return jsonify(code=200, status=0, message='ok', data=data)


@app.route('/api/set_client_ip_allowed', methods=['POST'])
def set_client_ip_allowed():
    """授权准入"""
    params = request.json
    if params is None:
        return jsonify(code=200, status=500, message='params error', data={}), 500
    ip = params.get('ip', None)
    if ip:
        rc.hset("mloger:mitmproxy:auth:hash", ip,
                json.dumps({'dt': int(time.time()), 'status': 1, 'user_name': current_user.user['name']}))
        db['user_allow_ip_log'].insert_one(
            {'dt': int(time.time()), 'client_ip': ip, 'user_name': current_user.user['name'], "action": "set"})
        logger.warning("{user}授权了{client_ip}".format(user=current_user.user['name'], client_ip=ip))
    return jsonify(code=200, status=0, message='ok', data={})


@app.route('/api/cancel_client_ip_allowed', methods=['POST'])
def cancel_client_ip_allowed():
    """撤销准入授权"""
    params = request.json
    if params is None:
        return jsonify(code=200, status=500, message='params error', data={}), 500
    ip = params.get('ip', None)
    if ip:
        data = rc.hget("mloger:mitmproxy:auth:hash", ip)
        if data:
            rc.hset("mloger:mitmproxy:auth:hash", ip,
                    json.dumps({'dt': int(time.time()), 'status': 0}))
            db['user_allow_ip_log'].insert_one(
                {'dt': int(time.time()), 'client_ip': ip, 'user_name': current_user.user['name'], "action": "cancel"})
            logger.warning("{user}撤销了{client_ip}".format(user=current_user.user['name'], client_ip=ip))
    return jsonify(code=200, status=0, message='ok', data={})


# HTTP拦截功能
def get_next(now_id=None, now_type=None):
    """获取下一条要展示的HTTP流量"""
    if now_id and now_type == 'req':
        now_req = db['intercept'].find_one({'flow_id': ObjectId(now_id)})
        if 'wait_response' in now_req and now_req['wait_response']:
            while 1:
                res = db['response_data'].find_one({'req_id': ObjectId(now_id)})
                if res:
                    d = db['response_data_text_map'].find_one({'data_id': res['_id']})
                    if not res['crypto'] or res['crypto'] and d:
                        res = get_response(res, pretty=False)
                        return {'type': 'res', 'data': res}
                time.sleep(0.1)
    while 1:
        req = db['request_data'].find_one(
            {'user_name': current_user.user['name'], 'intercept': True, 'isshow': None, 'exclude': False})
        if req:
            db['request_data'].update_one({'_id': req['_id']}, {'$set': {'isshow': True}})
            req = get_request(req)
            return {'type': 'req', 'data': req}
        time.sleep(0.1)


@app.route('/api/intercept', methods=['GET', 'POST'])
def intercept():
    """开启/关闭拦截"""
    params = request.json
    if params is None:
        params = {}
    status = params.get("status", 'off')
    if status not in ['on', 'off']:
        return jsonify(code=200, status=500, message='status error'), 500
    client_ip = params.get("client_ip", '')
    if client_ip == '':
        return jsonify(code=200, status=500, message='require args'), 500
    data = {}
    if status == 'on':
        rc.hset('mloger:intercept:client', client_ip, current_user.user['name'])
        rc.set('mloger:intercept:request:' + client_ip, 1, 3600)
        data = get_next()
    elif status == 'off':
        rc.hdel('mloger:intercept:client', client_ip, current_user.user['name'])
        rc.delete('mloger:intercept:request:' + client_ip)
        flows = list(db['request_data'].find(
            {'user_name': current_user.user['name'], 'intercept': True, 'wait_response': True, 'isshow': None}))
        for flow in flows:
            res = db['response_data'].find_one({'_id': flow['_id']})
            db['intercept'].insert_one(
                {'client_ip': client_ip, 'type': 'requests', 'flow_type': 'res', 'flow_id': res['_id'], 'forward': True,
                 'wait_response': False, 'edited': False, 'response': res['content'],
                 'response_edited': res['content']})
            rc.publish('intercept', json.dumps(
                {'client_ip': client_ip, 'type': 'requests', 'flow_type': 'res', 'flow_id': str(res['_id']),
                 'forward': True,
                 'wait_response': False, 'edited': False, 'response': res['content'],
                 'response_edited': res['content']}))
        flows = list(
            db['request_data'].find({'user_name': current_user.user['name'], 'intercept': True, 'isshow': None}))
        for req in flows:
            db['intercept'].insert_one(
                {'client_ip': client_ip, 'type': 'requests', 'flow_type': 'req', 'flow_id': req['_id'], 'forward': True,
                 'wait_response': False, 'edited': False, 'request': req['content'], 'request_edited': req['content']})
            db['request_data'].update_one({'_id': req['_id']}, {'$set': {'isshow': True}})
            rc.publish('intercept', json.dumps(
                {'client_ip': client_ip, 'type': 'requests', 'flow_type': 'req', 'flow_id': str(req['_id']),
                 'forward': True,
                 'wait_response': False, 'edited': False, 'request': req['content'], 'request_edited': req['content']}))
    return jsonify(code=200, status=0, message='ok', data=data)


@app.route('/api/intercept_op', methods=['GET', 'POST'])
def intercept_op():
    """放过/丢弃数据包"""
    params = request.json
    flow_id = params.get('id', None)
    forward = params.get('forward', False)
    wait_response = params.get('wait_response', False)
    flow_type = params.get('type', 'req')
    flow_content = params.get('flow_content', '')
    mzip = params.get('mzip', True)
    edited = params.get('edited', True)
    _request = unquote(base64.b64decode(flow_content).decode())
    if not flow_id:
        return jsonify(code=200, status=500, message='not found flow_id'), 500
    intercept = db['intercept'].find_one({'user_name': current_user.user['name'], 'type': 'requests'})
    client_ip = intercept['client_ip'] if intercept else ''
    if flow_type == 'req':
        req = db['request_data'].find_one({'_id': ObjectId(flow_id)}, {'update_time': 0})
        repeater = Repeater(db=db, _request=_request, target_host=req['host'], target_port=req['port'],
                            is_https=True if req['scheme'] == 'https' else False,
                            deal=False, client_ip=get_remote_addr(),
                            describe="intercept_op")
        content = repeater.content
        req = get_request(req)
        db['intercept'].insert_one(
            {'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': ObjectId(flow_id),
             'forward': forward, 'wait_response': wait_response, 'edited': edited, 'request': req['content'],
             'request_edited': content})
        if wait_response:
            rc.set('mloger:intercept:wait_response:' + flow_id, 1, 300)
        logger.info(json.dumps({'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': flow_id,
                                'forward': forward, 'wait_response': wait_response, 'edited': edited,
                                'request': req['content'],
                                'request_edited': content}))
        rc.publish('intercept',
                   json.dumps({'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': flow_id,
                               'forward': forward, 'wait_response': wait_response, 'edited': edited,
                               'request': req['content'],
                               'request_edited': content}))
    if flow_type == 'res':
        data = _request.split('\r\n\r\n')
        if len(data) < 2:
            data = _request.split('\n\n')
        content = data[-1]
        res = db['response_data'].find_one({'_id': ObjectId(flow_id)}, {'update_time': 0})
        while 1:
            req = db['request_data'].find_one({'_id': res['req_id']})
            if req:
                break
            logger.warning('拦截操作响应时找不到对应的请求')
            time.sleep(0.5)
        logger.info(json.dumps({'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': flow_id,
                                'forward': forward, 'wait_response': wait_response, 'edited': edited,
                                'response': res['content'],
                                'response_edited': content}))
        db['intercept'].insert_one(
            {'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': ObjectId(flow_id),
             'forward': forward, 'wait_response': wait_response, 'edited': edited, 'response': res['content'],
             'response_edited': content})
        rc.publish('intercept',
                   json.dumps({'client_ip': client_ip, 'type': 'requests', 'flow_type': flow_type, 'flow_id': flow_id,
                               'forward': forward, 'wait_response': wait_response, 'edited': edited,
                               'response': res['content'],
                               'response_edited': content}))
    data = get_next(flow_id, flow_type)
    return jsonify(code=200, status=0, message='ok', data=data)


# HTTP记录功能
@app.route('/api/edit_req_describe', methods=['POST'])
def edit_req_describe():
    """修改接口描述"""
    params = request.json
    _id = params.get("id", None)
    describe = params.get("describe", None)
    if not (_id and describe):
        return jsonify(code=200, status=500, message='require args'), 500
    req = db['request_data'].find_one({'_id': ObjectId(_id)})
    if not req:
        return jsonify(code=200, status=500, message='id error'), 500
    db['request_data'].update_one({'_id': ObjectId(_id)}, {'$set': {'describe': describe}})
    path = req["path"].split('?')[0]
    rd_path = replaceD(path)
    db['request_data'].update_many({'path': {'$regex': path}, 'describe': None}, {'$set': {'describe': describe}})
    db['apis'].update_one({'host': req['host'], 'rd_path': rd_path}, {'$set': {'describe': describe}})
    return jsonify(code=200, status=0, message='ok', data={})


# HTTP重放
@app.route('/api/repeater_go', methods=['POST'])
def repeater_go():
    """重放请求"""
    params = request.json
    keepua = params.get('keepua', None)
    concurrent_num = int(params.get('concurrent_num', 0))
    payload = params.get('payload', [])
    options_type = params.get('type', None)
    options = {}
    if options_type:
        options['type'] = options_type
        options['payload'] = payload
    if set(['request', 'host', 'port', 'ishttps']) > set(params.keys()):
        return jsonify(code=200, status=500, message='require args'), 500
    _request = params['request']
    repeater = Repeater(db=db, _request=_request, target_host=params['host'], target_port=params['port'],
                        is_https=params['ishttps'], deal=False,
                        client_ip=get_remote_addr(), describe="user_repeater", concurrent_num=concurrent_num,
                        keepua=keepua, concurrent_options=options)
    if concurrent_num == 0:
        repeater.go()
        response = repeater.response
        response = get_response(response)
        return jsonify(code=200, status=0, message='ok', data={"response": response})
    elif concurrent_num > 0:
        data = repeater.concurrent_go()
        return jsonify(code=200, status=0, message='ok', data={"data": data})
    else:
        return jsonify(code=200, status=500, message='concurrent_num < 0'), 500


@app.route('/api/repeater_history', methods=['POST'])
def repeater_history():
    """获取重放记录"""
    # params = request.json
    # page = int(params.get("page", None)) if params.get("page", None) and int(params.get("page", None)) > 1 else 1
    # size = int(params.get("size", None)) if params.get("size", None) and int(params.get("size", None)) > 0 else 10
    history = list(
        db['repeater'].find({"describe": "user_repeater", "overview_repeater_id": None}, sort=[('_id', -1)]).limit(
            20))
    count = 0
    result = []
    for req in history:
        req['_id'] = req['_id'].__str__()
        response = req.pop('response') if req['response'] else {}
        response = get_response(response)
        result.append({'request': req, 'response': response})
    return jsonify(code=200, status=0, message='ok', data={'history': result, 'count': count})


@app.route('/api/repeater_get', methods=['GET', 'POST'])
def repeater_get():
    """查看请求详情"""
    req_id = request.args.get("id")
    if req_id is None:
        return jsonify(code=200, status=500, message='params error', data=[{}]), 500
    repeater_data = db['repeater'].find_one({'_id': ObjectId(req_id)})
    if repeater_data:
        all_repeater_list = list(
            db['repeater'].find({'overview_repeater_id': str(repeater_data['_id'])}, sort=[('num_id', 1)]))
        result = []
        if len(all_repeater_list) < 1:
            all_repeater_list = [repeater_data]
        else:
            all_repeater_list.insert(0, repeater_data)
        for repeater_data in all_repeater_list:
            repeater_data['_id'] = str(repeater_data['_id'])
            response = repeater_data.pop('response') if repeater_data['response'] else {}
            response = get_response(response)
            result.append({'request': repeater_data, 'response': response})
        return jsonify(code=200, status=0, message='ok', data=result)
    else:
        req = db['request_data'].find_one({'_id': ObjectId(req_id)}, {'update_time': 0})
        if req:
            response = db['response_data'].find_one({'req_id': req['_id']}, {"update_time": 0})
            response = get_response(response)
            req = get_request(req)
            return jsonify(code=200, status=0, message='ok', data=[{'request': req, 'response': response}])
        else:
            api = db['apis'].find_one({'_id': ObjectId(req_id)})
            if api:
                api = get_request(api)
                return jsonify(code=200, status=0, message='ok', data=[{'request': api, 'response': {}}])
            else:
                return jsonify(code=200, status=0, message='not found', data=[{}])


@app.route('/api/repeater_share', methods=['POST'])
def share_request():
    return jsonify(code=200, status=0, message='ok', data={})


# TCP/WS测试
@app.route('/api/imws_repeater_go', methods=['GET', 'POST'])
def imws_repeater_go():
    """重放消息"""
    params = request.json
    conn_id = params.get('conn_id', None)
    flow_content = params.get('flow_content', None)
    direction = params.get('direction', 'send')
    concurrent_num = int(params.get('concurrent_num', 0))
    if flow_content is None:
        return jsonify(code=200, status=500, message='require flow_content'), 400
    conn = db['connections'].find_one({'_id': ObjectId(conn_id), 'live': True})
    if not conn:
        return jsonify(code=200, status=500, message='conn not exists or deaded'), 400
    mes_type = conn['type']
    # 判断是否为pb格式
    ispb = "embedded message" in flow_content
    if ispb:
        flow_content_pb_list = []
        ProtocEncode(json.loads(flow_content), flow_content_pb_list)
        flow_content = base64.b64encode(bytes(flow_content_pb_list)).decode()

    # 需要做特殊处理可以在这里做
    db['inject_repeater'].insert_one(
        {'client_id': conn['client_id'], 'server_id': conn['server_id'], 'direction': direction,
         'content': flow_content, 'type': mes_type, 'concurrent_num': concurrent_num})
    return jsonify(code=200, status=0, message='ok', data={})


# 历史记录

@app.route('/api/search', methods=['GET', 'POST'])
def search():
    """历史记录查询"""
    params = request.json
    if params is None:
        return jsonify(code=200, status=500, message='params error', data={}), 500
    keyword = params.get("keyword")
    # 加上双引号精确查询
    if not keyword.startswith('"') or not keyword.endswith('"'):
        keyword = '"' + keyword + '"'
    search_type = params.get("type", 'all')
    page = int(params.get("page", 1))
    size = int(params.get("size", 20))
    _id = None
    try:
        _id = ObjectId(keyword)
    except:
        pass
    data = {'data': [], 'count': 0}
    reqs_current_count = 0
    if search_type == 'logger' or search_type == 'all':
        if _id:
            reqs = db['request_data'].find_one({"_id": _id}, {'update_time': 0}, sort=[('_id', -1)])
            reqs = [reqs] if reqs else []
            reqs_count = len(reqs)
            reqs_current_count = len(reqs)
        else:
            reqs = db['request_data'].find(
                {"$text": {'$search': keyword}},
                {'update_time': 0}, sort=[('_id', -1)]).limit(size).skip((page - 1) * size)
            reqs_count = reqs.count()
            reqs_current_count = reqs.count(True)
        for req in list(reqs):
            response = db['response_data'].find_one({'req_id': req['_id']}, {"update_time": 0})
            response = get_response(response)
            req = get_request(req)
            data['data'].append({'request': req, 'response': response, 'type': 'logger'})
        data['logger_count'] = reqs_count
        data['count'] += reqs_count
    if search_type == 'repeater' or search_type == 'all':
        enough = reqs_current_count >= size
        if 'logger_count' in data and not enough:
            page -= int(data['logger_count'] / size)
            size -= data['logger_count'] % size
        if _id:
            history = db['repeater'].find_one({"describe": "user_repeater", "_id": _id})
            history = [history] if history else []
            repeater_count = len(history)
            reqs_current_count += repeater_count
        else:
            history = db['repeater'].find({"describe": "user_repeater",
                                           "$text": {'$search': keyword}, "overview_repeater_id": None},
                                          sort=[('_id', -1)]).limit(size).skip((page - 1) * size)
            repeater_count = history.count()
            reqs_current_count += history.count(True)
        if not enough:
            for req in list(history):
                req['_id'] = req['_id'].__str__()
                response = req.pop('response') if req['response'] else {}
                try:
                    response['content'] = response['content'].encode().decode('unicode_escape')
                except:
                    pass
                data['data'].append({'request': req, 'response': response, 'type': 'repeater'})
        data['repeater_count'] = repeater_count
        data['count'] += repeater_count
    if search_type == 'apis' or search_type == 'all':
        enough = reqs_current_count >= size
        if 'repeater_count' in data and not enough:
            page -= int(data['repeater_count'] / size)
            size -= data['repeater_count'] % size
        if _id:
            apis = db['apis'].find_one({'_id': _id})
            apis = [apis] if apis else []
            apis_count = len(apis)
            reqs_current_count += apis_count
        else:
            apis = db['apis'].find({"$or": [{'_id': _id}, {"$text": {'$search': keyword}}]},
                                   sort=[('_id', -1)]).limit(size).skip((page - 1) * size)
            apis_count = apis.count()
            reqs_current_count += apis.count(True)
        if not enough:
            for api in list(apis):
                api = get_request(api)
                if 'sql_taskid' in api:
                    api.pop('sql_taskid')
                data['data'].append({'request': api, 'response': {}, 'type': 'apis'})
        data['apis_count'] = apis_count
        data['count'] += apis_count
    data['type'] = search_type
    data['page'] = page
    data['size'] = size
    return jsonify(code=200, status=0, message='ok', data={'data': data})


# web socketio
# HTTP记录的socketio
@socketio.on('connect', namespace='/api/logerws')
def handle_connect():
    rc.hset('mloger:loggerws:client:filter', request.sid, '')


@socketio.on('disconnect', namespace='/api/logerws')
def handle_disconnect():
    rc.hdel('mloger:loggerws:client:filter', request.sid)
    disconnect()


@socketio.on('set_filter', namespace='/api/logerws')
def handle_set_filter(_filter):
    rc.hset('mloger:loggerws:client:filter', request.sid, _filter.get("ip", ''))


@cached(cache=TTLCache(maxsize=500, ttl=5))
def get_desc_by_path(host, path):
    path = path.split('?')[0]
    rd_path = replaceD(path)
    desc = None
    api = db['apis'].find_one({'host': host, 'rd_path': rd_path, 'describe': {'$ne': None}})
    if api:
        desc = api['describe']
    return desc


@cached(cache=TTLCache(maxsize=100, ttl=5))
def get_logger_black(user_name):
    data = list(db['user_logger_black'].find({'user_name': user_name}))
    return data


def black_filter(resp, black):
    for b in black:
        if b['host'] == resp['host'] and resp['path'].startswith(b['path']):
            return True
    return False


@socketio.on('get', namespace='/api/logerws')
def handle_get():
    ps = rc.pubsub()
    ps.subscribe('mloger:logger_request')
    try:
        while 1:
            client_ip = rc.hget('mloger:loggerws:client:filter', request.sid)
            message = ps.get_message(ignore_subscribe_messages=True, timeout=0.01)
            if message:
                resp: dict = json.loads(message['data'])
                if not resp:
                    continue
                if isinstance(resp, str):
                    resp = json.loads(resp)
                resp_client_ip = resp.get('client_ip', None)
                if client_ip and resp_client_ip and client_ip != resp_client_ip:
                    continue
                resp['pretty_text'] = resp['content']
                if resp.get('text', ''):
                    resp['pretty_text'] = pretty_content(resp.get('text'))
                try:
                    if resp.get('path') is not None:
                        if black_filter(resp, black=get_logger_black(current_user.user['name'])):
                            continue
                        resp['describe'] = get_desc_by_path(resp['host'], resp['path'])
                        if resp['describe']:
                            db['request_data'].update_one({"_id": resp['_id']},
                                                          {"$set": {"describe": resp['describe']}})
                        emit('get', {'request': resp})
                    else:
                        emit('get', {'response': resp})
                except:
                    traceback.print_exc()
                    # logger.warning(traceback.print_exc())
            else:
                time.sleep(0.02)
    except:
        pass
    finally:
        ps.close()
        disconnect()


# TCP/WS的socketio
@socketio.on('connect', namespace='/api/imws')
def handle_connect_imws():
    rc.hset('mloger:imws:client:filter', request.sid + '_ip', '')
    rc.hset('mloger:imws:client:filter', request.sid + '_type', 'all')


@socketio.on('disconnect', namespace='/api/imws')
def handle_disconnect_imws():
    rc.hdel('mloger:imws:client:filter', request.sid + '_ip')
    rc.hdel('mloger:imws:client:filter', request.sid + '_type')
    disconnect()


@socketio.on('set_filter', namespace='/api/imws')
def handle_set_filter_imws(_filter):
    rc.hset('mloger:imws:client:filter', request.sid + '_ip', _filter.get("ip", ''))
    rc.hset('mloger:imws:client:filter', request.sid + '_type', _filter.get("type", 'all'))


@socketio.on('get', namespace='/api/imws')
def handle_get_imws():
    client_ip = rc.hget('mloger:imws:client:filter', request.sid + '_ip')
    ps = rc.pubsub()
    ps.subscribe('mloger:imws_websocket')
    connections = list(db['connections'].find({'live': True, 'client_host': {'$regex': '{}'.format(client_ip)}}))
    for conn in connections:
        conn['_id'] = str(conn['_id'])
        emit('get_conn', conn)
    try:
        while 1:
            client_ip = rc.hget('mloger:imws:client:filter', request.sid + '_ip')
            mes_type = rc.hget('mloger:imws:client:filter', request.sid + '_type')

            message = ps.get_message(ignore_subscribe_messages=True, timeout=0.01)
            if message:
                resp: dict = json.loads(message['data'])
                if not resp:
                    continue
                if isinstance(resp, str):
                    resp = json.loads(resp)
                resp_client_ip = resp.get('client_ip', None)
                resp_type = resp.get('type', None)
                if client_ip and resp_client_ip and client_ip != resp_client_ip:
                    continue
                if mes_type != 'all' and resp_type and mes_type != resp_type:
                    continue
                if resp.get('live', None) is not None:
                    emit('get_conn', resp)
                    continue
                if resp.get('exclude', False):
                    continue
                if resp.get('text', None):
                    resp['content'] = resp.get('text')
                resp = get_message(resp)
                try:
                    emit('get_mes', resp)
                except:
                    logger.debug(traceback.print_exc())
            else:
                time.sleep(0.02)
    except:
        pass
    finally:
        ps.close()
        disconnect()
