#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import datetime
import json
import re
from concurrent.futures import ThreadPoolExecutor
from itertools import product

import requests
import urllib3
from hyper import HTTP20Connection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Repeater(object):
    """docstring for repeater"""

    def __init__(self, db, _request, target_host, target_port, is_https, deal, client_ip,
                 describe, concurrent_num=0, keepua=None, concurrent_options=None):
        super(Repeater, self).__init__()
        self.db = db
        self.describe = describe
        self.proxy = {}
        self.inserted_id = None

        # 这里目前只初始化，真实的值根据header中的Host来决定
        self.scheme = 'https' if is_https else 'http'
        self.host = target_host
        self.port = str(target_port)

        self.method = ''
        self.path = ''
        self.http_version = ''
        self.headers = {}
        self.content = ''
        self.text = None

        self.cookies = None
        self.key = None
        self.deal = True if deal == '1' or deal == True else False
        self.keepua = keepua if keepua is not None else self.deal
        self.init_request(_request)
        # 获取url的功能描述
        self.get_current_req_describe()

        self.res = None
        self.res_text = None
        self.response = None

        self.url = self.scheme + '://' + self.host + ':' + self.port + self.path
        self.client_ip = client_ip

        self.concurrent_num = 0 if concurrent_num < 0 else concurrent_num
        self.concurrent_result = None
        self.concurrent_data = []
        self.concurrent_options = concurrent_options

        self.payload = []
        self.concurrent_url = []
        self.concurrent_headers = []
        self.concurrent_content = []

    def init_request(self, _request):
        data = re.split(r'(?<!\\)\n', _request.replace('\r\n', '\n'))
        if re.match('^(GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH) *(.*?) *HTTP/(\d\.\d)$', data[0]):
            self.method = data[0].split(' ')[0]
            self.path = data[0].split(' ')[1]
            self.http_version = data[0].split(' ')[2]
        else:
            print('error')
        for d in range(1, len(data)):
            if data[d] == '':
                self.content = '\r\n'.join(data[d + 1:])
                break
            try:
                tmp_kv = re.findall('^ *(.*?) *: *(.*?) *$', data[d])
                if tmp_kv[0][0].lower() == 'content-length' or (
                        tmp_kv[0][0].lower() == 'user-agent' and not self.keepua):
                    continue
                if tmp_kv[0][0].lower() == 'cookie':
                    self.headers['cookie'] = tmp_kv[0][1]
                else:
                    self.headers[tmp_kv[0][0]] = tmp_kv[0][1]
            except Exception as e:
                raise Exception(f"init_request re find headers error :{e}")
        if 'Host' in self.headers:
            self.host = self.headers['Host'].split(':')[0]
            if len(self.headers['Host'].split(':')) == 2:
                self.port = self.headers['Host'].split(':')[1]
            self.headers['Host'] = self.host

        self.deal_third_id_and_cookie()

    def decode_response(self, content):
        try:
            return json.dumps(json.loads(content), ensure_ascii=False)
        except:
            if type(content) is str:
                return content.encode().decode('unicode_escape', 'replace')
            else:
                return content.decode('unicode_escape', 'replace')

    def show_request(self):
        print(self.method, self.host, self.path, self.http_version, self.headers, self.content)

    def go(self):
        if self.concurrent_num == 0:
            self.base_go()
        elif self.concurrent_num > 0:
            self.concurrent_go()
        else:
            raise Exception('concurrent_num < 0')

    def base_go(self):
        try:
            self.deal_mzip()
            if self.http_version == '2.0':
                conn = HTTP20Connection(host=self.host, secure=self.scheme == 'https')
                h2_response = conn.request(method=self.method, url=self.path, headers=self.headers,
                                           body=self.text.encode('utf-8'))
                res = conn.get_response(h2_response)
                self.res = {'status_code': res.status, 'reason': res.reason, 'content': res.read(),
                            'text': res.read()}
            else:
                self.res = requests.request(method=self.method, url=self.url, headers=self.headers,
                                            data=self.text.encode(), verify=False, proxies=self.proxy)
            self.deal_res()
        except Exception as e:
            raise e
        finally:
            if self.res is not None:
                self.response = {"content": self.decode_response(self.res_text), "headers": dict(self.res.headers),
                                 "http_version": self.http_version, "status_code": self.res.status_code,
                                 "reason": self.res.reason}
            rep = self.db['repeater'].insert_one(
                {"method": self.method, "scheme": self.scheme, "host": self.host, "port": self.port, "path": self.path,
                 "http_version": self.http_version, "headers": self.headers, "content": self.content,
                  "cookie": self.cookies,
                 "text": self.text, 'response': self.response, "client_ip": self.client_ip, "describe": self.describe,
                 "api_describe": self.api_describe})
            self.inserted_id = rep.inserted_id

    def base_concurrent(self, num_id):
        timestamp = datetime.datetime.now()
        res = requests.request(method=self.method,
                               url=self.concurrent_url[num_id] if len(self.concurrent_url) > 0 else self.url,
                               headers=self.concurrent_headers[num_id] if len(
                                   self.concurrent_headers) > 0 else self.headers,
                               data=self.concurrent_content[num_id] if len(self.concurrent_content) > 0 else self.text,
                               verify=False)
        return num_id + 1, res, timestamp

    def generate(self, data):
        data = data.split('§')
        result = []
        if self.concurrent_options['type'] == 'sniper':
            assert len(self.concurrent_options['payload']) > 0
            for x in range(0, int(len(data) / 2)):
                for i in self.concurrent_options['payload'][0]:
                    self.payload.append(str(i))
                    payload = ''.join(data[:2 * x + 1]) + str(i) + ''.join(data[2 * x + 2:])
                    result.append(payload)
        elif self.concurrent_options['type'] == 'battering ram':
            assert len(self.concurrent_options['payload']) > 0
            for i in self.concurrent_options['payload'][0]:
                self.payload.append(str(i))
                payload = ''
                for x in range(0, int(len(data) / 2)):
                    payload += data[2 * x] + str(i)
                payload += data[-1]
                result.append(payload)
        elif self.concurrent_options['type'] == 'pitchfork':
            assert len(self.concurrent_options['payload']) > 0 and len(self.concurrent_options['payload']) == int(
                len(data) / 2)
            for payload_no in range(len(self.concurrent_options['payload'][0])):
                payload = ''
                tmp_p = ''
                for x in range(0, int(len(data) / 2)):
                    payload += data[2 * x] + self.concurrent_options['payload'][x][payload_no]
                    tmp_p += self.concurrent_options['payload'][x][payload_no] + ' '
                payload += data[-1]
                self.payload.append(tmp_p)
                result.append(payload)
        elif self.concurrent_options['type'] == 'cluster bomb':
            assert len(self.concurrent_options['payload']) > 0 and len(self.concurrent_options['payload']) == int(
                len(data) / 2)
            payload_bomb = product(*self.concurrent_options['payload'])
            for i in payload_bomb:
                payload = ''
                for x in range(0, int(len(data) / 2)):
                    payload += data[2 * x] + i[x]
                payload += data[-1]
                self.payload.append(''.join(i))
                result.append(payload)

        return result

    def concurrent_go(self):
        try:
            if self.concurrent_options:
                if '§' in self.url and '§' not in self.content:
                    self.concurrent_url = self.generate(self.url)
                    pass
                elif '§' not in self.url and '§' in self.content:
                    self.concurrent_content = self.generate(self.content)
                    pass
                elif '§' in self.url and '§' in self.content:
                    result = self.generate(self.url + '_mloger_split_' + self.content)
                    for i in result:
                        self.concurrent_url.append(i.split('_mloger_split_')[0])
                        self.concurrent_content.append(i.split('_mloger_split_')[1])
                elif '§' not in self.url and '§' not in self.content and '§' in json.dumps(self.headers, ensure_ascii=False):
                    result = self.generate(json.dumps(self.headers, ensure_ascii=False))
                    for i in result:
                        self.concurrent_headers.append(json.loads(i))
                else:
                    pass
            self.deal_mzip()
            with ThreadPoolExecutor(max_workers=15) as executor:
                self.concurrent_result = executor.map(self.base_concurrent, [i for i in range(self.concurrent_num)])
        except Exception as e:
            raise e
        all_repeater_data = []
        for result in self.concurrent_result:
            num_id, res, timestamp = result
            if num_id == 1:
                self.response = {"content": '', "headers": dict(res.headers), "http_version": self.http_version,
                                 "status_code": res.status_code, "reason": res.reason}
            if res is not None:
                self.res = res
                self.deal_res()
                text = self.res_text
                text = self.decode_response(text)
                self.response['content'] += (self.payload[num_id - 1] if len(
                    self.payload) > 0 else 'None') + text + '\n'
                self.concurrent_data.append(
                    {'num_id': num_id, 'content': text, 'status_code': res.status_code, 'headers': dict(res.headers),
                     'http_version': self.http_version, 'reason': res.reason,
                     'payload': self.payload[num_id - 1] if len(self.payload) > 0 else 'None', "timestamp": timestamp})
                all_repeater_data.append(
                    {"method": self.method, "scheme": self.scheme, "host": self.host, "port": self.port,
                     "path": self.path,
                     "http_version": self.http_version,
                     "headers": self.concurrent_headers[num_id - 1] if len(
                         self.concurrent_headers) > 0 else self.headers,
                     "content": self.content,
                     "cookie": self.cookies,
                     "text": self.concurrent_content[num_id - 1] if len(self.concurrent_content) > 0 else self.text,
                     "payload": self.payload[num_id - 1] if len(self.payload) > 0 else 'None',
                     "num_id": num_id,
                     'response': {"content": text, "headers": dict(res.headers), "http_version": self.http_version,
                                  "status_code": res.status_code, "reason": res.reason}, "client_ip": self.client_ip,
                     "describe": self.describe,
                     "api_describe": self.api_describe})

            else:
                self.response['content'] += '\n'
                self.concurrent_data.append(
                    {'num_id': num_id, 'content': 'None', 'status_code': 'None', 'headers': {}, 'http_version': 'None',
                     'reason': 'None', 'payload': 'None', "timestamp": "None"})
                all_repeater_data.append(
                    {"method": self.method, "scheme": self.scheme, "host": self.host, "port": self.port,
                     "path": self.path,
                     "http_version": self.http_version,
                     "headers": self.concurrent_headers[num_id - 1] if len(
                         self.concurrent_headers) > 0 else self.headers,
                     "content": self.content,
                     "cookie": self.cookies,
                     "text": self.concurrent_content[num_id - 1] if len(self.concurrent_content) > 0 else self.text,
                     "payload": self.payload[num_id - 1] if len(self.payload) > 0 else 'None',
                     "num_id": num_id,
                     'response': {"content": 'None', "headers": {}, "http_version": 'None',
                                  "status_code": 'None', "reason": 'None'}, "client_ip": self.client_ip,
                     "describe": self.describe,
                     "api_describe": self.api_describe})
        rep = self.db['repeater'].insert_one(
            {"method": self.method, "scheme": self.scheme, "host": self.host, "port": self.port, "path": self.path,
             "http_version": self.http_version, "headers": self.headers, "content": self.content,
              "cookie": self.cookies,
             "text": self.text, 'response': self.response, "client_ip": self.client_ip, "describe": self.describe,
             "api_describe": self.api_describe})
        self.inserted_id = rep.inserted_id
        for request_data in all_repeater_data:
            request_data['overview_repeater_id'] = str(self.inserted_id)
            self.db['repeater'].insert_one(request_data)
        return self.concurrent_data

    def deal_mzip(self):
        self.text = self.content
        return

    def deal_res(self):
        self.res_text = self.res.text
        return

    def deal_third_id_and_cookie(self):
        pass

    def deal_third_req(self, mzip):
        pass

    def get_current_req_describe(self):
        path = self.path.split('?')[0]
        api = self.db['apis'].find_one({'path': path, 'host': self.host, 'describe': {'$ne': None}})
        if api:
            self.api_describe = api['describe']
        else:
            self.api_describe = None
