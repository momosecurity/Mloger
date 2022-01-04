import os
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path

from utils.log import logger

CURRENT_PATH = Path(__file__).parent
HTTP_SCRIPT_FILE = CURRENT_PATH / 'http_mitm_script.py'
SOCKS5_SCRIPT_FILE = CURRENT_PATH / 'socks5_mitm_script.py'

mitmdump_path = os.path.join(os.path.dirname(sys.executable), "mitmdump")


class ProxyServer:

    def __init__(self):
        super().__init__()
        cfg = ConfigParser()
        cfg.read('./config/config.ini')
        self.http_proxy_switch = bool(int(cfg.get('mitm', 'http_switch')))
        self.socks5_proxy_switch = bool(int(cfg.get('mitm', 'socks5_switch')))
        self.http_proxy_port = str(cfg.get('mitm', 'http_port'))
        self.socks5_proxy_port = str(cfg.get('mitm', 'socks5_port'))
        self._http_proxy_server_process = None
        self._socks5_proxy_server_process = None

    def start(self):
        mitm_arguments = [
            '-s', str(HTTP_SCRIPT_FILE),
            '--listen-host', '0.0.0.0',
            '-p', str(self.http_proxy_port),
            # '--set', 'confdir=/root/.mitmproxy/',
            '> ./log/http.log'
        ]
        if self.http_proxy_switch:
            self._http_proxy_server_process = subprocess.Popen(f'{mitmdump_path} {" ".join(mitm_arguments)}',
                                                               shell=True)
            logger.warning(f'start http proxy on 8081 port, pid {self._http_proxy_server_process.pid}')
        mitm_arguments = [
            '-s', str(SOCKS5_SCRIPT_FILE),
            '--listen-host', '0.0.0.0',
            '-p', str(self.socks5_proxy_port),
            # '--set', 'confdir=/root/.mitmproxy/',
            '--mode', 'socks5',
            '--rawtcp',
            '> ./log/socks.log'
        ]
        if self.socks5_proxy_switch:
            self._socks5_proxy_server_process = subprocess.Popen(f'{mitmdump_path} {" ".join(mitm_arguments)}',
                                                                 shell=True)
            logger.warning(f'start socks proxy on 8082 port, pid {self._socks5_proxy_server_process.pid}')

    def stop(self):
        if self._http_proxy_server_process:
            self._http_proxy_server_process.terminate()
            logger.warning(f'http ProxyServer {self._http_proxy_server_process.pid} shutdown')
        if self._socks5_proxy_server_process:
            self._socks5_proxy_server_process.terminate()
            logger.warning(f'socks ProxyServer {self._socks5_proxy_server_process.pid} shutdown')
