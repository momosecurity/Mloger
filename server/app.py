import os
import signal
from configparser import ConfigParser

from web_server.api import socketio, app
from utils.log import logger
from proxy.proxy_server import ProxyServer
from task_server.task import BackgroundTaskServer
from task_server.match import add2apis, timeout_for_ip_acl

server = {}


def start_server():
    for name in server:
        logger.warning(f'start {name}')
        server[name].start()


def stop_server():
    for name in server:
        logger.warning(f'stop {name}')
        server[name].stop()


def signal_handler(signum, frame):
    stop_server()
    logger.warning('!!!Ctrl-C pressed. Stop!!!')
    os._exit(0)


def init_task():
    server['task'].add_task('归类api', add2apis)
    server['task'].add_task('自动过期代理ip权限', timeout_for_ip_acl)


def background_server():
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        return
    server['proxy'] = ProxyServer()
    server['task'] = BackgroundTaskServer()
    start_server()
    init_task()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_web_cofnig():
    cfg = ConfigParser()
    cfg.read('./config/config.ini')
    _host = cfg.get('web', 'listen_host')
    _port = int(cfg.get('web', 'listen_port'))
    _debug = bool(int(cfg.get('web', 'debug')))
    return _host, _port, _debug


if __name__ == '__main__':
    background_server()
    host, port, debug = get_web_cofnig()
    socketio.run(app, host=host, port=port, debug=debug)
